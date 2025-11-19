"""
Approval Workflow API Views

REST API viewsets for approval workflow system.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q, Count, Prefetch

from floor_app.operations.approvals.models import (
    ApprovalWorkflow,
    ApprovalLevel,
    ApprovalRequest,
    ApprovalStep,
    ApprovalHistory,
    ApprovalDelegation
)
from .serializers import (
    ApprovalWorkflowSerializer,
    ApprovalLevelSerializer,
    ApprovalRequestSerializer,
    ApprovalRequestCreateSerializer,
    ApprovalStepSerializer,
    ApprovalHistorySerializer,
    ApprovalActionSerializer,
    ApprovalDelegationSerializer
)


class ApprovalWorkflowViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing approval workflows.

    list: Get all active workflows
    retrieve: Get a specific workflow with all levels
    create: Create a new workflow (admin only)
    update: Update a workflow (admin only)
    destroy: Deactivate a workflow (admin only)
    """

    queryset = ApprovalWorkflow.objects.filter(is_active=True).prefetch_related('levels__approvers')
    serializer_class = ApprovalWorkflowSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['workflow_type', 'is_active']
    search_fields = ['name', 'description']

    def get_permissions(self):
        """Only admins can create/update/delete workflows."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return super().get_permissions()

    @action(detail=True, methods=['get'])
    def levels(self, request, pk=None):
        """
        Get all levels for a workflow.

        GET /api/approval-workflows/{id}/levels/
        """
        workflow = self.get_object()
        levels = workflow.levels.all().order_by('level_number')

        serializer = ApprovalLevelSerializer(levels, many=True)
        return Response(serializer.data)


class ApprovalRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing approval requests.

    list: Get all approval requests (filtered by permissions)
    retrieve: Get a specific approval request
    create: Create a new approval request
    """

    serializer_class = ApprovalRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['status', 'priority', 'workflow']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'priority', 'submitted_at']
    ordering = ['-created_at']

    def get_queryset(self):
        """Get approval requests visible to current user."""
        user = self.request.user

        # Admin can see all requests
        if user.is_staff:
            return ApprovalRequest.objects.all().select_related(
                'workflow', 'requester'
            ).prefetch_related('steps', 'history_entries')

        # Regular users see requests where they are:
        # 1. Requester
        # 2. Approver
        # 3. In visible_to_users
        # 4. visible_to_all is True
        queryset = ApprovalRequest.objects.filter(
            Q(requester=user) |
            Q(steps__approver=user) |
            Q(visible_to_users=user) |
            Q(visible_to_all=True)
        ).distinct().select_related(
            'workflow', 'requester'
        ).prefetch_related('steps', 'history_entries')

        return queryset

    def get_serializer_class(self):
        """Use different serializer for create action."""
        if self.action == 'create':
            return ApprovalRequestCreateSerializer
        return ApprovalRequestSerializer

    def create(self, request, *args, **kwargs):
        """
        Create a new approval request.

        POST /api/approval-requests/
        Body: {
            "workflow_id": 1,
            "title": "Purchase Order #12345",
            "description": "Approve purchase of equipment",
            "priority": "HIGH",
            "metadata": {"amount": 15000, "vendor": "ACME Corp"}
        }
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        # Get workflow
        workflow = ApprovalWorkflow.objects.get(id=data['workflow_id'])

        # Create approval request
        approval_request = ApprovalRequest.objects.create(
            workflow=workflow,
            title=data['title'],
            description=data.get('description', ''),
            requester=request.user,
            priority=data.get('priority', 'NORMAL'),
            visible_to_all=data.get('visible_to_all', False),
            metadata=data.get('metadata', {})
        )

        # Set visibility
        if data.get('visible_to_department_ids'):
            from floor_app.hr.models import HRDepartment
            departments = HRDepartment.objects.filter(
                id__in=data['visible_to_department_ids']
            )
            approval_request.visible_to_departments.set(departments)

        if data.get('visible_to_user_ids'):
            from django.contrib.auth import get_user_model
            User = get_user_model()
            users = User.objects.filter(id__in=data['visible_to_user_ids'])
            approval_request.visible_to_users.set(users)

        # Initialize approval steps
        approval_request.initialize_steps()

        # Submit request
        approval_request.submit()

        output_serializer = ApprovalRequestSerializer(approval_request)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        Approve an approval request.

        POST /api/approval-requests/{id}/approve/
        Body: {
            "comments": "Approved. Looks good.",
            "metadata": {}
        }
        """
        approval_request = self.get_object()
        user = request.user

        # Check if user can approve
        if not approval_request.can_user_approve(user):
            return Response(
                {'error': 'You do not have permission to approve this request'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = ApprovalActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        comments = serializer.validated_data.get('comments', '')
        metadata = serializer.validated_data.get('metadata', {})

        # Approve request
        try:
            approval_request.approve(
                user=user,
                comments=comments,
                metadata=metadata
            )

            output_serializer = self.get_serializer(approval_request)
            return Response(output_serializer.data)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """
        Reject an approval request.

        POST /api/approval-requests/{id}/reject/
        Body: {
            "comments": "Rejected. Missing documentation.",
            "metadata": {}
        }
        """
        approval_request = self.get_object()
        user = request.user

        # Check if user can reject
        if not approval_request.can_user_approve(user):
            return Response(
                {'error': 'You do not have permission to reject this request'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = ApprovalActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        comments = serializer.validated_data.get('comments', '')
        metadata = serializer.validated_data.get('metadata', {})

        # Reject request
        try:
            approval_request.reject(
                user=user,
                comments=comments,
                metadata=metadata
            )

            output_serializer = self.get_serializer(approval_request)
            return Response(output_serializer.data)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel an approval request (requester only).

        POST /api/approval-requests/{id}/cancel/
        Body: {
            "reason": "No longer needed"
        }
        """
        approval_request = self.get_object()
        user = request.user

        # Only requester or admin can cancel
        if approval_request.requester != user and not user.is_staff:
            return Response(
                {'error': 'Only the requester can cancel this request'},
                status=status.HTTP_403_FORBIDDEN
            )

        reason = request.data.get('reason', 'Cancelled by requester')

        # Cancel request
        try:
            approval_request.cancel(cancelled_by=user, reason=reason)

            output_serializer = self.get_serializer(approval_request)
            return Response(output_serializer.data)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def pending(self, request):
        """
        Get pending approval requests for current user.

        GET /api/approval-requests/pending/
        """
        user = request.user
        queryset = self.get_queryset().filter(
            steps__approver=user,
            steps__status='PENDING',
            status='PENDING'
        ).distinct()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_requests(self, request):
        """
        Get approval requests created by current user.

        GET /api/approval-requests/my_requests/
        """
        user = request.user
        queryset = self.get_queryset().filter(requester=user)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get approval statistics for current user.

        GET /api/approval-requests/stats/
        """
        user = request.user
        queryset = self.get_queryset()

        stats = {
            'total': queryset.count(),
            'pending': queryset.filter(status='PENDING').count(),
            'approved': queryset.filter(status='APPROVED').count(),
            'rejected': queryset.filter(status='REJECTED').count(),
            'my_pending_approvals': queryset.filter(
                steps__approver=user,
                steps__status='PENDING',
                status='PENDING'
            ).distinct().count(),
            'my_requests': queryset.filter(requester=user).count(),
        }

        return Response(stats)

    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """
        Get complete history for an approval request.

        GET /api/approval-requests/{id}/history/
        """
        approval_request = self.get_object()
        history = approval_request.history_entries.all().order_by('-created_at')

        serializer = ApprovalHistorySerializer(history, many=True)
        return Response(serializer.data)


class ApprovalDelegationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing approval delegations.

    list: Get all active delegations
    retrieve: Get a specific delegation
    create: Create a new delegation
    update: Update a delegation
    destroy: Delete a delegation
    """

    serializer_class = ApprovalDelegationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['status', 'workflow']
    ordering = ['-created_at']

    def get_queryset(self):
        """Users can only see their own delegations."""
        user = self.request.user

        if user.is_staff:
            return ApprovalDelegation.objects.all()

        return ApprovalDelegation.objects.filter(
            Q(delegator=user) | Q(delegate=user)
        ).select_related('delegator', 'delegate', 'workflow')

    def perform_create(self, serializer):
        """Set delegator to current user."""
        serializer.save(delegator=self.request.user)

    @action(detail=False, methods=['get'])
    def active(self, request):
        """
        Get active delegations for current user.

        GET /api/approval-delegations/active/
        """
        user = request.user
        now = timezone.now().date()

        queryset = self.get_queryset().filter(
            status='ACTIVE',
            start_date__lte=now,
            end_date__gte=now
        )

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

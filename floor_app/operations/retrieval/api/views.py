"""REST API Views for Retrieval System"""
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.contrib.contenttypes.models import ContentType
from django.apps import apps
from django.utils import timezone

from ..models import RetrievalRequest, RetrievalMetric
from ..services import RetrievalService
from .serializers import (
    RetrievalRequestSerializer,
    RetrievalMetricSerializer,
    CreateRetrievalRequestSerializer,
    ApprovalSerializer
)


class RetrievalRequestListView(generics.ListAPIView):
    """List retrieval requests for current user"""
    serializer_class = RetrievalRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return RetrievalRequest.objects.filter(
            employee=self.request.user
        ).order_by('-submitted_at')


class RetrievalRequestDetailView(generics.RetrieveAPIView):
    """Get details of a specific retrieval request"""
    serializer_class = RetrievalRequestSerializer
    permission_classes = [IsAuthenticated]
    queryset = RetrievalRequest.objects.all()


class CreateRetrievalRequestView(APIView):
    """Create a new retrieval request"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreateRetrievalRequestSerializer(data=request.data)
        if serializer.is_valid():
            content_type = serializer.validated_data['content_type']
            object_id = serializer.validated_data['object_id']
            reason = serializer.validated_data['reason']

            # Get the object
            try:
                model = content_type.model_class()
                obj = model.objects.get(pk=object_id)
            except model.DoesNotExist:
                return Response(
                    {'error': 'Object not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Check if object has retrieval capability
            if not hasattr(obj, 'create_retrieval_request'):
                return Response(
                    {'error': 'This object type does not support retrieval'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Create retrieval request
            try:
                retrieval_request = obj.create_retrieval_request(
                    employee=request.user,
                    reason=reason
                )
                serializer = RetrievalRequestSerializer(retrieval_request)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ApproveRetrievalView(APIView):
    """Approve a retrieval request (supervisor only)"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        retrieval_request = get_object_or_404(RetrievalRequest, pk=pk)

        # Check if user is the supervisor
        if retrieval_request.supervisor != request.user:
            return Response(
                {'error': 'Only the supervisor can approve this request'},
                status=status.HTTP_403_FORBIDDEN
            )

        if retrieval_request.status not in ['PENDING']:
            return Response(
                {'error': 'Request cannot be approved in current status'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ApprovalSerializer(data=request.data)
        if serializer.is_valid():
            comments = serializer.validated_data.get('comments', '')

            retrieval_request.status = 'APPROVED'
            retrieval_request.approved_at = timezone.now()
            retrieval_request.save()

            # Send notification to employee
            RetrievalService.notify_employee_decision(retrieval_request)

            return Response({
                'message': 'Retrieval request approved successfully',
                'retrieval_request': RetrievalRequestSerializer(retrieval_request).data
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RejectRetrievalView(APIView):
    """Reject a retrieval request (supervisor only)"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        retrieval_request = get_object_or_404(RetrievalRequest, pk=pk)

        # Check if user is the supervisor
        if retrieval_request.supervisor != request.user:
            return Response(
                {'error': 'Only the supervisor can reject this request'},
                status=status.HTTP_403_FORBIDDEN
            )

        if retrieval_request.status not in ['PENDING']:
            return Response(
                {'error': 'Request cannot be rejected in current status'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ApprovalSerializer(data=request.data)
        if serializer.is_valid():
            rejection_reason = serializer.validated_data.get('comments', '')

            retrieval_request.status = 'REJECTED'
            retrieval_request.rejection_reason = rejection_reason
            retrieval_request.save()

            # Send notification to employee
            RetrievalService.notify_employee_decision(retrieval_request)

            return Response({
                'message': 'Retrieval request rejected',
                'retrieval_request': RetrievalRequestSerializer(retrieval_request).data
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CancelRetrievalView(APIView):
    """Cancel a pending retrieval request"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        retrieval_request = get_object_or_404(RetrievalRequest, pk=pk)

        # Check if user is the employee who created it
        if retrieval_request.employee != request.user:
            return Response(
                {'error': 'Only the requester can cancel this request'},
                status=status.HTTP_403_FORBIDDEN
            )

        if retrieval_request.status not in ['PENDING']:
            return Response(
                {'error': 'Only pending requests can be cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )

        retrieval_request.status = 'CANCELLED'
        retrieval_request.save()

        return Response({
            'message': 'Retrieval request cancelled successfully'
        })


class CompleteRetrievalView(APIView):
    """Complete an approved retrieval request"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        retrieval_request = get_object_or_404(RetrievalRequest, pk=pk)

        # Check if user is the employee or supervisor
        if retrieval_request.employee != request.user and retrieval_request.supervisor != request.user:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        if retrieval_request.status not in ['APPROVED', 'AUTO_APPROVED']:
            return Response(
                {'error': 'Only approved requests can be completed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Get the object and perform retrieval
            obj = retrieval_request.content_object
            if obj and hasattr(obj, 'perform_retrieval'):
                obj.perform_retrieval(retrieval_request)

                return Response({
                    'message': 'Retrieval completed successfully',
                    'retrieval_request': RetrievalRequestSerializer(retrieval_request).data
                })
            else:
                return Response(
                    {'error': 'Object not found or retrieval not supported'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            return Response(
                {'error': f'Retrieval failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SupervisorPendingRequestsView(generics.ListAPIView):
    """List pending retrieval requests for supervisor"""
    serializer_class = RetrievalRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return RetrievalRequest.objects.filter(
            supervisor=self.request.user,
            status='PENDING'
        ).order_by('-submitted_at')


class EmployeeMetricsView(APIView):
    """Get retrieval metrics for an employee"""
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        period = request.query_params.get('period', 'month')

        metrics = RetrievalService.calculate_employee_accuracy(
            user_id=user_id,
            period=period
        )

        serializer = RetrievalMetricSerializer(metrics)
        return Response(serializer.data)


class DepartmentMetricsView(APIView):
    """Get aggregated metrics for a department"""
    permission_classes = [IsAuthenticated]

    def get(self, request, department):
        period = request.query_params.get('period', 'month')

        # Get all employees in department
        # This would need to be adjusted based on your User/Employee model structure
        from django.contrib.auth import get_user_model
        User = get_user_model()

        # Aggregate metrics for department
        # This is a simplified version - adjust based on your needs
        metrics = {
            'department': department,
            'period': period,
            'total_requests': RetrievalRequest.objects.filter(
                employee__department=department  # Adjust field name as needed
            ).count()
        }

        return Response(metrics)


class CheckRetrievableView(APIView):
    """Check if an object can be retrieved"""
    permission_classes = [IsAuthenticated]

    def get(self, request, content_type, object_id):
        try:
            # Get ContentType
            ct = ContentType.objects.get(pk=content_type)
            model = ct.model_class()
            obj = model.objects.get(pk=object_id)

            # Check if object has retrieval capability
            if not hasattr(obj, 'can_be_retrieved'):
                return Response({
                    'can_retrieve': False,
                    'reason': 'Object type does not support retrieval'
                })

            can_retrieve, reason = obj.can_be_retrieved()

            return Response({
                'can_retrieve': can_retrieve,
                'reason': reason,
                'time_window_minutes': getattr(obj, 'RETRIEVAL_TIME_WINDOW_MINUTES', 15)
            })

        except ContentType.DoesNotExist:
            return Response(
                {'error': 'Invalid content type'},
                status=status.HTTP_404_NOT_FOUND
            )
        except model.DoesNotExist:
            return Response(
                {'error': 'Object not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

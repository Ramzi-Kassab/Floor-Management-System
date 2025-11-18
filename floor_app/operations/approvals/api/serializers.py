"""
Approval Workflow API Serializers

Serializers for approval workflow REST API.
"""

from rest_framework import serializers
from floor_app.operations.approvals.models import (
    ApprovalWorkflow,
    ApprovalLevel,
    ApprovalRequest,
    ApprovalStep,
    ApprovalHistory,
    ApprovalDelegation
)


class ApprovalLevelSerializer(serializers.ModelSerializer):
    """Serializer for approval levels."""

    approval_mode_display = serializers.CharField(
        source='get_approval_mode_display',
        read_only=True
    )
    approver_names = serializers.SerializerMethodField()

    class Meta:
        model = ApprovalLevel
        fields = [
            'id',
            'workflow',
            'level_number',
            'level_name',
            'approval_mode',
            'approval_mode_display',
            'approvers',
            'approver_names',
            'can_skip',
            'skip_conditions',
            'timeout_hours',
            'created_at',
        ]
        read_only_fields = ['created_at']

    def get_approver_names(self, obj):
        """Get names of all approvers."""
        return [user.get_full_name() or user.username for user in obj.approvers.all()]


class ApprovalWorkflowSerializer(serializers.ModelSerializer):
    """Serializer for approval workflows."""

    levels = ApprovalLevelSerializer(many=True, read_only=True)
    levels_count = serializers.IntegerField(source='levels.count', read_only=True)

    class Meta:
        model = ApprovalWorkflow
        fields = [
            'id',
            'name',
            'description',
            'workflow_type',
            'is_active',
            'requires_all_levels',
            'auto_approve_threshold',
            'levels',
            'levels_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class ApprovalHistorySerializer(serializers.ModelSerializer):
    """Serializer for approval history."""

    actor_name = serializers.SerializerMethodField()
    action_display = serializers.CharField(
        source='get_action_display',
        read_only=True
    )

    class Meta:
        model = ApprovalHistory
        fields = [
            'id',
            'approval_request',
            'step',
            'actor',
            'actor_name',
            'action',
            'action_display',
            'comments',
            'metadata',
            'created_at',
        ]
        read_only_fields = ['created_at']

    def get_actor_name(self, obj):
        """Get actor's name."""
        if obj.actor:
            return obj.actor.get_full_name() or obj.actor.username
        return 'System'


class ApprovalStepSerializer(serializers.ModelSerializer):
    """Serializer for approval steps."""

    approver_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    level_name = serializers.CharField(source='level.level_name', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = ApprovalStep
        fields = [
            'id',
            'approval_request',
            'level',
            'level_name',
            'approver',
            'approver_name',
            'status',
            'status_display',
            'approved_at',
            'rejected_at',
            'comments',
            'is_overdue',
            'created_at',
        ]
        read_only_fields = ['approved_at', 'rejected_at', 'created_at']

    def get_approver_name(self, obj):
        """Get approver's name."""
        if obj.approver:
            return obj.approver.get_full_name() or obj.approver.username
        return 'Unassigned'


class ApprovalRequestSerializer(serializers.ModelSerializer):
    """Serializer for approval requests."""

    requester_name = serializers.SerializerMethodField()
    workflow_name = serializers.CharField(source='workflow.name', read_only=True)
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    priority_display = serializers.CharField(
        source='get_priority_display',
        read_only=True
    )
    steps = ApprovalStepSerializer(many=True, read_only=True)
    history = ApprovalHistorySerializer(many=True, read_only=True, source='history_entries')
    can_user_approve = serializers.SerializerMethodField()
    current_step = serializers.SerializerMethodField()
    progress_percentage = serializers.SerializerMethodField()

    class Meta:
        model = ApprovalRequest
        fields = [
            'id',
            'workflow',
            'workflow_name',
            'title',
            'description',
            'requester',
            'requester_name',
            'status',
            'status_display',
            'priority',
            'priority_display',
            'current_level',
            'current_step',
            'submitted_at',
            'completed_at',
            'visible_to_all',
            'metadata',
            'steps',
            'history',
            'can_user_approve',
            'progress_percentage',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'requester',
            'status',
            'current_level',
            'submitted_at',
            'completed_at',
            'created_at',
            'updated_at',
        ]

    def get_requester_name(self, obj):
        """Get requester's name."""
        if obj.requester:
            return obj.requester.get_full_name() or obj.requester.username
        return 'System'

    def get_can_user_approve(self, obj):
        """Check if current user can approve this request."""
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            return obj.can_user_approve(request.user)
        return False

    def get_current_step(self, obj):
        """Get the current pending step for this request."""
        step = obj.steps.filter(status='PENDING').first()
        if step:
            return ApprovalStepSerializer(step).data
        return None

    def get_progress_percentage(self, obj):
        """Calculate approval progress percentage."""
        total_steps = obj.steps.count()
        if total_steps == 0:
            return 0

        completed_steps = obj.steps.filter(
            status__in=['APPROVED', 'SKIPPED']
        ).count()

        return int((completed_steps / total_steps) * 100)


class ApprovalRequestCreateSerializer(serializers.Serializer):
    """Serializer for creating approval requests via API."""

    workflow_id = serializers.IntegerField()
    title = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False)
    priority = serializers.ChoiceField(
        choices=['LOW', 'NORMAL', 'HIGH', 'URGENT'],
        default='NORMAL'
    )
    visible_to_all = serializers.BooleanField(default=False)
    visible_to_department_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    visible_to_user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    metadata = serializers.JSONField(required=False)


class ApprovalActionSerializer(serializers.Serializer):
    """Serializer for approval actions (approve/reject)."""

    action = serializers.ChoiceField(choices=['approve', 'reject'])
    comments = serializers.CharField(required=False, allow_blank=True)
    metadata = serializers.JSONField(required=False)


class ApprovalDelegationSerializer(serializers.ModelSerializer):
    """Serializer for approval delegations."""

    delegator_name = serializers.SerializerMethodField()
    delegate_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )

    class Meta:
        model = ApprovalDelegation
        fields = [
            'id',
            'delegator',
            'delegator_name',
            'delegate',
            'delegate_name',
            'workflow',
            'start_date',
            'end_date',
            'reason',
            'status',
            'status_display',
            'created_at',
        ]
        read_only_fields = ['created_at']

    def get_delegator_name(self, obj):
        """Get delegator's name."""
        return obj.delegator.get_full_name() or obj.delegator.username

    def get_delegate_name(self, obj):
        """Get delegate's name."""
        return obj.delegate.get_full_name() or obj.delegate.username

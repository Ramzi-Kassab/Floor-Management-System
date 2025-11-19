"""REST API Serializers for Retrieval System"""
from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from ..models import RetrievalRequest, RetrievalMetric


class RetrievalRequestSerializer(serializers.ModelSerializer):
    """Serializer for RetrievalRequest"""
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    supervisor_name = serializers.CharField(source='supervisor.get_full_name', read_only=True)
    content_type_name = serializers.CharField(source='content_type.model', read_only=True)
    time_elapsed_minutes = serializers.SerializerMethodField()
    can_be_completed = serializers.SerializerMethodField()

    class Meta:
        model = RetrievalRequest
        fields = [
            'id',
            'employee',
            'employee_name',
            'supervisor',
            'supervisor_name',
            'content_type',
            'content_type_name',
            'object_id',
            'action_type',
            'reason',
            'original_data',
            'status',
            'submitted_at',
            'approved_at',
            'completed_at',
            'time_elapsed_minutes',
            'has_dependent_processes',
            'dependent_process_details',
            'supervisor_notified_at',
            'notification_sent',
            'can_be_completed',
        ]
        read_only_fields = [
            'id',
            'submitted_at',
            'approved_at',
            'completed_at',
            'supervisor_notified_at',
            'notification_sent',
        ]

    def get_time_elapsed_minutes(self, obj):
        """Calculate time elapsed since submission"""
        from django.utils import timezone
        if obj.submitted_at:
            delta = timezone.now() - obj.submitted_at
            return int(delta.total_seconds() / 60)
        return None

    def get_can_be_completed(self, obj):
        """Check if request can be completed"""
        return obj.status in ['APPROVED', 'AUTO_APPROVED']


class CreateRetrievalRequestSerializer(serializers.Serializer):
    """Serializer for creating a retrieval request"""
    content_type = serializers.PrimaryKeyRelatedField(
        queryset=ContentType.objects.all()
    )
    object_id = serializers.IntegerField()
    reason = serializers.CharField(max_length=500)

    def validate_reason(self, value):
        """Validate reason is not empty"""
        if not value or len(value.strip()) < 10:
            raise serializers.ValidationError(
                "Please provide a detailed reason (at least 10 characters)"
            )
        return value


class ApprovalSerializer(serializers.Serializer):
    """Serializer for approval/rejection"""
    comments = serializers.CharField(max_length=500, required=False, allow_blank=True)


class RetrievalMetricSerializer(serializers.ModelSerializer):
    """Serializer for RetrievalMetric"""
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    accuracy_display = serializers.SerializerMethodField()
    error_rate_display = serializers.SerializerMethodField()

    class Meta:
        model = RetrievalMetric
        fields = [
            'id',
            'employee',
            'employee_name',
            'period_type',
            'period_start',
            'period_end',
            'total_actions',
            'total_retrieval_requests',
            'auto_approved_count',
            'manually_approved_count',
            'rejected_count',
            'accuracy_rate',
            'accuracy_display',
            'error_rate',
            'error_rate_display',
        ]

    def get_accuracy_display(self, obj):
        """Format accuracy rate as percentage"""
        return f"{obj.accuracy_rate:.1f}%"

    def get_error_rate_display(self, obj):
        """Format error rate as percentage"""
        return f"{obj.error_rate:.1f}%"

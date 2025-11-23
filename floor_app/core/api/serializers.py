"""
REST API Serializers for Core Models

Provides serialization for:
- AuditLog
- ActivityLog
- SystemEvent
- ChangeHistory
- Notification
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from ..models import AuditLog, ActivityLog, SystemEvent, ChangeHistory
from ..notifications import Notification


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff']
        read_only_fields = ['id', 'username', 'email', 'is_staff']


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer for AuditLog"""

    user = UserSerializer(read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            'id', 'user', 'username', 'action', 'action_display',
            'model_name', 'object_id', 'object_repr',
            'field_name', 'old_value', 'new_value',
            'timestamp', 'ip_address', 'user_agent',
            'message', 'extra_data'
        ]
        read_only_fields = fields


class ActivityLogSerializer(serializers.ModelSerializer):
    """Serializer for ActivityLog"""

    user = UserSerializer(read_only=True)
    activity_type_display = serializers.CharField(source='get_activity_type_display', read_only=True)

    class Meta:
        model = ActivityLog
        fields = [
            'id', 'user', 'activity_type', 'activity_type_display',
            'path', 'query_params', 'description',
            'timestamp', 'duration_ms',
            'ip_address', 'user_agent', 'session_key',
            'metadata'
        ]
        read_only_fields = fields


class SystemEventSerializer(serializers.ModelSerializer):
    """Serializer for SystemEvent"""

    user = UserSerializer(read_only=True)
    resolved_by = UserSerializer(read_only=True)
    level_display = serializers.CharField(source='get_level_display', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = SystemEvent
        fields = [
            'id', 'level', 'level_display', 'category', 'category_display',
            'event_name', 'message',
            'exception_type', 'exception_message', 'stack_trace',
            'timestamp', 'user',
            'request_path', 'request_method', 'ip_address',
            'extra_data',
            'is_resolved', 'resolved_at', 'resolved_by', 'resolution_notes'
        ]
        read_only_fields = [
            'id', 'level', 'category', 'event_name', 'message',
            'exception_type', 'exception_message', 'stack_trace',
            'timestamp', 'user', 'request_path', 'request_method',
            'ip_address', 'extra_data'
        ]

    def update(self, instance, validated_data):
        """Allow updating resolution fields only"""
        instance.is_resolved = validated_data.get('is_resolved', instance.is_resolved)
        instance.resolution_notes = validated_data.get('resolution_notes', instance.resolution_notes)

        if instance.is_resolved and not instance.resolved_at:
            from django.utils import timezone
            instance.resolved_at = timezone.now()
            if 'request' in self.context:
                instance.resolved_by = self.context['request'].user

        instance.save()
        return instance


class ChangeHistorySerializer(serializers.ModelSerializer):
    """Serializer for ChangeHistory"""

    changed_by = UserSerializer(read_only=True)
    changes_display = serializers.CharField(source='get_changes_display', read_only=True)

    class Meta:
        model = ChangeHistory
        fields = [
            'id', 'content_type', 'object_id',
            'field_changes', 'changes_display', 'change_summary',
            'changed_by', 'changed_at', 'change_reason', 'ip_address'
        ]
        read_only_fields = fields


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for Notification"""

    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id', 'notification_type', 'notification_type_display',
            'title', 'message',
            'content_type', 'object_id',
            'action_url', 'action_text',
            'is_read', 'read_at',
            'created_at', 'expires_at',
            'email_sent', 'email_sent_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'email_sent', 'email_sent_at',
            'read_at'
        ]

    def update(self, instance, validated_data):
        """Allow marking as read"""
        if validated_data.get('is_read') and not instance.is_read:
            instance.mark_as_read()
        return instance


class NotificationCreateSerializer(serializers.Serializer):
    """Serializer for creating notifications"""

    user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
        help_text="List of user IDs to notify"
    )
    notification_type = serializers.ChoiceField(
        choices=Notification.NOTIFICATION_TYPES,
        default='INFO'
    )
    title = serializers.CharField(max_length=200)
    message = serializers.CharField()
    action_url = serializers.CharField(max_length=500, required=False, allow_blank=True)
    action_text = serializers.CharField(max_length=100, required=False, allow_blank=True)
    send_email = serializers.BooleanField(default=False)
    expires_in_days = serializers.IntegerField(required=False, allow_null=True)

    def create(self, validated_data):
        """Create notifications for multiple users"""
        from django.contrib.auth.models import User

        user_ids = validated_data.pop('user_ids')
        users = User.objects.filter(id__in=user_ids)

        notifications = Notification.bulk_create_notifications(
            users=users,
            **validated_data
        )

        return notifications


# Summary Serializers

class SystemHealthSerializer(serializers.Serializer):
    """Serializer for system health summary"""

    health_status = serializers.CharField()
    error_count = serializers.IntegerField()
    warning_count = serializers.IntegerField()
    critical_count = serializers.IntegerField()
    unresolved_count = serializers.IntegerField()
    timestamp = serializers.DateTimeField()


class ActivityStatsSerializer(serializers.Serializer):
    """Serializer for activity statistics"""

    total_activities = serializers.IntegerField()
    unique_users = serializers.IntegerField()
    by_type = serializers.ListField()
    by_hour = serializers.ListField()
    top_users = serializers.ListField()
    date_range = serializers.DictField()


class AuditStatsSerializer(serializers.Serializer):
    """Serializer for audit statistics"""

    total_audits = serializers.IntegerField()
    by_action = serializers.ListField()
    by_model = serializers.ListField()
    by_user = serializers.ListField()
    date_range = serializers.DictField()

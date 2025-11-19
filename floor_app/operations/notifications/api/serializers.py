"""
Notification API Serializers

Serializers for notification system REST API.
"""

from rest_framework import serializers
from floor_app.operations.notifications.models import (
    NotificationChannel,
    NotificationTemplate,
    Notification,
    NotificationDelivery,
    UserNotificationPreference,
    Announcement,
    AnnouncementRead
)


class NotificationChannelSerializer(serializers.ModelSerializer):
    """Serializer for notification channels."""

    class Meta:
        model = NotificationChannel
        fields = [
            'id',
            'channel_type',
            'is_enabled',
            'max_per_hour',
            'max_per_day',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']

    # Hide configuration (contains sensitive API keys)
    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Only show configuration to admins
        request = self.context.get('request')
        if request and request.user and request.user.is_staff:
            data['configuration_keys'] = list(instance.configuration.keys())
        return data


class NotificationTemplateSerializer(serializers.ModelSerializer):
    """Serializer for notification templates."""

    class Meta:
        model = NotificationTemplate
        fields = [
            'id',
            'name',
            'description',
            'template_category',
            'subject_template',
            'body_template',
            'default_channels',
            'default_priority',
            'variables',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class NotificationDeliverySerializer(serializers.ModelSerializer):
    """Serializer for notification delivery records."""

    channel_display = serializers.CharField(
        source='get_channel_display',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )

    class Meta:
        model = NotificationDelivery
        fields = [
            'id',
            'notification',
            'channel',
            'channel_display',
            'status',
            'status_display',
            'sent_at',
            'delivered_at',
            'failed_at',
            'failure_reason',
            'retry_count',
            'provider_message_id',
        ]
        read_only_fields = [
            'sent_at',
            'delivered_at',
            'failed_at',
            'retry_count',
            'provider_message_id',
        ]


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for notifications."""

    deliveries = NotificationDeliverySerializer(many=True, read_only=True)
    priority_display = serializers.CharField(
        source='get_priority_display',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    recipient_name = serializers.SerializerMethodField()
    time_since = serializers.SerializerMethodField()
    is_read = serializers.BooleanField(source='read_at', read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id',
            'recipient_user',
            'recipient_employee',
            'recipient_name',
            'title',
            'message',
            'priority',
            'priority_display',
            'channels_to_send',
            'category',
            'action_url',
            'action_label',
            'status',
            'status_display',
            'sent_at',
            'read_at',
            'is_read',
            'time_since',
            'metadata',
            'deliveries',
            'created_at',
        ]
        read_only_fields = ['sent_at', 'read_at', 'status', 'created_at']

    def get_recipient_name(self, obj):
        """Get recipient's name."""
        if obj.recipient_employee:
            return obj.recipient_employee.full_name
        elif obj.recipient_user:
            return obj.recipient_user.get_full_name() or obj.recipient_user.username
        return 'Unknown'

    def get_time_since(self, obj):
        """Get human-readable time since creation."""
        from django.utils import timezone
        from datetime import timedelta

        now = timezone.now()
        diff = now - obj.created_at

        if diff < timedelta(minutes=1):
            return 'Just now'
        elif diff < timedelta(hours=1):
            minutes = int(diff.total_seconds() / 60)
            return f'{minutes}m ago'
        elif diff < timedelta(days=1):
            hours = int(diff.total_seconds() / 3600)
            return f'{hours}h ago'
        elif diff < timedelta(days=7):
            days = diff.days
            return f'{days}d ago'
        else:
            return obj.created_at.strftime('%b %d, %Y')


class NotificationCreateSerializer(serializers.Serializer):
    """Serializer for creating notifications via API."""

    recipient_user_id = serializers.IntegerField(required=False)
    recipient_employee_id = serializers.IntegerField(required=False)
    title = serializers.CharField(max_length=200)
    message = serializers.CharField()
    priority = serializers.ChoiceField(
        choices=['LOW', 'NORMAL', 'HIGH', 'URGENT'],
        default='NORMAL'
    )
    channels = serializers.ListField(
        child=serializers.ChoiceField(
            choices=['WHATSAPP', 'EMAIL', 'SMS', 'PUSH', 'IN_APP']
        ),
        required=False
    )
    category = serializers.CharField(max_length=50, required=False)
    action_url = serializers.CharField(max_length=500, required=False)
    action_label = serializers.CharField(max_length=50, required=False)
    template_name = serializers.CharField(max_length=100, required=False)
    template_variables = serializers.JSONField(required=False)

    def validate(self, data):
        """Validate that at least one recipient is provided."""
        if not data.get('recipient_user_id') and not data.get('recipient_employee_id'):
            raise serializers.ValidationError(
                "Either recipient_user_id or recipient_employee_id must be provided"
            )
        return data


class UserNotificationPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for user notification preferences."""

    class Meta:
        model = UserNotificationPreference
        fields = [
            'id',
            'user',
            'employee',
            'email_enabled',
            'sms_enabled',
            'push_enabled',
            'whatsapp_enabled',
            'in_app_enabled',
            'approval_notifications',
            'job_notifications',
            'inventory_notifications',
            'qc_notifications',
            'system_notifications',
            'quiet_hours_enabled',
            'quiet_hours_start',
            'quiet_hours_end',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class AnnouncementReadSerializer(serializers.ModelSerializer):
    """Serializer for announcement read tracking."""

    reader_name = serializers.SerializerMethodField()

    class Meta:
        model = AnnouncementRead
        fields = [
            'id',
            'announcement',
            'user',
            'employee',
            'reader_name',
            'read_at',
        ]
        read_only_fields = ['read_at']

    def get_reader_name(self, obj):
        """Get reader's name."""
        if obj.employee:
            return obj.employee.full_name
        elif obj.user:
            return obj.user.get_full_name() or obj.user.username
        return 'Unknown'


class AnnouncementSerializer(serializers.ModelSerializer):
    """Serializer for announcements."""

    target_type_display = serializers.CharField(
        source='get_target_type_display',
        read_only=True
    )
    priority_display = serializers.CharField(
        source='get_priority_display',
        read_only=True
    )
    author_name = serializers.SerializerMethodField()
    read_count = serializers.SerializerMethodField()
    is_read_by_current_user = serializers.SerializerMethodField()

    class Meta:
        model = Announcement
        fields = [
            'id',
            'title',
            'content',
            'target_type',
            'target_type_display',
            'priority',
            'priority_display',
            'publish_at',
            'expire_at',
            'is_published',
            'send_notification',
            'author',
            'author_name',
            'read_count',
            'is_read_by_current_user',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['author', 'created_at', 'updated_at']

    def get_author_name(self, obj):
        """Get author's name."""
        if obj.author:
            return obj.author.get_full_name() or obj.author.username
        return 'System'

    def get_read_count(self, obj):
        """Get count of users who read this announcement."""
        return obj.read_by.count()

    def get_is_read_by_current_user(self, obj):
        """Check if current user has read this announcement."""
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            return obj.read_by.filter(user=request.user).exists()
        return False


class AnnouncementCreateSerializer(serializers.Serializer):
    """Serializer for creating announcements via API."""

    title = serializers.CharField(max_length=200)
    content = serializers.CharField()
    target_type = serializers.ChoiceField(
        choices=['ALL', 'DEPARTMENT', 'ROLE', 'LOCATION', 'CUSTOM']
    )
    target_department_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    target_user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    priority = serializers.ChoiceField(
        choices=['INFO', 'IMPORTANT', 'URGENT', 'CRITICAL'],
        default='INFO'
    )
    publish_at = serializers.DateTimeField(required=False)
    expire_at = serializers.DateTimeField(required=False)
    is_published = serializers.BooleanField(default=True)
    send_notification = serializers.BooleanField(default=False)

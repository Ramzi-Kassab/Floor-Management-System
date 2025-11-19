"""
Notification & Announcement System

Multi-channel notification system supporting:
- WhatsApp Business API
- Email (Outlook/SMTP)
- SMS
- Push notifications (mobile/web)
- In-app notifications
- Telegram (optional)

Features:
- Priority levels (low, normal, high, urgent)
- Targeted delivery (role-based, user-based, location-based)
- Read/unread tracking
- Delivery status tracking
- Template system
- User preferences
- Announcement boards
- Approval workflow integration
"""

from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.conf import settings

from floor_app.mixins import AuditMixin, SoftDeleteMixin


class NotificationChannel(models.Model):
    """
    Available notification channels.

    Channels can be enabled/disabled globally or per user.
    """

    CHANNEL_TYPES = (
        ('WHATSAPP', 'WhatsApp'),
        ('EMAIL', 'Email'),
        ('SMS', 'SMS'),
        ('PUSH', 'Push Notification'),
        ('IN_APP', 'In-App Notification'),
        ('TELEGRAM', 'Telegram'),
    )

    channel_type = models.CharField(
        max_length=20,
        choices=CHANNEL_TYPES,
        unique=True
    )
    is_enabled = models.BooleanField(
        default=True,
        help_text="Is this channel enabled globally?"
    )
    configuration = models.JSONField(
        default=dict,
        help_text="Channel-specific configuration (API keys, endpoints, etc.)"
    )
    priority = models.PositiveIntegerField(
        default=100,
        help_text="Delivery priority (lower = higher priority)"
    )

    # Rate limiting
    max_per_hour = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Max messages per hour (null = unlimited)"
    )
    max_per_day = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Max messages per day (null = unlimited)"
    )

    class Meta:
        db_table = 'notifications_channel'
        ordering = ['priority', 'channel_type']

    def __str__(self):
        return f"{self.get_channel_type_display()} ({'Enabled' if self.is_enabled else 'Disabled'})"


class NotificationTemplate(AuditMixin):
    """
    Reusable notification templates.

    Supports variables like {{user_name}}, {{job_card}}, etc.
    """

    TEMPLATE_TYPES = (
        ('APPROVAL_REQUEST', 'Approval Request'),
        ('APPROVAL_APPROVED', 'Approval Approved'),
        ('APPROVAL_REJECTED', 'Approval Rejected'),
        ('JOB_CREATED', 'Job Created'),
        ('JOB_COMPLETED', 'Job Completed'),
        ('STAGE_COMPLETED', 'Stage Completed'),
        ('VALIDATION_FAILED', 'Validation Failed'),
        ('LOW_STOCK', 'Low Stock Alert'),
        ('OUT_OF_STOCK', 'Out of Stock Alert'),
        ('CUTTER_SUBSTITUTION', 'Cutter Substitution'),
        ('QC_REQUIRED', 'QC Required'),
        ('NDT_REQUIRED', 'NDT Required'),
        ('REWORK_REQUIRED', 'Rework Required'),
        ('CUSTOM', 'Custom Message'),
    )

    template_type = models.CharField(
        max_length=50,
        choices=TEMPLATE_TYPES
    )
    name = models.CharField(
        max_length=200,
        help_text="Template name"
    )

    # Channel-specific templates
    whatsapp_template = models.TextField(
        blank=True,
        help_text="WhatsApp message template"
    )
    email_subject = models.CharField(
        max_length=200,
        blank=True,
        help_text="Email subject line"
    )
    email_template = models.TextField(
        blank=True,
        help_text="Email body template (supports HTML)"
    )
    sms_template = models.TextField(
        blank=True,
        help_text="SMS template (160 chars recommended)"
    )
    push_title = models.CharField(
        max_length=100,
        blank=True,
        help_text="Push notification title"
    )
    push_body = models.TextField(
        blank=True,
        help_text="Push notification body"
    )
    in_app_title = models.CharField(
        max_length=200,
        blank=True,
        help_text="In-app notification title"
    )
    in_app_message = models.TextField(
        blank=True,
        help_text="In-app notification message"
    )

    # Template variables documentation
    available_variables = models.JSONField(
        default=list,
        help_text="List of available template variables"
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'notifications_template'
        unique_together = [('template_type', 'name')]
        indexes = [
            models.Index(fields=['template_type', 'is_active']),
        ]

    def __str__(self):
        return f"{self.get_template_type_display()} - {self.name}"


class NotificationPreference(models.Model):
    """
    User notification preferences.

    Users can choose which channels they want for which notification types.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )
    employee = models.ForeignKey(
        'hr.HREmployee',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notification_preferences'
    )

    # Channel preferences
    enable_whatsapp = models.BooleanField(default=True)
    enable_email = models.BooleanField(default=True)
    enable_sms = models.BooleanField(default=False)
    enable_push = models.BooleanField(default=True)
    enable_in_app = models.BooleanField(default=True)
    enable_telegram = models.BooleanField(default=False)

    # Contact information
    whatsapp_number = models.CharField(
        max_length=20,
        blank=True,
        help_text="WhatsApp number (international format)"
    )
    telegram_chat_id = models.CharField(
        max_length=50,
        blank=True
    )

    # Notification type preferences (JSON)
    notification_types = models.JSONField(
        default=dict,
        help_text="Per-type channel preferences"
    )

    # Quiet hours
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)

    # Digest preferences
    enable_daily_digest = models.BooleanField(default=False)
    digest_time = models.TimeField(null=True, blank=True)

    class Meta:
        db_table = 'notifications_preference'
        unique_together = [('user', 'employee')]

    def __str__(self):
        return f"Preferences for {self.user.username}"


class Notification(AuditMixin):
    """
    Individual notification record.

    Tracks notification content, delivery status, and read status.
    """

    PRIORITY_CHOICES = (
        ('LOW', 'Low'),
        ('NORMAL', 'Normal'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    )

    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('SENT', 'Sent'),
        ('DELIVERED', 'Delivered'),
        ('READ', 'Read'),
        ('FAILED', 'Failed'),
    )

    # Recipient
    recipient_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications_received',
        null=True,
        blank=True
    )
    recipient_employee = models.ForeignKey(
        'hr.HREmployee',
        on_delete=models.CASCADE,
        related_name='notifications_received',
        null=True,
        blank=True
    )

    # Content
    title = models.CharField(max_length=200)
    message = models.TextField()
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='NORMAL'
    )

    # Template reference
    template = models.ForeignKey(
        NotificationTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    template_variables = models.JSONField(
        default=dict,
        help_text="Variables used to render template"
    )

    # Linked object (optional - what this notification is about)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='floor_notifications'
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object = GenericForeignKey('content_type', 'object_id')

    # Delivery
    channels_to_send = models.JSONField(
        default=list,
        help_text="Channels to deliver on (e.g., ['WHATSAPP', 'EMAIL'])"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )

    # Tracking
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.TextField(blank=True)

    # Metadata
    action_url = models.CharField(
        max_length=500,
        blank=True,
        help_text="URL for action button (e.g., approve, view details)"
    )
    action_label = models.CharField(
        max_length=50,
        blank=True,
        help_text="Label for action button"
    )

    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Expiry date for time-sensitive notifications"
    )

    class Meta:
        db_table = 'notifications_notification'
        indexes = [
            models.Index(fields=['recipient_user', 'status', '-created_at']),
            models.Index(fields=['recipient_employee', 'status', '-created_at']),
            models.Index(fields=['priority', 'status']),
            models.Index(fields=['content_type', 'object_id']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        recipient = self.recipient_user or self.recipient_employee
        return f"{self.title} → {recipient}"

    def mark_as_read(self):
        """Mark notification as read."""
        if not self.read_at:
            self.read_at = timezone.now()
            self.status = 'READ'
            self.save(update_fields=['read_at', 'status'])

    @property
    def is_read(self):
        """Check if notification has been read."""
        return self.read_at is not None

    @property
    def is_expired(self):
        """Check if notification has expired."""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False


class NotificationDelivery(models.Model):
    """
    Track delivery status per channel.

    One notification can have multiple delivery records (one per channel).
    """

    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('SENDING', 'Sending'),
        ('SENT', 'Sent'),
        ('DELIVERED', 'Delivered'),
        ('FAILED', 'Failed'),
        ('BOUNCED', 'Bounced'),
    )

    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name='deliveries'
    )
    channel = models.ForeignKey(
        NotificationChannel,
        on_delete=models.CASCADE
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )

    # Tracking
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.TextField(blank=True)

    # Provider response
    provider_message_id = models.CharField(
        max_length=200,
        blank=True,
        help_text="Message ID from provider (WhatsApp, email server, etc.)"
    )
    provider_response = models.JSONField(
        default=dict,
        help_text="Full response from provider"
    )

    # Retry tracking
    retry_count = models.PositiveIntegerField(default=0)
    last_retry_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'notifications_delivery'
        unique_together = [('notification', 'channel')]
        indexes = [
            models.Index(fields=['status', 'sent_at']),
            models.Index(fields=['channel', 'status']),
        ]

    def __str__(self):
        return f"{self.notification.title} via {self.channel.get_channel_type_display()}: {self.status}"


class Announcement(AuditMixin, SoftDeleteMixin):
    """
    System-wide or targeted announcements.

    Announcements are visible on announcement boards and can be sent as notifications.
    """

    PRIORITY_CHOICES = (
        ('LOW', 'Low'),
        ('NORMAL', 'Normal'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    )

    TARGET_TYPES = (
        ('ALL', 'All Users'),
        ('DEPARTMENT', 'Specific Department'),
        ('ROLE', 'Specific Role'),
        ('LOCATION', 'Specific Location'),
        ('CUSTOM', 'Custom User List'),
    )

    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('SCHEDULED', 'Scheduled'),
        ('PUBLISHED', 'Published'),
        ('ARCHIVED', 'Archived'),
    )

    # Content
    title = models.CharField(max_length=200)
    message = models.TextField()
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='NORMAL'
    )

    # Rich content
    image = models.ImageField(
        upload_to='announcements/images/',
        null=True,
        blank=True
    )
    attachments = models.JSONField(
        default=list,
        help_text="List of attachment URLs/paths"
    )

    # Targeting
    target_type = models.CharField(
        max_length=20,
        choices=TARGET_TYPES,
        default='ALL'
    )
    target_departments = models.ManyToManyField(
        'hr.Department',
        blank=True,
        related_name='announcements'
    )
    target_locations = models.ManyToManyField(
        'inventory.Location',
        blank=True,
        related_name='announcements'
    )
    target_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='targeted_announcements'
    )

    # Publishing
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT'
    )
    publish_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When to publish (null = publish immediately)"
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When announcement expires"
    )

    # Author
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='announcements_created'
    )

    # Notification
    send_notification = models.BooleanField(
        default=False,
        help_text="Send as notification to targeted users?"
    )
    notification_channels = models.JSONField(
        default=list,
        help_text="Channels to send notification on"
    )

    # Action
    action_url = models.CharField(
        max_length=500,
        blank=True,
        help_text="URL for action button"
    )
    action_label = models.CharField(
        max_length=50,
        blank=True,
        help_text="Label for action button"
    )

    # Pinning
    is_pinned = models.BooleanField(
        default=False,
        help_text="Pin to top of announcement board?"
    )

    class Meta:
        db_table = 'notifications_announcement'
        indexes = [
            models.Index(fields=['-is_pinned', '-publish_at']),
            models.Index(fields=['status', '-publish_at']),
            models.Index(fields=['target_type']),
        ]
        ordering = ['-is_pinned', '-publish_at']

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    @property
    def is_published(self):
        """Check if announcement is published and not expired."""
        if self.status != 'PUBLISHED':
            return False
        if self.publish_at and self.publish_at > timezone.now():
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return True

    def get_target_users(self):
        """Get list of users who should see this announcement."""
        from django.contrib.auth import get_user_model
        User = get_user_model()

        if self.target_type == 'ALL':
            return User.objects.filter(is_active=True)
        elif self.target_type == 'DEPARTMENT':
            # Get users in target departments
            return User.objects.filter(
                hremployee__current_department__in=self.target_departments.all(),
                is_active=True
            ).distinct()
        elif self.target_type == 'LOCATION':
            # Get users in target locations
            return User.objects.filter(
                hremployee__work_location__in=self.target_locations.all(),
                is_active=True
            ).distinct()
        elif self.target_type == 'CUSTOM':
            return self.target_users.filter(is_active=True)

        return User.objects.none()


class AnnouncementRead(models.Model):
    """
    Track which users have read which announcements.
    """

    announcement = models.ForeignKey(
        Announcement,
        on_delete=models.CASCADE,
        related_name='reads'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='announcements_read'
    )
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications_announcement_read'
        unique_together = [('announcement', 'user')]
        indexes = [
            models.Index(fields=['announcement', 'read_at']),
            models.Index(fields=['user', 'read_at']),
        ]

    def __str__(self):
        return f"{self.user.username} read {self.announcement.title}"

"""
Core models for the Floor Management System

Includes audit logging, change history, and base models.
"""
from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone
import json


class TimeStampedModel(models.Model):
    """
    Abstract base model that provides self-updating
    'created_at' and 'updated_at' fields
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class AuditLog(models.Model):
    """
    Comprehensive audit log for tracking all changes in the system

    Tracks:
    - Who made the change (user)
    - What was changed (model, object_id, field)
    - When it was changed (timestamp)
    - What changed (old_value, new_value)
    - Why/How (action, ip_address, user_agent)
    """
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('VIEW', 'View'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('APPROVE', 'Approve'),
        ('REJECT', 'Reject'),
        ('EXPORT', 'Export'),
        ('IMPORT', 'Import'),
    ]

    # Who
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    username = models.CharField(max_length=150, blank=True)  # Backup if user deleted

    # What
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    object_id = models.CharField(max_length=255, null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    model_name = models.CharField(max_length=100, blank=True)
    object_repr = models.CharField(max_length=200, blank=True)

    # Action details
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    field_name = models.CharField(max_length=100, blank=True)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)

    # When
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)

    # Where/How
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    session_key = models.CharField(max_length=40, blank=True)

    # Additional context
    message = models.TextField(blank=True)
    extra_data = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['content_type', 'object_id', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
            models.Index(fields=['-timestamp']),
        ]
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'

    def __str__(self):
        return f"{self.username} - {self.action} - {self.model_name} - {self.timestamp}"

    @classmethod
    def log_action(cls, user, action, obj=None, message='', ip_address=None,
                   user_agent=None, field_name='', old_value='', new_value='', **extra):
        """
        Convenience method to create audit log entries

        Usage:
            AuditLog.log_action(
                user=request.user,
                action='UPDATE',
                obj=employee,
                message='Updated employee status',
                ip_address=request.META.get('REMOTE_ADDR'),
                field_name='employment_status',
                old_value='ACTIVE',
                new_value='TERMINATED'
            )
        """
        log_entry = cls(
            user=user,
            username=user.username if user else 'system',
            action=action,
            message=message,
            ip_address=ip_address,
            user_agent=user_agent or '',
            field_name=field_name,
            old_value=str(old_value) if old_value else '',
            new_value=str(new_value) if new_value else '',
            extra_data=extra
        )

        if obj:
            log_entry.content_object = obj
            log_entry.model_name = obj.__class__.__name__
            log_entry.object_repr = str(obj)
            log_entry.object_id = str(obj.pk)

        log_entry.save()
        return log_entry


class ChangeHistory(models.Model):
    """
    Detailed change history for specific models

    Stores complete before/after snapshots of objects
    """
    # What changed
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE
    )
    object_id = models.CharField(max_length=255)
    content_object = GenericForeignKey('content_type', 'object_id')

    # Change details
    field_changes = models.JSONField(
        help_text="JSON object with field: {old, new} pairs"
    )
    change_summary = models.TextField(blank=True)

    # Who and when
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='change_history'
    )
    changed_at = models.DateTimeField(default=timezone.now, db_index=True)

    # Metadata
    change_reason = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-changed_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id', '-changed_at']),
            models.Index(fields=['changed_by', '-changed_at']),
        ]
        verbose_name = 'Change History'
        verbose_name_plural = 'Change Histories'

    def __str__(self):
        return f"{self.content_type.model} {self.object_id} - {self.changed_at}"

    def get_changes_display(self):
        """Return a human-readable summary of changes"""
        changes = []
        for field, values in self.field_changes.items():
            old = values.get('old', '')
            new = values.get('new', '')
            changes.append(f"{field}: '{old}' → '{new}'")
        return ', '.join(changes)


class ActivityLog(models.Model):
    """
    User activity tracking for monitoring and analytics

    Lighter-weight than AuditLog, focused on user actions and navigation
    """
    ACTIVITY_TYPES = [
        ('PAGE_VIEW', 'Page View'),
        ('SEARCH', 'Search'),
        ('FILTER', 'Filter'),
        ('DOWNLOAD', 'Download'),
        ('UPLOAD', 'Upload'),
        ('API_CALL', 'API Call'),
        ('REPORT', 'Report Generation'),
        ('PRINT', 'Print'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='activity_logs'
    )
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)

    # Activity details
    path = models.CharField(max_length=500, blank=True)
    query_params = models.JSONField(default=dict, blank=True)
    description = models.TextField(blank=True)

    # Timing
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    duration_ms = models.IntegerField(
        null=True,
        blank=True,
        help_text="Duration of the activity in milliseconds"
    )

    # Context
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    session_key = models.CharField(max_length=40, blank=True)

    # Metadata
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['activity_type', '-timestamp']),
            models.Index(fields=['-timestamp']),
        ]
        verbose_name = 'Activity Log'
        verbose_name_plural = 'Activity Logs'

    def __str__(self):
        return f"{self.user.username} - {self.activity_type} - {self.timestamp}"


class SystemEvent(models.Model):
    """
    System-level events and errors

    For tracking system health, errors, and important events
    """
    EVENT_LEVELS = [
        ('DEBUG', 'Debug'),
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
    ]

    EVENT_CATEGORIES = [
        ('SYSTEM', 'System'),
        ('SECURITY', 'Security'),
        ('DATABASE', 'Database'),
        ('EMAIL', 'Email'),
        ('API', 'API'),
        ('TASK', 'Background Task'),
        ('INTEGRATION', 'Integration'),
    ]

    level = models.CharField(max_length=20, choices=EVENT_LEVELS)
    category = models.CharField(max_length=20, choices=EVENT_CATEGORIES)

    # Event details
    event_name = models.CharField(max_length=200)
    message = models.TextField()

    # Exception details (if applicable)
    exception_type = models.CharField(max_length=200, blank=True)
    exception_message = models.TextField(blank=True)
    stack_trace = models.TextField(blank=True)

    # Context
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='system_events'
    )

    # Technical details
    request_path = models.CharField(max_length=500, blank=True)
    request_method = models.CharField(max_length=10, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    # Additional data
    extra_data = models.JSONField(default=dict, blank=True)

    # Status
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_events'
    )
    resolution_notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['level', '-timestamp']),
            models.Index(fields=['category', '-timestamp']),
            models.Index(fields=['is_resolved', '-timestamp']),
        ]
        verbose_name = 'System Event'
        verbose_name_plural = 'System Events'

    def __str__(self):
        return f"{self.level} - {self.event_name} - {self.timestamp}"

    @classmethod
    def log_event(cls, level, category, event_name, message, user=None,
                  request=None, exception=None, **extra):
        """
        Convenience method to log system events

        Usage:
            SystemEvent.log_event(
                level='ERROR',
                category='EMAIL',
                event_name='Email Send Failed',
                message='Failed to send welcome email',
                user=user,
                exception=e
            )
        """
        event = cls(
            level=level,
            category=category,
            event_name=event_name,
            message=message,
            user=user,
            extra_data=extra
        )

        if request:
            event.request_path = request.path
            event.request_method = request.method
            event.ip_address = request.META.get('REMOTE_ADDR')

        if exception:
            event.exception_type = exception.__class__.__name__
            event.exception_message = str(exception)
            import traceback
            event.stack_trace = traceback.format_exc()

        event.save()
        return event

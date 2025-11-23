"""
Notification system for Floor Management System

Provides:
- In-app notifications for users
- Email notification integration
- Notification preferences
- Real-time notification delivery
"""
from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings


class Notification(models.Model):
    """
    User notifications

    Types: INFO, SUCCESS, WARNING, ERROR
    """
    NOTIFICATION_TYPES = [
        ('INFO', 'Information'),
        ('SUCCESS', 'Success'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('TASK', 'Task'),
        ('REMINDER', 'Reminder'),
    ]

    # Recipient
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    # Notification content
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='INFO')
    title = models.CharField(max_length=200)
    message = models.TextField()

    # Related object (optional)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    object_id = models.CharField(max_length=255, null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    # Action link (optional)
    action_url = models.CharField(max_length=500, blank=True)
    action_text = models.CharField(max_length=100, blank=True)

    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    # Email notification
    email_sent = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_read']),
        ]

    def __str__(self):
        return f"{self.title} - {self.user.username}"

    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])

    def send_email(self, force=False):
        """
        Send email notification

        Args:
            force: Send even if already sent
        """
        if self.email_sent and not force:
            return False

        if not self.user.email:
            return False

        try:
            subject = f"[{self.get_notification_type_display()}] {self.title}"

            # Build email message
            message_parts = [
                f"Hello {self.user.first_name or self.user.username},\n",
                self.message,
                "\n"
            ]

            if self.action_url:
                site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
                full_url = f"{site_url}{self.action_url}"
                message_parts.append(f"\n{self.action_text or 'View Details'}: {full_url}\n")

            message_parts.append("\n---\nFloor Management System")

            message = '\n'.join(message_parts)

            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[self.user.email],
                fail_silently=False
            )

            self.email_sent = True
            self.email_sent_at = timezone.now()
            self.save(update_fields=['email_sent', 'email_sent_at'])

            return True

        except Exception as e:
            # Log error
            from .models import SystemEvent
            SystemEvent.log_event(
                level='ERROR',
                category='EMAIL',
                event_name='Notification Email Failed',
                message=f'Failed to send notification email to {self.user.username}',
                exception=e
            )
            return False

    @classmethod
    def create_notification(cls, user, title, message, notification_type='INFO',
                          related_object=None, action_url='', action_text='',
                          send_email_notification=False, expires_in_days=None):
        """
        Create a notification

        Usage:
            Notification.create_notification(
                user=user,
                title='Leave Request Approved',
                message='Your leave request has been approved',
                notification_type='SUCCESS',
                related_object=leave_request,
                action_url='/hr/leave-requests/123/',
                action_text='View Request',
                send_email_notification=True
            )
        """
        expires_at = None
        if expires_in_days:
            from datetime import timedelta
            expires_at = timezone.now() + timedelta(days=expires_in_days)

        notification = cls.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            content_object=related_object,
            action_url=action_url,
            action_text=action_text,
            expires_at=expires_at
        )

        # Send email if requested
        if send_email_notification:
            notification.send_email()

        return notification

    @classmethod
    def bulk_create_notifications(cls, users, title, message, **kwargs):
        """
        Create notifications for multiple users

        Usage:
            Notification.bulk_create_notifications(
                users=User.objects.filter(is_staff=True),
                title='System Maintenance',
                message='System will be down for maintenance',
                notification_type='WARNING'
            )
        """
        notifications = []
        for user in users:
            notification = cls.create_notification(
                user=user,
                title=title,
                message=message,
                **kwargs
            )
            notifications.append(notification)

        return notifications

    @classmethod
    def get_unread_count(cls, user):
        """Get count of unread notifications for user"""
        return cls.objects.filter(user=user, is_read=False).count()

    @classmethod
    def mark_all_as_read(cls, user):
        """Mark all notifications as read for user"""
        return cls.objects.filter(
            user=user,
            is_read=False
        ).update(
            is_read=True,
            read_at=timezone.now()
        )

    @classmethod
    def cleanup_old_notifications(cls, days=90):
        """
        Delete old read notifications

        Args:
            days: Keep notifications from last N days

        Returns:
            Number of deleted notifications
        """
        from datetime import timedelta
        cutoff_date = timezone.now() - timedelta(days=days)

        count, _ = cls.objects.filter(
            is_read=True,
            created_at__lt=cutoff_date
        ).delete()

        return count


class NotificationPreference(models.Model):
    """
    User notification preferences

    Controls how users receive notifications
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='notification_preference'
    )

    # Email preferences
    email_enabled = models.BooleanField(default=True)
    email_for_errors = models.BooleanField(default=True)
    email_for_warnings = models.BooleanField(default=True)
    email_for_info = models.BooleanField(default=False)
    email_for_tasks = models.BooleanField(default=True)

    # Digest settings
    daily_digest = models.BooleanField(default=False)
    digest_time = models.TimeField(default='09:00:00')

    # Notification settings
    play_sound = models.BooleanField(default=True)
    desktop_notifications = models.BooleanField(default=True)

    # Updated
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Notification Preference'
        verbose_name_plural = 'Notification Preferences'

    def __str__(self):
        return f"Preferences for {self.user.username}"

    def should_send_email(self, notification_type):
        """
        Check if email should be sent for notification type

        Args:
            notification_type: Type of notification

        Returns:
            bool: True if email should be sent
        """
        if not self.email_enabled:
            return False

        type_mapping = {
            'ERROR': self.email_for_errors,
            'WARNING': self.email_for_warnings,
            'INFO': self.email_for_info,
            'TASK': self.email_for_tasks,
            'REMINDER': self.email_for_tasks,
            'SUCCESS': self.email_for_info,
        }

        return type_mapping.get(notification_type, False)

    @classmethod
    def get_or_create_for_user(cls, user):
        """Get or create notification preferences for user"""
        preference, created = cls.objects.get_or_create(user=user)
        return preference


# Notification utility functions

def notify_user(user, title, message, **kwargs):
    """
    Convenience function to notify a user

    Usage:
        notify_user(
            user=request.user,
            title='Welcome!',
            message='Welcome to the system',
            notification_type='SUCCESS'
        )
    """
    # Get user preferences
    preference = NotificationPreference.get_or_create_for_user(user)

    notification_type = kwargs.get('notification_type', 'INFO')

    # Check if email should be sent
    send_email = (
        kwargs.pop('send_email_notification', False) or
        preference.should_send_email(notification_type)
    )

    return Notification.create_notification(
        user=user,
        title=title,
        message=message,
        send_email_notification=send_email,
        **kwargs
    )


def notify_users(users, title, message, **kwargs):
    """
    Convenience function to notify multiple users

    Usage:
        notify_users(
            users=User.objects.filter(is_staff=True),
            title='Maintenance Alert',
            message='System will be down for maintenance'
        )
    """
    return Notification.bulk_create_notifications(
        users=users,
        title=title,
        message=message,
        **kwargs
    )


def notify_admins(title, message, **kwargs):
    """
    Notify all administrators

    Usage:
        notify_admins(
            title='Critical Error',
            message='Database connection failed',
            notification_type='ERROR'
        )
    """
    admins = User.objects.filter(is_superuser=True, is_active=True)
    return notify_users(admins, title, message, **kwargs)


def notify_staff(title, message, **kwargs):
    """
    Notify all staff members

    Usage:
        notify_staff(
            title='New Feature',
            message='A new feature has been released',
            notification_type='INFO'
        )
    """
    staff = User.objects.filter(is_staff=True, is_active=True)
    return notify_users(staff, title, message, **kwargs)

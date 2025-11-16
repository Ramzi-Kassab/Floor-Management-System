from django.conf import settings
from django.db import models


class HRAuditLog(models.Model):
    """
    Audit log for tracking User creation, permission changes, and RBAC updates.
    Records all security-relevant HR actions for compliance and debugging.
    """

    ACTION_CHOICES = [
        ('USER_CREATED', 'User Account Created'),
        ('USER_LINKED', 'User Linked to Employee'),
        ('USER_DEACTIVATED', 'User Account Deactivated'),
        ('GROUP_ADDED', 'User Added to Group'),
        ('GROUP_REMOVED', 'User Removed from Group'),
        ('PERMISSION_ADDED', 'Permission Added'),
        ('PERMISSION_REMOVED', 'Permission Removed'),
        ('POSITION_CHANGED', 'Employee Position Changed'),
        ('PASSWORD_RESET', 'Password Reset Required'),
        ('EMPLOYEE_CREATED', 'Employee Record Created'),
        ('EMPLOYEE_UPDATED', 'Employee Record Updated'),
    ]

    timestamp = models.DateTimeField(auto_now_add=True)

    action = models.CharField(max_length=50, choices=ACTION_CHOICES)

    # Optional links to related objects
    employee = models.ForeignKey(
        'HREmployee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )

    affected_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='hr_audit_entries'
    )

    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='hr_actions_performed'
    )

    # Details of the change
    details = models.TextField(blank=True, help_text='JSON or text details of the change')

    # Request metadata
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'hr_audit_log'
        ordering = ['-timestamp']
        verbose_name = 'HR Audit Log'
        verbose_name_plural = 'HR Audit Logs'
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['action']),
            models.Index(fields=['employee']),
            models.Index(fields=['affected_user']),
        ]

    def __str__(self):
        user_str = f"User {self.affected_user}" if self.affected_user else "Unknown"
        return f"{self.timestamp.strftime('%Y-%m-%d %H:%M')} - {self.get_action_display()} - {user_str}"

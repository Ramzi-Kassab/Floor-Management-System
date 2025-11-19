"""
Retrieval/Undo System Models

Allows employees to undo mistakes within a time window with supervisor approval.
Tracks all retrievals for employee accuracy metrics and audit trails.
"""

from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from floor_app.mixins import AuditMixin
from datetime import timedelta


class RetrievalRequest(AuditMixin):
    """
    Tracks retrieval/undo requests from employees.

    Features:
    - Auto-approval within time window (default 15 minutes)
    - Supervisor notification and manual approval
    - Dependency checking (prevents retrieval if dependent processes exist)
    - Full audit trail of original data
    - Employee accuracy metrics tracking
    """

    STATUS_CHOICES = (
        ('PENDING', 'Pending Supervisor Approval'),
        ('AUTO_APPROVED', 'Auto-Approved (Within Time Window)'),
        ('APPROVED', 'Approved by Supervisor'),
        ('REJECTED', 'Rejected'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    )

    ACTION_TYPE_CHOICES = (
        ('DELETE', 'Delete Record'),
        ('EDIT', 'Edit/Revert Changes'),
        ('UNDO', 'Undo Action'),
        ('RESTORE', 'Restore Deleted Record'),
    )

    # Employee who made the request
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='retrieval_requests',
        help_text='Employee requesting the retrieval'
    )

    # Supervisor who will approve
    supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='retrieval_approvals',
        help_text='Supervisor responsible for approval'
    )

    # Generic foreign key to any model that needs retrieval
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        help_text='Type of object to retrieve'
    )

    object_id = models.PositiveIntegerField(
        help_text='ID of object to retrieve'
    )

    content_object = GenericForeignKey('content_type', 'object_id')

    # Request details
    action_type = models.CharField(
        max_length=20,
        choices=ACTION_TYPE_CHOICES,
        default='UNDO',
        help_text='Type of retrieval action'
    )

    reason = models.TextField(
        help_text='Reason for retrieval request'
    )

    # Snapshot of original data before any changes
    original_data = models.JSONField(
        default=dict,
        blank=True,
        help_text='Snapshot of original object data'
    )

    # Status and workflow
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )

    # Timing information
    submitted_at = models.DateTimeField(
        auto_now_add=True,
        help_text='When the request was submitted'
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the request was approved'
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the retrieval was completed'
    )

    time_elapsed = models.DurationField(
        null=True,
        blank=True,
        help_text='Time elapsed from object creation to retrieval request'
    )

    # Dependency tracking
    has_dependent_processes = models.BooleanField(
        default=False,
        help_text='Whether dependent processes exist'
    )

    dependent_process_details = models.JSONField(
        default=dict,
        blank=True,
        help_text='Details of dependent processes'
    )

    # Notification tracking
    supervisor_notified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When supervisor was notified'
    )

    notification_sent = models.BooleanField(
        default=False,
        help_text='Whether notification was sent to supervisor'
    )

    # Rejection details
    rejection_reason = models.TextField(
        blank=True,
        help_text='Reason for rejection if rejected'
    )

    rejected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rejected_retrievals',
        help_text='User who rejected the request'
    )

    rejected_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the request was rejected'
    )

    class Meta:
        db_table = 'retrieval_request'
        verbose_name = 'Retrieval Request'
        verbose_name_plural = 'Retrieval Requests'
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['employee', 'status']),
            models.Index(fields=['supervisor', 'status']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['status', '-submitted_at']),
            models.Index(fields=['-submitted_at']),
        ]

    def __str__(self):
        return f"Retrieval Request #{self.id} - {self.employee.username} - {self.get_status_display()}"

    def is_within_time_window(self, window_minutes=15):
        """
        Check if request is within the auto-approval time window.

        Args:
            window_minutes: Number of minutes for auto-approval window

        Returns:
            bool: True if within window, False otherwise
        """
        if not self.time_elapsed:
            return False

        window = timedelta(minutes=window_minutes)
        return self.time_elapsed <= window

    def can_auto_approve(self, window_minutes=15):
        """
        Check if this request can be auto-approved.

        Conditions:
        - Must be within time window
        - Must not have dependent processes
        - Status must be PENDING

        Args:
            window_minutes: Number of minutes for auto-approval window

        Returns:
            tuple: (can_approve: bool, reason: str)
        """
        if self.status != 'PENDING':
            return False, "Request is not in PENDING status"

        if self.has_dependent_processes:
            return False, "Dependent processes exist"

        if not self.is_within_time_window(window_minutes):
            return False, f"Request is outside {window_minutes} minute time window"

        return True, "All conditions met for auto-approval"

    def approve(self, approved_by=None, auto=False):
        """
        Approve the retrieval request.

        Args:
            approved_by: User who approved the request
            auto: Whether this is an auto-approval
        """
        if auto:
            self.status = 'AUTO_APPROVED'
        else:
            self.status = 'APPROVED'

        self.approved_at = timezone.now()
        if approved_by:
            self.updated_by = approved_by

        self.save(update_fields=['status', 'approved_at', 'updated_at', 'updated_by'])

    def reject(self, rejected_by, reason):
        """
        Reject the retrieval request.

        Args:
            rejected_by: User who rejected the request
            reason: Reason for rejection
        """
        self.status = 'REJECTED'
        self.rejected_by = rejected_by
        self.rejected_at = timezone.now()
        self.rejection_reason = reason
        self.save(update_fields=['status', 'rejected_by', 'rejected_at', 'rejection_reason', 'updated_at'])

    def complete(self):
        """Mark the retrieval as completed."""
        self.status = 'COMPLETED'
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at', 'updated_at'])

    def cancel(self):
        """Cancel the retrieval request."""
        self.status = 'CANCELLED'
        self.save(update_fields=['status', 'updated_at'])

    def get_status_badge_class(self):
        """Get Bootstrap badge class for status display."""
        badge_classes = {
            'PENDING': 'warning',
            'AUTO_APPROVED': 'success',
            'APPROVED': 'success',
            'REJECTED': 'danger',
            'COMPLETED': 'primary',
            'CANCELLED': 'secondary',
        }
        return badge_classes.get(self.status, 'secondary')

    def get_object_display(self):
        """Get human-readable display of the related object."""
        if self.content_object:
            return str(self.content_object)
        return f"{self.content_type.model} #{self.object_id}"

    @property
    def is_pending(self):
        """Check if request is pending approval."""
        return self.status == 'PENDING'

    @property
    def is_approved(self):
        """Check if request is approved (manual or auto)."""
        return self.status in ['APPROVED', 'AUTO_APPROVED']

    @property
    def is_completed(self):
        """Check if retrieval is completed."""
        return self.status == 'COMPLETED'

    @property
    def is_rejected(self):
        """Check if request is rejected."""
        return self.status == 'REJECTED'

    @property
    def can_be_completed(self):
        """Check if request can be completed."""
        return self.is_approved and not self.is_completed


class RetrievalMetric(models.Model):
    """
    Aggregated metrics for employee retrieval accuracy.

    Calculated periodically to track employee performance and accuracy.
    """

    PERIOD_CHOICES = (
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly'),
        ('QUARTERLY', 'Quarterly'),
        ('YEARLY', 'Yearly'),
    )

    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='retrieval_metrics',
        help_text='Employee being measured'
    )

    period_type = models.CharField(
        max_length=20,
        choices=PERIOD_CHOICES,
        help_text='Type of period'
    )

    period_start = models.DateField(
        help_text='Start of period'
    )

    period_end = models.DateField(
        help_text='End of period'
    )

    # Counts
    total_actions = models.PositiveIntegerField(
        default=0,
        help_text='Total actions performed by employee'
    )

    retrieval_requests = models.PositiveIntegerField(
        default=0,
        help_text='Number of retrieval requests'
    )

    auto_approved = models.PositiveIntegerField(
        default=0,
        help_text='Number of auto-approved retrievals'
    )

    manually_approved = models.PositiveIntegerField(
        default=0,
        help_text='Number of manually approved retrievals'
    )

    rejected = models.PositiveIntegerField(
        default=0,
        help_text='Number of rejected retrievals'
    )

    completed = models.PositiveIntegerField(
        default=0,
        help_text='Number of completed retrievals'
    )

    # Calculated metrics
    accuracy_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=100.00,
        help_text='Accuracy rate (percentage)'
    )

    average_time_to_request = models.DurationField(
        null=True,
        blank=True,
        help_text='Average time from action to retrieval request'
    )

    # Audit
    calculated_at = models.DateTimeField(
        auto_now_add=True,
        help_text='When metrics were calculated'
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = 'retrieval_metric'
        verbose_name = 'Retrieval Metric'
        verbose_name_plural = 'Retrieval Metrics'
        ordering = ['-period_end', 'employee']
        unique_together = [['employee', 'period_type', 'period_start', 'period_end']]
        indexes = [
            models.Index(fields=['employee', 'period_type', '-period_end']),
            models.Index(fields=['period_type', '-period_end']),
        ]

    def __str__(self):
        return f"{self.employee.username} - {self.period_type} ({self.period_start} to {self.period_end})"

    def calculate_accuracy(self):
        """
        Calculate accuracy rate.

        Accuracy = (total_actions - retrieval_requests) / total_actions * 100
        """
        if self.total_actions == 0:
            self.accuracy_rate = 100.00
        else:
            errors = self.retrieval_requests
            self.accuracy_rate = ((self.total_actions - errors) / self.total_actions) * 100

        self.save(update_fields=['accuracy_rate', 'updated_at'])

    @property
    def error_rate(self):
        """Calculate error rate (inverse of accuracy)."""
        return 100.00 - float(self.accuracy_rate)

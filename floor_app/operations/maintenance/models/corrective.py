"""
Corrective Maintenance Models

Models for maintenance requests and work orders.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from floor_app.mixins import AuditMixin, SoftDeleteMixin, PublicIdMixin
from .asset import Asset


class MaintenanceRequest(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Request from operators/supervisors for maintenance.
    Simple form to report issues that need to be addressed.
    """

    STATUS_CHOICES = (
        ('NEW', 'New'),
        ('REVIEWED', 'Reviewed'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CONVERTED', 'Converted to Work Order'),
    )

    PRIORITY_CHOICES = (
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical - Production Stopped'),
    )

    # Identification
    request_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Unique request number (e.g., REQ-2025-0001)"
    )

    # Asset
    asset = models.ForeignKey(
        Asset,
        on_delete=models.PROTECT,
        related_name='maintenance_requests',
        help_text="Asset requiring maintenance"
    )

    # Request details
    title = models.CharField(
        max_length=200,
        help_text="Brief title of the issue"
    )
    description = models.TextField(
        help_text="Detailed description of the problem"
    )
    symptoms = models.TextField(
        blank=True,
        default="",
        help_text="Observable symptoms (noise, smell, vibration, etc.)"
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='MEDIUM',
        db_index=True,
        help_text="Urgency of the request"
    )

    # Requester information
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='maintenance_requests_created',
        help_text="User who created this request"
    )
    request_date = models.DateTimeField(
        auto_now_add=True,
        help_text="When request was submitted"
    )
    requester_phone = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="Contact phone for requester"
    )
    requester_location = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Location of the requester"
    )

    # Status workflow
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='NEW',
        db_index=True,
        help_text="Current status of the request"
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='requests_reviewed',
        help_text="Who reviewed this request"
    )
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When request was reviewed"
    )
    rejection_reason = models.TextField(
        blank=True,
        default="",
        help_text="Reason for rejection (if rejected)"
    )

    # Resulting work order
    work_order = models.OneToOneField(
        'WorkOrder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='source_request',
        help_text="Work order created from this request"
    )

    # Attachments (handled separately but we track count)
    has_attachments = models.BooleanField(
        default=False,
        help_text="Whether this request has attachments"
    )

    # Production impact
    is_production_stopped = models.BooleanField(
        default=False,
        help_text="Is production currently stopped due to this issue?"
    )
    estimated_downtime_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Estimated downtime if not fixed"
    )

    class Meta:
        db_table = "maintenance_request"
        verbose_name = "Maintenance Request"
        verbose_name_plural = "Maintenance Requests"
        ordering = ['-request_date']
        indexes = [
            models.Index(fields=['request_number'], name='ix_maint_req_num'),
            models.Index(fields=['status', 'priority'], name='ix_maint_req_stat_prio'),
            models.Index(fields=['asset', 'status'], name='ix_maint_req_asset_stat'),
            models.Index(fields=['requested_by', 'status'], name='ix_maint_req_user_stat'),
            models.Index(fields=['is_production_stopped'], name='ix_maint_req_prod_stop'),
        ]

    def __str__(self):
        return f"{self.request_number} - {self.title}"

    @property
    def status_display_class(self):
        """Bootstrap class for status badge."""
        mapping = {
            'NEW': 'primary',
            'REVIEWED': 'info',
            'APPROVED': 'success',
            'REJECTED': 'danger',
            'CONVERTED': 'secondary',
        }
        return mapping.get(self.status, 'secondary')

    @property
    def priority_display_class(self):
        """Bootstrap class for priority badge."""
        mapping = {
            'LOW': 'info',
            'MEDIUM': 'primary',
            'HIGH': 'warning',
            'CRITICAL': 'danger',
        }
        return mapping.get(self.priority, 'secondary')

    @property
    def age_in_hours(self):
        """How long since request was created."""
        delta = timezone.now() - self.request_date
        return int(delta.total_seconds() / 3600)

    @property
    def age_display(self):
        """Human-readable age."""
        hours = self.age_in_hours
        if hours < 1:
            minutes = int((timezone.now() - self.request_date).total_seconds() / 60)
            return f"{minutes} min ago"
        elif hours < 24:
            return f"{hours}h ago"
        else:
            days = hours // 24
            return f"{days}d ago"

    def approve(self, user):
        """Approve the request."""
        self.status = 'APPROVED'
        self.reviewed_by = user
        self.reviewed_at = timezone.now()
        self.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'updated_at'])

    def reject(self, user, reason=""):
        """Reject the request."""
        self.status = 'REJECTED'
        self.reviewed_by = user
        self.reviewed_at = timezone.now()
        self.rejection_reason = reason
        self.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'rejection_reason', 'updated_at'])


class WorkOrder(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Main work order - the job executed by maintenance team.
    Can be created from PM tasks, requests, or directly.
    """

    STATUS_CHOICES = (
        ('PLANNED', 'Planned'),
        ('ASSIGNED', 'Assigned'),
        ('IN_PROGRESS', 'In Progress'),
        ('WAITING_PARTS', 'Waiting for Parts'),
        ('WAITING_VENDOR', 'Waiting for Vendor'),
        ('ON_HOLD', 'On Hold'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    )

    PRIORITY_CHOICES = (
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    )

    TYPE_CHOICES = (
        ('CORRECTIVE', 'Corrective'),
        ('PREVENTIVE', 'Preventive'),
        ('EMERGENCY', 'Emergency'),
        ('IMPROVEMENT', 'Improvement'),
        ('INSPECTION', 'Inspection'),
    )

    ROOT_CAUSE_CHOICES = (
        ('MECHANICAL', 'Mechanical Failure'),
        ('ELECTRICAL', 'Electrical Failure'),
        ('HYDRAULIC', 'Hydraulic Issue'),
        ('PNEUMATIC', 'Pneumatic Issue'),
        ('CONTROL_SOFTWARE', 'Control/Software Issue'),
        ('WEAR', 'Normal Wear'),
        ('MISUSE', 'Operator Misuse'),
        ('SAFETY_EVENT', 'Safety Event'),
        ('UTILITY', 'Utility (Power/Air/Water)'),
        ('CALIBRATION', 'Calibration Issue'),
        ('CONTAMINATION', 'Contamination'),
        ('EXTERNAL', 'External Factor'),
        ('UNKNOWN', 'Unknown'),
        ('OTHER', 'Other'),
    )

    # Identification
    wo_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Unique work order number (e.g., WO-2025-0001)"
    )

    # Asset
    asset = models.ForeignKey(
        Asset,
        on_delete=models.PROTECT,
        related_name='work_orders',
        help_text="Asset being worked on"
    )

    # Classification
    wo_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='CORRECTIVE',
        db_index=True,
        help_text="Type of maintenance work"
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='MEDIUM',
        db_index=True,
        help_text="Work order priority"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PLANNED',
        db_index=True,
        help_text="Current status"
    )

    # Problem description
    title = models.CharField(
        max_length=200,
        help_text="Brief title of the work"
    )
    problem_description = models.TextField(
        help_text="Detailed description of the problem/work needed"
    )

    # Planning
    planned_start = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Planned start date/time"
    )
    planned_end = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Planned completion date/time"
    )
    estimated_duration_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Estimated time to complete (minutes)"
    )

    # Execution
    actual_start = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When work actually started"
    )
    actual_end = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When work was completed"
    )
    actual_duration_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Actual time spent (minutes)"
    )

    # Assignment
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_work_orders',
        help_text="Primary person assigned"
    )
    assigned_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the WO was assigned"
    )

    # Team members (comma-separated IDs or names for simplicity)
    team_member_ids = models.TextField(
        blank=True,
        default="",
        help_text="IDs of additional team members (comma-separated)"
    )
    team_member_names = models.TextField(
        blank=True,
        default="",
        help_text="Names of team members (denormalized)"
    )

    # Root Cause Analysis
    root_cause_category = models.CharField(
        max_length=20,
        choices=ROOT_CAUSE_CHOICES,
        blank=True,
        default="",
        help_text="Primary root cause category"
    )
    root_cause_detail = models.TextField(
        blank=True,
        default="",
        help_text="Detailed root cause analysis"
    )

    # Solution
    solution_summary = models.TextField(
        blank=True,
        default="",
        help_text="Summary of solution implemented"
    )
    actions_taken = models.TextField(
        blank=True,
        default="",
        help_text="Detailed actions taken"
    )

    # Follow-up
    follow_up_required = models.BooleanField(
        default=False,
        help_text="Whether follow-up work is needed"
    )
    follow_up_notes = models.TextField(
        blank=True,
        default="",
        help_text="Details about required follow-up"
    )
    follow_up_wo = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='parent_wo',
        help_text="Follow-up work order created"
    )

    # Source tracking
    source_pm_task_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="PM Task ID if created from PM"
    )
    # source_request handled via OneToOne in MaintenanceRequest

    # Costs
    labor_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Labor cost"
    )
    parts_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Parts and materials cost"
    )
    external_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="External services cost (vendor, contractor)"
    )

    # Completion
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='completed_work_orders',
        help_text="Who marked as complete"
    )

    # On-hold/Waiting info
    waiting_reason = models.TextField(
        blank=True,
        default="",
        help_text="Reason for waiting (parts, vendor, etc.)"
    )
    waiting_since = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When waiting status started"
    )

    # Cancellation
    cancellation_reason = models.TextField(
        blank=True,
        default="",
        help_text="Reason for cancellation"
    )
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cancelled_work_orders',
        help_text="Who cancelled the WO"
    )

    class Meta:
        db_table = "maintenance_work_order"
        verbose_name = "Work Order"
        verbose_name_plural = "Work Orders"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['wo_number'], name='ix_maint_wo_num'),
            models.Index(fields=['status', 'priority'], name='ix_maint_wo_stat_prio'),
            models.Index(fields=['asset', 'status'], name='ix_maint_wo_asset_stat'),
            models.Index(fields=['wo_type', 'status'], name='ix_maint_wo_type_stat'),
            models.Index(fields=['assigned_to', 'status'], name='ix_maint_wo_assigned'),
            models.Index(fields=['planned_start'], name='ix_maint_wo_planned'),
        ]

    def __str__(self):
        return f"{self.wo_number} - {self.title}"

    @property
    def status_display_class(self):
        """Bootstrap class for status badge."""
        mapping = {
            'PLANNED': 'secondary',
            'ASSIGNED': 'info',
            'IN_PROGRESS': 'warning',
            'WAITING_PARTS': 'warning',
            'WAITING_VENDOR': 'warning',
            'ON_HOLD': 'dark',
            'COMPLETED': 'success',
            'CANCELLED': 'danger',
        }
        return mapping.get(self.status, 'secondary')

    @property
    def priority_display_class(self):
        """Bootstrap class for priority badge."""
        mapping = {
            'LOW': 'info',
            'MEDIUM': 'primary',
            'HIGH': 'warning',
            'CRITICAL': 'danger',
        }
        return mapping.get(self.priority, 'secondary')

    @property
    def total_cost(self):
        """Total cost of the work order."""
        return self.labor_cost + self.parts_cost + self.external_cost

    @property
    def is_overdue(self):
        """Check if WO is overdue."""
        if self.status in ['COMPLETED', 'CANCELLED']:
            return False
        if self.planned_end:
            return self.planned_end < timezone.now()
        return False

    @property
    def age_in_days(self):
        """Days since WO was created."""
        delta = timezone.now() - self.created_at
        return delta.days

    @property
    def estimated_duration_display(self):
        """Human-readable estimated duration."""
        if not self.estimated_duration_minutes:
            return "Not set"
        if self.estimated_duration_minutes < 60:
            return f"{self.estimated_duration_minutes} min"
        hours = self.estimated_duration_minutes // 60
        minutes = self.estimated_duration_minutes % 60
        if minutes:
            return f"{hours}h {minutes}m"
        return f"{hours}h"

    @property
    def actual_duration_display(self):
        """Human-readable actual duration."""
        if not self.actual_duration_minutes:
            return "Not recorded"
        if self.actual_duration_minutes < 60:
            return f"{self.actual_duration_minutes} min"
        hours = self.actual_duration_minutes // 60
        minutes = self.actual_duration_minutes % 60
        if minutes:
            return f"{hours}h {minutes}m"
        return f"{hours}h"

    def assign(self, user):
        """Assign the work order to a user."""
        self.assigned_to = user
        self.assigned_at = timezone.now()
        self.status = 'ASSIGNED'
        self.save(update_fields=['assigned_to', 'assigned_at', 'status', 'updated_at'])

    def start_work(self):
        """Start working on the WO."""
        self.status = 'IN_PROGRESS'
        self.actual_start = timezone.now()
        self.save(update_fields=['status', 'actual_start', 'updated_at'])

    def complete_work(self, user, solution="", actions=""):
        """Complete the work order."""
        self.status = 'COMPLETED'
        self.actual_end = timezone.now()
        self.completed_by = user

        if self.actual_start:
            delta = self.actual_end - self.actual_start
            self.actual_duration_minutes = int(delta.total_seconds() / 60)

        self.solution_summary = solution
        self.actions_taken = actions

        # Update asset's last maintenance date
        self.asset.last_maintenance_date = timezone.now().date()
        self.asset.save(update_fields=['last_maintenance_date', 'updated_at'])

        self.save()

    def set_waiting_parts(self, reason=""):
        """Set status to waiting for parts."""
        self.status = 'WAITING_PARTS'
        self.waiting_reason = reason
        self.waiting_since = timezone.now()
        self.save(update_fields=['status', 'waiting_reason', 'waiting_since', 'updated_at'])

    def set_waiting_vendor(self, reason=""):
        """Set status to waiting for vendor."""
        self.status = 'WAITING_VENDOR'
        self.waiting_reason = reason
        self.waiting_since = timezone.now()
        self.save(update_fields=['status', 'waiting_reason', 'waiting_since', 'updated_at'])

    def cancel(self, user, reason=""):
        """Cancel the work order."""
        self.status = 'CANCELLED'
        self.cancelled_by = user
        self.cancellation_reason = reason
        self.save(update_fields=['status', 'cancelled_by', 'cancellation_reason', 'updated_at'])


class WorkOrderAttachment(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Files attached to work orders (photos of defects, reports, etc.)
    """

    ATTACHMENT_TYPE_CHOICES = (
        ('PHOTO', 'Photo'),
        ('REPORT', 'Report'),
        ('INVOICE', 'Invoice'),
        ('MANUAL', 'Manual'),
        ('OTHER', 'Other'),
    )

    work_order = models.ForeignKey(
        WorkOrder,
        on_delete=models.CASCADE,
        related_name='attachments',
        help_text="Work order this file belongs to"
    )
    title = models.CharField(
        max_length=200,
        help_text="Attachment title"
    )
    attachment_type = models.CharField(
        max_length=20,
        choices=ATTACHMENT_TYPE_CHOICES,
        default='OTHER',
        help_text="Type of attachment"
    )
    file = models.FileField(
        upload_to='maintenance/wo_attachments/%Y/%m/',
        help_text="Uploaded file"
    )
    description = models.TextField(
        blank=True,
        default="",
        help_text="Description of the attachment"
    )

    class Meta:
        db_table = "maintenance_wo_attachment"
        verbose_name = "Work Order Attachment"
        verbose_name_plural = "Work Order Attachments"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['work_order', 'attachment_type'], name='ix_maint_woatt_wo_type'),
        ]

    def __str__(self):
        return f"{self.work_order.wo_number} - {self.title}"

    @property
    def file_extension(self):
        """Get file extension."""
        if self.file:
            return self.file.name.split('.')[-1].upper()
        return ""

    @property
    def file_size_display(self):
        """Get human-readable file size."""
        if self.file:
            size = self.file.size
            if size < 1024:
                return f"{size} B"
            elif size < 1024 * 1024:
                return f"{size / 1024:.1f} KB"
            else:
                return f"{size / (1024 * 1024):.1f} MB"
        return "0 B"

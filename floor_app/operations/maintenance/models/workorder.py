"""
Maintenance Request and Work Order models.
"""
from django.db import models
from django.conf import settings
from floor_app.mixins import AuditMixin, SoftDeleteMixin, PublicIdMixin
from .asset import Asset


class MaintenanceRequest(AuditMixin, SoftDeleteMixin, models.Model):
    """Request for maintenance from operators/supervisors."""

    class Priority(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'
        CRITICAL = 'CRITICAL', 'Critical - Production Stopped'

    class Status(models.TextChoices):
        NEW = 'NEW', 'New'
        UNDER_REVIEW = 'UNDER_REVIEW', 'Under Review'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        CONVERTED_TO_WO = 'CONVERTED_TO_WO', 'Converted to Work Order'
        CANCELLED = 'CANCELLED', 'Cancelled'

    request_number = models.CharField(max_length=50, unique=True, editable=False)
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT, related_name='maintenance_requests')

    title = models.CharField(max_length=255)
    description = models.TextField(help_text="Describe the problem/symptoms")
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)

    # Requester info
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='maintenance_requests'
    )
    department = models.ForeignKey(
        'hr.Department', on_delete=models.SET_NULL, null=True, blank=True
    )

    # Status & Review
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reviewed_maintenance_requests'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)

    # Conversion
    converted_work_order = models.OneToOneField(
        'maintenance.MaintenanceWorkOrder', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='source_request'
    )

    # Attachments (photos of problem)
    attachments = models.ManyToManyField(
        'knowledge.Document', blank=True, related_name='maintenance_requests'
    )

    class Meta:
        verbose_name = 'Maintenance Request'
        verbose_name_plural = 'Maintenance Requests'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['request_number']),
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['asset', 'status']),
        ]
        permissions = [
            ('can_approve_request', 'Can approve maintenance requests'),
        ]

    def __str__(self):
        return f"{self.request_number} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.request_number:
            from django.utils import timezone
            prefix = f"REQ-{timezone.now().strftime('%Y%m%d')}"
            last = MaintenanceRequest.all_objects.filter(
                request_number__startswith=prefix
            ).order_by('-request_number').first()
            if last:
                num = int(last.request_number.split('-')[-1]) + 1
            else:
                num = 1
            self.request_number = f"{prefix}-{num:04d}"
        super().save(*args, **kwargs)

    def approve(self, reviewer):
        """Approve request and prepare for work order creation."""
        from django.utils import timezone
        self.status = self.Status.APPROVED
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.save()

    def reject(self, reviewer, reason):
        """Reject the request."""
        from django.utils import timezone
        self.status = self.Status.REJECTED
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.rejection_reason = reason
        self.save()


class MaintenanceWorkOrder(AuditMixin, SoftDeleteMixin, PublicIdMixin, models.Model):
    """Work order for maintenance execution."""

    class WorkOrderType(models.TextChoices):
        PREVENTIVE = 'PREVENTIVE', 'Preventive Maintenance'
        CORRECTIVE = 'CORRECTIVE', 'Corrective/Breakdown'
        EMERGENCY = 'EMERGENCY', 'Emergency Repair'
        INSPECTION = 'INSPECTION', 'Inspection'
        MODIFICATION = 'MODIFICATION', 'Modification/Upgrade'
        INSTALLATION = 'INSTALLATION', 'Installation'

    class Priority(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'
        CRITICAL = 'CRITICAL', 'Critical'

    class Status(models.TextChoices):
        PLANNED = 'PLANNED', 'Planned'
        ASSIGNED = 'ASSIGNED', 'Assigned'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        WAITING_PARTS = 'WAITING_PARTS', 'Waiting for Parts'
        WAITING_VENDOR = 'WAITING_VENDOR', 'Waiting for Vendor'
        ON_HOLD = 'ON_HOLD', 'On Hold'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    class RootCauseCategory(models.TextChoices):
        MECHANICAL = 'MECHANICAL', 'Mechanical Failure'
        ELECTRICAL = 'ELECTRICAL', 'Electrical Issue'
        HYDRAULIC = 'HYDRAULIC', 'Hydraulic System'
        PNEUMATIC = 'PNEUMATIC', 'Pneumatic System'
        CONTROL_SOFTWARE = 'CONTROL_SOFTWARE', 'Control/Software'
        WEAR = 'WEAR', 'Normal Wear & Tear'
        MISUSE = 'MISUSE', 'Operator Misuse'
        SAFETY_EVENT = 'SAFETY_EVENT', 'Safety Event'
        UTILITY = 'UTILITY', 'Utility (Power/Air/Water)'
        ENVIRONMENTAL = 'ENVIRONMENTAL', 'Environmental'
        UNKNOWN = 'UNKNOWN', 'Unknown/Under Investigation'
        OTHER = 'OTHER', 'Other'

    # Core identification
    work_order_number = models.CharField(max_length=50, unique=True, editable=False)
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT, related_name='work_orders')

    # Description
    title = models.CharField(max_length=255)
    description = models.TextField()
    work_order_type = models.CharField(
        max_length=20, choices=WorkOrderType.choices, default=WorkOrderType.CORRECTIVE
    )
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PLANNED)

    # Scheduling
    planned_start = models.DateTimeField(null=True, blank=True)
    planned_end = models.DateTimeField(null=True, blank=True)
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)

    # Assignment
    assigned_to = models.ForeignKey(
        'hr.HREmployee', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_work_orders'
    )
    assigned_team = models.JSONField(
        default=list, blank=True, help_text="List of employee IDs on this work order"
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_work_orders'
    )
    assigned_at = models.DateTimeField(null=True, blank=True)

    # Problem Analysis
    problem_description = models.TextField(blank=True, help_text="Detailed problem analysis")
    failure_mode = models.CharField(max_length=255, blank=True)
    root_cause_category = models.CharField(
        max_length=20, choices=RootCauseCategory.choices, blank=True
    )
    root_cause_detail = models.TextField(blank=True, help_text="Detailed root cause explanation")

    # Solution
    solution_summary = models.TextField(blank=True)
    work_performed = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)

    # Costs
    labor_hours = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    labor_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    parts_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    external_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    # Completion
    completed_by = models.ForeignKey(
        'hr.HREmployee', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='completed_work_orders'
    )

    # Attachments
    attachments = models.ManyToManyField(
        'knowledge.Document', blank=True, related_name='work_orders'
    )

    # Flags
    requires_shutdown = models.BooleanField(default=False)
    safety_permit_required = models.BooleanField(default=False)
    contractor_involved = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Maintenance Work Order'
        verbose_name_plural = 'Maintenance Work Orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['work_order_number']),
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['asset', 'status']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['work_order_type', 'status']),
        ]
        permissions = [
            ('can_assign_workorder', 'Can assign work orders'),
            ('can_complete_workorder', 'Can complete work orders'),
        ]

    def __str__(self):
        return f"{self.work_order_number} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.work_order_number:
            from django.utils import timezone
            prefix = f"WO-{timezone.now().strftime('%Y%m')}"
            last = MaintenanceWorkOrder.all_objects.filter(
                work_order_number__startswith=prefix
            ).order_by('-work_order_number').first()
            if last:
                num = int(last.work_order_number.split('-')[-1]) + 1
            else:
                num = 1
            self.work_order_number = f"{prefix}-{num:05d}"

        # Calculate total cost
        if any([self.labor_cost, self.parts_cost, self.external_cost]):
            self.total_cost = (self.labor_cost or 0) + (self.parts_cost or 0) + (self.external_cost or 0)

        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        from django.utils import timezone
        if self.planned_end and self.status not in ['COMPLETED', 'CANCELLED']:
            return timezone.now() > self.planned_end
        return False

    @property
    def duration_hours(self):
        if self.actual_start and self.actual_end:
            delta = self.actual_end - self.actual_start
            return round(delta.total_seconds() / 3600, 2)
        return None


class WorkOrderNote(models.Model):
    """Comments and updates on work orders."""

    class NoteType(models.TextChoices):
        PROGRESS = 'PROGRESS', 'Progress Update'
        ISSUE = 'ISSUE', 'Issue Encountered'
        RESOLUTION = 'RESOLUTION', 'Resolution'
        GENERAL = 'GENERAL', 'General Note'
        PARTS = 'PARTS', 'Parts Related'

    work_order = models.ForeignKey(
        MaintenanceWorkOrder, on_delete=models.CASCADE, related_name='notes'
    )
    note_type = models.CharField(max_length=20, choices=NoteType.choices, default=NoteType.GENERAL)
    content = models.TextField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Work Order Note'
        verbose_name_plural = 'Work Order Notes'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.work_order.work_order_number} - {self.note_type} @ {self.created_at}"


class WorkOrderPart(models.Model):
    """Parts/consumables used in work order."""

    work_order = models.ForeignKey(
        MaintenanceWorkOrder, on_delete=models.CASCADE, related_name='parts_used'
    )
    part_number = models.CharField(max_length=100)
    part_description = models.CharField(max_length=255)
    quantity_used = models.DecimalField(max_digits=10, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    warehouse_location = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)

    # Future inventory integration
    inventory_item_id = models.PositiveBigIntegerField(null=True, blank=True)
    inventory_transaction_id = models.PositiveBigIntegerField(null=True, blank=True)

    class Meta:
        verbose_name = 'Work Order Part'
        verbose_name_plural = 'Work Order Parts'

    def __str__(self):
        return f"{self.work_order.work_order_number} - {self.part_number} x {self.quantity_used}"

    def save(self, *args, **kwargs):
        if self.unit_cost and self.quantity_used:
            self.total_cost = self.unit_cost * self.quantity_used
        super().save(*args, **kwargs)

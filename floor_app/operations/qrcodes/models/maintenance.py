"""
Equipment and Maintenance models for QR-based maintenance tracking.

Enables quick issue reporting and maintenance workflow via QR scanning.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone

from floor_app.mixins import AuditMixin, SoftDeleteMixin, PublicIdMixin


class EquipmentStatus:
    """Status constants for equipment."""
    OPERATIONAL = 'OPERATIONAL'
    MAINTENANCE_SCHEDULED = 'MAINTENANCE_SCHEDULED'
    UNDER_MAINTENANCE = 'UNDER_MAINTENANCE'
    OUT_OF_SERVICE = 'OUT_OF_SERVICE'
    DECOMMISSIONED = 'DECOMMISSIONED'

    CHOICES = (
        (OPERATIONAL, 'Operational'),
        (MAINTENANCE_SCHEDULED, 'Maintenance Scheduled'),
        (UNDER_MAINTENANCE, 'Under Maintenance'),
        (OUT_OF_SERVICE, 'Out of Service'),
        (DECOMMISSIONED, 'Decommissioned'),
    )


class MaintenancePriority:
    """Priority levels for maintenance requests."""
    LOW = 'LOW'
    MEDIUM = 'MEDIUM'
    HIGH = 'HIGH'
    CRITICAL = 'CRITICAL'

    CHOICES = (
        (LOW, 'Low'),
        (MEDIUM, 'Medium'),
        (HIGH, 'High'),
        (CRITICAL, 'Critical'),
    )


class MaintenanceRequestStatus:
    """Status constants for maintenance requests."""
    OPEN = 'OPEN'
    ACKNOWLEDGED = 'ACKNOWLEDGED'
    IN_PROGRESS = 'IN_PROGRESS'
    WAITING_PARTS = 'WAITING_PARTS'
    COMPLETED = 'COMPLETED'
    CANCELLED = 'CANCELLED'

    CHOICES = (
        (OPEN, 'Open'),
        (ACKNOWLEDGED, 'Acknowledged'),
        (IN_PROGRESS, 'In Progress'),
        (WAITING_PARTS, 'Waiting for Parts'),
        (COMPLETED, 'Completed'),
        (CANCELLED, 'Cancelled'),
    )


class EquipmentType:
    """Equipment type classification."""
    MACHINE = 'MACHINE'
    TOOL = 'TOOL'
    VEHICLE = 'VEHICLE'
    MEASUREMENT = 'MEASUREMENT'
    SAFETY = 'SAFETY'
    IT_EQUIPMENT = 'IT_EQUIPMENT'
    OTHER = 'OTHER'

    CHOICES = (
        (MACHINE, 'Machine'),
        (TOOL, 'Tool'),
        (VEHICLE, 'Vehicle'),
        (MEASUREMENT, 'Measurement Device'),
        (SAFETY, 'Safety Equipment'),
        (IT_EQUIPMENT, 'IT Equipment'),
        (OTHER, 'Other'),
    )


class EquipmentManager(models.Manager):
    """Custom manager for Equipment."""

    def operational(self):
        """Get operational equipment."""
        return self.filter(status=EquipmentStatus.OPERATIONAL, is_deleted=False)

    def needs_maintenance(self):
        """Get equipment needing maintenance."""
        return self.filter(
            status__in=[
                EquipmentStatus.MAINTENANCE_SCHEDULED,
                EquipmentStatus.OUT_OF_SERVICE
            ],
            is_deleted=False
        )

    def by_location(self, location_id):
        """Get equipment at a specific location."""
        return self.filter(location_id=location_id, is_deleted=False)


class Equipment(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Equipment master record for machines, tools, and other assets.

    Designed for QR code integration to enable quick maintenance reporting
    and history tracking via scanning.
    """

    # Basic identification
    code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Unique equipment code"
    )

    name = models.CharField(
        max_length=200,
        help_text="Equipment name"
    )

    description = models.TextField(
        blank=True,
        default="",
        help_text="Equipment description"
    )

    # Classification
    equipment_type = models.CharField(
        max_length=20,
        choices=EquipmentType.CHOICES,
        default=EquipmentType.MACHINE,
        db_index=True,
        help_text="Type of equipment"
    )

    # Manufacturer info
    manufacturer = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Manufacturer name"
    )

    model_number = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Model number"
    )

    serial_number = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Serial number"
    )

    # Location (link to inventory.Location)
    location_id = models.BigIntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Location ID where equipment is installed"
    )
    location_name = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Location name (cached)"
    )

    # Ownership
    department_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Department ID that owns this equipment"
    )
    department_name = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Department name (cached)"
    )

    # Status
    status = models.CharField(
        max_length=30,
        choices=EquipmentStatus.CHOICES,
        default=EquipmentStatus.OPERATIONAL,
        db_index=True,
        help_text="Current equipment status"
    )

    # Dates
    purchase_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date of purchase"
    )

    installation_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date of installation"
    )

    warranty_expiry_date = models.DateField(
        null=True,
        blank=True,
        help_text="Warranty expiration date"
    )

    last_maintenance_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date of last maintenance"
    )

    next_maintenance_date = models.DateField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Scheduled next maintenance"
    )

    # Maintenance schedule
    maintenance_interval_days = models.IntegerField(
        null=True,
        blank=True,
        help_text="Days between scheduled maintenance"
    )

    # Financial
    purchase_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Purchase cost"
    )

    current_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Current book value"
    )

    # Usage metrics
    total_hours_operated = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Total hours of operation"
    )

    # QR Code reference
    qcode_id = models.BigIntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="QCode ID for this equipment"
    )

    # Additional info
    specifications = models.JSONField(
        default=dict,
        blank=True,
        help_text="Technical specifications as JSON"
    )

    notes = models.TextField(
        blank=True,
        default="",
        help_text="Additional notes"
    )

    objects = EquipmentManager()

    class Meta:
        db_table = 'qrcode_equipment'
        verbose_name = 'Equipment'
        verbose_name_plural = 'Equipment'
        ordering = ['code']
        indexes = [
            models.Index(fields=['code'], name='ix_equipment_code'),
            models.Index(fields=['status'], name='ix_equipment_status'),
            models.Index(fields=['equipment_type'], name='ix_equipment_type'),
            models.Index(fields=['location_id'], name='ix_equipment_location'),
            models.Index(fields=['next_maintenance_date'], name='ix_equipment_maint'),
            models.Index(fields=['qcode_id'], name='ix_equipment_qcode'),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def needs_maintenance(self):
        """Check if equipment needs maintenance."""
        if not self.next_maintenance_date:
            return False
        return self.next_maintenance_date <= timezone.now().date()

    @property
    def days_until_maintenance(self):
        """Days until next scheduled maintenance."""
        if not self.next_maintenance_date:
            return None
        delta = self.next_maintenance_date - timezone.now().date()
        return delta.days


class MaintenanceRequest(AuditMixin):
    """
    Maintenance request record for equipment issues.

    Created via QR code scanning for quick issue reporting.
    """

    # Equipment being serviced
    equipment = models.ForeignKey(
        Equipment,
        on_delete=models.CASCADE,
        related_name='maintenance_requests',
        help_text="Equipment requiring maintenance"
    )

    # Request details
    title = models.CharField(
        max_length=200,
        help_text="Short description of issue"
    )

    description = models.TextField(
        help_text="Detailed description of the issue"
    )

    # Reporter info
    reported_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reported_maintenance_requests',
        help_text="User who reported the issue"
    )
    reported_by_employee_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="HR Employee ID of reporter"
    )
    reported_by_name = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Reporter name (cached)"
    )

    reported_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="When issue was reported"
    )

    # Priority and status
    priority = models.CharField(
        max_length=20,
        choices=MaintenancePriority.CHOICES,
        default=MaintenancePriority.MEDIUM,
        db_index=True,
        help_text="Request priority"
    )

    status = models.CharField(
        max_length=20,
        choices=MaintenanceRequestStatus.CHOICES,
        default=MaintenanceRequestStatus.OPEN,
        db_index=True,
        help_text="Current status"
    )

    # Assignment
    assigned_to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_maintenance_requests',
        help_text="Technician assigned to fix"
    )
    assigned_to_employee_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="HR Employee ID of assignee"
    )
    assigned_to_name = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Assignee name (cached)"
    )

    # Scheduling
    due_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Target completion date"
    )

    scheduled_start = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Scheduled start time"
    )

    # Work tracking
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When work actually started"
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When work was completed"
    )

    # Resolution
    resolution_notes = models.TextField(
        blank=True,
        default="",
        help_text="Notes about how the issue was resolved"
    )

    parts_used = models.TextField(
        blank=True,
        default="",
        help_text="Parts/materials used for repair"
    )

    labor_hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Hours of labor"
    )

    total_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total cost of maintenance"
    )

    # QR/Scan tracking
    scan_log_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="ScanLog ID that created this request"
    )

    # Type of maintenance
    maintenance_type = models.CharField(
        max_length=30,
        choices=(
            ('CORRECTIVE', 'Corrective (Breakdown)'),
            ('PREVENTIVE', 'Preventive (Scheduled)'),
            ('PREDICTIVE', 'Predictive (Condition-based)'),
            ('IMPROVEMENT', 'Improvement/Upgrade'),
        ),
        default='CORRECTIVE',
        help_text="Type of maintenance"
    )

    class Meta:
        db_table = 'qrcode_maintenance_request'
        verbose_name = 'Maintenance Request'
        verbose_name_plural = 'Maintenance Requests'
        ordering = ['-reported_at']
        indexes = [
            models.Index(fields=['equipment'], name='ix_maintreq_equipment'),
            models.Index(fields=['status'], name='ix_maintreq_status'),
            models.Index(fields=['priority'], name='ix_maintreq_priority'),
            models.Index(fields=['-reported_at'], name='ix_maintreq_reported'),
            models.Index(fields=['assigned_to_employee_id'], name='ix_maintreq_assigned'),
            models.Index(fields=['due_date'], name='ix_maintreq_due'),
        ]

    def __str__(self):
        return f"{self.equipment.code} - {self.title}"

    @property
    def is_overdue(self):
        """Check if request is overdue."""
        if not self.due_date:
            return False
        if self.status in [MaintenanceRequestStatus.COMPLETED, MaintenanceRequestStatus.CANCELLED]:
            return False
        return timezone.now() > self.due_date

    @property
    def resolution_time_hours(self):
        """Calculate time from report to completion."""
        if not self.completed_at:
            return None
        delta = self.completed_at - self.reported_at
        return delta.total_seconds() / 3600

    def acknowledge(self, user=None, employee_id=None, employee_name=""):
        """Mark request as acknowledged."""
        self.status = MaintenanceRequestStatus.ACKNOWLEDGED
        self.assigned_to_user = user
        self.assigned_to_employee_id = employee_id
        self.assigned_to_name = employee_name
        self.save()

    def start_work(self):
        """Mark work as started."""
        self.status = MaintenanceRequestStatus.IN_PROGRESS
        self.started_at = timezone.now()
        self.save()

    def complete(self, resolution_notes="", parts_used="", labor_hours=None, total_cost=None):
        """Mark request as completed."""
        self.status = MaintenanceRequestStatus.COMPLETED
        self.completed_at = timezone.now()
        self.resolution_notes = resolution_notes
        self.parts_used = parts_used
        if labor_hours is not None:
            self.labor_hours = labor_hours
        if total_cost is not None:
            self.total_cost = total_cost
        self.save()

        # Update equipment maintenance date
        self.equipment.last_maintenance_date = timezone.now().date()
        if self.equipment.maintenance_interval_days:
            from datetime import timedelta
            self.equipment.next_maintenance_date = (
                timezone.now().date() +
                timedelta(days=self.equipment.maintenance_interval_days)
            )
        self.equipment.status = EquipmentStatus.OPERATIONAL
        self.equipment.save()

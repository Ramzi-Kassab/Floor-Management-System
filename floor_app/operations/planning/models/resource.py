"""
Planning & KPI - Resource Management
Resource types and capacity tracking for scheduling.
"""
from django.db import models
from floor_app.mixins import PublicIdMixin, AuditMixin, SoftDeleteMixin


class ResourceType(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Categories of resources (machines, work stations, skills, tools).
    Used for capacity planning and resource allocation.
    """
    CATEGORY_CHOICES = [
        ('MACHINE', 'Machine/Equipment'),
        ('STATION', 'Work Station'),
        ('SKILL', 'Skill/Competency'),
        ('TOOL', 'Tooling'),
        ('AREA', 'Production Area'),
    ]

    code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Resource type code (e.g., CNC-GRINDING, BRAZING-STATION)"
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default="")
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    department = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="Department this resource belongs to"
    )

    # Capacity settings
    default_capacity_per_shift = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=8.0,
        help_text="Default available hours per shift"
    )
    efficiency_factor = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.85,
        help_text="Expected efficiency (0-1, e.g., 0.85 = 85%)"
    )

    # Planning constraints
    is_bottleneck = models.BooleanField(
        default=False,
        help_text="Known bottleneck resource - needs close monitoring"
    )
    is_active = models.BooleanField(default=True)

    # Setup and changeover
    setup_time_minutes = models.PositiveIntegerField(
        default=0,
        help_text="Average setup/changeover time in minutes"
    )
    min_batch_size = models.PositiveIntegerField(
        default=1,
        help_text="Minimum batch size for efficiency"
    )

    class Meta:
        db_table = "planning_resource_type"
        verbose_name = "Resource Type"
        verbose_name_plural = "Resource Types"
        ordering = ['category', 'code']
        indexes = [
            models.Index(fields=['code'], name='ix_plan_restype_code'),
            models.Index(fields=['category'], name='ix_plan_restype_cat'),
            models.Index(fields=['is_bottleneck'], name='ix_plan_restype_bottleneck'),
            models.Index(fields=['is_active'], name='ix_plan_restype_active'),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def effective_capacity_per_shift(self):
        """Calculate effective capacity considering efficiency."""
        return float(self.default_capacity_per_shift) * float(self.efficiency_factor)


class ResourceCapacity(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Available capacity by date and shift.
    Tracks planned vs actual resource utilization.
    """
    SHIFT_CHOICES = [
        ('DAY', 'Day Shift'),
        ('NIGHT', 'Night Shift'),
        ('ALL', 'All Day'),
    ]

    resource_type = models.ForeignKey(
        ResourceType,
        on_delete=models.CASCADE,
        related_name='capacity_records'
    )
    date = models.DateField(db_index=True)
    shift = models.CharField(
        max_length=20,
        choices=SHIFT_CHOICES,
        default='ALL'
    )

    # Available capacity
    available_hours = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        help_text="Total available hours for this resource on this date"
    )
    reserved_hours = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        help_text="Hours reserved for maintenance, training, etc."
    )

    # Calculated load
    planned_load_hours = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        help_text="Total planned work hours"
    )
    actual_load_hours = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        help_text="Actual hours used (updated from shop floor)"
    )

    # Notes
    notes = models.TextField(blank=True, default="")

    class Meta:
        db_table = "planning_resource_capacity"
        verbose_name = "Resource Capacity"
        verbose_name_plural = "Resource Capacities"
        ordering = ['date', 'resource_type']
        unique_together = ['resource_type', 'date', 'shift']
        indexes = [
            models.Index(
                fields=['resource_type', 'date'],
                name='ix_plan_rescap_type_date'
            ),
            models.Index(fields=['date'], name='ix_plan_rescap_date'),
        ]

    def __str__(self):
        return f"{self.resource_type.code} - {self.date} ({self.shift})"

    @property
    def net_available_hours(self):
        """Available hours minus reserved hours."""
        return float(self.available_hours) - float(self.reserved_hours)

    @property
    def utilization_percentage(self):
        """Calculate planned utilization percentage."""
        if self.available_hours > 0:
            return (float(self.planned_load_hours) / float(self.available_hours)) * 100
        return 0

    @property
    def actual_utilization_percentage(self):
        """Calculate actual utilization percentage."""
        if self.available_hours > 0:
            return (float(self.actual_load_hours) / float(self.available_hours)) * 100
        return 0

    @property
    def is_overloaded(self):
        """Check if planned load exceeds available capacity."""
        return float(self.planned_load_hours) > self.net_available_hours

    @property
    def remaining_capacity(self):
        """Calculate remaining available capacity."""
        return self.net_available_hours - float(self.planned_load_hours)

    def add_planned_load(self, hours):
        """Add hours to planned load."""
        self.planned_load_hours = float(self.planned_load_hours) + hours
        self.save()

    def update_actual_load(self, hours):
        """Update actual load hours."""
        self.actual_load_hours = float(self.actual_load_hours) + hours
        self.save()

"""
Sales & Lifecycle - Drilling Operations
Tracks drilling runs, operational parameters, and bit performance in the field.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from floor_app.mixins import PublicIdMixin, AuditMixin, SoftDeleteMixin
from .customer import Customer, Rig, Well


class DrillingRun(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    A single drilling run for a bit.
    Tracks operational data, footage drilled, and performance.
    A bit can have multiple runs (rerun after repair/retrofit).
    """
    STATUS_CHOICES = [
        ('PLANNED', 'Planned'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('TRIPPED', 'Tripped Out'),
        ('FAILED', 'Failed/Pulled Early'),
    ]

    # Identification
    run_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Unique run identifier"
    )

    # Bit Reference (loose coupling to inventory.SerialUnit)
    serial_unit_id = models.BigIntegerField(
        db_index=True,
        help_text="Reference to inventory.SerialUnit"
    )
    bit_serial_number = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Bit serial number (denormalized)"
    )
    mat_number = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="MAT at time of run"
    )
    bit_size_inches = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    # Run Sequence for this bit
    run_sequence = models.PositiveIntegerField(
        default=1,
        help_text="Run 1, Run 2, etc. for this bit"
    )

    # Location Context
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name='drilling_runs'
    )
    well = models.ForeignKey(
        Well,
        on_delete=models.PROTECT,
        related_name='drilling_runs'
    )
    rig = models.ForeignKey(
        Rig,
        on_delete=models.PROTECT,
        related_name='drilling_runs'
    )

    # Hole Section Details
    hole_section = models.CharField(
        max_length=50,
        help_text="Hole size (e.g., 8½\", 12¼\", 17½\")"
    )
    hole_type = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="Open hole, casing, etc."
    )

    # Depth Information
    depth_in_ft = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Measured Depth In (feet)"
    )
    depth_out_ft = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Measured Depth Out (feet)"
    )
    tvd_in_ft = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="True Vertical Depth In"
    )
    tvd_out_ft = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="True Vertical Depth Out"
    )

    # Footage & Performance
    footage_drilled = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total footage drilled"
    )
    hours_on_bottom = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Rotating hours on bottom"
    )
    avg_rop = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Average Rate of Penetration (ft/hr)"
    )
    max_rop = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maximum ROP achieved"
    )

    # Operating Parameters
    avg_wob_klbs = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Average Weight on Bit (1000 lbs)"
    )
    max_wob_klbs = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True
    )
    avg_rpm = models.DecimalField(
        max_digits=6,
        decimal_places=1,
        null=True,
        blank=True,
        help_text="Average rotary RPM"
    )
    max_rpm = models.DecimalField(
        max_digits=6,
        decimal_places=1,
        null=True,
        blank=True
    )
    avg_flow_rate_gpm = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Average flow rate (gallons/min)"
    )
    avg_standpipe_psi = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Average standpipe pressure (psi)"
    )
    avg_torque_kftlbs = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Average torque (1000 ft-lbs)"
    )

    # Mud Properties
    mud_type = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="WBM, OBM, SBM, etc."
    )
    mud_weight_ppg = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Mud weight (lbs/gallon)"
    )
    mud_properties_json = models.JSONField(
        default=dict,
        help_text="Additional mud properties"
    )

    # Nozzles
    nozzle_configuration = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Nozzle sizes (e.g., 5x14, 2x16)"
    )
    tfa_sqin = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        null=True,
        blank=True,
        help_text="Total Flow Area (sq.in.)"
    )

    # Formation
    formation_name = models.CharField(max_length=100, blank=True, default="")
    lithology = models.TextField(
        blank=True,
        default="",
        help_text="Formation description"
    )

    # Timing
    run_in_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When bit was run in hole"
    )
    run_out_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When bit was pulled out"
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PLANNED',
        db_index=True
    )

    # Trip Reason
    trip_reason = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Why bit was pulled (TD, wear, failure, etc.)"
    )

    # Problems Encountered
    problems_encountered = models.TextField(
        blank=True,
        default="",
        help_text="Vibrations, stability issues, losses, etc."
    )
    downhole_tool_failures = models.TextField(blank=True, default="")

    # Dull Grade Reference (will be set after evaluation)
    dull_grade_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Reference to DullGradeEvaluation"
    )

    # Additional Data (flexible JSON)
    bha_details_json = models.JSONField(
        default=dict,
        help_text="Bottom Hole Assembly details"
    )
    directional_data_json = models.JSONField(
        default=dict,
        help_text="Inclination, azimuth, DLS, etc."
    )
    operational_summary = models.TextField(blank=True, default="")

    # Data Source
    reported_by = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Drilling engineer/contractor who reported"
    )
    report_date = models.DateField(null=True, blank=True)

    notes = models.TextField(blank=True, default="")

    class Meta:
        db_table = "sales_drilling_run"
        verbose_name = "Drilling Run"
        verbose_name_plural = "Drilling Runs"
        ordering = ['bit_serial_number', 'run_sequence']
        indexes = [
            models.Index(fields=['run_number'], name='ix_sales_drun_number'),
            models.Index(fields=['serial_unit_id'], name='ix_sales_drun_serial'),
            models.Index(fields=['bit_serial_number'], name='ix_sales_drun_bitsn'),
            models.Index(fields=['customer'], name='ix_sales_drun_customer'),
            models.Index(fields=['well'], name='ix_sales_drun_well'),
            models.Index(fields=['status'], name='ix_sales_drun_status'),
            models.Index(
                fields=['bit_serial_number', 'run_sequence'],
                name='ix_sales_drun_bit_seq'
            ),
        ]

    def __str__(self):
        return f"{self.run_number} - {self.bit_serial_number} Run #{self.run_sequence}"

    @classmethod
    def generate_run_number(cls):
        """Generate unique run number."""
        year = timezone.now().year
        prefix = f"RUN-{year}-"
        last_run = cls.all_objects.filter(
            run_number__startswith=prefix
        ).order_by('-run_number').first()
        if last_run:
            try:
                last_num = int(last_run.run_number.split('-')[-1])
                next_num = last_num + 1
            except ValueError:
                next_num = 1
        else:
            next_num = 1
        return f"{prefix}{next_num:06d}"

    def save(self, *args, **kwargs):
        """Calculate footage and ROP if possible."""
        if self.depth_out_ft and self.depth_in_ft:
            self.footage_drilled = float(self.depth_out_ft) - float(self.depth_in_ft)

        if self.footage_drilled and self.hours_on_bottom and float(self.hours_on_bottom) > 0:
            self.avg_rop = float(self.footage_drilled) / float(self.hours_on_bottom)

        super().save(*args, **kwargs)

    @property
    def cost_per_foot(self):
        """Calculate cost per foot if data available."""
        # Would need bit cost and operational costs
        return None

    @property
    def performance_score(self):
        """Calculate a simple performance score."""
        # Based on ROP vs expected, footage vs target, etc.
        if self.avg_rop and self.footage_drilled:
            return float(self.avg_rop) * float(self.footage_drilled) / 1000
        return None

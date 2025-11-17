"""
Quality Management - Equipment Calibration Control
Tracking measuring instruments and their calibration status.
"""
from django.db import models
from django.utils import timezone
from datetime import timedelta
from floor_app.mixins import PublicIdMixin, AuditMixin, SoftDeleteMixin


class CalibratedEquipment(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Measuring instruments and equipment under calibration control.
    Tracks calibration schedules, status, and compliance.
    """
    EQUIPMENT_TYPE_CHOICES = [
        ('TORQUE_WRENCH', 'Torque Wrench'),
        ('THREAD_GAUGE', 'Thread Gauge'),
        ('BORE_GAUGE', 'Bore Gauge'),
        ('MICROMETER', 'Micrometer'),
        ('CALIPER', 'Caliper'),
        ('DEPTH_GAUGE', 'Depth Gauge'),
        ('HEIGHT_GAUGE', 'Height Gauge'),
        ('LPT_KIT', 'LPT Testing Kit'),
        ('MPI_EQUIPMENT', 'MPI Equipment'),
        ('HARDNESS_TESTER', 'Hardness Tester'),
        ('SURFACE_ROUGHNESS', 'Surface Roughness Tester'),
        ('OPTICAL_COMPARATOR', 'Optical Comparator'),
        ('CMM', 'Coordinate Measuring Machine'),
        ('OTHER', 'Other'),
    ]

    STATUS_CHOICES = [
        ('IN_SERVICE', 'In Service - Calibration Current'),
        ('DUE_SOON', 'Due for Calibration Soon'),
        ('OVERDUE', 'Calibration Overdue - Do Not Use'),
        ('OUT_OF_SERVICE', 'Out of Service'),
        ('UNDER_CALIBRATION', 'Under Calibration'),
        ('QUARANTINE', 'Quarantine - Investigation Needed'),
    ]

    CALIBRATION_RESULT_CHOICES = [
        ('PASS', 'Pass - Within Tolerance'),
        ('ADJUSTED', 'Adjusted - Now Within Tolerance'),
        ('FAIL', 'Fail - Out of Tolerance'),
        ('LIMITED', 'Limited Use - Conditional Pass'),
    ]

    # Identification
    equipment_id = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Internal equipment ID tag (e.g., CAL-001)"
    )
    name = models.CharField(max_length=200)
    equipment_type = models.CharField(
        max_length=50,
        choices=EQUIPMENT_TYPE_CHOICES
    )
    manufacturer = models.CharField(max_length=100, blank=True, default="")
    model = models.CharField(max_length=100, blank=True, default="")
    serial_number = models.CharField(max_length=100, blank=True, default="")

    # Calibration requirements
    calibration_interval_days = models.PositiveIntegerField(
        default=365,
        help_text="Days between calibrations"
    )
    calibration_procedure = models.TextField(
        blank=True,
        default="",
        help_text="Reference to calibration procedure document"
    )
    calibration_standard = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Standard used for calibration (e.g., ISO 17025)"
    )

    # Current calibration status
    last_calibration_date = models.DateField(null=True, blank=True)
    next_calibration_due = models.DateField(
        null=True,
        blank=True,
        db_index=True
    )
    last_calibration_result = models.CharField(
        max_length=20,
        choices=CALIBRATION_RESULT_CHOICES,
        blank=True,
        default=""
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='IN_SERVICE',
        db_index=True
    )

    # Location and custody
    location = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Physical location of equipment"
    )
    custodian = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Person responsible for this equipment"
    )

    # Certificate tracking
    certificate_number = models.CharField(
        max_length=100,
        blank=True,
        default=""
    )
    calibration_lab = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="External lab or internal calibration"
    )

    # Importance
    is_critical = models.BooleanField(
        default=False,
        help_text="Critical for product quality - requires expedited calibration"
    )

    # Additional metadata
    purchase_date = models.DateField(null=True, blank=True)
    warranty_expiry = models.DateField(null=True, blank=True)
    purchase_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    class Meta:
        db_table = "quality_calibrated_equipment"
        verbose_name = "Calibrated Equipment"
        verbose_name_plural = "Calibrated Equipment"
        ordering = ['equipment_id']
        indexes = [
            models.Index(fields=['equipment_id'], name='ix_qual_caleq_id'),
            models.Index(fields=['status'], name='ix_qual_caleq_status'),
            models.Index(
                fields=['next_calibration_due'],
                name='ix_qual_caleq_due'
            ),
            models.Index(
                fields=['equipment_type'],
                name='ix_qual_caleq_type'
            ),
            models.Index(
                fields=['is_critical', 'status'],
                name='ix_qual_caleq_crit_stat'
            ),
        ]

    def __str__(self):
        return f"{self.equipment_id} - {self.name}"

    def update_status(self):
        """Update status based on calibration due date."""
        if not self.next_calibration_due:
            return

        today = timezone.now().date()
        days_until_due = (self.next_calibration_due - today).days

        if self.status in ['OUT_OF_SERVICE', 'UNDER_CALIBRATION', 'QUARANTINE']:
            # Don't auto-update these manual states
            return

        if days_until_due < 0:
            self.status = 'OVERDUE'
        elif days_until_due <= 30:
            self.status = 'DUE_SOON'
        else:
            self.status = 'IN_SERVICE'

    def record_calibration(self, calibration_date, result, next_due_date=None):
        """Record a new calibration event and update status."""
        self.last_calibration_date = calibration_date
        self.last_calibration_result = result

        if next_due_date:
            self.next_calibration_due = next_due_date
        else:
            self.next_calibration_due = calibration_date + timedelta(
                days=self.calibration_interval_days
            )

        if result in ['PASS', 'ADJUSTED']:
            self.status = 'IN_SERVICE'
        elif result == 'LIMITED':
            self.status = 'IN_SERVICE'  # But with restrictions
        else:  # FAIL
            self.status = 'OUT_OF_SERVICE'

        self.update_status()
        self.save()

    @property
    def days_until_due(self):
        """Calculate days until next calibration."""
        if self.next_calibration_due:
            return (self.next_calibration_due - timezone.now().date()).days
        return None

    @property
    def is_usable(self):
        """Check if equipment is safe to use."""
        return self.status in ['IN_SERVICE', 'DUE_SOON']


class CalibrationRecord(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Historical record of calibration events.
    Maintains full calibration history for traceability.
    """
    equipment = models.ForeignKey(
        CalibratedEquipment,
        on_delete=models.CASCADE,
        related_name='calibration_records'
    )

    calibration_date = models.DateField()
    performed_by = models.CharField(
        max_length=100,
        help_text="Technician or lab who performed calibration"
    )
    calibration_lab = models.CharField(
        max_length=200,
        blank=True,
        default=""
    )
    certificate_number = models.CharField(max_length=100)

    result = models.CharField(
        max_length=20,
        choices=CalibratedEquipment.CALIBRATION_RESULT_CHOICES
    )
    adjustments_made = models.TextField(
        blank=True,
        default="",
        help_text="Description of any adjustments made"
    )
    out_of_tolerance_findings = models.TextField(
        blank=True,
        default="",
        help_text="Details of out-of-tolerance conditions found"
    )

    # Detailed measurements (flexible JSON structure)
    measurements_json = models.JSONField(
        default=dict,
        help_text="Actual measurement data from calibration"
    )

    next_due_date = models.DateField()
    cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    # Document reference
    certificate_file = models.FileField(
        upload_to='quality/calibration/',
        blank=True,
        null=True
    )

    class Meta:
        db_table = "quality_calibration_record"
        verbose_name = "Calibration Record"
        verbose_name_plural = "Calibration Records"
        ordering = ['equipment', '-calibration_date']
        indexes = [
            models.Index(fields=['equipment'], name='ix_qual_calrec_equip'),
            models.Index(
                fields=['calibration_date'],
                name='ix_qual_calrec_date'
            ),
            models.Index(
                fields=['certificate_number'],
                name='ix_qual_calrec_cert'
            ),
            models.Index(fields=['result'], name='ix_qual_calrec_result'),
        ]

    def __str__(self):
        return f"{self.equipment.equipment_id} - {self.calibration_date}"

    def save(self, *args, **kwargs):
        """Update equipment status after saving calibration record."""
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            # Update the equipment's calibration info
            self.equipment.record_calibration(
                self.calibration_date,
                self.result,
                self.next_due_date
            )
            # Update certificate info
            self.equipment.certificate_number = self.certificate_number
            self.equipment.calibration_lab = self.calibration_lab
            self.equipment.save()

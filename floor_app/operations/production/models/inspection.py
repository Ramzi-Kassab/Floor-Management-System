"""
NDT & Thread Inspection Layer

Models for non-destructive testing (LPT, MPI, etc.) and API thread inspection.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from floor_app.mixins import AuditMixin


class ApiThreadInspection(AuditMixin):
    """
    API thread/connection inspection record.

    Documents the condition and any repairs needed for the bit's threaded connection.
    """

    RESULT_CHOICES = (
        ('PASS', 'Pass'),
        ('FAIL', 'Fail'),
        ('REPAIR_REQUIRED', 'Repair Required'),
        ('CONDITIONAL_PASS', 'Conditional Pass'),
        ('REJECT', 'Reject'),
    )

    THREAD_TYPE_CHOICES = (
        ('API_REG', 'API Regular'),
        ('API_IF', 'API Internal Flush'),
        ('API_FH', 'API Full Hole'),
        ('OTHER', 'Other'),
    )

    DAMAGE_TYPE_CHOICES = (
        ('NONE', 'No Damage'),
        ('GALLING', 'Galling'),
        ('THREAD_WEAR', 'Thread Wear'),
        ('CROSS_THREAD', 'Cross Threading'),
        ('CORROSION', 'Corrosion'),
        ('MECHANICAL_DAMAGE', 'Mechanical Damage'),
        ('SEAL_AREA_DAMAGE', 'Seal Area Damage'),
        ('MULTIPLE', 'Multiple Issues'),
        ('OTHER', 'Other'),
    )

    job_card = models.ForeignKey(
        'JobCard',
        on_delete=models.CASCADE,
        related_name='thread_inspections',
        help_text="Job card being inspected"
    )

    # Inspection metadata
    inspection_date = models.DateTimeField(
        default=timezone.now,
        help_text="Date/time of inspection"
    )
    inspected_by = models.ForeignKey(
        'hr.HREmployee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='thread_inspections',
        help_text="Inspector"
    )

    # Thread details
    thread_type = models.CharField(
        max_length=20,
        choices=THREAD_TYPE_CHOICES,
        default='API_REG',
        help_text="Type of thread connection"
    )
    thread_size = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="Thread size specification"
    )

    # Inspection results
    result = models.CharField(
        max_length=20,
        choices=RESULT_CHOICES,
        default='PASS',
        db_index=True
    )
    damage_type = models.CharField(
        max_length=30,
        choices=DAMAGE_TYPE_CHOICES,
        default='NONE'
    )

    # Detailed findings
    description_of_issue = models.TextField(
        blank=True,
        default="",
        help_text="Detailed description of any issues found"
    )
    measurement_results = models.TextField(
        blank=True,
        default="",
        help_text="Specific measurements taken (e.g., pitch diameter, taper)"
    )

    # Repair actions
    repair_action = models.TextField(
        blank=True,
        default="",
        help_text="Repair actions taken or recommended"
    )
    repair_completed = models.BooleanField(
        default=False,
        help_text="Repair has been completed"
    )
    repair_completed_at = models.DateTimeField(
        null=True,
        blank=True
    )
    repaired_by = models.ForeignKey(
        'hr.HREmployee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='thread_repairs',
        help_text="Employee who performed repair"
    )

    # Final status
    final_status = models.CharField(
        max_length=20,
        choices=RESULT_CHOICES,
        default='PASS',
        help_text="Final status after any repairs"
    )
    final_notes = models.TextField(
        blank=True,
        default="",
        help_text="Final inspection notes"
    )

    # Verification
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_thread_inspections',
        help_text="User who verified the inspection"
    )
    verified_at = models.DateTimeField(
        null=True,
        blank=True
    )

    # Attachments (placeholder for future file storage)
    has_photos = models.BooleanField(
        default=False,
        help_text="Photos attached to this inspection"
    )

    class Meta:
        db_table = "production_api_thread_inspection"
        verbose_name = "API Thread Inspection"
        verbose_name_plural = "API Thread Inspections"
        ordering = ['-inspection_date']
        indexes = [
            models.Index(fields=['job_card'], name='ix_thread_jc'),
            models.Index(fields=['result'], name='ix_thread_result'),
            models.Index(fields=['inspection_date'], name='ix_thread_date'),
        ]

    def __str__(self):
        return f"{self.job_card.job_card_number} - Thread Inspection ({self.result})"

    @property
    def needs_repair(self):
        """Check if repair is required."""
        return self.result in ('FAIL', 'REPAIR_REQUIRED') and not self.repair_completed

    def complete_repair(self, employee, notes=''):
        """Mark repair as completed."""
        self.repair_completed = True
        self.repair_completed_at = timezone.now()
        self.repaired_by = employee
        if notes:
            self.final_notes = notes
        self.final_status = 'PASS'
        self.save(update_fields=[
            'repair_completed', 'repair_completed_at', 'repaired_by',
            'final_notes', 'final_status', 'updated_at'
        ])


class NdtReport(AuditMixin):
    """
    Non-Destructive Testing (NDT) report.

    Records results of tests like:
    - LPT (Liquid Penetrant Testing)
    - MPI (Magnetic Particle Inspection)
    - Die Check
    - Visual Inspection
    """

    TEST_TYPE_CHOICES = (
        ('LPT', 'Liquid Penetrant Testing'),
        ('MPI', 'Magnetic Particle Inspection'),
        ('DIE_CHECK', 'Die Check'),
        ('VISUAL', 'Visual Inspection'),
        ('UT', 'Ultrasonic Testing'),
        ('RT', 'Radiographic Testing'),
        ('OTHER', 'Other'),
    )

    RESULT_CHOICES = (
        ('PASS', 'Pass'),
        ('FAIL', 'Fail'),
        ('CONDITIONAL', 'Conditional Pass'),
        ('INCONCLUSIVE', 'Inconclusive'),
        ('RETEST_REQUIRED', 'Retest Required'),
    )

    SEVERITY_CHOICES = (
        ('NONE', 'No Defects'),
        ('MINOR', 'Minor Defects'),
        ('MODERATE', 'Moderate Defects'),
        ('SEVERE', 'Severe Defects'),
        ('CRITICAL', 'Critical Defects'),
    )

    job_card = models.ForeignKey(
        'JobCard',
        on_delete=models.CASCADE,
        related_name='ndt_reports',
        help_text="Job card being tested"
    )

    # Test metadata
    test_type = models.CharField(
        max_length=20,
        choices=TEST_TYPE_CHOICES,
        db_index=True
    )
    test_date = models.DateTimeField(
        default=timezone.now,
        help_text="Date/time of test"
    )

    # Personnel
    performed_by = models.ForeignKey(
        'hr.HREmployee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ndt_tests_performed',
        help_text="Technician who performed the test"
    )
    verified_by = models.ForeignKey(
        'hr.HREmployee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ndt_tests_verified',
        help_text="Inspector who verified results"
    )

    # Test details
    test_procedure = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Test procedure/standard used"
    )
    test_area = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Area of bit tested (e.g., 'blade faces', 'body', 'connection')"
    )

    # Results
    result = models.CharField(
        max_length=20,
        choices=RESULT_CHOICES,
        default='PASS',
        db_index=True
    )
    defect_severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        default='NONE'
    )

    # Findings
    defects_found = models.TextField(
        blank=True,
        default="",
        help_text="Description of defects found (if any)"
    )
    defect_locations = models.TextField(
        blank=True,
        default="",
        help_text="Location of defects on the bit"
    )
    recommendations = models.TextField(
        blank=True,
        default="",
        help_text="Recommendations based on findings"
    )

    # Equipment used
    equipment_used = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="NDT equipment/materials used"
    )
    calibration_ref = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Equipment calibration reference"
    )

    # Environmental conditions (can affect test results)
    ambient_temp = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        help_text="Ambient temperature during test (°C)"
    )
    humidity = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        help_text="Humidity percentage during test"
    )

    # General notes
    notes = models.TextField(
        blank=True,
        default="",
        help_text="Additional notes"
    )

    # Report reference
    report_number = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="NDT report/certificate number"
    )

    # Attachments placeholder
    has_photos = models.BooleanField(
        default=False,
        help_text="Photos attached to this report"
    )
    has_report_document = models.BooleanField(
        default=False,
        help_text="PDF/document attached"
    )

    class Meta:
        db_table = "production_ndt_report"
        verbose_name = "NDT Report"
        verbose_name_plural = "NDT Reports"
        ordering = ['-test_date']
        indexes = [
            models.Index(fields=['job_card', 'test_type'], name='ix_ndt_jc_type'),
            models.Index(fields=['result'], name='ix_ndt_result'),
            models.Index(fields=['test_date'], name='ix_ndt_date'),
        ]

    def __str__(self):
        return f"{self.job_card.job_card_number} - {self.get_test_type_display()} ({self.result})"

    @property
    def passed(self):
        """Check if test passed."""
        return self.result == 'PASS'

    @property
    def needs_retest(self):
        """Check if retest is needed."""
        return self.result in ('INCONCLUSIVE', 'RETEST_REQUIRED')

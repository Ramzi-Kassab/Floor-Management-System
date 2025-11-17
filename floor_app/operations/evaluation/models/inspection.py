"""
Inspection Models for Thread and NDT (Non-Destructive Testing)

These models track inspection results for API threads and NDT methods
such as Liquid Penetrant Testing (LPT), Magnetic Particle Inspection (MPI),
and Ultrasonic Testing (UT).
"""

from django.db import models
from django.utils import timezone


class ThreadInspection(models.Model):
    """
    API thread inspection results for the bit connection.

    Records the condition of pin/box threads, any damage found,
    measurements taken, and repair recommendations.
    """

    RESULT_CHOICES = (
        ('OK', 'OK - No Issues'),
        ('MINOR_DAMAGE', 'Minor Damage - Acceptable'),
        ('MAJOR_DAMAGE', 'Major Damage - Needs Attention'),
        ('REPAIRABLE', 'Repairable'),
        ('SCRAP', 'Scrap - Beyond Repair'),
    )

    THREAD_TYPE_CHOICES = (
        ('API_REG', 'API Regular'),
        ('API_IF', 'API Internal Flush'),
        ('API_FH', 'API Full Hole'),
        ('API_NC', 'API Numbered Connection'),
        ('HT', 'Hi-Torque'),
        ('OTHER', 'Other'),
    )

    CONNECTION_TYPE_CHOICES = (
        ('PIN', 'Pin (Male)'),
        ('BOX', 'Box (Female)'),
    )

    # Parent evaluation session
    evaluation_session = models.ForeignKey(
        'EvaluationSession',
        on_delete=models.CASCADE,
        related_name='thread_inspections',
        help_text="Parent evaluation session"
    )

    # Thread identification
    thread_type = models.CharField(
        max_length=20,
        choices=THREAD_TYPE_CHOICES,
        default='API_REG',
        help_text="Type of thread connection"
    )

    connection_type = models.CharField(
        max_length=10,
        choices=CONNECTION_TYPE_CHOICES,
        default='PIN',
        help_text="Connection type (pin or box)"
    )

    thread_size = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="Thread size specification (e.g., 4-1/2 REG)"
    )

    # Inspection result
    result = models.CharField(
        max_length=20,
        choices=RESULT_CHOICES,
        db_index=True,
        help_text="Overall inspection result"
    )

    description = models.TextField(
        blank=True,
        default="",
        help_text="Detailed description of findings"
    )

    # Measurements (stored as JSON for flexibility)
    measurements_json = models.JSONField(
        default=dict,
        blank=True,
        help_text="Thread measurements (pitch diameter, lead, taper, etc.)"
    )

    # Specific inspection points
    thread_crest_condition = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Condition of thread crests"
    )

    thread_root_condition = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Condition of thread roots"
    )

    shoulder_condition = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Condition of thread shoulder"
    )

    galling_observed = models.BooleanField(
        default=False,
        help_text="Whether galling was observed"
    )

    corrosion_observed = models.BooleanField(
        default=False,
        help_text="Whether corrosion was observed"
    )

    # Repair recommendation
    repair_recommendation = models.TextField(
        blank=True,
        default="",
        help_text="Recommended repair actions"
    )

    requires_recut = models.BooleanField(
        default=False,
        help_text="Whether thread needs recutting"
    )

    requires_replacement = models.BooleanField(
        default=False,
        help_text="Whether connection needs replacement"
    )

    # Personnel and timing
    inspected_by = models.ForeignKey(
        'hr.HREmployee',
        on_delete=models.PROTECT,
        related_name='thread_inspections_conducted',
        help_text="Employee who performed the inspection"
    )

    inspected_at = models.DateTimeField(
        default=timezone.now,
        help_text="When the inspection was performed"
    )

    # Attachments reference (for photos, gauge readings, etc.)
    attachment_refs = models.JSONField(
        default=list,
        blank=True,
        help_text="References to attached documents/images"
    )

    class Meta:
        db_table = "evaluation_thread_inspection"
        verbose_name = "Thread Inspection"
        verbose_name_plural = "Thread Inspections"
        ordering = ['-inspected_at']
        indexes = [
            models.Index(
                fields=['evaluation_session', 'result'],
                name='ix_thread_insp_session_result'
            ),
            models.Index(
                fields=['inspected_by', '-inspected_at'],
                name='ix_thread_insp_inspector'
            ),
            models.Index(
                fields=['result', '-inspected_at'],
                name='ix_thread_insp_result_date'
            ),
        ]

    def __str__(self):
        return f"Thread Insp: {self.connection_type} - {self.result}"

    @property
    def needs_attention(self):
        """Check if thread needs repair attention."""
        return self.result in ('MAJOR_DAMAGE', 'REPAIRABLE', 'SCRAP')

    @property
    def is_acceptable(self):
        """Check if thread is acceptable for use."""
        return self.result in ('OK', 'MINOR_DAMAGE')


class NDTInspection(models.Model):
    """
    Non-Destructive Testing (NDT) inspection results.

    Records results from various NDT methods like:
    - LPT: Liquid Penetrant Testing
    - MPI: Magnetic Particle Inspection
    - UT: Ultrasonic Testing
    """

    METHOD_CHOICES = (
        ('LPT', 'Liquid Penetrant Testing'),
        ('MPI', 'Magnetic Particle Inspection'),
        ('UT', 'Ultrasonic Testing'),
        ('RT', 'Radiographic Testing'),
        ('VT', 'Visual Testing'),
        ('OTHER', 'Other Method'),
    )

    RESULT_CHOICES = (
        ('PASS', 'Pass - No Defects'),
        ('FAIL', 'Fail - Critical Defects'),
        ('REPAIR_REQUIRED', 'Repair Required'),
        ('MONITOR', 'Monitor - Acceptable with Conditions'),
        ('INCONCLUSIVE', 'Inconclusive - Retest Required'),
    )

    # Parent evaluation session
    evaluation_session = models.ForeignKey(
        'EvaluationSession',
        on_delete=models.CASCADE,
        related_name='ndt_inspections',
        help_text="Parent evaluation session"
    )

    # Inspection method and result
    method = models.CharField(
        max_length=20,
        choices=METHOD_CHOICES,
        help_text="NDT method used"
    )

    result = models.CharField(
        max_length=20,
        choices=RESULT_CHOICES,
        db_index=True,
        help_text="Overall inspection result"
    )

    # Areas and findings
    areas_inspected = models.TextField(
        help_text="Description of areas inspected (e.g., body, blades, shank)"
    )

    indications_description = models.TextField(
        blank=True,
        default="",
        help_text="Description of any indications/defects found"
    )

    # Specific findings
    crack_indications = models.BooleanField(
        default=False,
        help_text="Whether crack indications were found"
    )

    porosity_indications = models.BooleanField(
        default=False,
        help_text="Whether porosity indications were found"
    )

    inclusion_indications = models.BooleanField(
        default=False,
        help_text="Whether inclusion indications were found"
    )

    # Severity classification
    max_indication_size = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        null=True,
        blank=True,
        help_text="Maximum indication size (mm)"
    )

    indication_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of indications found"
    )

    # Acceptance criteria
    acceptance_standard = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Standard used for acceptance (e.g., ASME, API, company standard)"
    )

    meets_acceptance_criteria = models.BooleanField(
        default=True,
        help_text="Whether findings meet acceptance criteria"
    )

    # Recommendations
    recommendations = models.TextField(
        blank=True,
        default="",
        help_text="Recommendations based on findings"
    )

    requires_retest = models.BooleanField(
        default=False,
        help_text="Whether a retest is required"
    )

    retest_due_date = models.DateField(
        null=True,
        blank=True,
        help_text="When retest should be performed"
    )

    # Equipment and certification
    equipment_used = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Equipment/instrument used for inspection"
    )

    calibration_date = models.DateField(
        null=True,
        blank=True,
        help_text="Last calibration date of equipment"
    )

    inspector_certification = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Inspector's certification level (e.g., Level II)"
    )

    # Personnel and timing
    inspector = models.ForeignKey(
        'hr.HREmployee',
        on_delete=models.PROTECT,
        related_name='ndt_inspections_conducted',
        help_text="Certified inspector who performed the test"
    )

    inspected_at = models.DateTimeField(
        default=timezone.now,
        help_text="When the inspection was performed"
    )

    # Report reference
    report_number = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="NDT report reference number"
    )

    # Attachments reference
    attachment_refs = models.JSONField(
        default=list,
        blank=True,
        help_text="References to attached reports/images"
    )

    class Meta:
        db_table = "evaluation_ndt_inspection"
        verbose_name = "NDT Inspection"
        verbose_name_plural = "NDT Inspections"
        ordering = ['-inspected_at']
        indexes = [
            models.Index(
                fields=['evaluation_session', 'method'],
                name='ix_ndt_insp_session_method'
            ),
            models.Index(
                fields=['method', 'result'],
                name='ix_ndt_insp_method_result'
            ),
            models.Index(
                fields=['inspector', '-inspected_at'],
                name='ix_ndt_insp_inspector'
            ),
            models.Index(
                fields=['result', '-inspected_at'],
                name='ix_ndt_insp_result_date'
            ),
        ]

    def __str__(self):
        return f"{self.get_method_display()}: {self.result}"

    @property
    def is_critical(self):
        """Check if inspection found critical defects."""
        return self.result in ('FAIL', 'REPAIR_REQUIRED')

    @property
    def is_acceptable(self):
        """Check if inspection result is acceptable."""
        return self.result in ('PASS', 'MONITOR')

    @property
    def has_indications(self):
        """Check if any indications were found."""
        return any([
            self.crack_indications,
            self.porosity_indications,
            self.inclusion_indications,
            self.indication_count > 0
        ])

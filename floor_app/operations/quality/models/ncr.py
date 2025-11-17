"""
Quality Management - Nonconformance Report Models
NCR lifecycle management including root cause analysis and corrective actions.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from floor_app.mixins import PublicIdMixin, AuditMixin, SoftDeleteMixin
from .reference import DefectCategory, RootCauseCategory


class NonconformanceReport(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Central NCR tracking model.
    Manages the complete lifecycle of nonconformance reports from detection to closure.
    """
    NCR_STATUS_CHOICES = [
        ('OPEN', 'Open - Under Investigation'),
        ('CONTAINED', 'Contained - Immediate Action Taken'),
        ('ROOT_CAUSE', 'Root Cause Analysis'),
        ('CORRECTIVE', 'Corrective Action In Progress'),
        ('VERIFICATION', 'Verification Pending'),
        ('CLOSED', 'Closed'),
        ('CANCELLED', 'Cancelled'),
    ]

    NCR_TYPE_CHOICES = [
        ('INTERNAL', 'Internal NC'),
        ('SUPPLIER', 'Supplier NC'),
        ('CUSTOMER', 'Customer Complaint'),
        ('PROCESS', 'Process Deviation'),
    ]

    SEVERITY_CHOICES = [
        ('CRITICAL', 'Critical - Safety/Major Customer Impact'),
        ('MAJOR', 'Major - Significant Quality Issue'),
        ('MINOR', 'Minor - Cosmetic/Documentation Issue'),
    ]

    DISPOSITION_CHOICES = [
        ('PENDING', 'Pending Decision'),
        ('USE_AS_IS', 'Use As Is'),
        ('REWORK', 'Rework'),
        ('REPAIR', 'Repair'),
        ('SCRAP', 'Scrap'),
        ('RETURN_SUPPLIER', 'Return to Supplier'),
        ('DOWNGRADE', 'Downgrade/Recategorize'),
    ]

    # Identification
    ncr_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Auto-generated NCR number (e.g., NCR-2025-0001)"
    )
    ncr_type = models.CharField(max_length=20, choices=NCR_TYPE_CHOICES)
    status = models.CharField(
        max_length=20,
        choices=NCR_STATUS_CHOICES,
        default='OPEN',
        db_index=True
    )

    # What is nonconforming (loose coupling to other modules)
    job_card_id = models.BigIntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Reference to production.JobCard"
    )
    serial_unit_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Reference to inventory.SerialUnit"
    )
    batch_order_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Reference to production.BatchOrder"
    )

    # Defect details
    defect_category = models.ForeignKey(
        DefectCategory,
        on_delete=models.PROTECT,
        related_name='ncrs'
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    detection_point = models.CharField(
        max_length=100,
        help_text="Where the issue was discovered (e.g., Incoming QC, Final Inspection)"
    )
    detection_method = models.CharField(
        max_length=100,
        help_text="How the issue was discovered (e.g., Visual, Dimensional, NDT)"
    )

    # Quantity affected
    quantity_affected = models.PositiveIntegerField(default=1)
    quantity_contained = models.PositiveIntegerField(default=0)

    # Severity and impact
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    customer_impact = models.BooleanField(
        default=False,
        help_text="Does this affect customer deliverables?"
    )
    production_impact = models.BooleanField(
        default=False,
        help_text="Does this impact production schedule?"
    )
    safety_impact = models.BooleanField(
        default=False,
        help_text="Does this have safety implications?"
    )

    # Disposition
    disposition = models.CharField(
        max_length=20,
        choices=DISPOSITION_CHOICES,
        default='PENDING'
    )
    disposition_reason = models.TextField(blank=True, default="")
    disposition_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='ncr_dispositions'
    )
    disposition_at = models.DateTimeField(null=True, blank=True)

    # Cost impact
    estimated_cost_impact = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Estimated cost of the nonconformance"
    )
    actual_cost_impact = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Actual cost after resolution"
    )
    lost_revenue = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Lost revenue due to this NCR"
    )

    # Workflow management
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='ncrs_reported'
    )
    reported_at = models.DateTimeField(default=timezone.now)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='ncrs_assigned'
    )
    target_closure_date = models.DateField(
        null=True,
        blank=True,
        help_text="Target date to close this NCR"
    )
    actual_closure_date = models.DateField(null=True, blank=True)
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='ncrs_closed'
    )

    class Meta:
        db_table = "quality_nonconformance_report"
        verbose_name = "Nonconformance Report"
        verbose_name_plural = "Nonconformance Reports"
        ordering = ['-reported_at']
        indexes = [
            models.Index(fields=['ncr_number'], name='ix_qual_ncr_number'),
            models.Index(fields=['status'], name='ix_qual_ncr_status'),
            models.Index(fields=['ncr_type'], name='ix_qual_ncr_type'),
            models.Index(fields=['severity'], name='ix_qual_ncr_severity'),
            models.Index(fields=['job_card_id'], name='ix_qual_ncr_jobcard'),
            models.Index(fields=['reported_at'], name='ix_qual_ncr_reported'),
            models.Index(
                fields=['status', 'severity', 'target_closure_date'],
                name='ix_qual_ncr_workflow'
            ),
        ]

    def __str__(self):
        return f"{self.ncr_number} - {self.title}"

    @property
    def is_overdue(self):
        """Check if NCR is past its target closure date."""
        if self.target_closure_date and self.status not in ['CLOSED', 'CANCELLED']:
            return timezone.now().date() > self.target_closure_date
        return False

    @property
    def days_open(self):
        """Calculate number of days the NCR has been open."""
        if self.actual_closure_date:
            return (self.actual_closure_date - self.reported_at.date()).days
        return (timezone.now().date() - self.reported_at.date()).days

    def close(self, user):
        """Close the NCR."""
        self.status = 'CLOSED'
        self.actual_closure_date = timezone.now().date()
        self.closed_by = user
        self.save()

    @classmethod
    def generate_ncr_number(cls):
        """Generate next NCR number."""
        year = timezone.now().year
        prefix = f"NCR-{year}-"

        last_ncr = cls.all_objects.filter(
            ncr_number__startswith=prefix
        ).order_by('-ncr_number').first()

        if last_ncr:
            try:
                last_num = int(last_ncr.ncr_number.split('-')[-1])
                next_num = last_num + 1
            except ValueError:
                next_num = 1
        else:
            next_num = 1

        return f"{prefix}{next_num:04d}"


class NCRRootCauseAnalysis(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Root cause analysis for an NCR using 5-Why methodology.
    Supports multiple analyses per NCR (different categories).
    """
    ncr = models.ForeignKey(
        NonconformanceReport,
        on_delete=models.CASCADE,
        related_name='root_cause_analyses'
    )
    category = models.ForeignKey(
        RootCauseCategory,
        on_delete=models.PROTECT,
        help_text="Ishikawa category (Man, Machine, Method, etc.)"
    )

    # 5-Why chain
    why_1 = models.TextField(help_text="First Why - immediate cause")
    why_2 = models.TextField(blank=True, default="", help_text="Second Why")
    why_3 = models.TextField(blank=True, default="", help_text="Third Why")
    why_4 = models.TextField(blank=True, default="", help_text="Fourth Why")
    why_5 = models.TextField(blank=True, default="", help_text="Fifth Why - root cause")

    root_cause_statement = models.TextField(
        help_text="Final root cause statement based on analysis"
    )
    is_systemic = models.BooleanField(
        default=False,
        help_text="Is this a systemic issue requiring broader corrective action?"
    )

    analyzed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='ncr_analyses'
    )
    analyzed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "quality_ncr_root_cause_analysis"
        verbose_name = "NCR Root Cause Analysis"
        verbose_name_plural = "NCR Root Cause Analyses"
        ordering = ['ncr', 'category']
        indexes = [
            models.Index(fields=['ncr'], name='ix_qual_rca_ncr'),
            models.Index(fields=['is_systemic'], name='ix_qual_rca_systemic'),
        ]

    def __str__(self):
        return f"{self.ncr.ncr_number} - {self.category.code}"

    @property
    def why_depth(self):
        """Count how many whys were filled out."""
        count = 1  # why_1 is required
        for why in [self.why_2, self.why_3, self.why_4, self.why_5]:
            if why:
                count += 1
            else:
                break
        return count


class NCRCorrectiveAction(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Corrective and preventive actions (CAPA) for NCRs.
    Tracks immediate containment, corrective actions, and preventive measures.
    """
    ACTION_TYPE_CHOICES = [
        ('IMMEDIATE', 'Immediate Containment'),
        ('CORRECTIVE', 'Corrective Action'),
        ('PREVENTIVE', 'Preventive Action'),
    ]

    ACTION_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('VERIFIED', 'Verified Effective'),
        ('CANCELLED', 'Cancelled'),
    ]

    ncr = models.ForeignKey(
        NonconformanceReport,
        on_delete=models.CASCADE,
        related_name='corrective_actions'
    )
    action_type = models.CharField(max_length=20, choices=ACTION_TYPE_CHOICES)
    description = models.TextField(help_text="What action needs to be taken")

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='ncr_actions_assigned'
    )
    due_date = models.DateField()
    completed_date = models.DateField(null=True, blank=True)

    status = models.CharField(
        max_length=20,
        choices=ACTION_STATUS_CHOICES,
        default='PENDING'
    )
    completion_notes = models.TextField(
        blank=True,
        default="",
        help_text="Notes on what was done to complete this action"
    )

    # Effectiveness verification
    effectiveness_verified = models.BooleanField(default=False)
    verification_notes = models.TextField(blank=True, default="")
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='ncr_actions_verified'
    )
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "quality_ncr_corrective_action"
        verbose_name = "NCR Corrective Action"
        verbose_name_plural = "NCR Corrective Actions"
        ordering = ['ncr', 'action_type', 'due_date']
        indexes = [
            models.Index(fields=['ncr'], name='ix_qual_capa_ncr'),
            models.Index(fields=['status'], name='ix_qual_capa_status'),
            models.Index(fields=['action_type'], name='ix_qual_capa_type'),
            models.Index(fields=['due_date'], name='ix_qual_capa_due'),
            models.Index(
                fields=['status', 'due_date'],
                name='ix_qual_capa_stat_due'
            ),
        ]

    def __str__(self):
        return f"{self.ncr.ncr_number} - {self.get_action_type_display()}"

    @property
    def is_overdue(self):
        """Check if action is past due date."""
        if self.status not in ['COMPLETED', 'VERIFIED', 'CANCELLED']:
            return timezone.now().date() > self.due_date
        return False

    def complete(self, completion_notes=""):
        """Mark action as completed."""
        self.status = 'COMPLETED'
        self.completed_date = timezone.now().date()
        if completion_notes:
            self.completion_notes = completion_notes
        self.save()

    def verify(self, user, notes=""):
        """Verify the effectiveness of the action."""
        self.effectiveness_verified = True
        self.verified_by = user
        self.verified_at = timezone.now()
        self.status = 'VERIFIED'
        if notes:
            self.verification_notes = notes
        self.save()

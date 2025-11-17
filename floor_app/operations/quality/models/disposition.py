"""
Quality Management - Quality Disposition
Final quality decisions and release authorization for jobs.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from floor_app.mixins import PublicIdMixin, AuditMixin, SoftDeleteMixin
from .reference import AcceptanceCriteriaTemplate
from .ncr import NonconformanceReport


class QualityDisposition(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Final quality decision per job.
    Authorizes release or holds product based on quality assessment.
    Links to evaluation sessions and any NCRs.
    """
    DECISION_CHOICES = [
        ('APPROVED', 'Approved - Meets All Requirements'),
        ('CONDITIONAL', 'Conditional Approval - With Deviations'),
        ('REJECTED', 'Rejected - Does Not Meet Requirements'),
        ('HOLD', 'On Quality Hold - Pending Review'),
    ]

    # What is being dispositioned (loose coupling)
    job_card_id = models.BigIntegerField(
        db_index=True,
        help_text="Reference to production.JobCard"
    )
    evaluation_session_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Reference to evaluation.EvaluationSession"
    )

    # Decision
    decision = models.CharField(max_length=20, choices=DECISION_CHOICES)
    disposition_date = models.DateTimeField(default=timezone.now)

    # Who made the decision
    quality_engineer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='quality_dispositions'
    )

    # Supporting evidence
    inspection_summary = models.TextField(
        help_text="Summary of inspection results supporting the decision"
    )
    deviations_accepted = models.TextField(
        blank=True,
        default="",
        help_text="For conditional approval - list deviations accepted"
    )
    customer_concession = models.BooleanField(
        default=False,
        help_text="Was customer concession obtained for deviations?"
    )
    concession_reference = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Customer concession reference number"
    )

    # Acceptance criteria
    acceptance_template = models.ForeignKey(
        AcceptanceCriteriaTemplate,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='dispositions'
    )
    criteria_results_json = models.JSONField(
        default=dict,
        help_text="Actual vs required criteria values"
    )

    # NCRs linked to this disposition
    ncrs_closed = models.ManyToManyField(
        NonconformanceReport,
        blank=True,
        related_name='dispositions'
    )

    # Certificate of Conformance
    coc_number = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Certificate of Conformance number"
    )
    coc_generated_at = models.DateTimeField(null=True, blank=True)

    # Customer-specific fields
    customer_name = models.CharField(
        max_length=100,
        blank=True,
        default=""
    )
    customer_po_number = models.CharField(
        max_length=100,
        blank=True,
        default=""
    )
    customer_requirements_met = models.BooleanField(default=True)

    # Additional notes
    notes = models.TextField(blank=True, default="")

    # Release authorization
    released_for_shipment = models.BooleanField(default=False)
    release_date = models.DateTimeField(null=True, blank=True)
    released_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='quality_releases'
    )

    class Meta:
        db_table = "quality_disposition"
        verbose_name = "Quality Disposition"
        verbose_name_plural = "Quality Dispositions"
        ordering = ['-disposition_date']
        indexes = [
            models.Index(
                fields=['job_card_id'],
                name='ix_qual_disp_jobcard'
            ),
            models.Index(fields=['decision'], name='ix_qual_disp_decision'),
            models.Index(
                fields=['disposition_date'],
                name='ix_qual_disp_date'
            ),
            models.Index(
                fields=['released_for_shipment'],
                name='ix_qual_disp_released'
            ),
            models.Index(
                fields=['decision', 'released_for_shipment'],
                name='ix_qual_disp_dec_rel'
            ),
        ]

    def __str__(self):
        return f"Job #{self.job_card_id} - {self.get_decision_display()}"

    @property
    def is_releasable(self):
        """Check if this disposition allows release."""
        return self.decision in ['APPROVED', 'CONDITIONAL']

    @property
    def has_open_ncrs(self):
        """Check if there are unclosed NCRs linked."""
        return self.ncrs_closed.exclude(status='CLOSED').exists()

    def release(self, user):
        """Authorize release for shipment."""
        if not self.is_releasable:
            raise ValueError(f"Cannot release - decision is {self.decision}")
        if self.has_open_ncrs:
            raise ValueError("Cannot release - there are open NCRs")

        self.released_for_shipment = True
        self.release_date = timezone.now()
        self.released_by = user
        self.save()

    def generate_coc_number(self):
        """Generate Certificate of Conformance number."""
        year = timezone.now().year
        prefix = f"COC-{year}-"

        # Find the latest COC number
        last_disp = QualityDisposition.all_objects.filter(
            coc_number__startswith=prefix
        ).order_by('-coc_number').first()

        if last_disp and last_disp.coc_number:
            try:
                last_num = int(last_disp.coc_number.split('-')[-1])
                next_num = last_num + 1
            except ValueError:
                next_num = 1
        else:
            next_num = 1

        self.coc_number = f"{prefix}{next_num:05d}"
        self.coc_generated_at = timezone.now()
        self.save()
        return self.coc_number

    def add_criteria_result(self, criterion_name, actual_value, required_value, passed):
        """Add a criterion result to the JSON field."""
        if not self.criteria_results_json:
            self.criteria_results_json = {}

        self.criteria_results_json[criterion_name] = {
            'actual': actual_value,
            'required': required_value,
            'passed': passed,
            'timestamp': timezone.now().isoformat()
        }
        self.save()

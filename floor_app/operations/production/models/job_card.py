"""
Job Card Layer - Per Serial Bit/Unit

The central anchor for all technical and production data.
Links to SerialUnit (physical bit), MAT revisions, evaluations, routing, etc.
"""

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from floor_app.mixins import AuditMixin, SoftDeleteMixin, PublicIdMixin


class JobCard(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Per-bit/unit job card representing work and tracking.

    This is the central model that links:
    - SerialUnit (physical bit)
    - MAT revisions (initial and current)
    - Evaluations
    - Route/operations
    - NDT/Inspections
    - Checklists
    """

    STATUS_CHOICES = (
        ('NEW', 'New'),
        ('EVALUATION_IN_PROGRESS', 'Evaluation In Progress'),
        ('AWAITING_APPROVAL', 'Awaiting Approval'),
        ('AWAITING_MATERIALS', 'Awaiting Materials'),
        ('RELEASED_TO_SHOP', 'Released to Shop'),
        ('IN_PRODUCTION', 'In Production'),
        ('UNDER_QC', 'Under QC'),
        ('QC_APPROVED', 'QC Approved'),
        ('COMPLETE', 'Complete'),
        ('ON_HOLD', 'On Hold'),
        ('SCRAPPED', 'Scrapped'),
        ('CANCELLED', 'Cancelled'),
    )

    JOB_TYPE_CHOICES = (
        ('NEW_PRODUCTION', 'New Production'),
        ('REPAIR', 'Repair'),
        ('RETROFIT', 'Retrofit'),
        ('TEST_BIT', 'Test Bit'),
        ('REWORK', 'Rework'),
        ('EVALUATION_ONLY', 'Evaluation Only'),
    )

    PRIORITY_CHOICES = (
        ('LOW', 'Low'),
        ('NORMAL', 'Normal'),
        ('HIGH', 'High'),
        ('RUSH', 'Rush'),
        ('CRITICAL', 'Critical'),
    )

    # Core identification
    job_card_number = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Unique job card number"
    )

    # Batch relationship (optional for stand-alone jobs)
    batch_order = models.ForeignKey(
        'BatchOrder',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='job_cards',
        help_text="Parent batch order (optional)"
    )

    # Link to physical bit/unit
    serial_unit = models.ForeignKey(
        'inventory.SerialUnit',
        on_delete=models.PROTECT,
        related_name='job_cards',
        help_text="Physical bit/unit being processed"
    )

    # MAT/Design tracking
    initial_mat = models.ForeignKey(
        'engineering.BitDesignRevision',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='job_cards_initial',
        help_text="Initial MAT used for BOM and expectations"
    )
    current_mat = models.ForeignKey(
        'engineering.BitDesignRevision',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='job_cards_current',
        help_text="Current MAT after changes (retrofit, substitution)"
    )

    # BOM reference (optional: specific BOM for this job)
    bom_header = models.ForeignKey(
        'engineering.BOMHeader',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='job_cards',
        help_text="Specific BOM to use (if different from MAT default)"
    )

    # Customer/Job tracking
    customer_order_ref = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Customer's order reference"
    )
    customer_name = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Customer name (denormalized for quick access)"
    )

    # Bit details (denormalized for quick access)
    bit_size = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="Bit size (e.g., 12-1/4 inch)"
    )
    bit_type = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Bit type (e.g., HDBS Type, SMI Type)"
    )

    # Location/Job site info
    well_name = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Well name"
    )
    rig_name = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Rig name"
    )
    field_name = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Field/area name"
    )

    # Job classification
    job_type = models.CharField(
        max_length=20,
        choices=JOB_TYPE_CHOICES,
        default='REPAIR',
        db_index=True,
        help_text="Type of job"
    )

    # Rework tracking
    rework_of = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rework_jobs',
        help_text="Original job card if this is a rework"
    )
    rework_reason = models.TextField(
        blank=True,
        default="",
        help_text="Reason for rework"
    )

    # Status and priority
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='NEW',
        db_index=True
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='NORMAL',
        db_index=True
    )

    # Workflow timestamps
    created_date = models.DateTimeField(
        default=timezone.now,
        help_text="Job card creation date/time"
    )
    evaluation_started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When evaluation began"
    )
    evaluation_completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When evaluation was completed"
    )
    released_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When released to shop floor"
    )
    released_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='released_job_cards',
        help_text="User who released the job card"
    )
    production_started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When production began"
    )
    qc_started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When QC inspection began"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When job was completed"
    )
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='closed_job_cards',
        help_text="User who closed the job card"
    )

    # Scheduling
    planned_start_date = models.DateField(
        null=True,
        blank=True,
        help_text="Planned start date"
    )
    planned_end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Planned completion date"
    )
    actual_start_date = models.DateField(
        null=True,
        blank=True,
        help_text="Actual start date"
    )
    actual_end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Actual completion date"
    )

    # Costing
    estimated_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Estimated job cost"
    )
    actual_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Actual job cost"
    )
    quoted_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Quoted price to customer"
    )

    # Notes and instructions
    notes = models.TextField(
        blank=True,
        default="",
        help_text="Internal notes"
    )
    special_instructions = models.TextField(
        blank=True,
        default="",
        help_text="Special processing instructions"
    )
    customer_requirements = models.TextField(
        blank=True,
        default="",
        help_text="Customer-specific requirements"
    )

    # Integration hooks (for future modules)
    # These nullable fields allow linking to other systems
    shipping_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Future: Link to shipping/logistics"
    )

    # ERP Integration
    erp_production_order_number = models.CharField(
        max_length=50,
        blank=True,
        help_text='ERP Production Order Number'
    )
    cost_center = models.ForeignKey(
        'core.CostCenter',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='job_cards',
        help_text='Cost center for this job'
    )

    class Meta:
        db_table = "production_job_card"
        verbose_name = "Job Card"
        verbose_name_plural = "Job Cards"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['job_card_number'], name='ix_jc_number'),
            models.Index(fields=['status', 'priority'], name='ix_jc_status_prio'),
            models.Index(fields=['batch_order', 'status'], name='ix_jc_batch_status'),
            models.Index(fields=['serial_unit'], name='ix_jc_serial_unit'),
            models.Index(fields=['job_type', 'status'], name='ix_jc_type_status'),
            models.Index(fields=['customer_name', 'status'], name='ix_jc_cust_status'),
            models.Index(fields=['created_date'], name='ix_jc_created_date'),
            models.Index(fields=['planned_end_date'], name='ix_jc_planned_end'),
            # Additional performance indexes
            models.Index(fields=['actual_start_date', 'actual_end_date'], name='ix_jc_actual_times'),
        ]

    def __str__(self):
        return f"{self.job_card_number} - {self.serial_unit.serial_number}"

    def clean(self):
        """Validate job card data."""
        super().clean()

        # Ensure serial_unit is linked
        if not self.serial_unit_id:
            raise ValidationError({
                'serial_unit': "A serial unit (physical bit) must be selected."
            })

        # If rework, must have original job card
        if self.job_type == 'REWORK' and not self.rework_of:
            raise ValidationError({
                'rework_of': "Rework jobs must reference the original job card."
            })

    @property
    def is_overdue(self):
        """Check if job is overdue."""
        if self.planned_end_date and self.status not in ('COMPLETE', 'SCRAPPED', 'CANCELLED'):
            return self.planned_end_date < timezone.now().date()
        return False

    @property
    def duration_hours(self):
        """Calculate total job duration in hours."""
        if self.production_started_at and self.completed_at:
            delta = self.completed_at - self.production_started_at
            return round(delta.total_seconds() / 3600, 2)
        return None

    @property
    def mat_number(self):
        """Get current MAT number."""
        if self.current_mat:
            return self.current_mat.mat_number
        elif self.initial_mat:
            return self.initial_mat.mat_number
        return None

    def start_evaluation(self, user=None):
        """Mark job as starting evaluation."""
        self.status = 'EVALUATION_IN_PROGRESS'
        self.evaluation_started_at = timezone.now()
        self.save(update_fields=['status', 'evaluation_started_at', 'updated_at'])

    def complete_evaluation(self, user=None):
        """Mark evaluation as complete."""
        self.status = 'AWAITING_APPROVAL'
        self.evaluation_completed_at = timezone.now()
        self.save(update_fields=['status', 'evaluation_completed_at', 'updated_at'])

    def release_to_shop(self, user=None):
        """Release job card to shop floor."""
        self.status = 'RELEASED_TO_SHOP'
        self.released_at = timezone.now()
        self.released_by = user
        self.save(update_fields=['status', 'released_at', 'released_by', 'updated_at'])

    def start_production(self):
        """Mark production as started."""
        self.status = 'IN_PRODUCTION'
        self.production_started_at = timezone.now()
        if not self.actual_start_date:
            self.actual_start_date = timezone.now().date()
        self.save(update_fields=['status', 'production_started_at', 'actual_start_date', 'updated_at'])

    def start_qc(self):
        """Mark QC inspection as started."""
        self.status = 'UNDER_QC'
        self.qc_started_at = timezone.now()
        self.save(update_fields=['status', 'qc_started_at', 'updated_at'])

    def complete_job(self, user=None):
        """Mark job as complete."""
        self.status = 'COMPLETE'
        self.completed_at = timezone.now()
        self.closed_by = user
        self.actual_end_date = timezone.now().date()
        self.save(update_fields=['status', 'completed_at', 'closed_by', 'actual_end_date', 'updated_at'])

        # Update batch completion status
        if self.batch_order:
            self.batch_order.update_completion_status()

    def scrap_job(self, reason='', user=None):
        """Mark job as scrapped."""
        self.status = 'SCRAPPED'
        self.notes = f"{self.notes}\n\nSCRAPPED: {reason}".strip()
        self.closed_by = user
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'notes', 'closed_by', 'completed_at', 'updated_at'])

    def change_mat(self, new_mat, reason='', user=None):
        """
        Change the current MAT for this job card.
        Also updates the serial unit's MAT.
        """
        old_mat = self.current_mat
        self.current_mat = new_mat

        # Record reason in notes
        if reason:
            from django.utils import timezone as tz
            timestamp = tz.now().strftime('%Y-%m-%d %H:%M')
            old_mat_num = old_mat.mat_number if old_mat else 'None'
            self.notes = f"{self.notes}\n\n[{timestamp}] MAT Changed: {old_mat_num} -> {new_mat.mat_number}. Reason: {reason}".strip()

        self.save(update_fields=['current_mat', 'notes', 'updated_at'])

        # Update serial unit's MAT
        if self.serial_unit:
            self.serial_unit.change_mat(new_mat, reason='RETROFIT', user=user, notes=f"Job Card: {self.job_card_number}")

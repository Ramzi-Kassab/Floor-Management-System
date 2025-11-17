"""
Batch Order Layer

Represents groups of bits/jobs under one customer order.
Supports partial shipments and multiple releases.
"""

from django.db import models
from django.conf import settings
from floor_app.mixins import AuditMixin, SoftDeleteMixin, PublicIdMixin


class BatchOrder(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Production batch representing a group of bits under one customer/order.

    Examples:
    - 20 ARAMCO bits in one project
    - 5 bits for Halliburton repair job
    - 10 new PDC bits for ENO stock
    """

    STATUS_CHOICES = (
        ('PLANNED', 'Planned'),
        ('IN_PROGRESS', 'In Progress'),
        ('PARTIAL_COMPLETE', 'Partially Complete'),
        ('COMPLETE', 'Complete'),
        ('ON_HOLD', 'On Hold'),
        ('CANCELLED', 'Cancelled'),
    )

    BIT_FAMILY_CHOICES = (
        ('PDC', 'PDC Bit'),
        ('ROLLER_CONE', 'Roller Cone'),
        ('MATRIX', 'Matrix Infiltration'),
        ('OTHER', 'Other'),
    )

    PRIORITY_CHOICES = (
        ('LOW', 'Low'),
        ('NORMAL', 'Normal'),
        ('HIGH', 'High'),
        ('RUSH', 'Rush'),
        ('CRITICAL', 'Critical'),
    )

    # Core identification
    code = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Batch code (e.g., 2025-ARDT-LV4-015)"
    )
    description = models.CharField(
        max_length=500,
        blank=True,
        default="",
        help_text="Batch description"
    )

    # Customer/Order info
    customer_name = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Customer name"
    )
    # Future: customer = models.ForeignKey('Customer', ...)
    customer_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Future: FK to Customer table"
    )

    main_order_number = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Main customer order/PO number"
    )
    customer_reference = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Customer's reference for this batch"
    )

    # Product classification
    bit_family = models.CharField(
        max_length=20,
        choices=BIT_FAMILY_CHOICES,
        default='PDC',
        help_text="Product family"
    )

    # Quantities
    target_quantity = models.IntegerField(
        default=1,
        help_text="Target number of bits/units in batch"
    )
    completed_quantity = models.IntegerField(
        default=0,
        help_text="Number of bits/units completed"
    )
    shipped_quantity = models.IntegerField(
        default=0,
        help_text="Number of bits/units shipped"
    )

    # Scheduling
    created_date = models.DateField(
        auto_now_add=True,
        help_text="Batch creation date"
    )
    due_date = models.DateField(
        null=True,
        blank=True,
        help_text="Target completion date"
    )
    start_date = models.DateField(
        null=True,
        blank=True,
        help_text="Actual start date"
    )
    completion_date = models.DateField(
        null=True,
        blank=True,
        help_text="Actual completion date"
    )

    # Status and priority
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PLANNED',
        db_index=True
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='NORMAL',
        db_index=True
    )

    # Location tracking
    current_location = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Current batch location (warehouse, shop floor, etc.)"
    )

    # Notes and comments
    notes = models.TextField(
        blank=True,
        default="",
        help_text="Internal notes"
    )
    special_instructions = models.TextField(
        blank=True,
        default="",
        help_text="Special handling or processing instructions"
    )

    # Integration hooks
    # Future: Link to inventory transactions, shipping, etc.

    class Meta:
        db_table = "production_batch_order"
        verbose_name = "Batch Order"
        verbose_name_plural = "Batch Orders"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['code'], name='ix_batch_code'),
            models.Index(fields=['status', 'priority'], name='ix_batch_status_prio'),
            models.Index(fields=['customer_name', 'status'], name='ix_batch_cust_status'),
            models.Index(fields=['due_date'], name='ix_batch_due_date'),
            models.Index(fields=['bit_family', 'status'], name='ix_batch_family_stat'),
        ]

    def __str__(self):
        return f"{self.code} ({self.customer_name})"

    @property
    def completion_percentage(self):
        """Calculate completion percentage."""
        if self.target_quantity > 0:
            return round((self.completed_quantity / self.target_quantity) * 100, 1)
        return 0

    @property
    def is_overdue(self):
        """Check if batch is overdue."""
        from django.utils import timezone
        if self.due_date and self.status not in ('COMPLETE', 'CANCELLED'):
            return self.due_date < timezone.now().date()
        return False

    @property
    def remaining_quantity(self):
        """Calculate remaining units to complete."""
        return max(0, self.target_quantity - self.completed_quantity)

    def update_completion_status(self):
        """
        Update batch status based on job card completions.
        Called when job cards are updated.
        """
        from .job_card import JobCard

        total_jobs = self.job_cards.count()
        completed_jobs = self.job_cards.filter(status='COMPLETE').count()

        self.completed_quantity = completed_jobs

        if completed_jobs == 0:
            if self.status == 'IN_PROGRESS':
                pass  # Keep in progress
        elif completed_jobs >= self.target_quantity:
            self.status = 'COMPLETE'
            from django.utils import timezone
            self.completion_date = timezone.now().date()
        elif completed_jobs > 0:
            if self.status in ('PLANNED', 'ON_HOLD'):
                self.status = 'IN_PROGRESS'
            elif self.status != 'CANCELLED':
                self.status = 'PARTIAL_COMPLETE'

        self.save(update_fields=['completed_quantity', 'status', 'completion_date', 'updated_at'])

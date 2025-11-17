"""
Checklist Instance Layer

Runtime checklist instances for job cards.
These are created from ChecklistTemplates and track actual completion.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from floor_app.mixins import AuditMixin


class JobChecklistInstance(AuditMixin):
    """
    Instance of a checklist for a specific job card.

    Created from a ChecklistTemplate when a job card is created or when needed.
    """

    STATUS_CHOICES = (
        ('NOT_STARTED', 'Not Started'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('BLOCKED', 'Blocked'),
    )

    job_card = models.ForeignKey(
        'JobCard',
        on_delete=models.CASCADE,
        related_name='checklists',
        help_text="Job card this checklist belongs to"
    )

    template = models.ForeignKey(
        'ChecklistTemplate',
        on_delete=models.PROTECT,
        related_name='instances',
        help_text="Template this checklist was created from"
    )

    name = models.CharField(
        max_length=100,
        help_text="Checklist name (copied from template)"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='NOT_STARTED',
        db_index=True
    )

    # Completion tracking
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When checklist was started"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When checklist was completed"
    )
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='completed_checklists',
        help_text="User who marked checklist as complete"
    )

    # Summary
    total_items = models.IntegerField(
        default=0,
        help_text="Total number of items"
    )
    completed_items = models.IntegerField(
        default=0,
        help_text="Number of completed items"
    )
    mandatory_items = models.IntegerField(
        default=0,
        help_text="Number of mandatory items"
    )
    mandatory_completed = models.IntegerField(
        default=0,
        help_text="Number of mandatory items completed"
    )

    notes = models.TextField(
        blank=True,
        default="",
        help_text="General notes for this checklist instance"
    )

    class Meta:
        db_table = "production_job_checklist_instance"
        verbose_name = "Job Checklist"
        verbose_name_plural = "Job Checklists"
        ordering = ['job_card', 'template__sort_order']
        indexes = [
            models.Index(fields=['job_card', 'status'], name='ix_chklist_jc_status'),
            models.Index(fields=['status'], name='ix_chklist_status'),
        ]

    def __str__(self):
        return f"{self.job_card.job_card_number} - {self.name}"

    @property
    def completion_percentage(self):
        """Calculate completion percentage."""
        if self.total_items > 0:
            return round((self.completed_items / self.total_items) * 100, 1)
        return 0

    @property
    def is_complete(self):
        """Check if checklist is fully complete."""
        return self.status == 'COMPLETED'

    @property
    def all_mandatory_complete(self):
        """Check if all mandatory items are complete."""
        return self.mandatory_completed >= self.mandatory_items

    def update_summary(self):
        """Recalculate summary from items."""
        items = self.items.all()
        self.total_items = items.count()
        self.completed_items = items.filter(status='DONE').count()
        self.mandatory_items = items.filter(is_mandatory=True).count()
        self.mandatory_completed = items.filter(is_mandatory=True, status='DONE').count()

        # Update status
        if self.completed_items == 0:
            self.status = 'NOT_STARTED'
        elif self.completed_items >= self.total_items:
            self.status = 'COMPLETED'
            if not self.completed_at:
                self.completed_at = timezone.now()
        else:
            self.status = 'IN_PROGRESS'
            if not self.started_at:
                self.started_at = timezone.now()

        self.save(update_fields=[
            'total_items', 'completed_items', 'mandatory_items',
            'mandatory_completed', 'status', 'started_at', 'completed_at', 'updated_at'
        ])

    @classmethod
    def create_from_template(cls, job_card, template):
        """
        Create a checklist instance from a template.

        Copies all template items into runtime items.
        """
        # Create instance
        instance = cls.objects.create(
            job_card=job_card,
            template=template,
            name=template.name,
            total_items=template.items.count(),
            mandatory_items=template.items.filter(is_mandatory=True).count()
        )

        # Create items
        for item_template in template.items.all():
            JobChecklistItem.objects.create(
                checklist=instance,
                item_template=item_template,
                text=item_template.text,
                required_role=item_template.required_role,
                is_mandatory=item_template.is_mandatory,
                sequence=item_template.sequence,
                help_text=item_template.help_text
            )

        return instance


class JobChecklistItem(AuditMixin):
    """
    Individual checklist item instance.

    Tracks completion status for a specific checklist item.
    """

    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('DONE', 'Done'),
        ('NOT_APPLICABLE', 'Not Applicable'),
        ('BLOCKED', 'Blocked'),
    )

    checklist = models.ForeignKey(
        JobChecklistInstance,
        on_delete=models.CASCADE,
        related_name='items',
        help_text="Parent checklist instance"
    )

    item_template = models.ForeignKey(
        'ChecklistItemTemplate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='instances',
        help_text="Template this item was created from"
    )

    # Item content (copied from template, can be customized)
    text = models.CharField(
        max_length=500,
        help_text="Checklist item text"
    )
    required_role = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Role required to complete this item"
    )
    is_mandatory = models.BooleanField(
        default=True,
        help_text="Item must be completed"
    )
    sequence = models.IntegerField(
        default=10,
        help_text="Order in checklist"
    )
    help_text = models.TextField(
        blank=True,
        default="",
        help_text="Guidance for completing this item"
    )

    # Completion tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        db_index=True
    )
    checked_by = models.ForeignKey(
        'hr.HREmployee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='checked_items',
        help_text="Employee who checked this item"
    )
    checked_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When item was checked"
    )

    # Additional input
    comment = models.TextField(
        blank=True,
        default="",
        help_text="Comments or notes for this item"
    )
    value_entered = models.CharField(
        max_length=500,
        blank=True,
        default="",
        help_text="Value entered (for items requiring input)"
    )

    # Verification (if needed)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_checklist_items'
    )
    verified_at = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        db_table = "production_job_checklist_item"
        verbose_name = "Job Checklist Item"
        verbose_name_plural = "Job Checklist Items"
        ordering = ['checklist', 'sequence']
        indexes = [
            models.Index(fields=['checklist', 'sequence'], name='ix_chkitem_chk_seq'),
            models.Index(fields=['status'], name='ix_chkitem_status'),
        ]

    def __str__(self):
        return f"{self.checklist.name} - #{self.sequence}: {self.text[:50]}"

    @property
    def is_done(self):
        """Check if item is completed."""
        return self.status == 'DONE'

    def mark_done(self, employee, comment=''):
        """Mark item as completed."""
        self.status = 'DONE'
        self.checked_by = employee
        self.checked_at = timezone.now()
        if comment:
            self.comment = comment
        self.save(update_fields=['status', 'checked_by', 'checked_at', 'comment', 'updated_at'])

        # Update parent checklist summary
        self.checklist.update_summary()

    def mark_not_applicable(self, reason=''):
        """Mark item as not applicable."""
        self.status = 'NOT_APPLICABLE'
        if reason:
            self.comment = f"N/A: {reason}"
        self.save(update_fields=['status', 'comment', 'updated_at'])

        # Update parent checklist summary
        self.checklist.update_summary()

    def block_item(self, reason=''):
        """Block this item."""
        self.status = 'BLOCKED'
        self.comment = f"BLOCKED: {reason}"
        self.save(update_fields=['status', 'comment', 'updated_at'])

        # Update parent checklist status
        self.checklist.status = 'BLOCKED'
        self.checklist.save(update_fields=['status', 'updated_at'])

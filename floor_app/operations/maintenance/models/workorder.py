"""
Work Order Notes and Parts models.
"""
from django.db import models
from django.conf import settings


class WorkOrderNote(models.Model):
    """Comments and updates on work orders."""

    class NoteType(models.TextChoices):
        PROGRESS = 'PROGRESS', 'Progress Update'
        ISSUE = 'ISSUE', 'Issue Encountered'
        RESOLUTION = 'RESOLUTION', 'Resolution'
        GENERAL = 'GENERAL', 'General Note'
        PARTS = 'PARTS', 'Parts Related'

    work_order = models.ForeignKey(
        'maintenance.WorkOrder', on_delete=models.CASCADE, related_name='notes'
    )
    note_type = models.CharField(max_length=20, choices=NoteType.choices, default=NoteType.GENERAL)
    content = models.TextField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Work Order Note'
        verbose_name_plural = 'Work Order Notes'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.work_order.work_order_number} - {self.note_type} @ {self.created_at}"


class WorkOrderPart(models.Model):
    """Parts/consumables used in work order."""

    work_order = models.ForeignKey(
        'maintenance.WorkOrder', on_delete=models.CASCADE, related_name='work_order_parts'
    )
    part_number = models.CharField(max_length=100)
    part_description = models.CharField(max_length=255)
    quantity_used = models.DecimalField(max_digits=10, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    warehouse_location = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)

    # Future inventory integration
    inventory_item_id = models.PositiveBigIntegerField(null=True, blank=True)
    inventory_transaction_id = models.PositiveBigIntegerField(null=True, blank=True)

    class Meta:
        verbose_name = 'Work Order Part'
        verbose_name_plural = 'Work Order Parts'

    def __str__(self):
        return f"{self.work_order.work_order_number} - {self.part_number} x {self.quantity_used}"

    def save(self, *args, **kwargs):
        if self.unit_cost and self.quantity_used:
            self.total_cost = self.unit_cost * self.quantity_used
        super().save(*args, **kwargs)

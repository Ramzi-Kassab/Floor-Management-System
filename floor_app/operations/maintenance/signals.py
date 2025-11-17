"""
Signals for Maintenance module.
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone


@receiver(post_save, sender='maintenance.MaintenanceWorkOrder')
def update_asset_status_on_work_order(sender, instance, **kwargs):
    """Update asset status based on work order status changes."""
    from .models import Asset

    if instance.asset:
        if instance.status in ['IN_PROGRESS', 'WAITING_PARTS']:
            if instance.asset.status != Asset.Status.UNDER_MAINTENANCE:
                instance.asset.status = Asset.Status.UNDER_MAINTENANCE
                instance.asset.save(update_fields=['status', 'updated_at'])
        elif instance.status == 'COMPLETED':
            if instance.asset.status == Asset.Status.UNDER_MAINTENANCE:
                instance.asset.status = Asset.Status.IN_SERVICE
                instance.asset.save(update_fields=['status', 'updated_at'])


@receiver(post_save, sender='maintenance.PMTask')
def update_schedule_on_pm_completion(sender, instance, **kwargs):
    """Update PM schedule when task is completed."""
    if instance.status == 'COMPLETED' and instance.schedule:
        schedule = instance.schedule
        if instance.actual_end:
            schedule.last_performed_at = instance.actual_end
        else:
            schedule.last_performed_at = timezone.now()

        # Calculate next due date based on template frequency
        if schedule.pm_template:
            if schedule.pm_template.frequency_type == 'TIME_BASED':
                from datetime import timedelta
                schedule.next_due_date = schedule.last_performed_at.date() + timedelta(
                    days=schedule.pm_template.frequency_days or 30
                )
        schedule.save()


@receiver(post_save, sender='maintenance.MaintenanceRequest')
def auto_assign_reviewer(sender, instance, created, **kwargs):
    """Auto-assign request to maintenance manager if unassigned."""
    if created and instance.status == 'NEW':
        # Log for tracking
        pass  # Could auto-assign based on department rules


@receiver(post_save, sender='maintenance.DowntimeEvent')
def update_asset_downtime_stats(sender, instance, **kwargs):
    """Track total downtime for asset."""
    if instance.end_time and instance.asset:
        # Could update aggregate statistics on asset
        pass


@receiver(pre_save, sender='maintenance.MaintenanceWorkOrder')
def calculate_total_cost(sender, instance, **kwargs):
    """Calculate total cost before saving work order."""
    labor_cost = instance.labor_cost or 0
    parts_cost = instance.parts_cost or 0
    external_cost = instance.external_cost or 0
    instance.total_cost = labor_cost + parts_cost + external_cost


@receiver(post_save, sender='maintenance.WorkOrderPart')
def update_work_order_parts_cost(sender, instance, **kwargs):
    """Update work order total parts cost when parts are added."""
    if instance.work_order:
        from django.db.models import Sum
        from .models import WorkOrderPart

        total = WorkOrderPart.objects.filter(
            work_order=instance.work_order
        ).aggregate(total=Sum('total_cost'))['total'] or 0

        instance.work_order.parts_cost = total
        instance.work_order.save(update_fields=['parts_cost', 'total_cost', 'updated_at'])

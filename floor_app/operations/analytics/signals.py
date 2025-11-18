"""
Analytics Signals

Connect analytics to other parts of the system.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


# Example: Auto-create information request when certain conditions are met
# (This is optional - can be enabled as needed)

# @receiver(post_save, sender='production.JobCard')
# def check_for_delayed_job(sender, instance, created, **kwargs):
#     """
#     Example: If a job card is idle too long, check if this triggers any rules.
#     """
#     if not created:
#         # Check if job is delayed
#         # Could trigger rules or create information requests
#         pass


# Example: Trigger event-driven rules
# @receiver(post_save, sender='inventory.Item')
# def trigger_inventory_rules(sender, instance, created, **kwargs):
#     """
#     Example: When inventory changes, trigger relevant rules.
#     """
#     from floor_app.operations.analytics.models import AutomationRule
#
#     # Get rules that watch this model
#     rules = AutomationRule.objects.filter(
#         is_active=True,
#         is_approved=True,
#         trigger_mode='EVENT',
#         target_model='inventory.Item'
#     )
#
#     for rule in rules:
#         # Execute rule for this specific object
#         rule.execute(target_object=instance)


def connect_signals():
    """
    Connect signals when app is ready.

    Call this from AppConfig.ready() if needed.
    """
    pass

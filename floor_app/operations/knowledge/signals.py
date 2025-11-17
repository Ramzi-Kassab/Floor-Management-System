"""
Signals for Knowledge & Instructions module.
Automatically evaluate rules when models are saved/changed.
"""
from django.db.models.signals import post_save, pre_save, pre_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User

# Import models lazily to avoid circular imports


def get_current_user():
    """Get current user from thread-local storage (set by middleware)."""
    try:
        from floor_app.middleware import get_current_request
        request = get_current_request()
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            return request.user
    except:
        pass
    return None


def get_current_request():
    """Get current request from thread-local storage."""
    try:
        from floor_app.middleware import get_current_request
        return get_current_request()
    except:
        pass
    return None


# Cache to avoid infinite loops
_processing_rules = set()


def evaluate_rules_for_model(sender, instance, **kwargs):
    """
    Generic signal handler to evaluate instruction rules when any model is saved.
    This is the POWERFUL hook that makes instructions automatic.
    """
    # Avoid re-entry
    cache_key = f"{sender.__name__}_{instance.pk}"
    if cache_key in _processing_rules:
        return
    _processing_rules.add(cache_key)

    try:
        from floor_app.operations.knowledge.services import RuleEngine

        # Get ContentType for this model
        ct = ContentType.objects.get_for_model(sender)

        # Build context
        context = {ct.id: instance}

        # Create rule engine
        user = get_current_user()
        request = get_current_request()
        engine = RuleEngine(user=user, request=request)

        # Evaluate rules
        created = kwargs.get('created', False)
        trigger_event = 'create' if created else 'update'

        results = engine.evaluate_for_context(context, trigger_event=trigger_event)

        # Store results in instance for views to access
        if not hasattr(instance, '_instruction_results'):
            instance._instruction_results = []
        instance._instruction_results.append(results)

        # Handle blocking actions
        if results.get('prevented'):
            # Log but don't prevent (prevention happens in views/forms)
            pass

    except Exception as e:
        # Log error but don't break the save
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error evaluating rules for {sender.__name__}: {e}")
    finally:
        _processing_rules.discard(cache_key)


# Auto-update article statistics
@receiver(post_save, sender='knowledge.Article')
def update_category_stats(sender, instance, **kwargs):
    """Update category statistics when article is saved."""
    pass  # Stats are calculated on-the-fly


# Training completion notifications
@receiver(post_save, sender='knowledge.TrainingEnrollment')
def handle_training_completion(sender, instance, **kwargs):
    """Handle training completion events."""
    if instance.status == 'COMPLETED' and instance.certificate_issued:
        # Could send notification email here
        pass


# Auto-archive expired instructions
@receiver(pre_save, sender='knowledge.InstructionRule')
def check_instruction_expiry(sender, instance, **kwargs):
    """Auto-archive expired instructions."""
    from django.utils import timezone

    if instance.valid_until and instance.valid_until < timezone.now():
        if instance.status == 'ACTIVE':
            instance.status = 'INACTIVE'


# Connect to all models for automatic rule evaluation
def connect_rule_evaluation():
    """
    Connect rule evaluation to all relevant models.
    Called from AppConfig.ready()
    """
    # List of models that should trigger rule evaluation
    # This can be extended as more modules are added
    models_to_watch = [
        # HR models
        ('hr', 'HREmployee'),
        ('hr', 'HRPeople'),
        ('hr', 'Department'),
        ('hr', 'Position'),
        # Future: Inventory models
        # ('inventory', 'BitDesign'),
        # ('inventory', 'JobCard'),
        # Future: Production models
        # ('production', 'Operation'),
    ]

    for app_label, model_name in models_to_watch:
        try:
            ct = ContentType.objects.get(app_label=app_label, model=model_name.lower())
            model_class = ct.model_class()
            if model_class:
                post_save.connect(
                    evaluate_rules_for_model,
                    sender=model_class,
                    weak=False,
                    dispatch_uid=f'rule_eval_{app_label}_{model_name}'
                )
        except Exception:
            pass  # Model might not exist yet


# Note: connect_rule_evaluation() is called from AppConfig.ready()

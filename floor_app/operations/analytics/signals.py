"""
Signals for automatic activity tracking
"""
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from .models import UserActivity, UserSession, ErrorLog
from django.utils import timezone


@receiver(user_logged_in)
def track_user_login(sender, request, user, **kwargs):
    """Track user login and create session"""
    from .utils import get_client_ip, parse_user_agent

    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    device_info = parse_user_agent(user_agent)

    # Create user session
    session = UserSession.objects.create(
        user=user,
        session_key=request.session.session_key,
        ip_address=ip_address,
        user_agent=user_agent,
        device_type=device_info.get('device_type', ''),
        browser=device_info.get('browser', ''),
        operating_system=device_info.get('os', ''),
        is_active=True
    )

    # Store session ID in session for tracking
    request.session['analytics_session_id'] = session.id

    # Log activity
    UserActivity.objects.create(
        session=session,
        user=user,
        action_type='login',
        module='auth',
        description=f"User logged in from {ip_address}",
        success=True,
        metadata={
            'ip_address': ip_address,
            'user_agent': user_agent,
            'device_type': device_info.get('device_type', ''),
        }
    )


@receiver(user_logged_out)
def track_user_logout(sender, request, user, **kwargs):
    """Track user logout and close session"""
    if user and hasattr(request, 'session'):
        session_id = request.session.get('analytics_session_id')
        if session_id:
            try:
                session = UserSession.objects.get(id=session_id, user=user)
                session.logout_time = timezone.now()
                session.is_active = False
                session.calculate_duration()
                session.save()

                # Log activity
                UserActivity.objects.create(
                    session=session,
                    user=user,
                    action_type='logout',
                    module='auth',
                    description=f"User logged out (session duration: {session.get_duration_display()})",
                    success=True,
                    metadata={
                        'session_duration': session.duration_seconds,
                    }
                )
            except UserSession.DoesNotExist:
                pass


def log_model_activity(instance, action_type, user=None):
    """Helper function to log model CRUD activities"""
    if not user:
        # Try to get user from current request
        from .middleware import get_current_user
        user = get_current_user()

    if not user or not user.is_authenticated:
        return

    # Get model information
    content_type = ContentType.objects.get_for_model(instance)
    model_name = content_type.model
    module = instance._meta.app_label

    # Create activity description
    action_display = action_type.upper()
    object_display = str(instance)[:100]
    description = f"{action_display} {model_name}: {object_display}"

    # Get session
    session_id = None
    try:
        from floor_app.middleware import get_current_request
        request = get_current_request()
        if request and hasattr(request, 'session'):
            session_id = request.session.get('analytics_session_id')
    except:
        pass

    session = None
    if session_id:
        try:
            session = UserSession.objects.get(id=session_id)
        except UserSession.DoesNotExist:
            pass

    # Log activity
    UserActivity.objects.create(
        session=session,
        user=user,
        action_type=action_type,
        module=module,
        description=description,
        content_type=content_type,
        object_id=instance.pk,
        success=True,
        metadata={
            'model': model_name,
            'object_str': str(instance)[:200],
        }
    )


# Track important model operations (you can customize which models to track)
TRACKED_APPS = ['hr', 'inventory', 'production', 'evaluation', 'purchasing', 'sales', 'quality', 'maintenance']


@receiver(post_save)
def track_model_save(sender, instance, created, **kwargs):
    """Track model creation and updates"""
    # Skip analytics models to avoid recursion
    if sender._meta.app_label == 'analytics':
        return

    # Only track specified apps
    if sender._meta.app_label not in TRACKED_APPS:
        return

    # Skip tracking for certain models
    skip_models = ['migration', 'session', 'logentry']
    if sender._meta.model_name in skip_models:
        return

    action_type = 'create' if created else 'update'

    try:
        log_model_activity(instance, action_type)
    except Exception as e:
        # Don't let tracking errors break the application
        print(f"Error tracking {action_type}: {e}")


@receiver(post_delete)
def track_model_delete(sender, instance, **kwargs):
    """Track model deletions"""
    # Skip analytics models
    if sender._meta.app_label == 'analytics':
        return

    # Only track specified apps
    if sender._meta.app_label not in TRACKED_APPS:
        return

    # Skip tracking for certain models
    skip_models = ['migration', 'session', 'logentry']
    if sender._meta.model_name in skip_models:
        return

    try:
        log_model_activity(instance, 'delete')
    except Exception as e:
        print(f"Error tracking delete: {e}")

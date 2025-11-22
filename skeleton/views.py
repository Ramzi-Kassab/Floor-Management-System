"""
Skeleton app views for Floor Management System.

Includes:
- Authentication views (login, logout, password reset/change)
- Landing page
- Main dashboard
- Account/profile views
- Global search
"""
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta


# ============================================================================
# AUTHENTICATION VIEWS
# ============================================================================

class CustomLoginView(auth_views.LoginView):
    """Custom login view with custom template."""
    template_name = 'skeleton/auth/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('skeleton:dashboard')


class CustomLogoutView(auth_views.LogoutView):
    """Custom logout view."""
    next_page = 'skeleton:home'


class CustomPasswordChangeView(auth_views.PasswordChangeView):
    """Custom password change view."""
    template_name = 'skeleton/auth/password_change_form.html'
    success_url = reverse_lazy('skeleton:password_change_done')


class CustomPasswordChangeDoneView(auth_views.PasswordChangeDoneView):
    """Custom password change done view."""
    template_name = 'skeleton/auth/password_change_done.html'


class CustomPasswordResetView(auth_views.PasswordResetView):
    """Custom password reset view."""
    template_name = 'skeleton/auth/password_reset_form.html'
    email_template_name = 'skeleton/auth/password_reset_email.html'
    success_url = reverse_lazy('skeleton:password_reset_done')


class CustomPasswordResetDoneView(auth_views.PasswordResetDoneView):
    """Custom password reset done view."""
    template_name = 'skeleton/auth/password_reset_done.html'


class CustomPasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    """Custom password reset confirm view."""
    template_name = 'skeleton/auth/password_reset_confirm.html'
    success_url = reverse_lazy('skeleton:password_reset_complete')


class CustomPasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    """Custom password reset complete view."""
    template_name = 'skeleton/auth/password_reset_complete.html'


# ============================================================================
# LANDING PAGE & DASHBOARD
# ============================================================================

def home(request):
    """
    Landing page view.

    If user is authenticated → redirect to dashboard
    If not authenticated → show landing page with login button
    """
    if request.user.is_authenticated:
        return redirect('skeleton:dashboard')

    return render(request, 'skeleton/home.html')


@login_required
def dashboard(request):
    """
    Main dashboard view.

    Shows:
    - Module cards (HR, Inventory, Engineering, Production, Evaluation, Quality)
    - KPIs (placeholders for now):
      - Open Job Cards
      - Pending Leave Requests
      - Low Stock Items
      - Active Employees
    - Recent activity (from ActivityLog)
    """
    # Get KPIs
    kpis = {
        'open_job_cards': 0,  # Placeholder - will be implemented in Production phase
        'pending_leaves': 0,  # Placeholder - will be implemented in HR phase
        'low_stock_items': 0,  # Placeholder - will be implemented in Inventory phase
        'active_employees': 0,  # Placeholder - will be implemented in HR phase
    }

    # Try to get real data if models exist
    try:
        from floor_app.operations.hr.models import HREmployee
        kpis['active_employees'] = HREmployee.objects.filter(status='active').count()
    except (ImportError, Exception):
        pass

    try:
        from floor_app.operations.hr.models import LeaveRequest
        kpis['pending_leaves'] = LeaveRequest.objects.filter(status='submitted').count()
    except (ImportError, Exception):
        pass

    # Get recent activity
    try:
        from core.models import ActivityLog
        recent_activity = ActivityLog.objects.select_related('user').order_by('-created_at')[:10]
    except (ImportError, Exception):
        recent_activity = []

    # Get unread notifications count
    try:
        from core.models import Notification
        unread_notifications_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
    except (ImportError, Exception):
        unread_notifications_count = 0

    context = {
        'kpis': kpis,
        'recent_activity': recent_activity,
        'unread_notifications_count': unread_notifications_count,
    }

    return render(request, 'skeleton/dashboard.html', context)


# ============================================================================
# ACCOUNT VIEWS
# ============================================================================

@login_required
def account_profile(request):
    """
    User account profile view.

    Shows info from auth.User and links to HR employee if exists.
    """
    hr_employee = None
    try:
        from floor_app.operations.hr.models import HREmployee
        hr_employee = HREmployee.objects.filter(
            person__user=request.user
        ).select_related('person', 'department', 'position').first()
    except (ImportError, Exception):
        pass

    context = {
        'hr_employee': hr_employee,
    }

    return render(request, 'skeleton/account/profile.html', context)


@login_required
def account_settings(request):
    """
    User account settings view.

    Shows and allows editing of UserPreference.
    """
    from core.models import UserPreference

    user_preference, created = UserPreference.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        # Update preferences
        user_preference.theme = request.POST.get('theme', 'light')
        user_preference.table_density = request.POST.get('table_density', 'normal')
        user_preference.font_size = request.POST.get('font_size', 'normal')
        user_preference.default_landing_page = request.POST.get('default_landing_page', 'dashboard')
        user_preference.sidebar_collapsed = request.POST.get('sidebar_collapsed') == 'on'
        user_preference.save()

        return redirect('skeleton:account_settings')

    context = {
        'user_preference': user_preference,
    }

    return render(request, 'skeleton/account/settings.html', context)


# ============================================================================
# GLOBAL SEARCH
# ============================================================================

@login_required
def global_search(request):
    """
    Global search view.

    Searches across:
    - Employees
    - Items
    - Locations
    - Job Cards
    - (more to be added)
    """
    query = request.GET.get('q', '').strip()
    results = {
        'employees': [],
        'items': [],
        'locations': [],
        'job_cards': [],
    }

    if query:
        # Search employees
        try:
            from floor_app.operations.hr.models import HREmployee
            results['employees'] = HREmployee.objects.filter(
                Q(person__first_name__icontains=query) |
                Q(person__last_name__icontains=query) |
                Q(employee_code__icontains=query)
            ).select_related('person', 'department')[:10]
        except (ImportError, Exception):
            pass

        # Search items (inventory)
        try:
            from floor_app.operations.inventory.models import Item
            results['items'] = Item.objects.filter(
                Q(item_code__icontains=query) |
                Q(name__icontains=query)
            )[:10]
        except (ImportError, Exception):
            pass

        # Search locations
        try:
            from floor_app.operations.inventory.models import Location
            results['locations'] = Location.objects.filter(
                Q(code__icontains=query) |
                Q(name__icontains=query)
            )[:10]
        except (ImportError, Exception):
            pass

        # Search job cards
        try:
            from floor_app.operations.production.models import JobCard
            results['job_cards'] = JobCard.objects.filter(
                jobcard_number__icontains=query
            )[:10]
        except (ImportError, Exception):
            pass

    context = {
        'query': query,
        'results': results,
    }

    return render(request, 'skeleton/search_results.html', context)


# ============================================================================
# NOTIFICATIONS VIEW
# ============================================================================

@login_required
def notifications_list(request):
    """
    List all notifications for the current user.
    """
    from core.models import Notification

    notifications = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')

    # Mark as read if requested
    if request.GET.get('mark_read'):
        notification_id = request.GET.get('mark_read')
        try:
            notification = notifications.get(id=notification_id)
            notification.mark_as_read()
        except Notification.DoesNotExist:
            pass

    context = {
        'notifications': notifications,
    }

    return render(request, 'skeleton/notifications.html', context)

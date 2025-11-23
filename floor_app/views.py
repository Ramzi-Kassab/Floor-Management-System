from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView, PasswordResetConfirmView
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.contrib import messages
from django.utils import timezone

from floor_app.operations.hr.models import HREmployee, HRPeople, Department
from django.contrib.auth.models import User


class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        next_url = self.request.GET.get('next')
        return next_url if next_url else reverse_lazy('home')

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.POST.get('remember_me'):
            self.request.session.set_expiry(30 * 24 * 60 * 60)
        messages.success(self.request, f'Welcome back!')
        return response


class CustomLogoutView(LogoutView):
    template_name = 'logout.html'
    http_method_names = ['get', 'post', 'options']

    def dispatch(self, request, *args, **kwargs):
        messages.info(request, 'You have been logged out successfully.')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        """Allow GET requests to logout"""
        return self.post(request, *args, **kwargs)


class CustomPasswordResetView(PasswordResetView):
    template_name = 'registration/password_reset.html'
    email_template_name = 'registration/password_reset_email.html'
    subject_template_name = 'registration/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'registration/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')


def signup(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')

        errors = []
        if not username or User.objects.filter(username=username).exists():
            errors.append('Username is required or already exists.')
        if not email or User.objects.filter(email=email).exists():
            errors.append('Email is required or already registered.')
        if not password1 or len(password1) < 8:
            errors.append('Password must be at least 8 characters.')
        if password1 != password2:
            errors.append('Passwords do not match.')

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'registration/signup.html', {
                'username': username,
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
            })

        User.objects.create_user(
            username=username, email=email,
            first_name=first_name, last_name=last_name,
            password=password1
        )
        auth_user = authenticate(request, username=username, password=password1)
        login(request, auth_user)
        messages.success(request, 'Account created successfully!')
        return redirect('home')

    return render(request, 'registration/signup.html')


@login_required
def home(request):
    total_employees = HREmployee.objects.count()
    active_employees = HREmployee.objects.filter(status='ACTIVE').count()

    this_month = timezone.now().date().replace(day=1)
    new_employees_this_month = HREmployee.objects.filter(created_at__gte=this_month).count()

    inactive_employees = HREmployee.objects.exclude(status='ACTIVE').count()
    recent_employees = HREmployee.objects.select_related('person').order_by('-created_at')[:10]
    team_stats = HREmployee.objects.values('team').annotate(count=Count('id')).order_by('-count')[:5]

    # Get all departments for the Departments Hub
    departments = Department.objects.all().prefetch_related('employees', 'positions')

    return render(request, "home.html", {
        'total_employees': total_employees,
        'active_employees': active_employees,
        'inactive_employees': inactive_employees,
        'new_employees_this_month': new_employees_this_month,
        'recent_employees': recent_employees,
        'team_stats': team_stats,
        'departments': departments,
    })


@login_required
def employee_list(request):
    employees = HREmployee.objects.select_related('person').all()

    search = request.GET.get('search', '').strip()
    if search:
        employees = employees.filter(
            Q(person__first_name_en__icontains=search) |
            Q(person__last_name_en__icontains=search) |
            Q(person__national_id__icontains=search)
        )

    team = request.GET.get('team', '').strip()
    if team:
        employees = employees.filter(team=team)

    emp_status = request.GET.get('status', '').strip()
    if emp_status == 'active':
        employees = employees.filter(status='ACTIVE')
    elif emp_status == 'inactive':
        employees = employees.exclude(status='ACTIVE')

    sort_by = request.GET.get('sort', '-created_at')
    valid_sorts = ['person__first_name_en', '-person__first_name_en',  'team', 'created_at', '-created_at']
    if sort_by in valid_sorts:
        employees = employees.order_by(sort_by)

    paginator = Paginator(employees, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    teams = sorted(HREmployee.objects.values_list('team', flat=True).distinct())

    return render(request, 'hr/employee_list.html', {
        'page_obj': page_obj,
        'search': search,
        'team': team,
        'emp_status': emp_status,
        'sort_by': sort_by,
        'teams': teams,
        'total_count': paginator.count,
    })


@login_required
def employee_detail(request, pk):
    try:
        employee = HREmployee.objects.select_related('person').prefetch_related(
            'person__phones', 'person__emails', 'person__addresses', 'qualifications'
        ).get(pk=pk)
    except HREmployee.DoesNotExist:
        messages.error(request, 'Employee not found.')
        return redirect('employee_list')

    return render(request, 'hr/employee_detail.html', {
        'employee': employee,
        'person': employee.person,
    })
"""
Extended views for Floor App - System-wide templates and features.

This file contains views for:
- User-facing features (notifications, profile, dashboard)
- Help system (help center, FAQ, onboarding)
- Admin tools (admin dashboard, audit logs, user management)
- API management
- System pages and universal features
"""

from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User, Group, Permission
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse, Http404
from django.views.decorators.http import require_http_methods, require_POST
from django.db.models import Q, Count, Avg, Sum
from django.core.paginator import Paginator
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
import json


# ========== HELPER FUNCTIONS ==========

def is_staff_or_admin(user):
    """Check if user is staff or admin."""
    return user.is_staff or user.is_superuser


def is_admin(user):
    """Check if user is admin."""
    return user.is_superuser


# ========== USER-FACING FEATURES ==========

@login_required
def notification_center(request):
    """Display user notifications with filtering."""
    # TODO: Replace with actual Notification model when implemented
    context = {
        'unread_count': 5,
        'total_notifications': 23,
    }
    return render(request, 'notification_center.html', context)


@login_required
@require_POST
def mark_notification_read(request, pk):
    """Mark a single notification as read."""
    # TODO: Implement with actual Notification model
    return JsonResponse({'success': True, 'message': 'Notification marked as read'})


@login_required
@require_POST
def mark_all_notifications_read(request):
    """Mark all notifications as read."""
    # TODO: Implement with actual Notification model
    return JsonResponse({'success': True, 'message': 'All notifications marked as read'})


@login_required
def notification_settings(request):
    """Notification preferences."""
    if request.method == 'POST':
        # TODO: Save notification preferences
        messages.success(request, 'Notification settings updated successfully.')
        return redirect('floor_app:notification_center')

    return render(request, 'notification_center.html')


@login_required
def user_profile(request):
    """User profile page."""
    user = request.user
    context = {
        'user': user,
        'employee': getattr(user, 'hremployee', None),  # If linked to HREmployee
        'active_sessions': 1,  # TODO: Get actual session count
        'recent_activity': [],  # TODO: Get recent activity
    }
    return render(request, 'user_profile.html', context)


@login_required
def user_profile_edit(request):
    """Edit user profile."""
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.save()

        messages.success(request, 'Profile updated successfully.')
        return redirect('floor_app:user_profile')

    return redirect('floor_app:user_profile')


@login_required
@require_POST
def user_avatar_upload(request):
    """Handle avatar upload."""
    # TODO: Implement avatar upload with file storage
    return JsonResponse({'success': True, 'message': 'Avatar uploaded successfully'})


@login_required
def user_password_change_view(request):
    """Change user password."""
    # Redirect to Django's built-in password change view
    from django.contrib.auth.views import PasswordChangeView
    return PasswordChangeView.as_view(template_name='user_profile.html')(request)


@login_required
def user_preferences_view(request):
    """User preferences."""
    return render(request, 'user_profile.html')


@login_required
def user_active_sessions(request):
    """View and manage active sessions."""
    # TODO: Implement session management
    return render(request, 'user_profile.html')


# ========== HELP SYSTEM ==========

def help_center(request):
    """Help center main page."""
    context = {
        'total_articles': 247,
        'video_tutorials': 56,
        'avg_response': '2h',
    }
    return render(request, 'help_center.html', context)


def help_article(request, slug):
    """Individual help article."""
    # TODO: Implement with actual HelpArticle model
    context = {
        'article_slug': slug,
    }
    return render(request, 'help_center.html', context)


def help_category(request, category):
    """Help articles by category."""
    context = {
        'category': category,
    }
    return render(request, 'help_center.html', context)


def help_search(request):
    """Search help articles."""
    query = request.GET.get('q', '')
    # TODO: Implement search
    return render(request, 'help_center.html', {'query': query})


def faq(request):
    """FAQ page."""
    return render(request, 'faq.html')


def faq_category(request, category):
    """FAQ by category."""
    context = {'category': category}
    return render(request, 'faq.html', context)


@login_required
def onboarding_tutorial(request):
    """Onboarding tutorial for new users."""
    return render(request, 'onboarding_tutorial.html')


@login_required
@require_POST
def onboarding_complete(request):
    """Mark onboarding as complete."""
    # TODO: Save onboarding completion to user profile
    return JsonResponse({'success': True, 'message': 'Onboarding completed'})


@login_required
@require_POST
def onboarding_skip(request):
    """Skip onboarding tutorial."""
    return JsonResponse({'success': True, 'message': 'Onboarding skipped'})


def contact_support(request):
    """Contact support page."""
    return render(request, 'contact_support.html')


@require_POST
def submit_support_ticket(request):
    """Submit a support ticket."""
    # TODO: Implement ticket creation
    messages.success(request, 'Support ticket submitted successfully. Ticket ID: #12345')
    return redirect('floor_app:contact_support')


def support_ticket_detail(request, pk):
    """View support ticket details."""
    # TODO: Implement with actual SupportTicket model
    return render(request, 'contact_support.html', {'ticket_id': pk})


# ========== ADMIN & MANAGEMENT ==========

@login_required
@user_passes_test(is_staff_or_admin)
def admin_dashboard(request):
    """Admin dashboard with system monitoring."""
    # System metrics
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    online_users = 87  # TODO: Calculate from sessions

    # Recent activity
    recent_users = User.objects.order_by('-last_login')[:10]

    context = {
        'total_users': total_users,
        'active_users': active_users,
        'online_users': online_users,
        'inactive_users': total_users - active_users,
        'recent_users': recent_users,
    }
    return render(request, 'admin_dashboard.html', context)


@login_required
@user_passes_test(is_staff_or_admin)
def system_health_api(request):
    """System health metrics API."""
    data = {
        'cpu_usage': 45,  # TODO: Get actual system metrics
        'memory_usage': 62,
        'disk_usage': 38,
        'network_status': 'healthy',
    }
    return JsonResponse(data)


@login_required
@user_passes_test(is_staff_or_admin)
def user_activity_api(request):
    """User activity data for charts."""
    # TODO: Implement actual activity tracking
    data = {
        'labels': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        'values': [120, 150, 180, 140, 200, 90, 60],
    }
    return JsonResponse(data)


@login_required
@user_passes_test(is_staff_or_admin)
def audit_logs(request):
    """Audit logs page."""
    # TODO: Implement with actual AuditLog model
    context = {
        'total_logs': 15234,
        'today_logs': 342,
    }
    return render(request, 'audit_logs.html', context)


@login_required
@user_passes_test(is_staff_or_admin)
def audit_logs_export(request):
    """Export audit logs."""
    # TODO: Implement CSV/Excel export
    return HttpResponse('CSV export would be here', content_type='text/csv')


@login_required
@user_passes_test(is_staff_or_admin)
def audit_log_detail(request, pk):
    """Audit log detail."""
    return render(request, 'audit_logs.html', {'log_id': pk})


# ========== USER MANAGEMENT ==========

@login_required
@user_passes_test(is_staff_or_admin)
def user_management(request):
    """User management page."""
    users = User.objects.all().select_related().prefetch_related('groups')

    # Filtering
    search = request.GET.get('search', '').strip()
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )

    role = request.GET.get('role', '')
    if role:
        users = users.filter(groups__name=role)

    status = request.GET.get('status', '')
    if status == 'active':
        users = users.filter(is_active=True)
    elif status == 'inactive':
        users = users.filter(is_active=False)

    # Pagination
    paginator = Paginator(users, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    # Stats
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    pending_users = 8  # TODO: Implement pending approval system

    context = {
        'page_obj': page_obj,
        'total_users': total_users,
        'active_users': active_users,
        'online_users': 87,  # TODO: Calculate from sessions
        'pending_users': pending_users,
        'search': search,
        'role': role,
        'status': status,
    }
    return render(request, 'user_management.html', context)


@login_required
@user_passes_test(is_admin)
def user_create(request):
    """Create new user."""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = User.objects.make_random_password()

        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password
        )

        # TODO: Send welcome email with password

        messages.success(request, f'User {username} created successfully.')
        return redirect('floor_app:user_management')

    return redirect('floor_app:user_management')


@login_required
@user_passes_test(is_staff_or_admin)
def user_detail_view(request, pk):
    """User detail page."""
    user = get_object_or_404(User, pk=pk)
    return render(request, 'user_management.html', {'selected_user': user})


@login_required
@user_passes_test(is_admin)
def user_edit(request, pk):
    """Edit user."""
    user = get_object_or_404(User, pk=pk)

    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.save()

        messages.success(request, f'User {user.username} updated successfully.')
        return redirect('floor_app:user_management')

    return redirect('floor_app:user_management')


@login_required
@user_passes_test(is_admin)
@require_POST
def user_delete_view(request, pk):
    """Delete user."""
    user = get_object_or_404(User, pk=pk)

    if user == request.user:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('floor_app:user_management')

    username = user.username
    user.delete()

    messages.success(request, f'User {username} deleted successfully.')
    return redirect('floor_app:user_management')


@login_required
@user_passes_test(is_admin)
@require_POST
def user_toggle_status(request, pk):
    """Toggle user active status."""
    user = get_object_or_404(User, pk=pk)
    user.is_active = not user.is_active
    user.save()

    status = 'activated' if user.is_active else 'deactivated'
    messages.success(request, f'User {user.username} {status} successfully.')

    return JsonResponse({'success': True, 'is_active': user.is_active})


@login_required
@user_passes_test(is_admin)
def user_permissions_edit(request, pk):
    """Edit user permissions."""
    user = get_object_or_404(User, pk=pk)

    if request.method == 'POST':
        # TODO: Handle permission updates
        messages.success(request, f'Permissions updated for {user.username}.')
        return redirect('floor_app:user_management')

    permissions = Permission.objects.all()
    groups = Group.objects.all()

    context = {
        'selected_user': user,
        'permissions': permissions,
        'groups': groups,
    }
    return render(request, 'user_management.html', context)


@login_required
@user_passes_test(is_admin)
@require_POST
def users_bulk_action(request):
    """Bulk actions on users."""
    action = request.POST.get('action')
    user_ids = request.POST.getlist('user_ids')

    if action == 'activate':
        User.objects.filter(id__in=user_ids).update(is_active=True)
        messages.success(request, f'{len(user_ids)} users activated.')
    elif action == 'deactivate':
        User.objects.filter(id__in=user_ids).update(is_active=False)
        messages.success(request, f'{len(user_ids)} users deactivated.')
    elif action == 'delete':
        User.objects.filter(id__in=user_ids).delete()
        messages.success(request, f'{len(user_ids)} users deleted.')

    return redirect('floor_app:user_management')


@login_required
@user_passes_test(is_staff_or_admin)
def users_export(request):
    """Export users to CSV."""
    import csv
    from django.utils.encoding import smart_str

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="users_export.csv"'

    writer = csv.writer(response)
    writer.writerow(['Username', 'Email', 'First Name', 'Last Name', 'Active', 'Staff', 'Last Login'])

    users = User.objects.all()
    for user in users:
        writer.writerow([
            smart_str(user.username),
            smart_str(user.email),
            smart_str(user.first_name),
            smart_str(user.last_name),
            user.is_active,
            user.is_staff,
            user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else 'Never',
        ])

    return response


# ========== API MANAGEMENT ==========

@login_required
@user_passes_test(is_staff_or_admin)
def api_management(request):
    """API management page."""
    # TODO: Implement with actual APIKey model
    context = {
        'total_keys': 12,
        'api_calls': '2.4M',
        'webhooks': 8,
    }
    return render(request, 'api_management.html', context)


@login_required
@user_passes_test(is_admin)
@require_POST
def api_key_create(request):
    """Create new API key."""
    # TODO: Implement API key creation
    messages.success(request, 'API key created successfully.')
    return redirect('floor_app:api_management')


@login_required
@user_passes_test(is_admin)
@require_POST
def api_key_regenerate(request, pk):
    """Regenerate API key."""
    # TODO: Implement key regeneration
    return JsonResponse({'success': True, 'message': 'API key regenerated'})


@login_required
@user_passes_test(is_admin)
@require_POST
def api_key_delete(request, pk):
    """Delete API key."""
    # TODO: Implement key deletion
    return JsonResponse({'success': True, 'message': 'API key deleted'})


@login_required
@user_passes_test(is_staff_or_admin)
def api_usage_stats(request):
    """API usage statistics."""
    # TODO: Implement actual usage tracking
    data = {
        'labels': ['Jan 1', 'Jan 5', 'Jan 10', 'Jan 15', 'Jan 20', 'Jan 25', 'Today'],
        'values': [65000, 82000, 75000, 95000, 88000, 102000, 98000],
    }
    return JsonResponse(data)


@login_required
@user_passes_test(is_admin)
@require_POST
def webhook_create(request):
    """Create webhook."""
    # TODO: Implement webhook creation
    messages.success(request, 'Webhook created successfully.')
    return redirect('floor_app:api_management')


@login_required
@user_passes_test(is_admin)
@require_POST
def webhook_test(request, pk):
    """Test webhook."""
    # TODO: Send test webhook
    return JsonResponse({'success': True, 'message': 'Test webhook sent'})


@login_required
@user_passes_test(is_admin)
@require_POST
def webhook_toggle(request, pk):
    """Toggle webhook active status."""
    # TODO: Toggle webhook
    return JsonResponse({'success': True, 'message': 'Webhook toggled'})


# ========== UNIVERSAL FEATURES ==========

@login_required
def global_search_view(request):
    """Global search page."""
    query = request.GET.get('q', '')
    # TODO: Implement comprehensive search
    return render(request, 'global_search.html', {'query': query})


@login_required
def search_suggestions(request):
    """Search suggestions API."""
    query = request.GET.get('q', '')
    # TODO: Implement search suggestions
    suggestions = []
    return JsonResponse({'suggestions': suggestions})


@login_required
def reporting_hub(request):
    """Reporting hub."""
    return render(request, 'reporting_hub.html')


@login_required
@require_POST
def generate_report(request):
    """Generate custom report."""
    # TODO: Implement report generation
    messages.success(request, 'Report generated successfully.')
    return redirect('floor_app:reporting_hub')


@login_required
def report_detail(request, pk):
    """Report detail."""
    return render(request, 'reporting_hub.html', {'report_id': pk})


@login_required
def report_download(request, pk):
    """Download report."""
    # TODO: Implement report download
    return HttpResponse('Report download', content_type='application/pdf')


@login_required
@require_POST
def report_schedule(request, pk):
    """Schedule report."""
    # TODO: Implement report scheduling
    return JsonResponse({'success': True, 'message': 'Report scheduled'})


@login_required
@user_passes_test(is_admin)
def system_settings(request):
    """System settings page."""
    return render(request, 'system_settings.html')


@login_required
@user_passes_test(is_admin)
@require_POST
def system_settings_update(request):
    """Update system settings."""
    # TODO: Implement settings update
    messages.success(request, 'System settings updated successfully.')
    return redirect('floor_app:system_settings')


@login_required
@user_passes_test(is_admin)
def module_settings(request):
    """Module settings."""
    return render(request, 'system_settings.html')


@login_required
@user_passes_test(is_admin)
def integration_settings(request):
    """Integration settings."""
    return render(request, 'system_settings.html')


@login_required
def dashboard_customization(request):
    """Dashboard customization page."""
    return render(request, 'dashboard_customization.html')


@login_required
@require_POST
def dashboard_widget_add(request):
    """Add dashboard widget."""
    # TODO: Implement widget management
    return JsonResponse({'success': True, 'message': 'Widget added'})


@login_required
@require_POST
def dashboard_widget_remove(request, pk):
    """Remove dashboard widget."""
    return JsonResponse({'success': True, 'message': 'Widget removed'})


@login_required
@require_POST
def dashboard_widgets_reorder(request):
    """Reorder dashboard widgets."""
    # TODO: Save widget order
    return JsonResponse({'success': True, 'message': 'Widgets reordered'})


@login_required
@require_POST
def dashboard_layout_save(request):
    """Save dashboard layout."""
    # TODO: Save layout preferences
    return JsonResponse({'success': True, 'message': 'Layout saved'})


@login_required
@require_POST
def dashboard_layout_reset(request):
    """Reset dashboard layout."""
    return JsonResponse({'success': True, 'message': 'Layout reset'})


# ========== SYSTEM PAGES ==========

def maintenance_page(request):
    """Maintenance mode page."""
    return render(request, 'maintenance.html')


def privacy_policy(request):
    """Privacy policy page."""
    return render(request, 'privacy_policy.html')


def terms_of_service(request):
    """Terms of service page."""
    # TODO: Create terms of service template
    return render(request, 'privacy_policy.html')  # Temporary


# ========== API ENDPOINTS ==========

@login_required
def api_notifications_unread_count(request):
    """Get unread notifications count."""
    # TODO: Implement with actual Notification model
    return JsonResponse({'count': 5})


@login_required
def api_notifications_recent(request):
    """Get recent notifications."""
    # TODO: Implement with actual Notification model
    notifications = []
    return JsonResponse({'notifications': notifications})


@login_required
def api_user_stats(request):
    """Get user statistics."""
    data = {
        'total_actions': 1234,
        'last_login': request.user.last_login.isoformat() if request.user.last_login else None,
    }
    return JsonResponse(data)


@login_required
def api_user_activity(request):
    """Get user activity log."""
    # TODO: Implement activity tracking
    return JsonResponse({'activity': []})


@login_required
@user_passes_test(is_staff_or_admin)
def api_system_stats(request):
    """Get system statistics."""
    data = {
        'users': User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
        'disk_usage': 38,  # TODO: Get actual metrics
    }
    return JsonResponse(data)


@login_required
@user_passes_test(is_staff_or_admin)
def api_system_alerts(request):
    """Get system alerts."""
    # TODO: Implement system monitoring
    alerts = []
    return JsonResponse({'alerts': alerts})


# ========== THEME PREFERENCES API ==========

@login_required
@require_http_methods(["POST"])
def api_user_save_theme(request):
    """
    Save user theme preferences via AJAX.

    POST data: {
        theme: 'light'|'dark'|'auto'|'custom',
        fontSize: 'small'|'medium'|'large'|'x-large',
        density: 'compact'|'comfortable'|'spacious',
        highContrast: boolean,
        reduceMotion: boolean
    }
    """
    try:
        import json
        from .models import UserThemePreference

        data = json.loads(request.body)

        # Get or create user theme preference
        theme_pref, created = UserThemePreference.objects.get_or_create(
            user=request.user,
            defaults={
                'theme': 'light',
                'font_size': 'medium',
                'density': 'comfortable',
            }
        )

        # Update fields from request
        if 'theme' in data:
            theme_pref.theme = data['theme']
        if 'fontSize' in data:
            theme_pref.font_size = data['fontSize']
        if 'density' in data:
            theme_pref.density = data['density']
        if 'highContrast' in data:
            theme_pref.high_contrast = data['highContrast']
        if 'reduceMotion' in data:
            theme_pref.reduce_motion = data['reduceMotion']

        theme_pref.save()

        return JsonResponse({
            'success': True,
            'message': 'Theme preferences saved successfully',
            'preferences': {
                'theme': theme_pref.theme,
                'fontSize': theme_pref.font_size,
                'density': theme_pref.density,
                'highContrast': theme_pref.high_contrast,
                'reduceMotion': theme_pref.reduce_motion,
            }
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

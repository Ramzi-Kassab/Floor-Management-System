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

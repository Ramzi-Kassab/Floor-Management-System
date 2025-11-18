"""
Training Management Views
Comprehensive views for training programs, sessions, and employee enrollment
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Count, Avg, Sum
from django.utils import timezone
from django.http import JsonResponse

from floor_app.operations.hr.models import (
    TrainingProgram, TrainingSession, EmployeeTraining,
    HREmployee, TrainingStatus, TrainingType
)
from floor_app.operations.hr.forms.training_forms import (
    TrainingProgramForm, TrainingSessionForm, EnrollmentForm,
    TrainingCompletionForm, TrainingFeedbackForm, TrainingSearchForm
)


def is_staff(user):
    """Check if user is staff"""
    return user.is_staff


# ============================================================================
# TRAINING PROGRAM VIEWS
# ============================================================================

class TrainingProgramListView(LoginRequiredMixin, ListView):
    """List all training programs"""
    model = TrainingProgram
    template_name = 'hr/training/program_list.html'
    context_object_name = 'programs'
    paginate_by = 20

    def get_queryset(self):
        queryset = TrainingProgram.objects.filter(is_deleted=False)

        # Filter by active status
        is_active = self.request.GET.get('is_active')
        if is_active:
            queryset = queryset.filter(is_active=(is_active == 'true'))

        # Filter by training type
        training_type = self.request.GET.get('training_type')
        if training_type:
            queryset = queryset.filter(training_type=training_type)

        # Search by name or code
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(code__icontains=search)
            )

        return queryset.order_by('training_type', 'name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['training_types'] = TrainingType.CHOICES
        return context


class TrainingProgramDetailView(LoginRequiredMixin, DetailView):
    """View training program details"""
    model = TrainingProgram
    template_name = 'hr/training/program_detail.html'
    context_object_name = 'program'

    def get_queryset(self):
        return TrainingProgram.objects.filter(is_deleted=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get statistics
        context['total_sessions'] = self.object.sessions.filter(is_deleted=False).count()
        context['active_sessions'] = self.object.sessions.filter(
            is_deleted=False,
            status__in=[TrainingStatus.SCHEDULED, TrainingStatus.IN_PROGRESS]
        ).count()
        context['total_participants'] = EmployeeTraining.objects.filter(
            training_session__program=self.object
        ).count()
        context['completion_rate'] = EmployeeTraining.objects.filter(
            training_session__program=self.object,
            completion_status=TrainingStatus.COMPLETED
        ).count()

        # Recent sessions
        context['recent_sessions'] = self.object.sessions.filter(
            is_deleted=False
        ).order_by('-start_date')[:5]

        return context


class TrainingProgramCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create new training program"""
    model = TrainingProgram
    form_class = TrainingProgramForm
    template_name = 'hr/training/program_form.html'

    def test_func(self):
        return self.request.user.is_staff

    def get_success_url(self):
        return reverse('hr:training_program_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, f'Training program "{form.instance.name}" created successfully!')
        return super().form_valid(form)


class TrainingProgramUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Update training program"""
    model = TrainingProgram
    form_class = TrainingProgramForm
    template_name = 'hr/training/program_form.html'

    def test_func(self):
        return self.request.user.is_staff

    def get_queryset(self):
        return TrainingProgram.objects.filter(is_deleted=False)

    def get_success_url(self):
        return reverse('hr:training_program_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, f'Training program "{form.instance.name}" updated successfully!')
        return super().form_valid(form)


# ============================================================================
# TRAINING SESSION VIEWS
# ============================================================================

class TrainingSessionListView(LoginRequiredMixin, ListView):
    """List all training sessions"""
    model = TrainingSession
    template_name = 'hr/training/session_list.html'
    context_object_name = 'sessions'
    paginate_by = 20

    def get_queryset(self):
        queryset = TrainingSession.objects.filter(is_deleted=False).select_related('program')

        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        # Filter by program
        program_id = self.request.GET.get('program')
        if program_id:
            queryset = queryset.filter(program_id=program_id)

        # Filter by date range
        date_from = self.request.GET.get('date_from')
        if date_from:
            queryset = queryset.filter(start_date__gte=date_from)

        date_to = self.request.GET.get('date_to')
        if date_to:
            queryset = queryset.filter(end_date__lte=date_to)

        return queryset.order_by('-start_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['programs'] = TrainingProgram.objects.filter(is_deleted=False, is_active=True)
        context['statuses'] = TrainingStatus.CHOICES

        # Statistics
        queryset = self.get_queryset()
        context['total_sessions'] = queryset.count()
        context['upcoming_sessions'] = queryset.filter(
            status=TrainingStatus.SCHEDULED,
            start_date__gte=timezone.now().date()
        ).count()
        context['in_progress_sessions'] = queryset.filter(status=TrainingStatus.IN_PROGRESS).count()

        return context


class TrainingSessionDetailView(LoginRequiredMixin, DetailView):
    """View training session details"""
    model = TrainingSession
    template_name = 'hr/training/session_detail.html'
    context_object_name = 'session'

    def get_queryset(self):
        return TrainingSession.objects.filter(is_deleted=False).select_related('program')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get participants
        context['participants'] = self.object.participants.select_related('employee').order_by('employee__employee_no')

        # Check if user can manage
        context['can_manage'] = self.request.user.is_staff

        # Check if seats available
        max_participants = self.object.program.max_participants
        current_participants = self.object.participants.count()
        context['seats_available'] = max_participants - current_participants
        context['is_full'] = current_participants >= max_participants

        return context


class TrainingSessionCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create new training session"""
    model = TrainingSession
    form_class = TrainingSessionForm
    template_name = 'hr/training/session_form.html'

    def test_func(self):
        return self.request.user.is_staff

    def get_success_url(self):
        return reverse('hr:training_session_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, f'Training session "{form.instance.session_code}" created successfully!')
        return super().form_valid(form)


class TrainingSessionUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Update training session"""
    model = TrainingSession
    form_class = TrainingSessionForm
    template_name = 'hr/training/session_form.html'

    def test_func(self):
        return self.request.user.is_staff

    def get_queryset(self):
        return TrainingSession.objects.filter(is_deleted=False)

    def get_success_url(self):
        return reverse('hr:training_session_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, f'Training session "{form.instance.session_code}" updated successfully!')
        return super().form_valid(form)


# ============================================================================
# ENROLLMENT VIEWS
# ============================================================================

@login_required
@user_passes_test(is_staff)
def enroll_employees(request, session_id):
    """Enroll employees in a training session"""
    session = get_object_or_404(TrainingSession, pk=session_id, is_deleted=False)

    if request.method == 'POST':
        form = EnrollmentForm(request.POST, session=session)
        if form.is_valid():
            employees = form.cleaned_data['employees']
            notes = form.cleaned_data['notes']

            # Check if session is full
            max_participants = session.program.max_participants
            current_count = session.participants.count()
            available_seats = max_participants - current_count

            if len(employees) > available_seats:
                messages.error(
                    request,
                    f'Cannot enroll {len(employees)} employees. Only {available_seats} seats available.'
                )
                return redirect('hr:training_session_detail', pk=session_id)

            # Enroll employees
            enrolled_count = 0
            for employee in employees:
                EmployeeTraining.objects.create(
                    employee=employee,
                    training_session=session,
                    registered_by_id=request.user.id,
                    notes=notes,
                    cost_incurred=session.program.cost_per_person
                )
                enrolled_count += 1

            # Update session counts
            session.registered_count = session.participants.count()
            session.save()

            messages.success(request, f'Successfully enrolled {enrolled_count} employee(s) in the training session.')
            return redirect('hr:training_session_detail', pk=session_id)
    else:
        form = EnrollmentForm(session=session)

    return render(request, 'hr/training/enroll.html', {
        'form': form,
        'session': session,
    })


@login_required
def my_training_dashboard(request):
    """Employee's personal training dashboard"""
    try:
        employee = request.user.hremployee
    except:
        messages.error(request, 'Employee record not found.')
        return redirect('hr:dashboard')

    # Get employee's training records
    training_records = EmployeeTraining.objects.filter(
        employee=employee
    ).select_related('training_session__program').order_by('-training_session__start_date')

    # Upcoming trainings
    upcoming_trainings = training_records.filter(
        training_session__start_date__gte=timezone.now().date(),
        completion_status__in=[TrainingStatus.SCHEDULED, TrainingStatus.IN_PROGRESS]
    )

    # Completed trainings
    completed_trainings = training_records.filter(
        completion_status=TrainingStatus.COMPLETED
    )

    # Available sessions (not enrolled)
    enrolled_session_ids = training_records.values_list('training_session_id', flat=True)
    available_sessions = TrainingSession.objects.filter(
        is_deleted=False,
        status=TrainingStatus.SCHEDULED,
        start_date__gte=timezone.now().date()
    ).exclude(id__in=enrolled_session_ids).select_related('program')[:10]

    context = {
        'employee': employee,
        'training_records': training_records[:10],
        'upcoming_trainings': upcoming_trainings,
        'completed_trainings': completed_trainings,
        'available_sessions': available_sessions,
        'total_hours': completed_trainings.aggregate(
            total=Sum('training_session__program__duration_hours')
        )['total'] or 0,
    }

    return render(request, 'hr/training/my_dashboard.html', context)


@login_required
@user_passes_test(is_staff)
def complete_training(request, pk):
    """Mark employee training as completed"""
    training = get_object_or_404(EmployeeTraining, pk=pk)

    if request.method == 'POST':
        form = TrainingCompletionForm(request.POST, instance=training)
        if form.is_valid():
            training = form.save(commit=False)

            if training.passed:
                training.mark_completed(
                    passed=True,
                    score=training.assessment_score
                )
            else:
                training.completion_status = TrainingStatus.COMPLETED
                training.completed_at = timezone.now()
                training.save()

            # Update session counts
            session = training.training_session
            session.attended_count = session.participants.filter(attended=True).count()
            session.passed_count = session.participants.filter(passed=True).count()
            session.save()

            messages.success(
                request,
                f'Training completion recorded for {training.employee.get_full_name()}'
            )
            return redirect('hr:training_session_detail', pk=training.training_session_id)
    else:
        form = TrainingCompletionForm(instance=training)

    return render(request, 'hr/training/complete.html', {
        'form': form,
        'training': training,
    })


@login_required
def submit_feedback(request, pk):
    """Submit feedback for completed training"""
    training = get_object_or_404(EmployeeTraining, pk=pk)

    # Check ownership
    if not request.user.is_staff:
        try:
            if training.employee != request.user.hremployee:
                messages.error(request, 'You can only submit feedback for your own training.')
                return redirect('hr:my_training_dashboard')
        except:
            messages.error(request, 'Employee record not found.')
            return redirect('hr:my_training_dashboard')

    if request.method == 'POST':
        form = TrainingFeedbackForm(request.POST, instance=training)
        if form.is_valid():
            form.save()
            messages.success(request, 'Thank you for your feedback!')
            return redirect('hr:my_training_dashboard')
    else:
        form = TrainingFeedbackForm(instance=training)

    return render(request, 'hr/training/feedback.html', {
        'form': form,
        'training': training,
    })

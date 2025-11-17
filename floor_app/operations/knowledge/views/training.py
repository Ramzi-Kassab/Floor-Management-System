"""
Training Center views.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.utils import timezone

from ..models import (
    TrainingCourse, TrainingLesson, TrainingEnrollment,
    TrainingLessonProgress, TrainingSchedule, TrainingScheduleRegistration
)
from ..services import TrainingService


@login_required
def training_dashboard(request):
    """Training center main dashboard."""
    user_training = None

    if hasattr(request.user, 'employee'):
        employee = request.user.employee
        user_training = TrainingService.get_employee_training_dashboard(employee)

    # Available courses
    available_courses = TrainingCourse.objects.filter(
        status=TrainingCourse.Status.PUBLISHED,
        is_deleted=False
    ).order_by('-is_mandatory', 'title')[:12]

    # Upcoming training sessions
    upcoming_sessions = TrainingSchedule.objects.filter(
        scheduled_date__gte=timezone.now().date(),
        registration_open=True,
        is_deleted=False
    ).order_by('scheduled_date')[:5]

    context = {
        'user_training': user_training,
        'available_courses': available_courses,
        'upcoming_sessions': upcoming_sessions,
    }

    return render(request, 'knowledge/training_dashboard.html', context)


class TrainingCourseListView(LoginRequiredMixin, ListView):
    """List all available training courses."""
    model = TrainingCourse
    template_name = 'knowledge/course_list.html'
    context_object_name = 'courses'
    paginate_by = 12

    def get_queryset(self):
        qs = TrainingCourse.objects.filter(
            status=TrainingCourse.Status.PUBLISHED,
            is_deleted=False
        ).select_related('owner_department')

        # Filter by type
        course_type = self.request.GET.get('type', '')
        if course_type:
            qs = qs.filter(course_type=course_type)

        # Filter by difficulty
        difficulty = self.request.GET.get('difficulty', '')
        if difficulty:
            qs = qs.filter(difficulty_level=difficulty)

        # Filter by mandatory
        mandatory = self.request.GET.get('mandatory', '')
        if mandatory == 'yes':
            qs = qs.filter(is_mandatory=True)
        elif mandatory == 'no':
            qs = qs.filter(is_mandatory=False)

        # Search
        query = self.request.GET.get('q', '')
        if query:
            from django.db.models import Q
            qs = qs.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(code__icontains=query)
            )

        return qs.order_by('-is_mandatory', 'title')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course_types'] = TrainingCourse.CourseType.choices
        context['difficulties'] = TrainingCourse.DifficultyLevel.choices
        return context


@login_required
def course_detail(request, code):
    """View course details and lessons."""
    course = get_object_or_404(
        TrainingCourse.objects.select_related('owner_department', 'grants_qualification')
        .prefetch_related('lessons', 'target_positions', 'prerequisite_courses'),
        code=code,
        is_deleted=False
    )

    enrollment = None
    lesson_progress = {}

    if hasattr(request.user, 'employee'):
        try:
            enrollment = TrainingEnrollment.objects.get(
                course=course,
                employee=request.user.employee
            )
            # Get lesson progress
            for progress in enrollment.lesson_progress.all():
                lesson_progress[progress.lesson_id] = progress
        except TrainingEnrollment.DoesNotExist:
            pass

    lessons = course.lessons.filter(is_deleted=False).order_by('sequence')

    context = {
        'course': course,
        'lessons': lessons,
        'enrollment': enrollment,
        'lesson_progress': lesson_progress,
        'stats': TrainingService.get_course_statistics(course),
    }

    return render(request, 'knowledge/course_detail.html', context)


@login_required
def course_enroll(request, code):
    """Enroll user in a training course."""
    if not hasattr(request.user, 'employee'):
        messages.error(request, 'You must be an employee to enroll in courses.')
        return redirect('knowledge:course_detail', code=code)

    course = get_object_or_404(
        TrainingCourse,
        code=code,
        status=TrainingCourse.Status.PUBLISHED,
        is_deleted=False
    )

    try:
        enrollment, created = TrainingService.enroll_employee(
            course, request.user.employee, request.user
        )
        if created:
            messages.success(request, f'You have been enrolled in "{course.title}".')
        else:
            messages.info(request, 'You are already enrolled in this course.')
    except ValueError as e:
        messages.error(request, str(e))

    return redirect('knowledge:course_detail', code=code)


@login_required
def lesson_view(request, code, sequence):
    """View a specific lesson content."""
    course = get_object_or_404(TrainingCourse, code=code, is_deleted=False)
    lesson = get_object_or_404(
        TrainingLesson,
        course=course,
        sequence=sequence,
        is_deleted=False
    )

    # Check enrollment
    enrollment = None
    progress = None

    if hasattr(request.user, 'employee'):
        try:
            enrollment = TrainingEnrollment.objects.get(
                course=course,
                employee=request.user.employee
            )
            progress = TrainingService.start_lesson(enrollment, lesson)
        except TrainingEnrollment.DoesNotExist:
            messages.warning(request, 'You are not enrolled in this course.')
            return redirect('knowledge:course_detail', code=code)

    # Get next/previous lessons
    lessons = course.lessons.filter(is_deleted=False).order_by('sequence')
    current_index = list(lessons.values_list('sequence', flat=True)).index(sequence)

    prev_lesson = None
    next_lesson = None

    if current_index > 0:
        prev_lesson = lessons[current_index - 1]
    if current_index < len(lessons) - 1:
        next_lesson = lessons[current_index + 1]

    context = {
        'course': course,
        'lesson': lesson,
        'enrollment': enrollment,
        'progress': progress,
        'prev_lesson': prev_lesson,
        'next_lesson': next_lesson,
    }

    return render(request, 'knowledge/lesson_view.html', context)


@login_required
def lesson_complete(request, code, sequence):
    """Mark a lesson as completed."""
    if not hasattr(request.user, 'employee'):
        return JsonResponse({'error': 'Not an employee'}, status=400)

    course = get_object_or_404(TrainingCourse, code=code, is_deleted=False)
    lesson = get_object_or_404(
        TrainingLesson, course=course, sequence=sequence, is_deleted=False
    )

    try:
        enrollment = TrainingEnrollment.objects.get(
            course=course,
            employee=request.user.employee
        )
    except TrainingEnrollment.DoesNotExist:
        return JsonResponse({'error': 'Not enrolled'}, status=400)

    # Get quiz score if applicable
    quiz_score = None
    if request.method == 'POST' and lesson.lesson_type == 'QUIZ':
        quiz_score = request.POST.get('score')
        if quiz_score:
            quiz_score = float(quiz_score)

    try:
        progress = TrainingService.complete_lesson(enrollment, lesson, quiz_score)
        messages.success(request, f'Lesson "{lesson.title}" completed!')

        # Reload enrollment for updated progress
        enrollment.refresh_from_db()

        return JsonResponse({
            'success': True,
            'progress': enrollment.progress_percentage,
            'completed': enrollment.status == TrainingEnrollment.Status.COMPLETED
        })
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def my_training(request):
    """View user's enrolled courses and progress."""
    if not hasattr(request.user, 'employee'):
        messages.error(request, 'You must be an employee to view training.')
        return redirect('knowledge:training_dashboard')

    employee = request.user.employee
    dashboard = TrainingService.get_employee_training_dashboard(employee)

    context = {
        'dashboard': dashboard,
        'enrollments': dashboard['enrollments'].select_related('course').order_by('-enrolled_at'),
    }

    return render(request, 'knowledge/my_training.html', context)


@login_required
def enrollment_detail(request, pk):
    """View detailed enrollment progress."""
    if not hasattr(request.user, 'employee'):
        messages.error(request, 'You must be an employee.')
        return redirect('knowledge:training_dashboard')

    enrollment = get_object_or_404(
        TrainingEnrollment.objects.select_related('course')
        .prefetch_related('lesson_progress__lesson'),
        pk=pk,
        employee=request.user.employee
    )

    context = {
        'enrollment': enrollment,
        'course': enrollment.course,
        'lesson_progress': enrollment.lesson_progress.all().select_related('lesson').order_by('lesson__sequence')
    }

    return render(request, 'knowledge/enrollment_detail.html', context)


class TrainingScheduleListView(LoginRequiredMixin, ListView):
    """List upcoming training sessions."""
    model = TrainingSchedule
    template_name = 'knowledge/schedule_list.html'
    context_object_name = 'schedules'
    paginate_by = 10

    def get_queryset(self):
        return TrainingSchedule.objects.filter(
            scheduled_date__gte=timezone.now().date(),
            is_deleted=False
        ).select_related('course', 'instructor').order_by('scheduled_date', 'start_time')


@login_required
def schedule_register(request, pk):
    """Register for a scheduled training session."""
    if not hasattr(request.user, 'employee'):
        messages.error(request, 'You must be an employee to register.')
        return redirect('knowledge:schedule_list')

    schedule = get_object_or_404(
        TrainingSchedule,
        pk=pk,
        registration_open=True,
        is_deleted=False
    )

    if schedule.is_full:
        messages.error(request, 'This session is full.')
        return redirect('knowledge:schedule_list')

    registration, created = TrainingScheduleRegistration.objects.get_or_create(
        schedule=schedule,
        employee=request.user.employee
    )

    if created:
        messages.success(request, f'You have been registered for {schedule.title}.')
    else:
        messages.info(request, 'You are already registered for this session.')

    return redirect('knowledge:schedule_list')

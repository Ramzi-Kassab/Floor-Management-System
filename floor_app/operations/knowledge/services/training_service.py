"""
Training Service - Business logic for training center operations.
"""
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import timedelta


class TrainingService:
    """Service layer for training operations."""

    @staticmethod
    def get_employee_training_dashboard(employee):
        """Get training overview for an employee."""
        from floor_app.operations.knowledge.models import (
            TrainingEnrollment,
            TrainingCourse
        )

        enrollments = TrainingEnrollment.objects.filter(employee=employee)

        # Get mandatory courses not yet enrolled
        mandatory_courses = TrainingCourse.objects.filter(
            is_mandatory=True,
            status=TrainingCourse.Status.PUBLISHED,
            is_deleted=False
        ).filter(
            Q(target_positions=employee.position) |
            Q(target_departments=employee.department) |
            Q(target_positions__isnull=True, target_departments__isnull=True)
        ).exclude(
            enrollments__employee=employee
        ).distinct()

        # Get expiring certifications
        expiring = enrollments.filter(
            status=TrainingEnrollment.Status.COMPLETED,
            expires_at__isnull=False,
            expires_at__lte=timezone.now() + timedelta(days=90)
        ).order_by('expires_at')

        return {
            'enrolled': enrollments.filter(status=TrainingEnrollment.Status.ENROLLED).count(),
            'in_progress': enrollments.filter(status=TrainingEnrollment.Status.IN_PROGRESS).count(),
            'completed': enrollments.filter(status=TrainingEnrollment.Status.COMPLETED).count(),
            'mandatory_pending': mandatory_courses.count(),
            'expiring_soon': expiring.count(),
            'enrollments': enrollments,
            'mandatory_courses': mandatory_courses,
            'expiring_certifications': expiring
        }

    @staticmethod
    def enroll_employee(course, employee, enrolled_by=None):
        """Enroll an employee in a training course."""
        from floor_app.operations.knowledge.models import TrainingEnrollment

        # Check prerequisites
        for prereq in course.prerequisite_courses.all():
            completed = TrainingEnrollment.objects.filter(
                employee=employee,
                course=prereq,
                status=TrainingEnrollment.Status.COMPLETED
            ).exists()
            if not completed:
                raise ValueError(f"Prerequisite not met: {prereq.title}")

        enrollment, created = TrainingEnrollment.objects.get_or_create(
            course=course,
            employee=employee,
            defaults={
                'enrolled_by': enrolled_by,
                'status': TrainingEnrollment.Status.ENROLLED
            }
        )

        if created:
            # Update course metrics
            course.total_enrollments += 1
            course.save(update_fields=['total_enrollments'])

        return enrollment, created

    @staticmethod
    def start_lesson(enrollment, lesson):
        """Start a lesson for an enrollment."""
        from floor_app.operations.knowledge.models import TrainingLessonProgress

        progress, created = TrainingLessonProgress.objects.get_or_create(
            enrollment=enrollment,
            lesson=lesson,
            defaults={'started_at': timezone.now()}
        )

        if not progress.started_at:
            progress.started_at = timezone.now()
            progress.save()

        # Update enrollment status
        if enrollment.status == TrainingEnrollment.Status.ENROLLED:
            enrollment.status = TrainingEnrollment.Status.IN_PROGRESS
            enrollment.started_at = timezone.now()
            enrollment.save()

        return progress

    @staticmethod
    def complete_lesson(enrollment, lesson, quiz_score=None):
        """Mark a lesson as completed."""
        from floor_app.operations.knowledge.models import TrainingLessonProgress

        progress, _ = TrainingLessonProgress.objects.get_or_create(
            enrollment=enrollment,
            lesson=lesson
        )

        if lesson.lesson_type == 'QUIZ' and quiz_score is not None:
            progress.quiz_score = quiz_score
            progress.quiz_attempts += 1
            if quiz_score < lesson.passing_score:
                raise ValueError(f"Quiz score {quiz_score}% is below passing score {lesson.passing_score}%")

        progress.mark_completed()
        return progress

    @staticmethod
    def get_course_statistics(course):
        """Get statistics for a training course."""
        enrollments = course.enrollments.all()

        completed = enrollments.filter(status=TrainingEnrollment.Status.COMPLETED)

        avg_score = completed.filter(
            final_score__isnull=False
        ).aggregate(avg=Avg('final_score'))['avg']

        avg_time = completed.filter(
            total_time_spent_minutes__gt=0
        ).aggregate(avg=Avg('total_time_spent_minutes'))['avg']

        return {
            'total_enrollments': enrollments.count(),
            'completed': completed.count(),
            'in_progress': enrollments.filter(status=TrainingEnrollment.Status.IN_PROGRESS).count(),
            'completion_rate': (completed.count() / enrollments.count() * 100) if enrollments.count() > 0 else 0,
            'average_score': avg_score,
            'average_completion_time': avg_time,
            'passed': completed.filter(passed_assessment=True).count(),
            'failed': enrollments.filter(status=TrainingEnrollment.Status.FAILED).count()
        }

    @staticmethod
    def get_department_training_summary(department):
        """Get training summary for a department."""
        from floor_app.operations.knowledge.models import TrainingEnrollment
        from floor_app.operations.hr.models import HREmployee

        employees = HREmployee.objects.filter(
            department=department,
            status='ACTIVE',
            is_deleted=False
        )

        total_employees = employees.count()
        if total_employees == 0:
            return {}

        enrollments = TrainingEnrollment.objects.filter(
            employee__in=employees
        )

        return {
            'total_employees': total_employees,
            'total_enrollments': enrollments.count(),
            'completed_courses': enrollments.filter(status=TrainingEnrollment.Status.COMPLETED).count(),
            'in_progress': enrollments.filter(status=TrainingEnrollment.Status.IN_PROGRESS).count(),
            'avg_per_employee': enrollments.count() / total_employees if total_employees > 0 else 0,
            'completion_rate': (
                enrollments.filter(status=TrainingEnrollment.Status.COMPLETED).count() /
                enrollments.count() * 100
            ) if enrollments.count() > 0 else 0
        }

    @staticmethod
    def get_overdue_training():
        """Get training that is overdue for employees."""
        from floor_app.operations.knowledge.models import TrainingCourse, TrainingEnrollment
        from floor_app.operations.hr.models import HREmployee

        # Find mandatory courses
        mandatory_courses = TrainingCourse.objects.filter(
            is_mandatory=True,
            status=TrainingCourse.Status.PUBLISHED,
            is_deleted=False
        )

        overdue = []

        for course in mandatory_courses:
            # Get target employees
            target_employees = HREmployee.objects.filter(
                status='ACTIVE',
                is_deleted=False
            )

            if course.target_departments.exists():
                target_employees = target_employees.filter(
                    department__in=course.target_departments.all()
                )

            if course.target_positions.exists():
                target_employees = target_employees.filter(
                    position__in=course.target_positions.all()
                )

            # Find those not enrolled
            enrolled_ids = course.enrollments.values_list('employee_id', flat=True)
            missing = target_employees.exclude(id__in=enrolled_ids)

            if missing.exists():
                overdue.append({
                    'course': course,
                    'missing_employees': missing,
                    'count': missing.count()
                })

        return overdue

    @staticmethod
    def bulk_enroll(course, employees, enrolled_by=None):
        """Bulk enroll multiple employees in a course."""
        results = {
            'success': [],
            'failed': [],
            'already_enrolled': []
        }

        for employee in employees:
            try:
                enrollment, created = TrainingService.enroll_employee(
                    course, employee, enrolled_by
                )
                if created:
                    results['success'].append(employee)
                else:
                    results['already_enrolled'].append(employee)
            except Exception as e:
                results['failed'].append({'employee': employee, 'error': str(e)})

        return results

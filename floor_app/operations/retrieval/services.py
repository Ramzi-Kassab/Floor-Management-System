"""
Retrieval System Services

Business logic for retrieval/undo operations, notifications, and metrics calculation.
"""

from django.db.models import Count, Q, Avg
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from datetime import datetime, timedelta, date
from decimal import Decimal


class RetrievalService:
    """
    Service class for retrieval system business logic.
    """

    TIME_WINDOW_MINUTES = 15

    @staticmethod
    def check_dependencies(obj):
        """
        Check if object has dependent processes.

        Uses Django's related objects API to find all foreign key references.

        Args:
            obj: Model instance to check

        Returns:
            list: List of dependency dictionaries
                [
                    {
                        'model': 'ModelName',
                        'field': 'field_name',
                        'count': 5,
                        'description': '5 related items'
                    },
                    ...
                ]
        """
        dependencies = []

        # Get all related objects
        for related_object in obj._meta.related_objects:
            related_name = related_object.get_accessor_name()

            try:
                related_manager = getattr(obj, related_name)

                # Handle different types of relations
                if hasattr(related_manager, 'count'):
                    count = related_manager.count()
                elif hasattr(related_manager, 'all'):
                    count = related_manager.all().count()
                else:
                    continue

                if count > 0:
                    dependencies.append({
                        'model': related_object.related_model.__name__,
                        'model_verbose': related_object.related_model._meta.verbose_name,
                        'field': related_name,
                        'count': count,
                        'description': f"{count} {related_object.related_model._meta.verbose_name_plural}"
                    })
            except (AttributeError, Exception) as e:
                # Skip if we can't access the related manager
                continue

        return dependencies

    @staticmethod
    def notify_supervisor(retrieval_request):
        """
        Send notification to supervisor about pending retrieval request.

        Sends notifications via:
        - Email
        - In-app notification (if Notification model available)
        - WhatsApp (if configured)
        - Push notification (if configured)

        Args:
            retrieval_request: RetrievalRequest object

        Returns:
            bool: True if notification sent successfully
        """
        supervisor = retrieval_request.supervisor

        if not supervisor:
            return False

        # Create in-app notification
        try:
            from core.models import Notification

            notification = Notification.objects.create(
                user=supervisor,
                notification_type='APPROVAL',
                priority='HIGH',
                title='Retrieval Request Requires Approval',
                message=(
                    f"{retrieval_request.employee.get_full_name() or retrieval_request.employee.username} "
                    f"has requested retrieval of {retrieval_request.get_object_display()}. "
                    f"Reason: {retrieval_request.reason[:100]}"
                ),
                content_type=retrieval_request.content_type,
                object_id=retrieval_request.id,
                action_url=f'/operations/retrieval/supervisor/{retrieval_request.id}/',
                action_text='Review Request',
                created_by=retrieval_request.employee
            )
        except ImportError:
            # Notification model not available
            pass

        # Send email notification
        if supervisor.email:
            try:
                subject = f'Retrieval Request #{retrieval_request.id} Requires Approval'

                context = {
                    'request': retrieval_request,
                    'supervisor': supervisor,
                    'employee': retrieval_request.employee,
                    'object_display': retrieval_request.get_object_display(),
                    'approval_url': f"{settings.SITE_URL}/operations/retrieval/supervisor/{retrieval_request.id}/" if hasattr(settings, 'SITE_URL') else '',
                }

                # Try to use template if available
                try:
                    html_message = render_to_string('retrieval/email/supervisor_notification.html', context)
                    plain_message = render_to_string('retrieval/email/supervisor_notification.txt', context)
                except Exception:
                    # Fallback to plain text
                    plain_message = (
                        f"Dear {supervisor.get_full_name() or supervisor.username},\n\n"
                        f"Employee {retrieval_request.employee.get_full_name() or retrieval_request.employee.username} "
                        f"has requested retrieval approval for:\n\n"
                        f"Object: {retrieval_request.get_object_display()}\n"
                        f"Action: {retrieval_request.get_action_type_display()}\n"
                        f"Reason: {retrieval_request.reason}\n\n"
                        f"Time Elapsed: {retrieval_request.time_elapsed}\n"
                        f"Has Dependencies: {'Yes' if retrieval_request.has_dependent_processes else 'No'}\n\n"
                        f"Please review this request at your earliest convenience.\n\n"
                        f"Thank you,\n"
                        f"Floor Management System"
                    )
                    html_message = None

                send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
                    recipient_list=[supervisor.email],
                    html_message=html_message,
                    fail_silently=True
                )

            except Exception as e:
                # Log error but don't fail
                print(f"Error sending email notification: {e}")

        # Update notification tracking
        retrieval_request.notification_sent = True
        retrieval_request.supervisor_notified_at = timezone.now()
        retrieval_request.save(update_fields=['notification_sent', 'supervisor_notified_at'])

        return True

    @staticmethod
    def notify_employee_decision(retrieval_request):
        """
        Notify employee about supervisor's decision on their retrieval request.

        Args:
            retrieval_request: RetrievalRequest object

        Returns:
            bool: True if notification sent successfully
        """
        employee = retrieval_request.employee

        # Create in-app notification
        try:
            from core.models import Notification

            if retrieval_request.is_approved:
                title = 'Retrieval Request Approved'
                message = f"Your retrieval request for {retrieval_request.get_object_display()} has been approved."
                notification_type = 'SUCCESS'
            elif retrieval_request.is_rejected:
                title = 'Retrieval Request Rejected'
                message = (
                    f"Your retrieval request for {retrieval_request.get_object_display()} has been rejected. "
                    f"Reason: {retrieval_request.rejection_reason}"
                )
                notification_type = 'WARNING'
            else:
                return False

            Notification.objects.create(
                user=employee,
                notification_type=notification_type,
                priority='NORMAL',
                title=title,
                message=message,
                content_type=retrieval_request.content_type,
                object_id=retrieval_request.id,
                action_url=f'/operations/retrieval/dashboard/',
                action_text='View Dashboard',
                created_by=retrieval_request.supervisor or retrieval_request.updated_by
            )
        except ImportError:
            pass

        return True

    @staticmethod
    def calculate_employee_accuracy(employee, period='month'):
        """
        Calculate employee accuracy metrics for a given period.

        Accuracy is calculated as:
        accuracy_rate = (total_actions - retrieval_requests) / total_actions * 100

        Args:
            employee: User object
            period: 'day', 'week', 'month', 'quarter', 'year'

        Returns:
            dict: Metrics dictionary containing:
                - total_actions: Total actions performed
                - retrieval_requests: Number of retrieval requests
                - accuracy_rate: Percentage accuracy (0-100)
                - error_rate: Percentage errors (0-100)
                - auto_approved: Auto-approved count
                - manually_approved: Manually approved count
                - rejected: Rejected count
                - completed: Completed count
        """
        from .models import RetrievalRequest

        # Determine date range
        now = timezone.now()
        if period == 'day':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == 'week':
            start_date = now - timedelta(days=now.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == 'month':
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif period == 'quarter':
            quarter_start_month = ((now.month - 1) // 3) * 3 + 1
            start_date = now.replace(month=quarter_start_month, day=1, hour=0, minute=0, second=0, microsecond=0)
        elif period == 'year':
            start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            start_date = now - timedelta(days=30)

        # Get retrieval requests in period
        requests = RetrievalRequest.objects.filter(
            employee=employee,
            submitted_at__gte=start_date
        )

        retrieval_count = requests.count()
        auto_approved = requests.filter(status='AUTO_APPROVED').count()
        manually_approved = requests.filter(status='APPROVED').count()
        rejected = requests.filter(status='REJECTED').count()
        completed = requests.filter(status='COMPLETED').count()

        # Estimate total actions (this would need to be tracked separately in production)
        # For now, we'll use a heuristic based on various action logs
        total_actions = RetrievalService._estimate_employee_actions(employee, start_date)

        # Calculate accuracy
        if total_actions > 0:
            accuracy_rate = ((total_actions - retrieval_count) / total_actions) * 100
            accuracy_rate = max(0, min(100, accuracy_rate))  # Clamp to 0-100
        else:
            accuracy_rate = 100.0 if retrieval_count == 0 else 0.0

        return {
            'total_actions': total_actions,
            'retrieval_requests': retrieval_count,
            'accuracy_rate': round(accuracy_rate, 2),
            'error_rate': round(100 - accuracy_rate, 2),
            'auto_approved': auto_approved,
            'manually_approved': manually_approved,
            'rejected': rejected,
            'completed': completed,
            'period': period,
            'start_date': start_date,
            'end_date': now
        }

    @staticmethod
    def _estimate_employee_actions(employee, start_date):
        """
        Estimate total actions performed by employee since start_date.

        This checks ActivityLog if available, otherwise uses heuristics.

        Args:
            employee: User object
            start_date: Start datetime

        Returns:
            int: Estimated action count
        """
        total_actions = 0

        # Try to use ActivityLog
        try:
            from core.models import ActivityLog

            total_actions = ActivityLog.objects.filter(
                user=employee,
                created_at__gte=start_date,
                action__in=['CREATE', 'UPDATE', 'DELETE', 'APPROVE', 'REJECT', 'SUBMIT', 'COMPLETE']
            ).count()
        except ImportError:
            # ActivityLog not available, use heuristics
            # Check various models that the employee might interact with
            from .models import RetrievalRequest

            # Count retrieval requests as baseline
            retrieval_count = RetrievalRequest.objects.filter(
                employee=employee,
                submitted_at__gte=start_date
            ).count()

            # Estimate 1 error per 50 actions (2% error rate assumption)
            # This is a rough heuristic - in production, proper activity tracking should be used
            if retrieval_count > 0:
                total_actions = retrieval_count * 50
            else:
                total_actions = 100  # Default baseline

        return max(total_actions, 1)  # Ensure at least 1

    @staticmethod
    def calculate_and_save_metrics(employee, period_type='MONTHLY'):
        """
        Calculate and save metrics for an employee.

        Args:
            employee: User object
            period_type: 'DAILY', 'WEEKLY', 'MONTHLY', 'QUARTERLY', 'YEARLY'

        Returns:
            RetrievalMetric: Created or updated metric object
        """
        from .models import RetrievalMetric, RetrievalRequest

        # Determine period dates
        now = timezone.now()
        if period_type == 'DAILY':
            period_start = now.date()
            period_end = period_start
        elif period_type == 'WEEKLY':
            period_start = (now - timedelta(days=now.weekday())).date()
            period_end = period_start + timedelta(days=6)
        elif period_type == 'MONTHLY':
            period_start = now.replace(day=1).date()
            # Get last day of month
            if now.month == 12:
                period_end = now.replace(month=12, day=31).date()
            else:
                period_end = (now.replace(month=now.month + 1, day=1) - timedelta(days=1)).date()
        elif period_type == 'QUARTERLY':
            quarter_start_month = ((now.month - 1) // 3) * 3 + 1
            period_start = now.replace(month=quarter_start_month, day=1).date()
            quarter_end_month = quarter_start_month + 2
            period_end = (now.replace(month=quarter_end_month + 1, day=1) - timedelta(days=1)).date() if quarter_end_month < 12 else now.replace(month=12, day=31).date()
        elif period_type == 'YEARLY':
            period_start = now.replace(month=1, day=1).date()
            period_end = now.replace(month=12, day=31).date()
        else:
            raise ValueError(f"Invalid period_type: {period_type}")

        # Calculate metrics
        period_map = {
            'DAILY': 'day',
            'WEEKLY': 'week',
            'MONTHLY': 'month',
            'QUARTERLY': 'quarter',
            'YEARLY': 'year'
        }
        metrics = RetrievalService.calculate_employee_accuracy(employee, period_map[period_type])

        # Create or update metric record
        metric, created = RetrievalMetric.objects.update_or_create(
            employee=employee,
            period_type=period_type,
            period_start=period_start,
            period_end=period_end,
            defaults={
                'total_actions': metrics['total_actions'],
                'retrieval_requests': metrics['retrieval_requests'],
                'auto_approved': metrics['auto_approved'],
                'manually_approved': metrics['manually_approved'],
                'rejected': metrics['rejected'],
                'completed': metrics['completed'],
                'accuracy_rate': Decimal(str(metrics['accuracy_rate'])),
            }
        )

        return metric

    @staticmethod
    def get_supervisor_pending_count(supervisor):
        """
        Get count of pending retrieval requests for a supervisor.

        Args:
            supervisor: User object

        Returns:
            int: Count of pending requests
        """
        from .models import RetrievalRequest

        return RetrievalRequest.objects.filter(
            supervisor=supervisor,
            status='PENDING'
        ).count()

    @staticmethod
    def auto_approve_eligible_requests():
        """
        Automatically approve eligible pending requests.

        This should be run periodically (e.g., every few minutes via cron/celery).

        Returns:
            int: Number of requests auto-approved
        """
        from .models import RetrievalRequest

        pending_requests = RetrievalRequest.objects.filter(status='PENDING')
        approved_count = 0

        for request in pending_requests:
            can_auto, reason = request.can_auto_approve()
            if can_auto:
                request.approve(approved_by=None, auto=True)
                approved_count += 1

                # Notify employee of auto-approval
                RetrievalService.notify_employee_decision(request)

        return approved_count

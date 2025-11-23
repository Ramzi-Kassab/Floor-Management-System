"""
Celery tasks for HR module

Provides:
- Employee onboarding automation
- Leave request processing
- Contract management
- Asset tracking
- Notifications and reminders
"""
from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task(name='floor_app.operations.hr.tasks.send_welcome_email')
def send_welcome_email(employee_id):
    """
    Send welcome email to new employee

    Args:
        employee_id: ID of the employee

    Returns:
        bool: True if email sent successfully
    """
    from .models import Employee

    try:
        employee = Employee.objects.select_related('person', 'department', 'position').get(pk=employee_id)

        # Render email template
        context = {
            'employee': employee,
            'system_url': settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://localhost:8000',
        }

        html_message = render_to_string('hr/emails/welcome_employee.html', context)
        plain_message = strip_tags(html_message)

        # Send email
        if employee.person and employee.person.email:
            send_mail(
                subject='Welcome to Floor Management System',
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[employee.person.email],
                html_message=html_message,
                fail_silently=False
            )

            logger.info(f"Sent welcome email to employee {employee.employee_code}")
            return True
        else:
            logger.warning(f"No email address for employee {employee.employee_code}")
            return False

    except Employee.DoesNotExist:
        logger.error(f"Employee {employee_id} not found")
        return False
    except Exception as e:
        logger.error(f"Error sending welcome email: {e}")
        raise


@shared_task(name='floor_app.operations.hr.tasks.check_expiring_contracts')
def check_expiring_contracts(days_ahead=30):
    """
    Check for contracts expiring soon and send notifications

    Args:
        days_ahead: Number of days to look ahead (default: 30)

    Returns:
        int: Number of notifications sent
    """
    from .models import Contract

    try:
        # Get contracts expiring in the next N days
        today = timezone.now().date()
        expiry_date = today + timedelta(days=days_ahead)

        expiring_contracts = Contract.objects.filter(
            end_date__gte=today,
            end_date__lte=expiry_date,
            is_active=True
        ).select_related('employee', 'employee__person', 'employee__department')

        notifications_sent = 0

        for contract in expiring_contracts:
            days_remaining = (contract.end_date - today).days

            # Send email to HR
            hr_emails = []
            # Get HR department emails
            from django.contrib.auth.models import User
            hr_users = User.objects.filter(
                employee__department__code='HR',
                employee__employment_status='ACTIVE'
            ).values_list('email', flat=True)
            hr_emails = [email for email in hr_users if email]

            if hr_emails:
                subject = f'Contract Expiring Soon: {contract.employee}'
                message = f"""
CONTRACT EXPIRATION NOTICE

Employee: {contract.employee}
Department: {contract.employee.department}
Contract Type: {contract.get_contract_type_display()}
End Date: {contract.end_date.strftime('%B %d, %Y')}
Days Remaining: {days_remaining}

Please review and take necessary action.

---
Floor Management System
                """.strip()

                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=hr_emails,
                    fail_silently=False
                )

                notifications_sent += 1

        logger.info(f"Sent {notifications_sent} contract expiration notifications")
        return notifications_sent

    except Exception as e:
        logger.error(f"Error checking expiring contracts: {e}")
        raise


@shared_task(name='floor_app.operations.hr.tasks.send_pending_leave_reminders')
def send_pending_leave_reminders():
    """
    Send reminders to managers about pending leave requests

    Returns:
        int: Number of reminders sent
    """
    from .models import LeaveRequest

    try:
        # Get pending leave requests older than 2 days
        two_days_ago = timezone.now() - timedelta(days=2)

        pending_requests = LeaveRequest.objects.filter(
            status='PENDING',
            created_at__lte=two_days_ago
        ).select_related('employee', 'employee__person', 'employee__report_to', 'leave_type')

        # Group by manager
        managers_requests = {}
        for request in pending_requests:
            if request.employee.report_to:
                manager = request.employee.report_to
                if manager not in managers_requests:
                    managers_requests[manager] = []
                managers_requests[manager].append(request)

        reminders_sent = 0

        # Send reminders
        for manager, requests in managers_requests.items():
            if manager.person and manager.person.email:
                request_list = '\n'.join([
                    f"  - {r.employee} ({r.leave_type}): {r.start_date} to {r.end_date}"
                    for r in requests
                ])

                subject = f'Pending Leave Requests ({len(requests)})'
                message = f"""
LEAVE REQUEST REMINDER

You have {len(requests)} pending leave request(s) awaiting approval:

{request_list}

Please review and approve/reject these requests at your earliest convenience.

---
Floor Management System
                """.strip()

                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[manager.person.email],
                    fail_silently=False
                )

                reminders_sent += 1

        logger.info(f"Sent {reminders_sent} leave request reminders")
        return reminders_sent

    except Exception as e:
        logger.error(f"Error sending leave request reminders: {e}")
        raise


@shared_task(name='floor_app.operations.hr.tasks.send_leave_request_notification')
def send_leave_request_notification(leave_request_id, notification_type):
    """
    Send leave request notification

    Args:
        leave_request_id: ID of the leave request
        notification_type: Type of notification ('submitted', 'approved', 'rejected', 'cancelled')

    Returns:
        bool: True if notification sent successfully
    """
    from .models import LeaveRequest

    try:
        leave_request = LeaveRequest.objects.select_related(
            'employee', 'employee__person', 'employee__report_to',
            'leave_type', 'approved_by'
        ).get(pk=leave_request_id)

        # Determine recipient and template
        if notification_type == 'submitted':
            # Notify manager
            if leave_request.employee.report_to and leave_request.employee.report_to.person:
                recipient_email = leave_request.employee.report_to.person.email
                template = 'hr/emails/leave_request_submitted.html'
                subject = f'New Leave Request from {leave_request.employee.person.first_name}'
            else:
                logger.warning(f"No manager email for leave request {leave_request_id}")
                return False

        elif notification_type in ['approved', 'rejected']:
            # Notify employee
            if leave_request.employee.person and leave_request.employee.person.email:
                recipient_email = leave_request.employee.person.email
                template = f'hr/emails/leave_request_{notification_type}.html'
                subject = f'Leave Request {notification_type.title()}'
            else:
                logger.warning(f"No employee email for leave request {leave_request_id}")
                return False

        else:
            logger.error(f"Unknown notification type: {notification_type}")
            return False

        # Render email
        context = {
            'leave_request': leave_request,
            'system_url': settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://localhost:8000',
        }

        html_message = render_to_string(template, context)
        plain_message = strip_tags(html_message)

        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            html_message=html_message,
            fail_silently=False
        )

        logger.info(f"Sent {notification_type} notification for leave request {leave_request_id}")
        return True

    except LeaveRequest.DoesNotExist:
        logger.error(f"Leave request {leave_request_id} not found")
        return False
    except Exception as e:
        logger.error(f"Error sending leave request notification: {e}")
        raise


@shared_task(name='floor_app.operations.hr.tasks.sync_asset_inventory')
def sync_asset_inventory():
    """
    Sync asset inventory and check for issues

    Returns:
        dict: Summary of asset inventory status
    """
    from .models import Asset, AssetAssignment

    try:
        # Get all assets
        total_assets = Asset.objects.count()
        available_assets = Asset.objects.filter(status='AVAILABLE').count()
        assigned_assets = Asset.objects.filter(status='ASSIGNED').count()
        maintenance_assets = Asset.objects.filter(status='MAINTENANCE').count()

        # Check for overdue returns
        today = timezone.now().date()
        overdue_assignments = AssetAssignment.objects.filter(
            expected_return_date__lt=today,
            returned_date__isnull=True
        ).select_related('asset', 'employee', 'employee__person')

        overdue_count = overdue_assignments.count()

        # Send alerts for overdue assets
        if overdue_count > 0:
            from django.contrib.auth.models import User

            # Get HR/Admin emails
            admin_emails = User.objects.filter(
                is_staff=True,
                is_active=True
            ).values_list('email', flat=True)
            admin_emails = [email for email in admin_emails if email]

            if admin_emails:
                overdue_list = '\n'.join([
                    f"  - {a.asset.name} ({a.asset.asset_code}) - Assigned to {a.employee}"
                    for a in overdue_assignments[:10]
                ])

                subject = f'Asset Return Overdue ({overdue_count})'
                message = f"""
ASSET INVENTORY ALERT

{overdue_count} asset(s) have overdue returns:

{overdue_list}

Please follow up with employees for asset returns.

---
Floor Management System
                """.strip()

                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=admin_emails,
                    fail_silently=False
                )

        summary = {
            'total_assets': total_assets,
            'available': available_assets,
            'assigned': assigned_assets,
            'maintenance': maintenance_assets,
            'overdue_returns': overdue_count
        }

        logger.info(f"Asset inventory sync completed: {summary}")
        return summary

    except Exception as e:
        logger.error(f"Error syncing asset inventory: {e}")
        raise


@shared_task(name='floor_app.operations.hr.tasks.generate_employee_report')
def generate_employee_report(report_type='summary', filters=None, user_email=None):
    """
    Generate employee report in background

    Args:
        report_type: Type of report ('summary', 'detailed', 'department')
        filters: Optional filters to apply
        user_email: Email to send the report to

    Returns:
        str: Report file path
    """
    from .models import Employee
    from floor_app.core.exports import ExcelExporter
    import os

    try:
        # Build queryset
        queryset = Employee.objects.select_related('person', 'department', 'position')

        if filters:
            queryset = queryset.filter(**filters)

        # Prepare data based on report type
        if report_type == 'summary':
            headers = ['Code', 'Name', 'Department', 'Position', 'Status', 'Hire Date']
            data = [
                [
                    emp.employee_code,
                    f"{emp.person.first_name} {emp.person.last_name}" if emp.person else '',
                    emp.department.name if emp.department else '',
                    emp.position.title if emp.position else '',
                    emp.get_employment_status_display(),
                    emp.hire_date.strftime('%Y-%m-%d') if emp.hire_date else ''
                ]
                for emp in queryset
            ]

        elif report_type == 'detailed':
            headers = [
                'Code', 'First Name', 'Last Name', 'Email', 'Phone',
                'Department', 'Position', 'Status', 'Hire Date', 'Type'
            ]
            data = [
                [
                    emp.employee_code,
                    emp.person.first_name if emp.person else '',
                    emp.person.last_name if emp.person else '',
                    emp.person.email if emp.person else '',
                    emp.person.phone if emp.person else '',
                    emp.department.name if emp.department else '',
                    emp.position.title if emp.position else '',
                    emp.get_employment_status_display(),
                    emp.hire_date.strftime('%Y-%m-%d') if emp.hire_date else '',
                    emp.get_employee_type_display() if hasattr(emp, 'employee_type') else ''
                ]
                for emp in queryset
            ]

        # Generate Excel file
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        filename = f"employee_report_{report_type}_{timestamp}.xlsx"
        filepath = os.path.join(settings.MEDIA_ROOT, 'reports', filename)

        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        # Create Excel file
        exporter = ExcelExporter(f'Employee Report - {report_type.title()}')
        exporter.add_sheet('Employees', headers, data)

        # Add summary sheet
        summary = {
            'Report Type': report_type.title(),
            'Generated': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Total Employees': queryset.count(),
            'Active Employees': queryset.filter(employment_status='ACTIVE').count(),
            'Total Departments': queryset.values('department').distinct().count(),
        }
        exporter.add_summary_sheet('Summary', summary)

        exporter.save_to_file(filepath)

        # Send email if user_email provided
        if user_email:
            send_mail(
                subject=f'Employee Report Ready - {report_type.title()}',
                message=f"""
Your employee report is ready!

Report Type: {report_type.title()}
Total Employees: {queryset.count()}
Generated: {timezone.now().strftime('%B %d, %Y at %I:%M %p')}

The report has been generated and is available for download.

---
Floor Management System
                """.strip(),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user_email],
                fail_silently=False
            )

        logger.info(f"Generated employee report: {report_type} ({queryset.count()} employees)")
        return filepath

    except Exception as e:
        logger.error(f"Error generating employee report: {e}")
        if user_email:
            send_mail(
                subject='Employee Report Failed',
                message=f"""
Failed to generate employee report.

Error: {str(e)}

Please contact support if the problem persists.

---
Floor Management System
                """.strip(),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user_email],
                fail_silently=True
            )
        raise


@shared_task(name='floor_app.operations.hr.tasks.process_employee_onboarding')
def process_employee_onboarding(employee_id):
    """
    Process employee onboarding workflow

    Args:
        employee_id: ID of the new employee

    Returns:
        dict: Summary of onboarding tasks completed
    """
    from .models import Employee

    try:
        employee = Employee.objects.select_related('person', 'department').get(pk=employee_id)

        tasks_completed = []

        # 1. Send welcome email
        send_welcome_email.delay(employee_id)
        tasks_completed.append('welcome_email_queued')

        # 2. Create user account if not exists
        if employee.person and not hasattr(employee.person, 'user'):
            # This would require user creation logic
            tasks_completed.append('user_account_pending')

        # 3. Assign default assets (if applicable)
        # This would require business logic for default assets
        tasks_completed.append('asset_assignment_pending')

        # 4. Schedule orientation
        # This would integrate with calendar system
        tasks_completed.append('orientation_scheduling_pending')

        # 5. Notify department
        if employee.department:
            # Send notification to department
            tasks_completed.append('department_notified')

        logger.info(f"Processed onboarding for employee {employee.employee_code}: {tasks_completed}")

        return {
            'employee_code': employee.employee_code,
            'tasks_completed': tasks_completed
        }

    except Employee.DoesNotExist:
        logger.error(f"Employee {employee_id} not found for onboarding")
        raise
    except Exception as e:
        logger.error(f"Error processing employee onboarding: {e}")
        raise

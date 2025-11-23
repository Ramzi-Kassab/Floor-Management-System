"""
HR Signals Module

Handles automatic User creation, RBAC group management, and audit logging.
This module provides:
- Automatic Django User creation when an Employee is created
- Automatic group assignment based on Position
- Audit logging for all security-relevant HR changes
"""

import json
import logging
import secrets
import string
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils.text import slugify

from .models import HREmployee, HREmail, HRAuditLog, LeaveRequest
from django.contrib.contenttypes.models import ContentType

logger = logging.getLogger(__name__)
User = get_user_model()


class EmployeeUserService:
    """
    Service layer for managing Employee <-> User relationship and RBAC.
    Provides centralized logic for user creation, group management, and auditing.
    """

    @staticmethod
    def generate_username(employee):
        """
        Generate a unique username from employee's person data.
        Format: first_name.last_name or first_name.last_name.N
        """
        person = employee.person
        base_username = slugify(
            f"{person.first_name_en}.{person.last_name_en}"
        ).replace('-', '_').lower()

        # Ensure username is valid (max 150 chars for Django User)
        base_username = base_username[:140]

        username = base_username
        counter = 1

        # Check for uniqueness and add suffix if needed
        while User.objects.filter(username=username).exists():
            username = f"{base_username}_{counter}"
            counter += 1
            if counter > 1000:  # Safety limit
                raise ValueError(f"Unable to generate unique username for {person.first_name_en} {person.last_name_en}")

        return username

    @staticmethod
    def get_primary_email(employee):
        """Get the primary business email for the employee."""
        person = employee.person

        # First try primary business email
        primary_email = HREmail.objects.filter(
            person=person,
            is_deleted=False,
            is_primary_hint=True,
            kind='BUSINESS'
        ).first()

        if primary_email:
            return primary_email.email

        # Fall back to any primary email
        primary_email = HREmail.objects.filter(
            person=person,
            is_deleted=False,
            is_primary_hint=True
        ).first()

        if primary_email:
            return primary_email.email

        # Fall back to any business email
        business_email = HREmail.objects.filter(
            person=person,
            is_deleted=False,
            kind='BUSINESS'
        ).first()

        if business_email:
            return business_email.email

        # Fall back to any email
        any_email = HREmail.objects.filter(
            person=person,
            is_deleted=False
        ).first()

        return any_email.email if any_email else None

    @staticmethod
    def generate_secure_password():
        """Generate a secure random password."""
        alphabet = string.ascii_letters + string.digits + string.punctuation
        # Generate 16-character password with at least one of each character type
        password = [
            secrets.choice(string.ascii_lowercase),
            secrets.choice(string.ascii_uppercase),
            secrets.choice(string.digits),
            secrets.choice(string.punctuation),
        ]
        password.extend(secrets.choice(alphabet) for _ in range(12))
        secrets.SystemRandom().shuffle(password)
        return ''.join(password)

    @classmethod
    def create_user_for_employee(cls, employee, performed_by=None):
        """
        Create a Django User account for an Employee.

        Returns tuple: (user, password, was_created)
        - user: The User object (created or linked)
        - password: The generated password (only if created)
        - was_created: Boolean indicating if user was newly created
        """
        if employee.user:
            logger.info(f"Employee {employee.employee_no} already has user {employee.user.username}")
            return employee.user, None, False

        person = employee.person
        email = cls.get_primary_email(employee)

        # Check if user with this email already exists
        if email and User.objects.filter(email=email).exists():
            existing_user = User.objects.get(email=email)

            # Check if this user is already linked to another employee
            if hasattr(existing_user, 'hr_employee') and existing_user.hr_employee != employee:
                logger.warning(
                    f"Email {email} already assigned to user {existing_user.username} "
                    f"linked to employee {existing_user.hr_employee.employee_no}"
                )
                # Generate unique email or leave as None
                email = None
            else:
                # Link existing user to this employee
                employee.user = existing_user
                employee.save(update_fields=['user'])

                cls.log_action(
                    action='USER_LINKED',
                    employee=employee,
                    affected_user=existing_user,
                    performed_by=performed_by,
                    details=json.dumps({
                        'reason': 'Existing user found with matching email',
                        'email': email,
                    })
                )

                return existing_user, None, False

        # Create new user
        username = cls.generate_username(employee)
        password = cls.generate_secure_password()

        user = User.objects.create_user(
            username=username,
            email=email or '',
            password=password,
            first_name=person.first_name_en[:30],  # Django User first_name max_length=30
            last_name=person.last_name_en[:150],   # Django User last_name max_length=150
            is_active=True,
            is_staff=False,
            is_superuser=False,
        )

        # Link user to employee
        employee.user = user
        employee.save(update_fields=['user'])

        # Log the action
        cls.log_action(
            action='USER_CREATED',
            employee=employee,
            affected_user=user,
            performed_by=performed_by,
            details=json.dumps({
                'username': username,
                'email': email,
                'requires_password_reset': True,
            })
        )

        logger.info(f"Created user {username} for employee {employee.employee_no}")

        return user, password, True

    @classmethod
    def sync_user_groups(cls, employee, performed_by=None):
        """
        Synchronize User's groups based on Employee's Position.
        Removes outdated groups and adds new ones.
        """
        if not employee.user:
            logger.warning(f"Employee {employee.employee_no} has no linked user")
            return

        user = employee.user
        current_groups = set(user.groups.all())
        expected_groups = set()

        # Get group from position
        if employee.position and employee.position.auth_group:
            expected_groups.add(employee.position.auth_group)

        # Add additional permission-based logic if needed
        # e.g., Department-based groups, Level-based groups

        # Determine changes
        groups_to_add = expected_groups - current_groups
        groups_to_remove = current_groups - expected_groups

        # Apply changes
        for group in groups_to_add:
            user.groups.add(group)
            cls.log_action(
                action='GROUP_ADDED',
                employee=employee,
                affected_user=user,
                performed_by=performed_by,
                details=json.dumps({
                    'group_name': group.name,
                    'reason': f'Position: {employee.position.name}' if employee.position else 'Unknown',
                })
            )
            logger.info(f"Added user {user.username} to group {group.name}")

        for group in groups_to_remove:
            user.groups.remove(group)
            cls.log_action(
                action='GROUP_REMOVED',
                employee=employee,
                affected_user=user,
                performed_by=performed_by,
                details=json.dumps({
                    'group_name': group.name,
                    'reason': 'Position changed or removed',
                })
            )
            logger.info(f"Removed user {user.username} from group {group.name}")

        # Sync additional permissions from position
        if employee.position and employee.position.permission_codenames:
            codenames = [c.strip() for c in employee.position.permission_codenames.split(',') if c.strip()]
            for codename in codenames:
                try:
                    perm = Permission.objects.get(codename=codename)
                    if perm not in user.user_permissions.all():
                        user.user_permissions.add(perm)
                        cls.log_action(
                            action='PERMISSION_ADDED',
                            employee=employee,
                            affected_user=user,
                            performed_by=performed_by,
                            details=json.dumps({
                                'permission': codename,
                                'source': 'Position permission_codenames',
                            })
                        )
                except Permission.DoesNotExist:
                    logger.warning(f"Permission {codename} not found")

    @classmethod
    def deactivate_user(cls, employee, performed_by=None):
        """Deactivate the User account when Employee is terminated or deleted."""
        if not employee.user:
            return

        user = employee.user
        user.is_active = False
        user.save(update_fields=['is_active'])

        cls.log_action(
            action='USER_DEACTIVATED',
            employee=employee,
            affected_user=user,
            performed_by=performed_by,
            details=json.dumps({
                'reason': f'Employee status: {employee.status}',
            })
        )

        logger.info(f"Deactivated user {user.username} for employee {employee.employee_no}")

    @staticmethod
    def log_action(action, employee=None, affected_user=None, performed_by=None, details='', ip_address=None, user_agent=''):
        """Create an audit log entry."""
        try:
            HRAuditLog.objects.create(
                action=action,
                employee=employee,
                affected_user=affected_user,
                performed_by=performed_by,
                details=details,
                ip_address=ip_address,
                user_agent=user_agent,
            )
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")


# Track position changes for group sync
_employee_previous_position = {}


@receiver(pre_save, sender=HREmployee)
def track_position_change(sender, instance, **kwargs):
    """Track position before save to detect changes."""
    if instance.pk:
        try:
            old_instance = HREmployee.objects.get(pk=instance.pk)
            _employee_previous_position[instance.pk] = old_instance.position_id
        except HREmployee.DoesNotExist:
            pass


@receiver(post_save, sender=HREmployee)
def handle_employee_save(sender, instance, created, **kwargs):
    """
    Handle Employee creation or update:
    - Create User account if new employee
    - Sync groups if position changed
    """
    try:
        if created:
            # New employee - create user account
            with transaction.atomic():
                user, password, was_created = EmployeeUserService.create_user_for_employee(instance)

                if was_created and password:
                    # Store password temporarily for notification
                    # In production, send via email or force reset on first login
                    logger.info(
                        f"Generated password for {user.username}: {password[:4]}... "
                        f"(Employee should reset on first login)"
                    )

                    # Mark that password reset is required
                    EmployeeUserService.log_action(
                        action='PASSWORD_RESET',
                        employee=instance,
                        affected_user=user,
                        details=json.dumps({
                            'reason': 'Initial password generated, reset required',
                            'temp_password_hint': password[:4] + '...',
                        })
                    )

                # Sync groups based on position
                EmployeeUserService.sync_user_groups(instance)

        else:
            # Existing employee - check for position changes
            old_position_id = _employee_previous_position.pop(instance.pk, None)
            current_position_id = instance.position_id

            if old_position_id != current_position_id:
                # Position changed - sync groups
                EmployeeUserService.log_action(
                    action='POSITION_CHANGED',
                    employee=instance,
                    affected_user=instance.user,
                    details=json.dumps({
                        'old_position_id': old_position_id,
                        'new_position_id': current_position_id,
                        'new_position_name': instance.position.name if instance.position else None,
                    })
                )

                EmployeeUserService.sync_user_groups(instance)

            # Check for termination
            if instance.status in ['TERMINATED', 'SUSPENDED'] and instance.user and instance.user.is_active:
                EmployeeUserService.deactivate_user(instance)

    except Exception as e:
        logger.error(f"Error handling employee save signal: {e}", exc_info=True)
        # Don't raise - allow the save to complete but log the error


# ============================================================================
# LEAVE REQUEST NOTIFICATION SIGNALS
# ============================================================================

@receiver(pre_save, sender=LeaveRequest)
def track_leave_status_change(sender, instance, **kwargs):
    """
    Track status changes in leave requests to avoid duplicate notifications.
    We store the previous status on the instance for comparison in post_save.
    """
    if instance.pk:
        try:
            previous = LeaveRequest.objects.get(pk=instance.pk)
            instance._previous_status = previous.status
        except LeaveRequest.DoesNotExist:
            instance._previous_status = None
    else:
        instance._previous_status = None


@receiver(post_save, sender=LeaveRequest)
def create_leave_request_notifications(sender, instance, created, **kwargs):
    """
    Create notifications when leave requests are created or status changes.

    - When created: Notify manager about new leave request
    - When approved: Notify employee that request was approved
    - When rejected: Notify employee that request was rejected
    """
    try:
        # Import here to avoid circular import
        from floor_app.operations.notifications.models import Notification

        content_type = ContentType.objects.get_for_model(LeaveRequest)

        if created:
            # New leave request - notify the manager
            if instance.employee.report_to and instance.employee.report_to.user:
                Notification.objects.create(
                    recipient=instance.employee.report_to.user,
                    notification_type='leave_request',
                    title='New Leave Request',
                    message=f'{instance.employee.person.full_name} has submitted a leave request for {instance.leave_type.name} from {instance.start_date} to {instance.end_date}.',
                    content_type=content_type,
                    object_id=instance.pk,
                    priority='normal'
                )
                logger.info(f"Created leave request notification for manager of {instance.employee.employee_no}")
        else:
            # Check if status changed
            if hasattr(instance, '_previous_status'):
                previous_status = instance._previous_status
                current_status = instance.status

                # Only create notification if status changed
                if previous_status != current_status:
                    if current_status == 'approved' and instance.employee.user:
                        # Avoid duplicate notifications
                        existing = Notification.objects.filter(
                            recipient=instance.employee.user,
                            notification_type='leave_approved',
                            object_id=instance.pk,
                            content_type=content_type
                        ).exists()

                        if not existing:
                            Notification.objects.create(
                                recipient=instance.employee.user,
                                notification_type='leave_approved',
                                title='Leave Request Approved',
                                message=f'Your leave request for {instance.leave_type.name} from {instance.start_date} to {instance.end_date} has been approved.',
                                content_type=content_type,
                                object_id=instance.pk,
                                priority='normal'
                            )
                            logger.info(f"Created leave approval notification for {instance.employee.employee_no}")

                    elif current_status == 'rejected' and instance.employee.user:
                        # Avoid duplicate notifications
                        existing = Notification.objects.filter(
                            recipient=instance.employee.user,
                            notification_type='leave_rejected',
                            object_id=instance.pk,
                            content_type=content_type
                        ).exists()

                        if not existing:
                            reject_reason = f' Reason: {instance.rejection_reason}' if instance.rejection_reason else ''
                            Notification.objects.create(
                                recipient=instance.employee.user,
                                notification_type='leave_rejected',
                                title='Leave Request Rejected',
                                message=f'Your leave request for {instance.leave_type.name} from {instance.start_date} to {instance.end_date} has been rejected.{reject_reason}',
                                content_type=content_type,
                                object_id=instance.pk,
                                priority='high'
                            )
                            logger.info(f"Created leave rejection notification for {instance.employee.employee_no}")

    except Exception as e:
        logger.error(f"Error creating leave request notification: {e}", exc_info=True)
        # Don't raise - allow the save to complete but log the error

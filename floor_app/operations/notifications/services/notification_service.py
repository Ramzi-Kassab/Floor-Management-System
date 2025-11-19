"""
Notification Service

Main orchestration service for sending notifications across all channels.

Handles:
- Template rendering
- User preference checking
- Multi-channel delivery
- Retry logic
- Approval notification integration
"""

from typing import List, Dict, Optional, Any
from django.utils import timezone
from django.template import Template, Context
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Main notification orchestration service.

    Coordinates notification delivery across multiple channels.
    """

    @classmethod
    def send(
        cls,
        recipient_user=None,
        recipient_employee=None,
        title: str = '',
        message: str = '',
        priority: str = 'NORMAL',
        channels: List[str] = None,
        template=None,
        template_variables: Dict = None,
        related_object=None,
        action_url: str = '',
        action_label: str = '',
        expires_at=None
    ):
        """
        Send notification to a user/employee.

        Args:
            recipient_user: User to send to
            recipient_employee: Employee to send to
            title: Notification title
            message: Notification message
            priority: Priority level (LOW, NORMAL, HIGH, URGENT)
            channels: List of channels to send on (e.g., ['WHATSAPP', 'EMAIL'])
            template: NotificationTemplate instance
            template_variables: Variables for template rendering
            related_object: Related object (for GenericForeignKey)
            action_url: URL for action button
            action_label: Label for action button
            expires_at: Expiry datetime

        Returns:
            Notification instance

        Example:
            NotificationService.send(
                recipient_employee=employee,
                title='Approval Required',
                message='Please approve BOM modification request #123',
                priority='HIGH',
                channels=['WHATSAPP', 'EMAIL', 'PUSH'],
                action_url='/approvals/123',
                action_label='View Request'
            )
        """
        from floor_app.operations.notifications.models import Notification
        from django.contrib.contenttypes.models import ContentType

        # Render template if provided
        if template:
            rendered = cls._render_template(template, template_variables or {})
            title = rendered.get('title', title)
            message = rendered.get('message', message)

        # Determine channels to use
        if channels is None:
            channels = cls._get_user_preferred_channels(recipient_user, recipient_employee)

        # Create notification
        notification = Notification.objects.create(
            recipient_user=recipient_user,
            recipient_employee=recipient_employee,
            title=title,
            message=message,
            priority=priority,
            template=template,
            template_variables=template_variables or {},
            channels_to_send=channels,
            action_url=action_url,
            action_label=action_label,
            expires_at=expires_at
        )

        # Set related object if provided
        if related_object:
            notification.content_type = ContentType.objects.get_for_model(related_object)
            notification.object_id = related_object.pk
            notification.save()

        # Send on all channels asynchronously
        cls._send_on_channels(notification)

        return notification

    @classmethod
    def send_bulk(
        cls,
        recipients: List[Dict],
        title: str,
        message: str,
        priority: str = 'NORMAL',
        channels: List[str] = None
    ) -> List:
        """
        Send same notification to multiple recipients.

        Args:
            recipients: List of dicts with 'user' or 'employee'
            title: Notification title
            message: Notification message
            priority: Priority level
            channels: Channels to use

        Returns:
            List of Notification instances

        Example:
            recipients = [
                {'employee': employee1},
                {'employee': employee2},
                {'user': user3}
            ]
            NotificationService.send_bulk(
                recipients=recipients,
                title='System Maintenance',
                message='System will be down for maintenance tomorrow',
                priority='HIGH',
                channels=['EMAIL', 'IN_APP']
            )
        """
        notifications = []

        for recipient in recipients:
            user = recipient.get('user')
            employee = recipient.get('employee')

            notification = cls.send(
                recipient_user=user,
                recipient_employee=employee,
                title=title,
                message=message,
                priority=priority,
                channels=channels
            )
            notifications.append(notification)

        return notifications

    @classmethod
    def send_announcement(cls, announcement):
        """
        Send announcement as notifications to targeted users.

        Args:
            announcement: Announcement instance

        Returns:
            List of Notification instances
        """
        if not announcement.send_notification:
            return []

        # Get target users
        target_users = announcement.get_target_users()

        # Send to all targets
        notifications = []
        for user in target_users:
            notification = cls.send(
                recipient_user=user,
                title=announcement.title,
                message=announcement.message,
                priority=announcement.priority,
                channels=announcement.notification_channels,
                related_object=announcement,
                action_url=announcement.action_url,
                action_label=announcement.action_label,
                expires_at=announcement.expires_at
            )
            notifications.append(notification)

        return notifications

    @classmethod
    def send_approval_request(cls, approval_request, approver):
        """
        Send approval request notification.

        Args:
            approval_request: ApprovalRequest instance
            approver: User who needs to approve

        Returns:
            Notification instance
        """
        from floor_app.operations.notifications.models import NotificationTemplate

        # Get template
        template = NotificationTemplate.objects.filter(
            template_type='APPROVAL_REQUEST',
            is_active=True
        ).first()

        # Template variables
        variables = {
            'approver_name': approver.get_full_name(),
            'request_title': approval_request.title,
            'requester_name': approval_request.requester.get_full_name() if approval_request.requester else 'Unknown',
            'priority': approval_request.get_priority_display(),
            'due_date': approval_request.due_at.strftime('%Y-%m-%d') if approval_request.due_at else 'N/A',
        }

        return cls.send(
            recipient_user=approver,
            title=f'Approval Required: {approval_request.title}',
            message=f'{approval_request.requester.get_full_name()} is requesting your approval for: {approval_request.title}',
            priority=approval_request.priority,
            template=template,
            template_variables=variables,
            related_object=approval_request,
            action_url=f'/approvals/{approval_request.id}/',
            action_label='Review Request'
        )

    @classmethod
    def send_approval_approved(cls, approval_request):
        """
        Send notification that approval was approved.

        Args:
            approval_request: ApprovalRequest instance

        Returns:
            Notification instance
        """
        from floor_app.operations.notifications.models import NotificationTemplate

        template = NotificationTemplate.objects.filter(
            template_type='APPROVAL_APPROVED',
            is_active=True
        ).first()

        variables = {
            'requester_name': approval_request.requester.get_full_name() if approval_request.requester else 'Unknown',
            'request_title': approval_request.title,
        }

        return cls.send(
            recipient_user=approval_request.requester,
            title=f'Approved: {approval_request.title}',
            message=f'Your request "{approval_request.title}" has been approved.',
            priority='NORMAL',
            template=template,
            template_variables=variables,
            related_object=approval_request,
            action_url=f'/approvals/{approval_request.id}/',
            action_label='View Details'
        )

    @classmethod
    def send_approval_rejected(cls, approval_request, rejected_by, reason):
        """
        Send notification that approval was rejected.

        Args:
            approval_request: ApprovalRequest instance
            rejected_by: User who rejected
            reason: Rejection reason

        Returns:
            Notification instance
        """
        from floor_app.operations.notifications.models import NotificationTemplate

        template = NotificationTemplate.objects.filter(
            template_type='APPROVAL_REJECTED',
            is_active=True
        ).first()

        variables = {
            'requester_name': approval_request.requester.get_full_name() if approval_request.requester else 'Unknown',
            'request_title': approval_request.title,
            'rejected_by_name': rejected_by.get_full_name(),
            'rejection_reason': reason,
        }

        return cls.send(
            recipient_user=approval_request.requester,
            title=f'Rejected: {approval_request.title}',
            message=f'Your request "{approval_request.title}" was rejected by {rejected_by.get_full_name()}. Reason: {reason}',
            priority='HIGH',
            template=template,
            template_variables=variables,
            related_object=approval_request,
            action_url=f'/approvals/{approval_request.id}/',
            action_label='View Details'
        )

    @classmethod
    def _render_template(cls, template, variables: Dict) -> Dict:
        """
        Render notification template with variables.

        Args:
            template: NotificationTemplate instance
            variables: Template variables

        Returns:
            Dict with rendered content per channel
        """
        from django.template import Template, Context

        rendered = {}

        # Render title
        if template.in_app_title:
            title_template = Template(template.in_app_title)
            rendered['title'] = title_template.render(Context(variables))

        # Render message
        if template.in_app_message:
            message_template = Template(template.in_app_message)
            rendered['message'] = message_template.render(Context(variables))

        # Render email
        if template.email_subject:
            subject_template = Template(template.email_subject)
            rendered['email_subject'] = subject_template.render(Context(variables))

        if template.email_template:
            email_template = Template(template.email_template)
            rendered['email_body'] = email_template.render(Context(variables))

        # Render WhatsApp
        if template.whatsapp_template:
            whatsapp_template = Template(template.whatsapp_template)
            rendered['whatsapp_message'] = whatsapp_template.render(Context(variables))

        # Render SMS
        if template.sms_template:
            sms_template = Template(template.sms_template)
            rendered['sms_message'] = sms_template.render(Context(variables))

        # Render Push
        if template.push_title:
            push_title_template = Template(template.push_title)
            rendered['push_title'] = push_title_template.render(Context(variables))

        if template.push_body:
            push_body_template = Template(template.push_body)
            rendered['push_body'] = push_body_template.render(Context(variables))

        return rendered

    @classmethod
    def _get_user_preferred_channels(cls, user, employee) -> List[str]:
        """
        Get user's preferred notification channels.

        Args:
            user: User instance
            employee: Employee instance

        Returns:
            List of enabled channels
        """
        from floor_app.operations.notifications.models import NotificationPreference

        # Try to get user preference
        if user:
            try:
                pref = NotificationPreference.objects.get(user=user)
                channels = []
                if pref.enable_whatsapp:
                    channels.append('WHATSAPP')
                if pref.enable_email:
                    channels.append('EMAIL')
                if pref.enable_sms:
                    channels.append('SMS')
                if pref.enable_push:
                    channels.append('PUSH')
                if pref.enable_in_app:
                    channels.append('IN_APP')
                if pref.enable_telegram:
                    channels.append('TELEGRAM')
                return channels
            except NotificationPreference.DoesNotExist:
                pass

        # Default channels
        return ['EMAIL', 'IN_APP']

    @classmethod
    def _send_on_channels(cls, notification):
        """
        Send notification on all specified channels.

        Args:
            notification: Notification instance
        """
        from floor_app.operations.notifications.models import NotificationChannel, NotificationDelivery

        for channel_type in notification.channels_to_send:
            # Get channel configuration
            try:
                channel = NotificationChannel.objects.get(
                    channel_type=channel_type,
                    is_enabled=True
                )
            except NotificationChannel.DoesNotExist:
                logger.warning(f"Channel {channel_type} not found or disabled")
                continue

            # Create delivery record
            delivery = NotificationDelivery.objects.create(
                notification=notification,
                channel=channel,
                status='PENDING'
            )

            # Send on channel
            try:
                if channel_type == 'WHATSAPP':
                    cls._send_whatsapp(notification, delivery)
                elif channel_type == 'EMAIL':
                    cls._send_email(notification, delivery)
                elif channel_type == 'SMS':
                    cls._send_sms(notification, delivery)
                elif channel_type == 'PUSH':
                    cls._send_push(notification, delivery)
                elif channel_type == 'IN_APP':
                    # In-app notifications are just the Notification record itself
                    delivery.status = 'DELIVERED'
                    delivery.delivered_at = timezone.now()
                    delivery.save()
                elif channel_type == 'TELEGRAM':
                    cls._send_telegram(notification, delivery)

            except Exception as e:
                logger.error(f"Error sending notification on {channel_type}: {str(e)}")
                delivery.status = 'FAILED'
                delivery.failure_reason = str(e)
                delivery.failed_at = timezone.now()
                delivery.save()

    @classmethod
    def _send_whatsapp(cls, notification, delivery):
        """Send WhatsApp notification."""
        from floor_app.operations.notifications.services.whatsapp_service import WhatsAppService

        # Get recipient WhatsApp number
        phone_number = cls._get_whatsapp_number(notification)
        if not phone_number:
            raise ValueError("No WhatsApp number for recipient")

        # Send
        WhatsAppService.send_message(
            phone_number=phone_number,
            message=notification.message,
            delivery=delivery
        )

    @classmethod
    def _send_email(cls, notification, delivery):
        """Send email notification."""
        from floor_app.operations.notifications.services.email_service import EmailService

        # Get recipient email
        email = cls._get_email(notification)
        if not email:
            raise ValueError("No email for recipient")

        # Send
        EmailService.send_email(
            to_email=email,
            subject=notification.title,
            body=notification.message,
            delivery=delivery
        )

    @classmethod
    def _send_sms(cls, notification, delivery):
        """Send SMS notification."""
        from floor_app.operations.notifications.services.sms_service import SMSService

        # Get recipient phone number
        phone_number = cls._get_phone_number(notification)
        if not phone_number:
            raise ValueError("No phone number for recipient")

        # Send
        SMSService.send_sms(
            phone_number=phone_number,
            message=notification.message,
            delivery=delivery
        )

    @classmethod
    def _send_push(cls, notification, delivery):
        """Send push notification."""
        from floor_app.operations.notifications.services.push_service import PushNotificationService

        # Send
        PushNotificationService.send_push(
            notification=notification,
            delivery=delivery
        )

    @classmethod
    def _send_telegram(cls, notification, delivery):
        """Send Telegram notification."""
        # TODO: Implement Telegram service
        raise NotImplementedError("Telegram service not yet implemented")

    @classmethod
    def _get_whatsapp_number(cls, notification) -> Optional[str]:
        """Get recipient's WhatsApp number."""
        from floor_app.operations.notifications.models import NotificationPreference

        user = notification.recipient_user
        if user:
            try:
                pref = NotificationPreference.objects.get(user=user)
                return pref.whatsapp_number
            except NotificationPreference.DoesNotExist:
                pass

        # Try employee phone
        employee = notification.recipient_employee
        if employee and hasattr(employee, 'mobile_number'):
            return employee.mobile_number

        return None

    @classmethod
    def _get_email(cls, notification) -> Optional[str]:
        """Get recipient's email."""
        user = notification.recipient_user
        if user and user.email:
            return user.email

        employee = notification.recipient_employee
        if employee and hasattr(employee, 'email'):
            return employee.email

        return None

    @classmethod
    def _get_phone_number(cls, notification) -> Optional[str]:
        """Get recipient's phone number."""
        employee = notification.recipient_employee
        if employee and hasattr(employee, 'mobile_number'):
            return employee.mobile_number

        return None

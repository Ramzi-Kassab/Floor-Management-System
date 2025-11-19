"""
WhatsApp Notification Service

Send WhatsApp messages using Twilio WhatsApp API.

Configuration:
Set these in NotificationChannel with channel_type='WHATSAPP':
{
    'account_sid': 'your_twilio_account_sid',
    'auth_token': 'your_twilio_auth_token',
    'from_number': 'whatsapp:+14155238886'  # Twilio WhatsApp number
}
"""

from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class WhatsAppService:
    """
    WhatsApp message delivery service using Twilio.
    """

    @classmethod
    def send_message(
        cls,
        phone_number: str,
        message: str,
        delivery=None
    ) -> bool:
        """
        Send WhatsApp message using Twilio.

        Args:
            phone_number: Recipient phone number (international format, e.g., +971501234567)
            message: Message text
            delivery: NotificationDelivery instance (optional)

        Returns:
            Boolean indicating success

        Example:
            WhatsAppService.send_message(
                phone_number='+971501234567',
                message='Your approval request has been submitted.'
            )
        """
        try:
            # Get Twilio configuration
            config = cls._get_configuration()
            if not config:
                raise ValueError("WhatsApp channel not configured")

            # Initialize Twilio client
            from twilio.rest import Client

            client = Client(
                config['account_sid'],
                config['auth_token']
            )

            # Format phone number for WhatsApp
            to_whatsapp = f"whatsapp:{phone_number}"
            from_whatsapp = config['from_number']

            # Send message
            twilio_message = client.messages.create(
                from_=from_whatsapp,
                to=to_whatsapp,
                body=message
            )

            # Update delivery record
            if delivery:
                delivery.status = 'SENT'
                delivery.sent_at = timezone.now()
                delivery.provider_message_id = twilio_message.sid
                delivery.provider_response = {
                    'sid': twilio_message.sid,
                    'status': twilio_message.status,
                    'date_created': str(twilio_message.date_created),
                }
                delivery.save()

            logger.info(f"WhatsApp message sent to {phone_number}: {twilio_message.sid}")
            return True

        except ImportError:
            logger.error("Twilio library not installed. Install with: pip install twilio")
            if delivery:
                delivery.status = 'FAILED'
                delivery.failure_reason = 'Twilio library not installed'
                delivery.failed_at = timezone.now()
                delivery.save()
            return False

        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {str(e)}")
            if delivery:
                delivery.status = 'FAILED'
                delivery.failure_reason = str(e)
                delivery.failed_at = timezone.now()
                delivery.save()
            return False

    @classmethod
    def send_template(
        cls,
        phone_number: str,
        template_name: str,
        template_params: list,
        delivery=None
    ) -> bool:
        """
        Send WhatsApp message using approved template.

        Args:
            phone_number: Recipient phone number
            template_name: WhatsApp approved template name
            template_params: List of parameters for template
            delivery: NotificationDelivery instance

        Returns:
            Boolean indicating success

        Note:
            WhatsApp Business API requires pre-approved templates.
            Template must be approved by WhatsApp before use.

        Example:
            WhatsAppService.send_template(
                phone_number='+971501234567',
                template_name='approval_request',
                template_params=['Ahmed', 'BOM-123', '2025-01-20']
            )
        """
        try:
            config = cls._get_configuration()
            if not config:
                raise ValueError("WhatsApp channel not configured")

            from twilio.rest import Client

            client = Client(
                config['account_sid'],
                config['auth_token']
            )

            # Send template message
            to_whatsapp = f"whatsapp:{phone_number}"
            from_whatsapp = config['from_number']

            # For Twilio WhatsApp templates, format is different
            # This is a simplified example - actual implementation depends on your templates
            content_variables = {str(i): param for i, param in enumerate(template_params, 1)}

            twilio_message = client.messages.create(
                from_=from_whatsapp,
                to=to_whatsapp,
                content_sid=template_name,  # Template SID from Twilio
                content_variables=content_variables
            )

            if delivery:
                delivery.status = 'SENT'
                delivery.sent_at = timezone.now()
                delivery.provider_message_id = twilio_message.sid
                delivery.provider_response = {
                    'sid': twilio_message.sid,
                    'status': twilio_message.status,
                }
                delivery.save()

            return True

        except Exception as e:
            logger.error(f"Error sending WhatsApp template: {str(e)}")
            if delivery:
                delivery.status = 'FAILED'
                delivery.failure_reason = str(e)
                delivery.failed_at = timezone.now()
                delivery.save()
            return False

    @classmethod
    def check_delivery_status(cls, message_sid: str) -> dict:
        """
        Check delivery status of a WhatsApp message.

        Args:
            message_sid: Twilio message SID

        Returns:
            Dict with status information

        Example:
            status = WhatsAppService.check_delivery_status('SM1234567890')
            # Returns: {'status': 'delivered', 'date_sent': '...', ...}
        """
        try:
            config = cls._get_configuration()
            if not config:
                raise ValueError("WhatsApp channel not configured")

            from twilio.rest import Client

            client = Client(
                config['account_sid'],
                config['auth_token']
            )

            message = client.messages(message_sid).fetch()

            return {
                'status': message.status,
                'date_sent': str(message.date_sent),
                'date_updated': str(message.date_updated),
                'error_code': message.error_code,
                'error_message': message.error_message,
            }

        except Exception as e:
            logger.error(f"Error checking WhatsApp status: {str(e)}")
            return {'status': 'unknown', 'error': str(e)}

    @classmethod
    def _get_configuration(cls) -> dict:
        """
        Get WhatsApp channel configuration.

        Returns:
            Dict with Twilio configuration or None
        """
        from floor_app.operations.notifications.models import NotificationChannel

        try:
            channel = NotificationChannel.objects.get(
                channel_type='WHATSAPP',
                is_enabled=True
            )
            return channel.configuration
        except NotificationChannel.DoesNotExist:
            return None

"""
SMS Notification Service

Send SMS messages using Twilio SMS API.

Configuration:
{
    'account_sid': 'your_twilio_account_sid',
    'auth_token': 'your_twilio_auth_token',
    'from_number': '+14155551234'  # Twilio phone number
}
"""

from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class SMSService:
    """
    SMS message delivery service using Twilio.
    """

    @classmethod
    def send_sms(
        cls,
        phone_number: str,
        message: str,
        delivery=None
    ) -> bool:
        """
        Send SMS message using Twilio.

        Args:
            phone_number: Recipient phone number (international format)
            message: Message text (max 160 chars recommended)
            delivery: NotificationDelivery instance

        Returns:
            Boolean indicating success

        Example:
            SMSService.send_sms(
                phone_number='+971501234567',
                message='Your approval request #123 has been submitted.'
            )
        """
        try:
            config = cls._get_configuration()
            if not config:
                raise ValueError("SMS channel not configured")

            from twilio.rest import Client

            client = Client(
                config['account_sid'],
                config['auth_token']
            )

            # Send SMS
            twilio_message = client.messages.create(
                from_=config['from_number'],
                to=phone_number,
                body=message[:160]  # Limit to 160 chars
            )

            # Update delivery record
            if delivery:
                delivery.status = 'SENT'
                delivery.sent_at = timezone.now()
                delivery.provider_message_id = twilio_message.sid
                delivery.provider_response = {
                    'sid': twilio_message.sid,
                    'status': twilio_message.status,
                }
                delivery.save()

            logger.info(f"SMS sent to {phone_number}: {twilio_message.sid}")
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
            logger.error(f"Error sending SMS: {str(e)}")
            if delivery:
                delivery.status = 'FAILED'
                delivery.failure_reason = str(e)
                delivery.failed_at = timezone.now()
                delivery.save()
            return False

    @classmethod
    def _get_configuration(cls) -> dict:
        """Get SMS channel configuration."""
        from floor_app.operations.notifications.models import NotificationChannel

        try:
            channel = NotificationChannel.objects.get(
                channel_type='SMS',
                is_enabled=True
            )
            return channel.configuration
        except NotificationChannel.DoesNotExist:
            return None

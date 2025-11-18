"""
Push Notification Service

Send push notifications using Firebase Cloud Messaging (FCM).

Configuration:
{
    'service_account_key': '/path/to/firebase-service-account.json',
    'project_id': 'your-firebase-project-id'
}

Or use JSON directly:
{
    'service_account_json': {
        "type": "service_account",
        "project_id": "your-project-id",
        "private_key_id": "...",
        "private_key": "...",
        ...
    }
}
"""

from django.utils import timezone
import logging
import json
import tempfile
import os

logger = logging.getLogger(__name__)


class PushNotificationService:
    """
    Push notification delivery service using Firebase Cloud Messaging.
    """

    @classmethod
    def send_push(
        cls,
        notification,
        delivery=None
    ) -> bool:
        """
        Send push notification via FCM.

        Args:
            notification: Notification instance
            delivery: NotificationDelivery instance

        Returns:
            Boolean indicating success

        Example:
            PushNotificationService.send_push(notification)
        """
        try:
            config = cls._get_configuration()
            if not config:
                raise ValueError("Push notification channel not configured")

            # Initialize Firebase Admin SDK
            cls._initialize_firebase(config)

            # Get FCM tokens for recipient
            fcm_tokens = cls._get_fcm_tokens(notification)
            if not fcm_tokens:
                logger.warning(f"No FCM tokens found for notification {notification.id}")
                if delivery:
                    delivery.status = 'FAILED'
                    delivery.failure_reason = 'No FCM tokens registered for recipient'
                    delivery.failed_at = timezone.now()
                    delivery.save()
                return False

            # Send to all devices
            success_count = 0
            failed_tokens = []

            for token in fcm_tokens:
                success = cls._send_to_token(
                    token=token,
                    title=notification.title,
                    body=notification.message,
                    data={
                        'notification_id': str(notification.id),
                        'priority': notification.priority,
                        'action_url': notification.action_url or '',
                        'category': notification.category,
                    }
                )

                if success:
                    success_count += 1
                else:
                    failed_tokens.append(token)

            # Update delivery record
            if delivery:
                if success_count > 0:
                    delivery.status = 'SENT'
                    delivery.sent_at = timezone.now()
                    delivery.provider_response = {
                        'total_tokens': len(fcm_tokens),
                        'success_count': success_count,
                        'failed_count': len(failed_tokens),
                        'failed_tokens': failed_tokens[:5],  # Limit for storage
                    }
                else:
                    delivery.status = 'FAILED'
                    delivery.failure_reason = 'Failed to send to all devices'
                    delivery.failed_at = timezone.now()
                    delivery.provider_response = {
                        'failed_tokens': failed_tokens[:5]
                    }
                delivery.save()

            logger.info(f"Push notification sent to {success_count}/{len(fcm_tokens)} devices")
            return success_count > 0

        except ImportError:
            logger.error("Firebase Admin SDK not installed. Install with: pip install firebase-admin")
            if delivery:
                delivery.status = 'FAILED'
                delivery.failure_reason = 'Firebase Admin SDK not installed'
                delivery.failed_at = timezone.now()
                delivery.save()
            return False

        except Exception as e:
            logger.error(f"Error sending push notification: {str(e)}")
            if delivery:
                delivery.status = 'FAILED'
                delivery.failure_reason = str(e)
                delivery.failed_at = timezone.now()
                delivery.save()
            return False

    @classmethod
    def _send_to_token(
        cls,
        token: str,
        title: str,
        body: str,
        data: dict = None
    ) -> bool:
        """
        Send push notification to a single FCM token.

        Args:
            token: FCM device token
            title: Notification title
            body: Notification body
            data: Additional data payload

        Returns:
            Boolean indicating success
        """
        try:
            from firebase_admin import messaging

            # Build notification message
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data=data or {},
                token=token,
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        sound='default',
                        channel_id='default'
                    )
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound='default',
                            badge=1
                        )
                    )
                )
            )

            # Send message
            response = messaging.send(message)
            logger.info(f"Successfully sent message to token: {token[:20]}... Response: {response}")
            return True

        except Exception as e:
            logger.error(f"Failed to send to token {token[:20]}...: {str(e)}")
            return False

    @classmethod
    def send_to_topic(
        cls,
        topic: str,
        title: str,
        body: str,
        data: dict = None
    ) -> bool:
        """
        Send push notification to a topic (all subscribers).

        Args:
            topic: FCM topic name
            title: Notification title
            body: Notification body
            data: Additional data payload

        Returns:
            Boolean indicating success

        Example:
            PushNotificationService.send_to_topic(
                topic='all_employees',
                title='System Maintenance',
                body='System will be down for maintenance tonight at 11 PM.'
            )
        """
        try:
            config = cls._get_configuration()
            if not config:
                raise ValueError("Push notification channel not configured")

            cls._initialize_firebase(config)

            from firebase_admin import messaging

            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data=data or {},
                topic=topic
            )

            response = messaging.send(message)
            logger.info(f"Successfully sent message to topic '{topic}': {response}")
            return True

        except Exception as e:
            logger.error(f"Error sending to topic '{topic}': {str(e)}")
            return False

    @classmethod
    def subscribe_to_topic(cls, tokens: list, topic: str) -> dict:
        """
        Subscribe device tokens to a topic.

        Args:
            tokens: List of FCM device tokens
            topic: Topic name to subscribe to

        Returns:
            Dict with success/failure counts

        Example:
            result = PushNotificationService.subscribe_to_topic(
                tokens=['token1', 'token2', 'token3'],
                topic='production_alerts'
            )
        """
        try:
            config = cls._get_configuration()
            if not config:
                raise ValueError("Push notification channel not configured")

            cls._initialize_firebase(config)

            from firebase_admin import messaging

            response = messaging.subscribe_to_topic(tokens, topic)

            return {
                'success_count': response.success_count,
                'failure_count': response.failure_count,
                'errors': [str(e) for e in response.errors] if response.errors else []
            }

        except Exception as e:
            logger.error(f"Error subscribing to topic '{topic}': {str(e)}")
            return {
                'success_count': 0,
                'failure_count': len(tokens),
                'errors': [str(e)]
            }

    @classmethod
    def unsubscribe_from_topic(cls, tokens: list, topic: str) -> dict:
        """
        Unsubscribe device tokens from a topic.

        Args:
            tokens: List of FCM device tokens
            topic: Topic name to unsubscribe from

        Returns:
            Dict with success/failure counts
        """
        try:
            config = cls._get_configuration()
            if not config:
                raise ValueError("Push notification channel not configured")

            cls._initialize_firebase(config)

            from firebase_admin import messaging

            response = messaging.unsubscribe_from_topic(tokens, topic)

            return {
                'success_count': response.success_count,
                'failure_count': response.failure_count,
                'errors': [str(e) for e in response.errors] if response.errors else []
            }

        except Exception as e:
            logger.error(f"Error unsubscribing from topic '{topic}': {str(e)}")
            return {
                'success_count': 0,
                'failure_count': len(tokens),
                'errors': [str(e)]
            }

    @classmethod
    def _get_fcm_tokens(cls, notification) -> list:
        """
        Get FCM tokens for notification recipient.

        Args:
            notification: Notification instance

        Returns:
            List of FCM tokens
        """
        from floor_app.operations.device_tracking.models import EmployeeDevice

        tokens = []

        # Get tokens from recipient's devices
        if notification.recipient_employee:
            devices = EmployeeDevice.objects.filter(
                employee=notification.recipient_employee,
                is_active=True,
                push_enabled=True,
                fcm_token__isnull=False
            ).exclude(fcm_token='')

            tokens = list(devices.values_list('fcm_token', flat=True))

        elif notification.recipient_user:
            # Get via user's employee record
            try:
                employee = notification.recipient_user.hremployee
                devices = EmployeeDevice.objects.filter(
                    employee=employee,
                    is_active=True,
                    push_enabled=True,
                    fcm_token__isnull=False
                ).exclude(fcm_token='')

                tokens = list(devices.values_list('fcm_token', flat=True))
            except Exception:
                pass

        return tokens

    @classmethod
    def _initialize_firebase(cls, config: dict):
        """
        Initialize Firebase Admin SDK.

        Args:
            config: Firebase configuration dict
        """
        try:
            import firebase_admin
            from firebase_admin import credentials

            # Check if already initialized
            try:
                firebase_admin.get_app()
                return  # Already initialized
            except ValueError:
                pass  # Not initialized yet

            # Initialize with service account
            if 'service_account_key' in config:
                # Path to service account JSON file
                cred = credentials.Certificate(config['service_account_key'])
            elif 'service_account_json' in config:
                # Service account as JSON dict
                # Write to temp file (Firebase SDK requires file path)
                service_account = config['service_account_json']

                # Create temporary file
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
                    json.dump(service_account, f)
                    temp_path = f.name

                cred = credentials.Certificate(temp_path)

                # Clean up temp file after initialization
                try:
                    os.unlink(temp_path)
                except Exception:
                    pass
            else:
                raise ValueError("No service account configuration found")

            firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin SDK initialized successfully")

        except ImportError:
            raise ImportError("Firebase Admin SDK not installed")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {str(e)}")
            raise

    @classmethod
    def _get_configuration(cls) -> dict:
        """Get push notification channel configuration."""
        from floor_app.operations.notifications.models import NotificationChannel

        try:
            channel = NotificationChannel.objects.get(
                channel_type='PUSH',
                is_enabled=True
            )
            return channel.configuration
        except NotificationChannel.DoesNotExist:
            return None

    @classmethod
    def send_data_message(
        cls,
        token: str,
        data: dict
    ) -> bool:
        """
        Send data-only message (no notification, silent).

        Useful for background updates without showing notification.

        Args:
            token: FCM device token
            data: Data payload

        Returns:
            Boolean indicating success

        Example:
            PushNotificationService.send_data_message(
                token='fcm_token_here',
                data={
                    'action': 'sync_data',
                    'timestamp': '2025-01-18T10:30:00Z'
                }
            )
        """
        try:
            config = cls._get_configuration()
            if not config:
                raise ValueError("Push notification channel not configured")

            cls._initialize_firebase(config)

            from firebase_admin import messaging

            message = messaging.Message(
                data=data,
                token=token
            )

            response = messaging.send(message)
            logger.info(f"Successfully sent data message: {response}")
            return True

        except Exception as e:
            logger.error(f"Error sending data message: {str(e)}")
            return False

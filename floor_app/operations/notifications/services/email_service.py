"""
Email Notification Service

Send emails via SMTP or Microsoft Graph API (for Outlook/Office 365).

Configuration options:
1. SMTP (Gmail, SendGrid, custom):
   {
       'method': 'smtp',
       'host': 'smtp.gmail.com',
       'port': 587,
       'username': 'your-email@gmail.com',
       'password': 'your-app-password',
       'use_tls': true,
       'from_email': 'noreply@yourcompany.com',
       'from_name': 'Floor Management System'
   }

2. Microsoft Graph (Outlook/Office 365):
   {
       'method': 'microsoft_graph',
       'client_id': 'your_azure_app_client_id',
       'client_secret': 'your_azure_app_secret',
       'tenant_id': 'your_azure_tenant_id',
       'from_email': 'noreply@yourcompany.com',
       'from_name': 'Floor Management System'
   }
"""

from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """
    Email delivery service supporting SMTP and Microsoft Graph.
    """

    @classmethod
    def send_email(
        cls,
        to_email: str,
        subject: str,
        body: str,
        html_body: str = None,
        delivery=None,
        cc: list = None,
        bcc: list = None,
        attachments: list = None
    ) -> bool:
        """
        Send email.

        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Plain text email body
            html_body: HTML email body (optional)
            delivery: NotificationDelivery instance
            cc: CC email addresses
            bcc: BCC email addresses
            attachments: List of attachment file paths

        Returns:
            Boolean indicating success

        Example:
            EmailService.send_email(
                to_email='ahmed@company.com',
                subject='Approval Required',
                body='Please approve request #123',
                html_body='<h1>Please approve request #123</h1>'
            )
        """
        try:
            config = cls._get_configuration()
            if not config:
                raise ValueError("Email channel not configured")

            method = config.get('method', 'smtp')

            if method == 'smtp':
                return cls._send_via_smtp(
                    to_email, subject, body, html_body,
                    delivery, cc, bcc, attachments, config
                )
            elif method == 'microsoft_graph':
                return cls._send_via_microsoft_graph(
                    to_email, subject, body, html_body,
                    delivery, cc, bcc, attachments, config
                )
            else:
                raise ValueError(f"Unknown email method: {method}")

        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            if delivery:
                delivery.status = 'FAILED'
                delivery.failure_reason = str(e)
                delivery.failed_at = timezone.now()
                delivery.save()
            return False

    @classmethod
    def send_bulk_email(
        cls,
        recipients: list,
        subject: str,
        body: str,
        html_body: str = None
    ) -> int:
        """
        Send same email to multiple recipients.

        Args:
            recipients: List of email addresses
            subject: Email subject
            body: Plain text body
            html_body: HTML body (optional)

        Returns:
            Number of successfully sent emails

        Example:
            EmailService.send_bulk_email(
                recipients=['user1@company.com', 'user2@company.com'],
                subject='System Maintenance',
                body='System will be down tomorrow'
            )
        """
        success_count = 0

        for recipient in recipients:
            if cls.send_email(recipient, subject, body, html_body):
                success_count += 1

        return success_count

    @classmethod
    def _send_via_smtp(
        cls,
        to_email: str,
        subject: str,
        body: str,
        html_body: str = None,
        delivery=None,
        cc: list = None,
        bcc: list = None,
        attachments: list = None,
        config: dict = None
    ) -> bool:
        """Send email via SMTP."""
        from django.core.mail import EmailMultiAlternatives
        from django.core.mail import get_connection

        try:
            # Create SMTP connection
            connection = get_connection(
                backend='django.core.mail.backends.smtp.EmailBackend',
                host=config.get('host'),
                port=config.get('port', 587),
                username=config.get('username'),
                password=config.get('password'),
                use_tls=config.get('use_tls', True),
                use_ssl=config.get('use_ssl', False),
            )

            # Create email
            from_email = f"{config.get('from_name', 'System')} <{config.get('from_email')}>"

            email = EmailMultiAlternatives(
                subject=subject,
                body=body,
                from_email=from_email,
                to=[to_email],
                cc=cc or [],
                bcc=bcc or [],
                connection=connection
            )

            # Add HTML body if provided
            if html_body:
                email.attach_alternative(html_body, "text/html")

            # Add attachments if provided
            if attachments:
                for attachment_path in attachments:
                    email.attach_file(attachment_path)

            # Send
            email.send()

            # Update delivery record
            if delivery:
                delivery.status = 'SENT'
                delivery.sent_at = timezone.now()
                delivery.provider_response = {
                    'method': 'smtp',
                    'to': to_email,
                    'subject': subject
                }
                delivery.save()

            logger.info(f"Email sent to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Error sending email via SMTP: {str(e)}")
            if delivery:
                delivery.status = 'FAILED'
                delivery.failure_reason = str(e)
                delivery.failed_at = timezone.now()
                delivery.save()
            return False

    @classmethod
    def _send_via_microsoft_graph(
        cls,
        to_email: str,
        subject: str,
        body: str,
        html_body: str = None,
        delivery=None,
        cc: list = None,
        bcc: list = None,
        attachments: list = None,
        config: dict = None
    ) -> bool:
        """
        Send email via Microsoft Graph API (Outlook/Office 365).

        Note: Requires msal library
        pip install msal
        """
        try:
            import requests
            import msal

            # Get access token
            authority = f"https://login.microsoftonline.com/{config['tenant_id']}"
            app = msal.ConfidentialClientApplication(
                config['client_id'],
                authority=authority,
                client_credential=config['client_secret']
            )

            scopes = ["https://graph.microsoft.com/.default"]
            result = app.acquire_token_for_client(scopes=scopes)

            if "access_token" not in result:
                raise ValueError("Failed to obtain access token")

            access_token = result['access_token']

            # Build email message
            message = {
                "message": {
                    "subject": subject,
                    "body": {
                        "contentType": "HTML" if html_body else "Text",
                        "content": html_body or body
                    },
                    "toRecipients": [
                        {"emailAddress": {"address": to_email}}
                    ]
                }
            }

            # Add CC if provided
            if cc:
                message["message"]["ccRecipients"] = [
                    {"emailAddress": {"address": email}} for email in cc
                ]

            # Add BCC if provided
            if bcc:
                message["message"]["bccRecipients"] = [
                    {"emailAddress": {"address": email}} for email in bcc
                ]

            # Send email
            endpoint = f"https://graph.microsoft.com/v1.0/users/{config['from_email']}/sendMail"
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }

            response = requests.post(endpoint, headers=headers, json=message)
            response.raise_for_status()

            # Update delivery record
            if delivery:
                delivery.status = 'SENT'
                delivery.sent_at = timezone.now()
                delivery.provider_response = {
                    'method': 'microsoft_graph',
                    'status_code': response.status_code
                }
                delivery.save()

            logger.info(f"Email sent via Microsoft Graph to {to_email}")
            return True

        except ImportError:
            logger.error("msal library not installed. Install with: pip install msal")
            if delivery:
                delivery.status = 'FAILED'
                delivery.failure_reason = 'msal library not installed'
                delivery.failed_at = timezone.now()
                delivery.save()
            return False

        except Exception as e:
            logger.error(f"Error sending email via Microsoft Graph: {str(e)}")
            if delivery:
                delivery.status = 'FAILED'
                delivery.failure_reason = str(e)
                delivery.failed_at = timezone.now()
                delivery.save()
            return False

    @classmethod
    def _get_configuration(cls) -> dict:
        """Get email channel configuration."""
        from floor_app.operations.notifications.models import NotificationChannel

        try:
            channel = NotificationChannel.objects.get(
                channel_type='EMAIL',
                is_enabled=True
            )
            return channel.configuration
        except NotificationChannel.DoesNotExist:
            return None

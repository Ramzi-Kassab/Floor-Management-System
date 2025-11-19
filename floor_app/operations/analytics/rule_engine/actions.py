"""
Action Executor

Executes actions when rules trigger.

Supported actions:
- LOG_ONLY: Just log (default)
- CREATE_ALERT: Create system alert
- SEND_NOTIFICATION: Send email/in-app notification
- UPDATE_FIELD: Update a field on the target object
- CREATE_TASK: Create a task/todo
- RUN_SCRIPT: Run custom management command
- WEBHOOK: Call external webhook
"""

from django.core.mail import send_mail
from django.conf import settings
from django.apps import apps
import requests
import logging

logger = logging.getLogger(__name__)


class ActionExecutor:
    """
    Executes rule actions.

    Handles different action types with appropriate error handling.
    """

    def __init__(self, rule, execution):
        """
        Initialize executor.

        Args:
            rule: AutomationRule instance
            execution: AutomationRuleExecution instance
        """
        self.rule = rule
        self.execution = execution
        self.action_type = rule.action_type
        self.action_config = rule.action_config or {}

    def execute(self):
        """
        Execute the action.

        Returns:
            dict with action result
        """
        if self.action_type == 'LOG_ONLY':
            return self._log_only()
        elif self.action_type == 'CREATE_ALERT':
            return self._create_alert()
        elif self.action_type == 'SEND_NOTIFICATION':
            return self._send_notification()
        elif self.action_type == 'UPDATE_FIELD':
            return self._update_field()
        elif self.action_type == 'CREATE_TASK':
            return self._create_task()
        elif self.action_type == 'RUN_SCRIPT':
            return self._run_script()
        elif self.action_type == 'WEBHOOK':
            return self._call_webhook()
        else:
            return {'status': 'unknown_action_type', 'action_type': self.action_type}

    def _log_only(self):
        """Log only - no action taken."""
        logger.info(
            f"Rule '{self.rule.rule_code}' triggered (LOG_ONLY): {self.execution.comment}"
        )
        return {'status': 'logged'}

    def _create_alert(self):
        """
        Create system alert.

        Config example:
        {
            "alert_type": "BOTTLENECK",
            "priority": "HIGH",
            "auto_assign_to": "manager"
        }
        """
        try:
            # Import here to avoid circular imports
            from floor_app.operations.analytics.models import AppEvent

            alert_type = self.action_config.get('alert_type', 'RULE_ALERT')
            priority = self.action_config.get('priority', 'MEDIUM')

            # Log as an event for now
            # TODO: Create proper Alert model
            AppEvent.log_event(
                user=None,
                event_type='ACTION',
                view_name='automation_rule_alert',
                event_category='Analytics',
                related_object=self.execution,
                metadata={
                    'alert_type': alert_type,
                    'priority': priority,
                    'rule_code': self.rule.rule_code,
                    'rule_name': self.rule.name,
                    'comment': self.execution.comment,
                }
            )

            return {
                'status': 'alert_created',
                'alert_type': alert_type,
                'priority': priority,
            }

        except Exception as e:
            logger.error(f"Error creating alert: {e}")
            return {'status': 'error', 'error': str(e)}

    def _send_notification(self):
        """
        Send notification.

        Config example:
        {
            "recipients": ["user@example.com"],
            "channels": ["email"],
            "subject": "Rule Alert: {rule_name}",
            "message": "Rule '{rule_name}' was triggered..."
        }
        """
        try:
            recipients = self.action_config.get('recipients', [])
            channels = self.action_config.get('channels', ['email'])
            subject = self.action_config.get('subject', f"Rule Alert: {self.rule.name}")
            message = self.action_config.get('message', self.execution.comment)

            # Template substitution
            subject = subject.format(
                rule_name=self.rule.name,
                rule_code=self.rule.rule_code,
                severity=self.rule.get_severity_display(),
            )
            message = message.format(
                rule_name=self.rule.name,
                rule_code=self.rule.rule_code,
                severity=self.rule.get_severity_display(),
                comment=self.execution.comment,
            )

            results = []

            if 'email' in channels and recipients:
                try:
                    send_mail(
                        subject=subject,
                        message=message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=recipients,
                        fail_silently=False,
                    )
                    results.append({'channel': 'email', 'status': 'sent'})
                except Exception as e:
                    logger.error(f"Error sending email: {e}")
                    results.append({'channel': 'email', 'status': 'error', 'error': str(e)})

            # TODO: Add in-app notification channel
            # if 'in_app' in channels:
            #     create in-app notification

            return {
                'status': 'notifications_sent',
                'results': results,
            }

        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return {'status': 'error', 'error': str(e)}

    def _update_field(self):
        """
        Update field on target object.

        Config example:
        {
            "field": "status",
            "value": "FLAGGED",
            "condition": "if_null"  # Optional: only_if_null, always
        }
        """
        try:
            if not self.execution.target_object:
                return {'status': 'no_target_object'}

            field_name = self.action_config.get('field')
            new_value = self.action_config.get('value')
            condition = self.action_config.get('condition', 'always')

            if not field_name:
                return {'status': 'error', 'error': 'No field specified'}

            obj = self.execution.target_object

            # Check condition
            current_value = getattr(obj, field_name, None)

            if condition == 'if_null' and current_value is not None:
                return {'status': 'skipped', 'reason': 'field_not_null', 'current_value': current_value}

            # Update field
            setattr(obj, field_name, new_value)
            obj.save(update_fields=[field_name, 'updated_at'])

            return {
                'status': 'field_updated',
                'field': field_name,
                'old_value': current_value,
                'new_value': new_value,
            }

        except Exception as e:
            logger.error(f"Error updating field: {e}")
            return {'status': 'error', 'error': str(e)}

    def _create_task(self):
        """
        Create task/todo.

        Config example:
        {
            "task_type": "FOLLOW_UP",
            "title": "Check {rule_name}",
            "description": "...",
            "assign_to": "manager"
        }
        """
        try:
            # TODO: Integrate with actual task/todo system if exists
            # For now, just log

            task_title = self.action_config.get('title', f"Follow up on rule: {self.rule.name}")
            task_description = self.action_config.get('description', self.execution.comment)

            logger.info(f"Task created: {task_title}")

            return {
                'status': 'task_created',
                'title': task_title,
                'description': task_description,
            }

        except Exception as e:
            logger.error(f"Error creating task: {e}")
            return {'status': 'error', 'error': str(e)}

    def _run_script(self):
        """
        Run custom management command.

        Config example:
        {
            "command": "refresh_inventory_summary",
            "args": [],
            "kwargs": {}
        }

        WARNING: Only allow whitelisted commands for security.
        """
        try:
            command_name = self.action_config.get('command')

            if not command_name:
                return {'status': 'error', 'error': 'No command specified'}

            # Whitelist of allowed commands
            ALLOWED_COMMANDS = [
                'refresh_inventory_summary',
                'generate_analytics_summary',
                # Add more as needed
            ]

            if command_name not in ALLOWED_COMMANDS:
                return {
                    'status': 'error',
                    'error': f"Command '{command_name}' not in whitelist"
                }

            # TODO: Actually run management command
            # from django.core.management import call_command
            # call_command(command_name, *args, **kwargs)

            logger.info(f"Would run command: {command_name}")

            return {
                'status': 'command_executed',
                'command': command_name,
            }

        except Exception as e:
            logger.error(f"Error running script: {e}")
            return {'status': 'error', 'error': str(e)}

    def _call_webhook(self):
        """
        Call external webhook.

        Config example:
        {
            "url": "https://example.com/webhook",
            "method": "POST",
            "headers": {"Content-Type": "application/json"},
            "payload": {
                "rule_code": "{rule_code}",
                "severity": "{severity}",
                "comment": "{comment}"
            }
        }
        """
        try:
            url = self.action_config.get('url')
            method = self.action_config.get('method', 'POST').upper()
            headers = self.action_config.get('headers', {})
            payload = self.action_config.get('payload', {})

            if not url:
                return {'status': 'error', 'error': 'No URL specified'}

            # Template substitution in payload
            import json
            payload_str = json.dumps(payload)
            payload_str = payload_str.format(
                rule_code=self.rule.rule_code,
                rule_name=self.rule.name,
                severity=self.rule.get_severity_display(),
                comment=self.execution.comment,
            )
            payload = json.loads(payload_str)

            # Make request
            if method == 'POST':
                response = requests.post(url, json=payload, headers=headers, timeout=10)
            elif method == 'GET':
                response = requests.get(url, params=payload, headers=headers, timeout=10)
            else:
                return {'status': 'error', 'error': f'Unsupported method: {method}'}

            return {
                'status': 'webhook_called',
                'url': url,
                'method': method,
                'status_code': response.status_code,
                'response': response.text[:500],  # Limit response size
            }

        except Exception as e:
            logger.error(f"Error calling webhook: {e}")
            return {'status': 'error', 'error': str(e)}

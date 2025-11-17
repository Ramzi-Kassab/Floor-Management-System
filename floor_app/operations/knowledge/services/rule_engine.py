"""
Rule Engine - Core service for evaluating and executing instruction rules.

This is the POWER behind dynamic instructions. It:
1. Evaluates conditions against any model
2. Executes actions when conditions are met
3. Logs all executions for audit
4. Handles complex condition logic (AND/OR with grouping)
"""
import json
import re
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.core.mail import send_mail
from django.conf import settings


class RuleEvaluator:
    """
    Evaluates rule conditions against provided context.
    """

    def __init__(self, instruction_rule):
        self.rule = instruction_rule
        self.conditions = list(instruction_rule.conditions.all().order_by('condition_group', 'order'))

    def evaluate(self, context):
        """
        Evaluate all conditions for this rule.

        Args:
            context: dict mapping ContentType IDs to model instances
                    e.g., {15: bit_design_instance, 23: job_card_instance}

        Returns:
            tuple: (bool result, dict evaluation_details)
        """
        if not self.conditions:
            # No conditions = always true (universal instruction)
            return True, {'no_conditions': True}

        evaluation_details = {}
        groups = {}

        # Group conditions
        for condition in self.conditions:
            group_id = condition.condition_group
            if group_id not in groups:
                groups[group_id] = []
            groups[group_id].append(condition)

        # Evaluate each group
        group_results = {}
        for group_id, group_conditions in sorted(groups.items()):
            group_result, group_details = self._evaluate_group(group_conditions, context)
            group_results[group_id] = group_result
            evaluation_details[f'group_{group_id}'] = {
                'result': group_result,
                'conditions': group_details
            }

        # Combine groups with OR (groups are OR'd together by default)
        final_result = any(group_results.values())
        evaluation_details['final_result'] = final_result
        evaluation_details['group_results'] = group_results

        return final_result, evaluation_details

    def _evaluate_group(self, conditions, context):
        """Evaluate a group of conditions (connected by AND/OR)"""
        if not conditions:
            return True, {}

        results = []
        details = []
        current_result = None

        for i, condition in enumerate(conditions):
            # Evaluate single condition
            result = condition.evaluate(context)
            results.append(result)

            details.append({
                'condition': str(condition),
                'target_model': condition.target_model.model,
                'field_path': condition.field_path,
                'operator': condition.operator,
                'value': condition.value,
                'result': result
            })

            # Combine with previous result
            if i == 0:
                current_result = result
            else:
                prev_condition = conditions[i - 1]
                if prev_condition.logical_operator == 'AND':
                    current_result = current_result and result
                else:  # OR
                    current_result = current_result or result

        return current_result, details


class RuleActionExecutor:
    """
    Executes actions for a triggered instruction rule.
    """

    def __init__(self, action, context, instruction_rule):
        self.action = action
        self.context = context
        self.rule = instruction_rule

    def execute(self):
        """
        Execute this action.
        Returns dict with execution results.
        """
        action_type = self.action.action_type
        result = {
            'action_type': action_type,
            'success': False,
            'message': '',
            'data': {}
        }

        # Dispatch to specific handler
        handler_name = f'_handle_{action_type.lower()}'
        handler = getattr(self, handler_name, self._handle_unknown)

        try:
            result.update(handler())
            result['success'] = True
        except Exception as e:
            result['success'] = False
            result['error'] = str(e)

        return result

    def _render_template(self, template):
        """Render message template with context placeholders"""
        if not template:
            return ''

        # Simple placeholder replacement {field_name}
        rendered = template
        for ct_id, obj in self.context.items():
            if obj is None:
                continue

            # Get all fields from object
            if hasattr(obj, '__dict__'):
                for key, value in obj.__dict__.items():
                    if not key.startswith('_'):
                        placeholder = f'{{{key}}}'
                        if placeholder in rendered:
                            rendered = rendered.replace(placeholder, str(value))

        return rendered

    # Action Handlers

    def _handle_show_message(self):
        """Display informational message"""
        message = self._render_template(self.action.message_template)
        return {
            'message': message,
            'severity': self.action.severity,
            'display_type': 'toast'
        }

    def _handle_show_warning(self):
        """Display warning message"""
        message = self._render_template(self.action.message_template)
        return {
            'message': message,
            'severity': 'warning',
            'display_type': 'alert'
        }

    def _handle_show_error(self):
        """Display blocking error"""
        message = self._render_template(self.action.message_template)
        return {
            'message': message,
            'severity': 'danger',
            'display_type': 'modal',
            'blocking': True
        }

    def _handle_show_info(self):
        """Display information panel"""
        message = self._render_template(self.action.message_template)
        return {
            'message': message,
            'severity': 'info',
            'display_type': 'panel'
        }

    def _handle_prevent_action(self):
        """Block the current action"""
        message = self._render_template(self.action.message_template) or 'Action prevented by system rule'
        return {
            'prevented': True,
            'message': message,
            'reason': f'Rule {self.rule.code}: {self.rule.title}'
        }

    def _handle_require_confirmation(self):
        """Require user confirmation to proceed"""
        message = self._render_template(self.action.message_template) or 'Please confirm this action'
        return {
            'requires_confirmation': True,
            'message': message,
            'confirmation_type': 'dialog'
        }

    def _handle_require_approval(self):
        """Require approval from authorized person"""
        message = self._render_template(self.action.message_template) or 'This action requires approval'
        return {
            'requires_approval': True,
            'message': message,
            'approval_roles': list(self.action.notify_roles.values_list('name', flat=True))
        }

    def _handle_require_override(self):
        """Require manager override"""
        message = self._render_template(self.action.message_template) or 'Manager override required'
        return {
            'requires_override': True,
            'message': message,
            'override_level': self.action.parameters.get('override_level', 'manager')
        }

    def _handle_send_email(self):
        """Send email notification"""
        subject = self.action.parameters.get('subject', f'Instruction Triggered: {self.rule.code}')
        message = self._render_template(self.action.message_template)

        recipients = list(self.action.notify_users.values_list('email', flat=True))

        # Add role-based recipients
        for position in self.action.notify_roles.all():
            from floor_app.operations.hr.models import HREmployee
            employee_emails = HREmployee.objects.filter(
                position=position,
                status='ACTIVE',
                user__isnull=False
            ).values_list('user__email', flat=True)
            recipients.extend(list(employee_emails))

        if recipients:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@fms.local',
                recipients,
                fail_silently=True
            )

        return {
            'email_sent': True,
            'recipients': recipients,
            'subject': subject
        }

    def _handle_create_notification(self):
        """Create in-app notification"""
        message = self._render_template(self.action.message_template)

        # This would integrate with a notification system
        # For now, store in action parameters
        return {
            'notification_created': True,
            'message': message,
            'recipients': list(self.action.notify_users.values_list('id', flat=True)),
            'priority': self.rule.priority
        }

    def _handle_set_field_value(self):
        """Set a field value on target model"""
        target_field = self.action.target_field
        value = self._evaluate_expression(self.action.value_expression)

        return {
            'field_to_set': target_field,
            'value': value,
            'auto_apply': self.action.parameters.get('auto_apply', False)
        }

    def _handle_calculate_value(self):
        """Calculate and suggest a value"""
        expression = self.action.value_expression
        result = self._evaluate_expression(expression)

        return {
            'calculated_value': result,
            'target_field': self.action.target_field,
            'expression': expression,
            'auto_apply': self.action.parameters.get('auto_apply', False)
        }

    def _handle_validate_field(self):
        """Validate a field value"""
        target_field = self.action.target_field
        validation_rule = self.action.parameters.get('validation_rule', '')

        return {
            'field_to_validate': target_field,
            'validation_rule': validation_rule,
            'error_message': self._render_template(self.action.message_template)
        }

    def _handle_enforce_minimum(self):
        """Enforce minimum value"""
        min_value = self.action.parameters.get('min_value', 0)

        return {
            'target_field': self.action.target_field,
            'minimum_value': min_value,
            'message': self._render_template(self.action.message_template)
        }

    def _handle_enforce_maximum(self):
        """Enforce maximum value"""
        max_value = self.action.parameters.get('max_value', 0)

        return {
            'target_field': self.action.target_field,
            'maximum_value': max_value,
            'message': self._render_template(self.action.message_template)
        }

    def _handle_highlight_field(self):
        """Highlight a field in UI"""
        return {
            'field_to_highlight': self.action.target_field,
            'highlight_color': self.action.parameters.get('color', '#ffc107'),
            'highlight_duration': self.action.parameters.get('duration', 5000)
        }

    def _handle_disable_field(self):
        """Disable a field in UI"""
        return {
            'field_to_disable': self.action.target_field,
            'reason': self._render_template(self.action.message_template)
        }

    def _handle_log_audit(self):
        """Create audit log entry"""
        return {
            'audit_logged': True,
            'message': self._render_template(self.action.message_template),
            'severity': self.action.severity
        }

    def _handle_change_status(self):
        """Change status of target object"""
        new_status = self.action.parameters.get('new_status', '')

        return {
            'status_change': new_status,
            'target_field': self.action.target_field or 'status',
            'message': self._render_template(self.action.message_template)
        }

    def _handle_unknown(self):
        """Handle unknown action type"""
        return {
            'message': f'Unknown action type: {self.action.action_type}',
            'severity': 'warning'
        }

    def _evaluate_expression(self, expression):
        """
        Safely evaluate a mathematical/logical expression.
        Supports: basic math, field references, simple functions
        """
        if not expression:
            return None

        # Replace field references with values
        rendered = expression

        for ct_id, obj in self.context.items():
            if obj is None:
                continue
            if hasattr(obj, '__dict__'):
                for key, value in obj.__dict__.items():
                    if not key.startswith('_'):
                        placeholder = f'{{{key}}}'
                        if placeholder in rendered:
                            rendered = rendered.replace(placeholder, str(value))

        # Safe evaluation (only allow math operations)
        allowed_chars = set('0123456789+-*/().% ')
        if all(c in allowed_chars for c in rendered):
            try:
                return eval(rendered)
            except:
                pass

        return rendered


class RuleEngine:
    """
    Main Rule Engine that orchestrates evaluation and execution of instructions.
    """

    def __init__(self, user=None, request=None):
        self.user = user
        self.request = request

    def evaluate_for_context(self, context, trigger_event='check'):
        """
        Evaluate all active instructions for given context.

        Args:
            context: dict mapping ContentType IDs to model instances
            trigger_event: what triggered this evaluation (save, view, approve, etc.)

        Returns:
            dict with evaluation results and actions to perform
        """
        from floor_app.operations.knowledge.models import InstructionRule, InstructionExecutionLog

        results = {
            'triggered_instructions': [],
            'actions': [],
            'blocking_actions': [],
            'warnings': [],
            'notifications': [],
            'field_modifications': [],
            'requires_confirmation': False,
            'requires_approval': False,
            'requires_override': False,
            'prevented': False,
            'prevention_reason': ''
        }

        # Get all active instructions
        active_instructions = InstructionRule.objects.filter(
            status=InstructionRule.Status.ACTIVE
        ).prefetch_related('conditions', 'actions', 'target_scopes').order_by('execution_order')

        for instruction in active_instructions:
            # Check validity period
            if not instruction.is_valid_now:
                continue

            # Check target scopes
            if not self._matches_scope(instruction, context):
                continue

            # Evaluate conditions
            evaluator = RuleEvaluator(instruction)
            result, evaluation_details = evaluator.evaluate(context)

            if result:
                # Instruction triggered!
                results['triggered_instructions'].append({
                    'instruction': instruction,
                    'code': instruction.code,
                    'title': instruction.title,
                    'priority': instruction.priority,
                    'type': instruction.instruction_type
                })

                # Execute actions
                stop_propagation = False
                for action in instruction.actions.all().order_by('order'):
                    executor = RuleActionExecutor(action, context, instruction)
                    action_result = executor.execute()

                    results['actions'].append({
                        'instruction_code': instruction.code,
                        'action': action,
                        'result': action_result
                    })

                    # Categorize action results
                    self._categorize_action_result(action_result, results)

                    if action.stop_propagation:
                        stop_propagation = True

                # Log execution
                self._log_execution(instruction, context, trigger_event, evaluation_details, results)

                # Increment trigger count
                instruction.increment_trigger()

                if stop_propagation:
                    break

        return results

    def _matches_scope(self, instruction, context):
        """Check if instruction applies to the given context based on target scopes"""
        scopes = list(instruction.target_scopes.all())

        if not scopes:
            # No scopes defined = applies to everything
            return True

        include_scopes = [s for s in scopes if s.scope_type == 'INCLUDE']
        exclude_scopes = [s for s in scopes if s.scope_type == 'EXCLUDE']

        # Check excludes first
        for scope in exclude_scopes:
            if self._scope_matches_context(scope, context):
                return False

        # If there are include scopes, at least one must match
        if include_scopes:
            return any(self._scope_matches_context(s, context) for s in include_scopes)

        return True

    def _scope_matches_context(self, scope, context):
        """Check if a single scope matches the context"""
        # Check if the ContentType is in context
        if scope.target_content_type.id not in context:
            return False

        obj = context[scope.target_content_type.id]

        # If specific object ID is set, check for exact match
        if scope.target_object_id:
            return obj.pk == scope.target_object_id

        # If field_filter is set, check filter conditions
        if scope.field_filter:
            try:
                model_class = scope.target_content_type.model_class()
                filtered = model_class.objects.filter(
                    pk=obj.pk,
                    **scope.field_filter
                ).exists()
                return filtered
            except:
                return False

        # ContentType matches and no specific restrictions
        return True

    def _categorize_action_result(self, action_result, results):
        """Categorize action results into appropriate buckets"""
        if action_result.get('prevented'):
            results['prevented'] = True
            results['prevention_reason'] = action_result.get('message', '')
            results['blocking_actions'].append(action_result)

        if action_result.get('requires_confirmation'):
            results['requires_confirmation'] = True

        if action_result.get('requires_approval'):
            results['requires_approval'] = True

        if action_result.get('requires_override'):
            results['requires_override'] = True

        if action_result.get('severity') == 'warning':
            results['warnings'].append(action_result)

        if action_result.get('email_sent') or action_result.get('notification_created'):
            results['notifications'].append(action_result)

        if action_result.get('field_to_set') or action_result.get('calculated_value'):
            results['field_modifications'].append(action_result)

    def _log_execution(self, instruction, context, trigger_event, evaluation_details, results):
        """Create audit log of instruction execution"""
        from floor_app.operations.knowledge.models import InstructionExecutionLog

        # Get trigger object info
        trigger_ct = None
        trigger_id = None

        # Use first object in context as trigger
        for ct_id, obj in context.items():
            if obj is not None:
                trigger_ct = ContentType.objects.get(id=ct_id)
                trigger_id = obj.pk
                break

        # Prepare action results for JSON storage
        actions_data = []
        for action_info in results['actions']:
            if action_info['instruction_code'] == instruction.code:
                actions_data.append({
                    'action_type': action_info['action'].action_type,
                    'result': action_info['result']
                })

        log = InstructionExecutionLog.objects.create(
            instruction=instruction,
            executed_by=self.user,
            trigger_content_type=trigger_ct,
            trigger_object_id=trigger_id,
            trigger_event=trigger_event,
            conditions_evaluated=evaluation_details,
            actions_executed=actions_data,
            ip_address=self.request.META.get('REMOTE_ADDR') if self.request else None,
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')[:500] if self.request else ''
        )

        return log

    def get_applicable_instructions(self, content_type, object_id=None):
        """
        Get all instructions that could apply to a specific model type/instance.
        Useful for displaying what rules might affect an object.
        """
        from floor_app.operations.knowledge.models import InstructionRule

        ct = ContentType.objects.get_for_model(content_type) if not isinstance(
            content_type, ContentType
        ) else content_type

        # Instructions with conditions or scopes targeting this ContentType
        instructions = InstructionRule.objects.filter(
            status=InstructionRule.Status.ACTIVE
        ).filter(
            models.Q(conditions__target_model=ct) |
            models.Q(target_scopes__target_content_type=ct)
        ).distinct()

        if object_id:
            # Filter to only those that could apply to specific instance
            instructions = instructions.filter(
                models.Q(target_scopes__target_object_id__isnull=True) |
                models.Q(target_scopes__target_object_id=object_id)
            )

        return instructions.order_by('execution_order')

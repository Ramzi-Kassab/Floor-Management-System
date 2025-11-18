"""
Automation Rule Engine Models

Data-driven rule system that monitors conditions and triggers actions.

NOT the same as "Technical Instructions" (which are procedural documents).
These are automation rules that:
- Watch data (inventory, job cards, workflow, etc.)
- Evaluate conditions
- Log when they fire
- Optionally trigger notifications or updates

Business Examples:
- "If cutter stock < BOM requirement, raise warning"
- "If job idle > 24h, flag delay"
- "If ENO reclaimed stock unused > 90 days, flag for review"
- "If bit in EVAL_QUEUE > 2x average time, bottleneck alert"
"""

from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from floor_app.mixins import AuditMixin, SoftDeleteMixin
import json


class AutomationRule(AuditMixin, SoftDeleteMixin):
    """
    Configurable automation rule.

    Defines:
    - What to watch (target model/domain)
    - What condition to check (JSON DSL)
    - What action to take (log, notify, update, etc.)
    - When to run (scheduled, event-driven, manual)
    """

    SCOPE_CHOICES = (
        ('INVENTORY', 'Inventory'),
        ('PRODUCTION', 'Production'),
        ('QUALITY', 'Quality'),
        ('PLANNING', 'Planning'),
        ('WORKFLOW', 'Workflow'),
        ('REQUIREMENTS', 'Requirements'),
        ('MAINTENANCE', 'Maintenance'),
        ('HR', 'HR'),
        ('FINANCE', 'Finance'),
        ('GENERIC', 'Generic / Cross-Domain'),
    )

    ACTION_TYPE_CHOICES = (
        ('LOG_ONLY', 'Log Only'),
        ('CREATE_ALERT', 'Create Alert'),
        ('SEND_NOTIFICATION', 'Send Notification'),
        ('UPDATE_FIELD', 'Update Field'),
        ('CREATE_TASK', 'Create Task'),
        ('RUN_SCRIPT', 'Run Custom Script'),
        ('WEBHOOK', 'Call Webhook'),
    )

    SEVERITY_CHOICES = (
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('CRITICAL', 'Critical'),
    )

    TRIGGER_MODE_CHOICES = (
        ('SCHEDULED', 'Scheduled (Cron)'),
        ('EVENT', 'Event-Driven'),
        ('MANUAL', 'Manual Only'),
    )

    # Identification
    name = models.CharField(
        max_length=200,
        unique=True,
        db_index=True,
        help_text="Unique rule name"
    )

    description = models.TextField(
        help_text="What this rule does and why"
    )

    rule_code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Unique code for programmatic reference"
    )

    # Scope and targeting
    rule_scope = models.CharField(
        max_length=20,
        choices=SCOPE_CHOICES,
        db_index=True,
        help_text="Domain this rule applies to"
    )

    target_model = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Django model path (e.g., 'production.JobCard', 'inventory.CutterDetail')"
    )

    # Condition definition (JSON DSL)
    condition_definition = models.JSONField(
        help_text="""
        JSON structure defining the condition.

        Examples:

        Simple threshold:
        {
            "type": "threshold",
            "field": "quantity_on_hand",
            "operator": "<",
            "value": 10
        }

        Time-based:
        {
            "type": "age",
            "field": "entered_at",
            "operator": ">",
            "value": 24,
            "unit": "hours"
        }

        Compound (AND/OR):
        {
            "type": "compound",
            "operator": "AND",
            "conditions": [
                {"type": "threshold", "field": "stock", "operator": "<", "value": 10},
                {"type": "age", "field": "last_usage", "operator": ">", "value": 90, "unit": "days"}
            ]
        }

        Queryset count:
        {
            "type": "queryset_count",
            "queryset": "CutterDetail.objects.filter(category='ENO_RECLAIMED')",
            "operator": ">",
            "value": 50
        }

        Field comparison:
        {
            "type": "field_comparison",
            "field1": "actual_quantity",
            "operator": "<",
            "field2": "required_quantity"
        }

        Custom eval (advanced - use with caution):
        {
            "type": "custom",
            "expression": "obj.time_in_stage_hours > (obj.stage.average_duration_hours * 1.5)"
        }
        """
    )

    # Action configuration
    action_type = models.CharField(
        max_length=20,
        choices=ACTION_TYPE_CHOICES,
        default='LOG_ONLY',
        help_text="What to do when rule fires"
    )

    action_config = models.JSONField(
        default=dict,
        blank=True,
        help_text="""
        Action-specific configuration.

        For SEND_NOTIFICATION:
        {
            "recipients": ["user@example.com"],
            "template": "notification_template_name",
            "channels": ["email", "in_app"]
        }

        For UPDATE_FIELD:
        {
            "field": "status",
            "value": "FLAGGED",
            "message": "Flagged by rule {rule_name}"
        }

        For CREATE_ALERT:
        {
            "alert_type": "BOTTLENECK",
            "priority": "HIGH",
            "auto_assign_to": "manager"
        }
        """
    )

    severity = models.CharField(
        max_length=10,
        choices=SEVERITY_CHOICES,
        default='WARNING',
        db_index=True,
        help_text="Severity level"
    )

    # Trigger configuration
    trigger_mode = models.CharField(
        max_length=20,
        choices=TRIGGER_MODE_CHOICES,
        default='SCHEDULED',
        help_text="How this rule is triggered"
    )

    schedule_cron = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Cron expression for scheduled rules (e.g., '0 */6 * * *' for every 6 hours)"
    )

    event_trigger = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Event name that triggers this rule (e.g., 'job_card_created', 'inventory_updated')"
    )

    # Control flags
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Rule is active and will be evaluated"
    )

    is_approved = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Rule has been reviewed and approved"
    )

    approved_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_rules',
        help_text="User who approved this rule"
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When rule was approved"
    )

    # Execution tracking
    last_run_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last time rule was evaluated"
    )

    last_status = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="Status of last execution (success, error, etc.)"
    )

    last_error = models.TextField(
        blank=True,
        default="",
        help_text="Error message from last failed execution"
    )

    total_executions = models.IntegerField(
        default=0,
        help_text="Total number of times evaluated"
    )

    total_triggers = models.IntegerField(
        default=0,
        help_text="Total number of times triggered (condition was true)"
    )

    # Rate limiting
    min_interval_seconds = models.IntegerField(
        default=0,
        help_text="Minimum seconds between executions (0 = no limit)"
    )

    max_triggers_per_day = models.IntegerField(
        null=True,
        blank=True,
        help_text="Max triggers per day (null = no limit)"
    )

    # Documentation
    notes = models.TextField(
        blank=True,
        default="",
        help_text="Additional notes about this rule"
    )

    tags = models.JSONField(
        default=list,
        blank=True,
        help_text="Tags for categorization"
    )

    class Meta:
        db_table = "analytics_automation_rule"
        verbose_name = "Automation Rule"
        verbose_name_plural = "Automation Rules"
        ordering = ['rule_scope', 'name']
        indexes = [
            models.Index(fields=['rule_scope', 'is_active'], name='ix_rule_scope_active'),
            models.Index(fields=['is_active'], name='ix_rule_active'),
            models.Index(fields=['trigger_mode'], name='ix_rule_trigger'),
        ]

    def __str__(self):
        return f"{self.rule_code} - {self.name}"

    def can_execute_now(self):
        """
        Check if rule can execute now based on rate limits.
        """
        if not self.is_active:
            return False, "Rule is not active"

        if not self.is_approved:
            return False, "Rule is not approved"

        # Check min interval
        if self.min_interval_seconds > 0 and self.last_run_at:
            elapsed = (timezone.now() - self.last_run_at).total_seconds()
            if elapsed < self.min_interval_seconds:
                return False, f"Min interval not met ({elapsed:.0f}s < {self.min_interval_seconds}s)"

        # Check daily trigger limit
        if self.max_triggers_per_day:
            from datetime import timedelta
            today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_triggers = self.executions.filter(
                executed_at__gte=today_start,
                was_triggered=True
            ).count()
            if today_triggers >= self.max_triggers_per_day:
                return False, f"Daily trigger limit reached ({today_triggers}/{self.max_triggers_per_day})"

        return True, "OK"

    def execute(self, target_object=None, context=None):
        """
        Execute this rule.

        Returns AutomationRuleExecution record.
        """
        from floor_app.operations.analytics.rule_engine.evaluator import RuleEvaluator

        # Check if can execute
        can_exec, reason = self.can_execute_now()
        if not can_exec:
            # Create execution record with skip status
            return AutomationRuleExecution.objects.create(
                rule=self,
                executed_at=timezone.now(),
                was_triggered=False,
                target_object=target_object,
                context_data={'skip_reason': reason},
                comment=f"Skipped: {reason}"
            )

        # Execute rule
        try:
            evaluator = RuleEvaluator(self)
            result = evaluator.evaluate(target_object=target_object, context=context)

            # Update rule stats
            self.last_run_at = timezone.now()
            self.last_status = 'success'
            self.last_error = ''
            self.total_executions += 1
            if result['triggered']:
                self.total_triggers += 1
            self.save(update_fields=[
                'last_run_at', 'last_status', 'last_error',
                'total_executions', 'total_triggers', 'updated_at'
            ])

            # Create execution record
            execution = AutomationRuleExecution.objects.create(
                rule=self,
                executed_at=timezone.now(),
                was_triggered=result['triggered'],
                target_object=target_object,
                context_data=result.get('context', {}),
                comment=result.get('comment', ''),
            )

            # Execute action if triggered
            if result['triggered'] and self.action_type != 'LOG_ONLY':
                execution.execute_action()

            return execution

        except Exception as e:
            # Record error
            self.last_run_at = timezone.now()
            self.last_status = 'error'
            self.last_error = str(e)
            self.total_executions += 1
            self.save(update_fields=[
                'last_run_at', 'last_status', 'last_error',
                'total_executions', 'updated_at'
            ])

            # Create error execution record
            return AutomationRuleExecution.objects.create(
                rule=self,
                executed_at=timezone.now(),
                was_triggered=False,
                context_data={'error': str(e)},
                comment=f"Error: {str(e)}"
            )

    def approve(self, user):
        """Approve this rule."""
        self.is_approved = True
        self.approved_by = user
        self.approved_at = timezone.now()
        self.save(update_fields=['is_approved', 'approved_by', 'approved_at', 'updated_at'])


class AutomationRuleExecution(models.Model):
    """
    Log of each time a rule was evaluated/executed.

    Provides:
    - Audit trail of rule activity
    - Analytics on rule effectiveness
    - Debugging information
    """

    # Which rule
    rule = models.ForeignKey(
        AutomationRule,
        on_delete=models.CASCADE,
        related_name='executions',
        help_text="Rule that was executed"
    )

    # When
    executed_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="When rule was evaluated"
    )

    # Result
    was_triggered = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Did the condition evaluate to true?"
    )

    # What it evaluated
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Type of target object"
    )

    object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="ID of target object"
    )

    target_object = GenericForeignKey('content_type', 'object_id')

    # Context and explanation
    context_data = models.JSONField(
        default=dict,
        help_text="""
        Context data that explains why rule fired (or didn't).

        Examples:
        {
            "current_stock": 5,
            "threshold": 10,
            "difference": -5,
            "evaluated_field": "quantity_on_hand"
        }

        {
            "time_in_stage_hours": 48.5,
            "average_duration_hours": 24.0,
            "ratio": 2.02,
            "stage": "EVAL_QUEUE"
        }
        """
    )

    comment = models.TextField(
        blank=True,
        default="",
        help_text="Human-readable explanation of what happened"
    )

    # Action execution
    action_executed = models.BooleanField(
        default=False,
        help_text="Was the action executed?"
    )

    action_result = models.JSONField(
        default=dict,
        blank=True,
        help_text="Result of action execution"
    )

    action_error = models.TextField(
        blank=True,
        default="",
        help_text="Error during action execution"
    )

    # Performance
    execution_duration_ms = models.IntegerField(
        null=True,
        blank=True,
        help_text="How long execution took (ms)"
    )

    # System tracking
    created_by_system = models.BooleanField(
        default=True,
        help_text="Created automatically by system (vs manual test)"
    )

    class Meta:
        db_table = "analytics_automation_rule_execution"
        verbose_name = "Rule Execution"
        verbose_name_plural = "Rule Executions"
        ordering = ['-executed_at']
        indexes = [
            models.Index(fields=['rule', 'executed_at'], name='ix_exec_rule_time'),
            models.Index(fields=['was_triggered', 'executed_at'], name='ix_exec_trig_time'),
            models.Index(fields=['executed_at'], name='ix_exec_time'),
        ]

    def __str__(self):
        status = "TRIGGERED" if self.was_triggered else "NO_TRIGGER"
        return f"{self.rule.rule_code} - {status} @ {self.executed_at.strftime('%Y-%m-%d %H:%M')}"

    def execute_action(self):
        """
        Execute the action defined in the rule.

        Called automatically when rule triggers (if action_type != LOG_ONLY).
        Can also be called manually for testing.
        """
        if self.action_executed:
            return  # Already executed

        try:
            from floor_app.operations.analytics.rule_engine.actions import ActionExecutor

            executor = ActionExecutor(self.rule, self)
            result = executor.execute()

            self.action_executed = True
            self.action_result = result
            self.save(update_fields=['action_executed', 'action_result'])

            return result

        except Exception as e:
            self.action_error = str(e)
            self.save(update_fields=['action_error'])
            raise


class RuleTemplate(AuditMixin):
    """
    Pre-configured rule templates for common scenarios.

    Users can create rules from templates with just parameter adjustments.
    """

    template_name = models.CharField(
        max_length=200,
        unique=True,
        help_text="Name of template"
    )

    description = models.TextField(
        help_text="What this template does"
    )

    rule_scope = models.CharField(
        max_length=20,
        choices=AutomationRule.SCOPE_CHOICES,
        help_text="Domain"
    )

    template_definition = models.JSONField(
        help_text="""
        Template structure with placeholders.

        Example:
        {
            "name": "Stock Alert: {item_name}",
            "target_model": "inventory.Item",
            "condition_definition": {
                "type": "threshold",
                "field": "quantity_on_hand",
                "operator": "<",
                "value": "{threshold}"
            },
            "parameters": {
                "item_name": {"type": "string", "required": true},
                "threshold": {"type": "integer", "default": 10, "required": true}
            }
        }
        """
    )

    usage_count = models.IntegerField(
        default=0,
        help_text="How many times this template has been used"
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Template is available for use"
    )

    class Meta:
        db_table = "analytics_rule_template"
        verbose_name = "Rule Template"
        verbose_name_plural = "Rule Templates"
        ordering = ['rule_scope', 'template_name']

    def __str__(self):
        return self.template_name

    def create_rule_from_template(self, parameters, created_by):
        """
        Create an AutomationRule instance from this template.

        parameters: dict of parameter values
        created_by: User who is creating the rule
        """
        import re

        definition = self.template_definition.copy()

        # Replace placeholders with actual values
        def replace_placeholders(obj):
            if isinstance(obj, str):
                # Replace {param_name} with actual value
                for key, value in parameters.items():
                    obj = obj.replace(f"{{{key}}}", str(value))
                return obj
            elif isinstance(obj, dict):
                return {k: replace_placeholders(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [replace_placeholders(item) for item in obj]
            else:
                return obj

        filled_definition = replace_placeholders(definition)

        # Create rule
        rule = AutomationRule.objects.create(
            name=filled_definition.get('name'),
            rule_code=filled_definition.get('rule_code', f"template_{self.id}_{timezone.now().timestamp()}"),
            description=self.description,
            rule_scope=self.rule_scope,
            target_model=filled_definition.get('target_model', ''),
            condition_definition=filled_definition.get('condition_definition'),
            action_type=filled_definition.get('action_type', 'LOG_ONLY'),
            action_config=filled_definition.get('action_config', {}),
            severity=filled_definition.get('severity', 'WARNING'),
            trigger_mode=filled_definition.get('trigger_mode', 'SCHEDULED'),
            is_active=False,  # Start inactive for review
            is_approved=False,
            created_by=created_by,
        )

        # Increment usage count
        self.usage_count += 1
        self.save(update_fields=['usage_count'])

        return rule

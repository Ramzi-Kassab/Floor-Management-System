"""
Instruction Rule Engine - The heart of the dynamic instructions system.
Allows users to define conditions on ANY model field and trigger various actions.
"""
from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from floor_app.mixins import AuditMixin, SoftDeleteMixin, PublicIdMixin
from .article import Article
from .document import Document


class InstructionRule(AuditMixin, SoftDeleteMixin, PublicIdMixin, models.Model):
    """
    A business rule/instruction that can be triggered based on conditions.

    Examples:
    - If bit SMI type is X and size is Y, then undercut gauge by Z
    - If serial is backloaded, notify supervisor
    - If customer is ARAMCO, apply special QC procedures
    - If operation is Grinding and material is certain type, use specific speed
    """

    class InstructionType(models.TextChoices):
        TECHNICAL = 'TECHNICAL', 'Technical'
        QUALITY = 'QUALITY', 'Quality Control'
        SAFETY = 'SAFETY', 'Safety'
        LOGISTICS = 'LOGISTICS', 'Logistics'
        COMMERCIAL = 'COMMERCIAL', 'Commercial'
        OPERATIONAL = 'OPERATIONAL', 'Operational'
        REGULATORY = 'REGULATORY', 'Regulatory/Compliance'
        MAINTENANCE = 'MAINTENANCE', 'Maintenance'

    class Priority(models.TextChoices):
        LOW = 'LOW', 'Low'
        NORMAL = 'NORMAL', 'Normal'
        HIGH = 'HIGH', 'High'
        CRITICAL = 'CRITICAL', 'Critical'
        MANDATORY = 'MANDATORY', 'Mandatory (Cannot Override)'

    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        IN_REVIEW = 'IN_REVIEW', 'In Review'
        APPROVED = 'APPROVED', 'Approved'
        ACTIVE = 'ACTIVE', 'Active'
        INACTIVE = 'INACTIVE', 'Inactive'
        ARCHIVED = 'ARCHIVED', 'Archived'

    # Core fields
    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique instruction code, e.g., 'INS-PRD-001'"
    )
    title = models.CharField(max_length=255)
    description = models.TextField(
        help_text="Detailed instruction text (supports HTML/Markdown)"
    )
    short_description = models.CharField(
        max_length=500,
        blank=True,
        help_text="Brief summary for quick display"
    )

    # Classification
    instruction_type = models.CharField(
        max_length=20,
        choices=InstructionType.choices,
        default=InstructionType.OPERATIONAL
    )
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.NORMAL
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )

    # Validity & Scope
    is_default = models.BooleanField(
        default=True,
        help_text="Default instruction (always applies) vs. temporary/special"
    )
    is_temporary = models.BooleanField(
        default=False,
        help_text="Temporary instruction with time limit"
    )
    valid_from = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When instruction becomes active"
    )
    valid_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When instruction expires (for temporary instructions)"
    )

    # Organization
    owner_department = models.ForeignKey(
        'hr.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='instruction_rules'
    )

    # Link to knowledge article (optional - instruction derived from procedure)
    source_article = models.ForeignKey(
        Article,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='derived_instructions',
        help_text="Knowledge article this instruction is based on"
    )

    # Attachments
    attachments = models.ManyToManyField(
        Document,
        blank=True,
        related_name='instructions',
        help_text="Supporting documents for this instruction"
    )

    # Approval workflow
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_instructions'
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    # Metrics
    trigger_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of times this instruction was triggered"
    )
    last_triggered_at = models.DateTimeField(null=True, blank=True)

    # Execution order
    execution_order = models.PositiveIntegerField(
        default=100,
        help_text="Order in which instructions are evaluated (lower = first)"
    )

    class Meta:
        verbose_name = 'Instruction Rule'
        verbose_name_plural = 'Instruction Rules'
        ordering = ['execution_order', '-priority', 'code']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['instruction_type', 'status']),
            models.Index(fields=['status', 'is_default']),
            models.Index(fields=['valid_from', 'valid_until']),
            models.Index(fields=['priority']),
            models.Index(fields=['execution_order']),
            models.Index(fields=['public_id']),
        ]
        permissions = [
            ('can_activate_instruction', 'Can activate instructions'),
            ('can_approve_instruction', 'Can approve instructions'),
        ]

    def __str__(self):
        return f"{self.code}: {self.title}"

    @property
    def is_valid_now(self):
        """Check if instruction is currently valid"""
        from django.utils import timezone
        now = timezone.now()
        if self.status != self.Status.ACTIVE:
            return False
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_until and now > self.valid_until:
            return False
        return True

    @property
    def days_until_expiry(self):
        """Days until this instruction expires"""
        if self.valid_until:
            from django.utils import timezone
            delta = self.valid_until - timezone.now()
            return max(0, delta.days)
        return None

    def increment_trigger(self):
        """Record that this instruction was triggered"""
        from django.utils import timezone
        self.trigger_count += 1
        self.last_triggered_at = timezone.now()
        self.save(update_fields=['trigger_count', 'last_triggered_at'])


class RuleCondition(models.Model):
    """
    A single condition in a rule. Multiple conditions form the "IF" part of the rule.

    This is the POWERFUL part: conditions can target ANY model and ANY field.
    Uses ContentType to reference any Django model dynamically.
    """

    class Operator(models.TextChoices):
        EQUALS = 'EQUALS', 'Equals (=)'
        NOT_EQUALS = 'NOT_EQUALS', 'Not Equals (!=)'
        GREATER_THAN = 'GREATER_THAN', 'Greater Than (>)'
        GREATER_EQUAL = 'GREATER_EQUAL', 'Greater Than or Equal (>=)'
        LESS_THAN = 'LESS_THAN', 'Less Than (<)'
        LESS_EQUAL = 'LESS_EQUAL', 'Less Than or Equal (<=)'
        CONTAINS = 'CONTAINS', 'Contains'
        NOT_CONTAINS = 'NOT_CONTAINS', 'Does Not Contain'
        STARTS_WITH = 'STARTS_WITH', 'Starts With'
        ENDS_WITH = 'ENDS_WITH', 'Ends With'
        IN_LIST = 'IN_LIST', 'In List'
        NOT_IN_LIST = 'NOT_IN_LIST', 'Not In List'
        IS_NULL = 'IS_NULL', 'Is Null/Empty'
        IS_NOT_NULL = 'IS_NOT_NULL', 'Is Not Null/Empty'
        REGEX = 'REGEX', 'Matches Regex'
        BETWEEN = 'BETWEEN', 'Between'

    class LogicalOperator(models.TextChoices):
        AND = 'AND', 'AND'
        OR = 'OR', 'OR'

    instruction = models.ForeignKey(
        InstructionRule,
        on_delete=models.CASCADE,
        related_name='conditions'
    )

    # Target model (using ContentType for maximum flexibility)
    target_model = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        help_text="The Django model to check (e.g., BitDesign, JobCard, Employee)"
    )

    # Field path (supports nested fields like 'customer__name' or 'bit_design__smi_type')
    field_path = models.CharField(
        max_length=255,
        help_text="Field to evaluate (supports nested: 'customer__region__name')"
    )

    # Operator and value
    operator = models.CharField(
        max_length=20,
        choices=Operator.choices,
        default=Operator.EQUALS
    )

    # Value to compare against (stored as JSON string for flexibility)
    value = models.TextField(
        help_text="Value to compare against (JSON format for complex values)"
    )

    # For BETWEEN operator
    value_max = models.TextField(
        blank=True,
        help_text="Maximum value for BETWEEN operator"
    )

    # Logical connection to next condition
    logical_operator = models.CharField(
        max_length=5,
        choices=LogicalOperator.choices,
        default=LogicalOperator.AND,
        help_text="How this condition connects to the next one"
    )

    # Grouping for complex conditions: (A AND B) OR (C AND D)
    condition_group = models.PositiveIntegerField(
        default=0,
        help_text="Group number for parenthetical grouping"
    )

    # Order within the rule
    order = models.PositiveIntegerField(default=0)

    # Case sensitivity
    case_sensitive = models.BooleanField(
        default=False,
        help_text="Case-sensitive comparison for strings"
    )

    class Meta:
        verbose_name = 'Rule Condition'
        verbose_name_plural = 'Rule Conditions'
        ordering = ['condition_group', 'order']
        indexes = [
            models.Index(fields=['instruction', 'order']),
            models.Index(fields=['target_model', 'field_path']),
        ]

    def __str__(self):
        return f"{self.target_model.model}.{self.field_path} {self.operator} {self.value}"

    def evaluate(self, context):
        """
        Evaluate this condition against provided context.
        Context is a dict mapping ContentType IDs to model instances or querysets.

        Returns: Boolean
        """
        import json
        from django.db.models import Q

        # Get the object(s) to evaluate
        model_instance = context.get(self.target_model.id)
        if model_instance is None:
            return False

        # Navigate the field path
        field_value = self._get_field_value(model_instance, self.field_path)

        # Parse the comparison value
        try:
            compare_value = json.loads(self.value)
        except (json.JSONDecodeError, TypeError):
            compare_value = self.value

        # Apply operator
        return self._apply_operator(field_value, compare_value)

    def _get_field_value(self, obj, field_path):
        """Navigate nested field path to get value"""
        parts = field_path.split('__')
        value = obj
        for part in parts:
            if value is None:
                return None
            if hasattr(value, part):
                value = getattr(value, part)
                # Handle callable (methods/properties)
                if callable(value):
                    value = value()
            elif isinstance(value, dict):
                value = value.get(part)
            else:
                return None
        return value

    def _apply_operator(self, field_value, compare_value):
        """Apply the comparison operator"""
        import json

        # Handle case sensitivity for strings
        if isinstance(field_value, str) and isinstance(compare_value, str):
            if not self.case_sensitive:
                field_value = field_value.lower()
                compare_value = compare_value.lower()

        if self.operator == self.Operator.EQUALS:
            return field_value == compare_value
        elif self.operator == self.Operator.NOT_EQUALS:
            return field_value != compare_value
        elif self.operator == self.Operator.GREATER_THAN:
            return field_value > compare_value
        elif self.operator == self.Operator.GREATER_EQUAL:
            return field_value >= compare_value
        elif self.operator == self.Operator.LESS_THAN:
            return field_value < compare_value
        elif self.operator == self.Operator.LESS_EQUAL:
            return field_value <= compare_value
        elif self.operator == self.Operator.CONTAINS:
            return compare_value in str(field_value)
        elif self.operator == self.Operator.NOT_CONTAINS:
            return compare_value not in str(field_value)
        elif self.operator == self.Operator.STARTS_WITH:
            return str(field_value).startswith(str(compare_value))
        elif self.operator == self.Operator.ENDS_WITH:
            return str(field_value).endswith(str(compare_value))
        elif self.operator == self.Operator.IN_LIST:
            if isinstance(compare_value, str):
                compare_value = [v.strip() for v in compare_value.split(',')]
            return field_value in compare_value
        elif self.operator == self.Operator.NOT_IN_LIST:
            if isinstance(compare_value, str):
                compare_value = [v.strip() for v in compare_value.split(',')]
            return field_value not in compare_value
        elif self.operator == self.Operator.IS_NULL:
            return field_value is None or field_value == ''
        elif self.operator == self.Operator.IS_NOT_NULL:
            return field_value is not None and field_value != ''
        elif self.operator == self.Operator.REGEX:
            import re
            pattern = re.compile(compare_value)
            return bool(pattern.search(str(field_value)))
        elif self.operator == self.Operator.BETWEEN:
            try:
                max_value = json.loads(self.value_max)
            except (json.JSONDecodeError, TypeError):
                max_value = self.value_max
            return compare_value <= field_value <= max_value

        return False


class RuleAction(models.Model):
    """
    Action to perform when instruction conditions are met.
    This is what makes instructions CONTROL the system, not just display text.
    """

    class ActionType(models.TextChoices):
        # Display actions
        SHOW_MESSAGE = 'SHOW_MESSAGE', 'Show Message/Alert'
        SHOW_WARNING = 'SHOW_WARNING', 'Show Warning'
        SHOW_ERROR = 'SHOW_ERROR', 'Show Error (Blocking)'
        SHOW_INFO = 'SHOW_INFO', 'Show Information'

        # Control actions
        PREVENT_ACTION = 'PREVENT_ACTION', 'Prevent/Block Action'
        REQUIRE_CONFIRMATION = 'REQUIRE_CONFIRMATION', 'Require Confirmation'
        REQUIRE_APPROVAL = 'REQUIRE_APPROVAL', 'Require Approval'
        REQUIRE_OVERRIDE = 'REQUIRE_OVERRIDE', 'Require Manager Override'

        # Notification actions
        SEND_EMAIL = 'SEND_EMAIL', 'Send Email Notification'
        SEND_SMS = 'SEND_SMS', 'Send SMS'
        CREATE_NOTIFICATION = 'CREATE_NOTIFICATION', 'Create System Notification'

        # Data modification actions
        SET_FIELD_VALUE = 'SET_FIELD_VALUE', 'Set Field Value'
        CALCULATE_VALUE = 'CALCULATE_VALUE', 'Calculate/Auto-fill Value'
        INCREMENT_COUNTER = 'INCREMENT_COUNTER', 'Increment Counter'

        # Workflow actions
        CHANGE_STATUS = 'CHANGE_STATUS', 'Change Status'
        ASSIGN_TO_USER = 'ASSIGN_TO_USER', 'Assign to User'
        CREATE_TASK = 'CREATE_TASK', 'Create Task/Work Order'
        ADD_TO_QUEUE = 'ADD_TO_QUEUE', 'Add to Queue'

        # Validation actions
        VALIDATE_FIELD = 'VALIDATE_FIELD', 'Validate Field'
        ENFORCE_MINIMUM = 'ENFORCE_MINIMUM', 'Enforce Minimum Value'
        ENFORCE_MAXIMUM = 'ENFORCE_MAXIMUM', 'Enforce Maximum Value'
        ENFORCE_PATTERN = 'ENFORCE_PATTERN', 'Enforce Pattern/Format'

        # Logging actions
        LOG_AUDIT = 'LOG_AUDIT', 'Create Audit Log'
        LOG_CUSTOM = 'LOG_CUSTOM', 'Log Custom Event'

        # UI actions
        HIGHLIGHT_FIELD = 'HIGHLIGHT_FIELD', 'Highlight Field'
        DISABLE_FIELD = 'DISABLE_FIELD', 'Disable Field'
        HIDE_FIELD = 'HIDE_FIELD', 'Hide Field'
        SHOW_FIELD = 'SHOW_FIELD', 'Show Hidden Field'

        # External actions
        CALL_WEBHOOK = 'CALL_WEBHOOK', 'Call External Webhook'
        CALL_API = 'CALL_API', 'Call External API'

    instruction = models.ForeignKey(
        InstructionRule,
        on_delete=models.CASCADE,
        related_name='actions'
    )

    action_type = models.CharField(
        max_length=30,
        choices=ActionType.choices,
        default=ActionType.SHOW_MESSAGE
    )

    # Action parameters (JSON for flexibility)
    parameters = models.JSONField(
        default=dict,
        help_text="Action-specific parameters in JSON format"
    )

    # Message template (supports placeholders like {field_name})
    message_template = models.TextField(
        blank=True,
        help_text="Message to display (supports {placeholders})"
    )

    # Target for SET_FIELD_VALUE, etc.
    target_field = models.CharField(
        max_length=255,
        blank=True,
        help_text="Target field path for data modification actions"
    )

    # Value or formula for calculations
    value_expression = models.TextField(
        blank=True,
        help_text="Value or formula for calculations (supports Python expressions)"
    )

    # Recipients for notifications
    notify_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='instruction_notifications',
        help_text="Users to notify"
    )
    notify_roles = models.ManyToManyField(
        'hr.Position',
        blank=True,
        related_name='instruction_notifications',
        help_text="Positions/roles to notify"
    )
    notify_departments = models.ManyToManyField(
        'hr.Department',
        blank=True,
        related_name='instruction_notifications',
        help_text="Departments to notify"
    )

    # Severity/styling
    severity = models.CharField(
        max_length=20,
        default='info',
        help_text="Visual severity: info, warning, danger, success"
    )

    # Order of execution
    order = models.PositiveIntegerField(default=0)

    # Stop further processing after this action
    stop_propagation = models.BooleanField(
        default=False,
        help_text="Stop evaluating further rules after this action"
    )

    class Meta:
        verbose_name = 'Rule Action'
        verbose_name_plural = 'Rule Actions'
        ordering = ['order']
        indexes = [
            models.Index(fields=['instruction', 'order']),
            models.Index(fields=['action_type']),
        ]

    def __str__(self):
        return f"{self.instruction.code} -> {self.get_action_type_display()}"

    def execute(self, context, instruction_instance):
        """
        Execute this action.
        Returns a dict with action results.
        """
        from .services import RuleActionExecutor
        executor = RuleActionExecutor(self, context, instruction_instance)
        return executor.execute()


class InstructionTargetScope(models.Model):
    """
    Define what entities an instruction applies to.
    Uses GenericForeignKey to target ANY model in the system.

    This allows instructions to be scoped to:
    - Specific customer
    - Specific bit design
    - Specific serial number
    - Specific operation type
    - Specific department
    - etc.
    """

    class ScopeType(models.TextChoices):
        INCLUDE = 'INCLUDE', 'Include (applies to)'
        EXCLUDE = 'EXCLUDE', 'Exclude (does not apply to)'

    instruction = models.ForeignKey(
        InstructionRule,
        on_delete=models.CASCADE,
        related_name='target_scopes'
    )

    scope_type = models.CharField(
        max_length=10,
        choices=ScopeType.choices,
        default=ScopeType.INCLUDE
    )

    # Generic target (can be any model)
    target_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        help_text="Type of entity this scope applies to"
    )
    target_object_id = models.PositiveBigIntegerField(
        null=True,
        blank=True,
        help_text="Specific object ID (null = all of this type)"
    )
    target = GenericForeignKey('target_content_type', 'target_object_id')

    # Optional: field-based filter instead of specific object
    field_filter = models.JSONField(
        null=True,
        blank=True,
        help_text="Django ORM filter dict, e.g., {'customer__region': 'MENA'}"
    )

    # Description for clarity
    description = models.CharField(
        max_length=255,
        blank=True,
        help_text="Human-readable scope description"
    )

    # Applies to new items only
    applies_to_new_only = models.BooleanField(
        default=False,
        help_text="Only apply to newly created items"
    )

    class Meta:
        verbose_name = 'Instruction Target Scope'
        verbose_name_plural = 'Instruction Target Scopes'
        indexes = [
            models.Index(fields=['instruction', 'scope_type']),
            models.Index(fields=['target_content_type', 'target_object_id']),
        ]

    def __str__(self):
        if self.target_object_id:
            return f"{self.instruction.code} {self.scope_type} {self.target}"
        return f"{self.instruction.code} {self.scope_type} all {self.target_content_type.model}"


class InstructionExecutionLog(models.Model):
    """
    Audit trail of instruction executions.
    Records when instructions are triggered, what actions were taken, and results.
    """
    instruction = models.ForeignKey(
        InstructionRule,
        on_delete=models.CASCADE,
        related_name='execution_logs'
    )
    executed_at = models.DateTimeField(auto_now_add=True)
    executed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # Context that triggered the instruction
    trigger_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    trigger_object_id = models.PositiveBigIntegerField(null=True, blank=True)
    trigger_object = GenericForeignKey('trigger_content_type', 'trigger_object_id')

    # What triggered it
    trigger_event = models.CharField(
        max_length=100,
        help_text="Event that triggered the instruction, e.g., 'save', 'view', 'approve'"
    )

    # Results
    conditions_evaluated = models.JSONField(
        default=dict,
        help_text="Condition evaluation results"
    )
    actions_executed = models.JSONField(
        default=list,
        help_text="List of actions executed and their results"
    )
    was_overridden = models.BooleanField(
        default=False,
        help_text="Was the instruction overridden by user/manager"
    )
    override_reason = models.TextField(
        blank=True,
        help_text="Reason for override if applicable"
    )
    override_approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='knowledge_instruction_overrides'
    )

    # Request info
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)

    class Meta:
        verbose_name = 'Instruction Execution Log'
        verbose_name_plural = 'Instruction Execution Logs'
        ordering = ['-executed_at']
        indexes = [
            models.Index(fields=['instruction', 'executed_at']),
            models.Index(fields=['executed_at']),
            models.Index(fields=['trigger_content_type', 'trigger_object_id']),
        ]

    def __str__(self):
        return f"{self.instruction.code} executed at {self.executed_at}"

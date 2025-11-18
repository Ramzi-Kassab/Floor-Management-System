"""
Job Requirements & Prerequisites System

Tracks what's needed to complete a job, including:
- Data requirements (design specs, customer data, etc.)
- Document requirements (permits, drawings, QC forms, etc.)
- Material/Item requirements (from BOM, consumables, etc.)
- Instruction requirements (technical procedures, work instructions)
- Approval requirements (customer sign-off, engineering approval, etc.)
- Tool/Equipment requirements (special tools, fixtures, etc.)

Features:
- Template-based auto-population for common job types
- Dependency tracking (Requirement B depends on Requirement A)
- Blocking vs non-blocking requirements
- Status tracking per requirement
- Checklist-style interface
"""

from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from floor_app.mixins import AuditMixin, SoftDeleteMixin, PublicIdMixin


class RequirementCategory(models.Model):
    """
    High-level categorization of requirements.

    Examples:
    - DATA: Design data, customer specifications, historical data
    - DOCUMENT: Permits, drawings, certifications, QC forms
    - MATERIAL: Items from BOM, consumables, spare parts
    - INSTRUCTION: Technical procedures, work instructions, standards
    - APPROVAL: Customer sign-off, engineering approval, management approval
    - TOOL_EQUIPMENT: Special tools, fixtures, test equipment
    - INSPECTION: NDT, thread inspection, pressure test
    - PERSONNEL: Certified operators, specific skill requirements
    """

    CATEGORY_TYPE_CHOICES = (
        ('DATA', 'Data/Information'),
        ('DOCUMENT', 'Document/Form'),
        ('MATERIAL', 'Material/Item'),
        ('INSTRUCTION', 'Instruction/Procedure'),
        ('APPROVAL', 'Approval/Sign-off'),
        ('TOOL_EQUIPMENT', 'Tool/Equipment'),
        ('INSPECTION', 'Inspection/Test'),
        ('PERSONNEL', 'Personnel/Skill'),
        ('OTHER', 'Other'),
    )

    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Category code (e.g., DATA, DOCUMENT, MATERIAL)"
    )
    name = models.CharField(
        max_length=100,
        help_text="Display name"
    )
    category_type = models.CharField(
        max_length=20,
        choices=CATEGORY_TYPE_CHOICES,
        default='OTHER'
    )
    description = models.TextField(blank=True, default="")
    icon = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="Icon class for UI (e.g., 'bi-file-earmark-text')"
    )
    color = models.CharField(
        max_length=20,
        blank=True,
        default="",
        help_text="Color for UI badges (e.g., 'primary', 'success', 'warning')"
    )
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "planning_requirement_category"
        verbose_name = "Requirement Category"
        verbose_name_plural = "Requirement Categories"
        ordering = ['sort_order', 'name']

    def __str__(self):
        return f"{self.code} - {self.name}"


class RequirementTemplate(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Template for requirements that can be auto-applied to job cards.

    Templates can be linked to:
    - Job types (REPAIR, RETROFIT, NEW_PRODUCTION, etc.)
    - MAT designs (specific MAT numbers)
    - Customers (customer-specific requirements)
    - Bit sizes (size-specific requirements)

    When a job card is created, matching templates are used to auto-populate
    JobRequirement records.
    """

    name = models.CharField(
        max_length=200,
        help_text="Template name (e.g., 'Standard Repair Requirements')"
    )
    description = models.TextField(
        blank=True,
        default="",
        help_text="Detailed description of this requirement template"
    )

    category = models.ForeignKey(
        RequirementCategory,
        on_delete=models.PROTECT,
        related_name='templates',
        help_text="Requirement category"
    )

    # Template applicability filters
    applies_to_job_types = models.JSONField(
        default=list,
        blank=True,
        help_text="List of job types this applies to (e.g., ['REPAIR', 'RETROFIT']). Empty = all types."
    )
    applies_to_customers = models.JSONField(
        default=list,
        blank=True,
        help_text="List of customer codes this applies to. Empty = all customers."
    )
    applies_to_mat_levels = models.JSONField(
        default=list,
        blank=True,
        help_text="List of MAT levels this applies to (e.g., ['L3', 'L4', 'L5']). Empty = all levels."
    )
    applies_to_bit_sizes = models.JSONField(
        default=list,
        blank=True,
        help_text="List of bit sizes this applies to (e.g., ['8.5', '12.25']). Empty = all sizes."
    )

    # Requirement details
    requirement_text = models.TextField(
        help_text="Full requirement description (what needs to be done/provided)"
    )

    is_blocking = models.BooleanField(
        default=False,
        help_text="If True, job cannot proceed until this requirement is met"
    )

    is_mandatory = models.BooleanField(
        default=True,
        help_text="If False, requirement is optional/recommended but not required"
    )

    # Links to related objects (optional)
    linked_item = models.ForeignKey(
        'inventory.Item',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='requirement_templates',
        help_text="For MATERIAL requirements: link to specific item"
    )

    linked_document_type = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="For DOCUMENT requirements: document type (e.g., 'Drawing', 'Permit')"
    )

    linked_instruction = models.ForeignKey(
        'TechnicalInstruction',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='requirement_templates',
        help_text="For INSTRUCTION requirements: link to technical instruction"
    )

    # Auto-completion logic
    auto_complete_trigger = models.CharField(
        max_length=50,
        blank=True,
        default="",
        choices=(
            ('', 'Manual Only'),
            ('BOM_AVAILABLE', 'BOM Available'),
            ('EVALUATION_COMPLETE', 'Evaluation Complete'),
            ('ROUTING_COMPLETE', 'Routing Complete'),
            ('QC_APPROVED', 'QC Approved'),
            ('CUSTOMER_APPROVAL', 'Customer Approval'),
        ),
        help_text="If set, requirement auto-completes when trigger condition is met"
    )

    # Expected timeline
    expected_days_from_start = models.IntegerField(
        null=True,
        blank=True,
        help_text="Expected days from job start to complete this requirement"
    )

    # Dependencies
    depends_on_templates = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        related_name='dependent_templates',
        help_text="Other requirement templates that must be completed first"
    )

    # Display
    sort_order = models.IntegerField(
        default=0,
        help_text="Display order in requirements list"
    )
    is_active = models.BooleanField(default=True)

    # Additional metadata
    notes = models.TextField(
        blank=True,
        default="",
        help_text="Internal notes about this requirement template"
    )

    class Meta:
        db_table = "planning_requirement_template"
        verbose_name = "Requirement Template"
        verbose_name_plural = "Requirement Templates"
        ordering = ['category', 'sort_order', 'name']
        indexes = [
            models.Index(fields=['category', 'is_active'], name='ix_rt_cat_active'),
        ]

    def __str__(self):
        return f"{self.category.code}: {self.name}"

    def applies_to_job_card(self, job_card):
        """
        Check if this template applies to a given job card.

        Args:
            job_card: JobCard instance

        Returns:
            bool: True if template should be applied to this job card
        """
        # Check job type
        if self.applies_to_job_types and job_card.job_type not in self.applies_to_job_types:
            return False

        # Check customer
        if self.applies_to_customers and job_card.customer_name not in self.applies_to_customers:
            return False

        # Check MAT level
        if self.applies_to_mat_levels and job_card.current_mat:
            if job_card.current_mat.level.code not in self.applies_to_mat_levels:
                return False

        # Check bit size
        if self.applies_to_bit_sizes and job_card.bit_size not in self.applies_to_bit_sizes:
            return False

        return True


class JobRequirement(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Actual requirement instance for a specific job card.

    Created from RequirementTemplate or manually added by users.
    Tracks status, completion, and dependencies.
    """

    STATUS_CHOICES = (
        ('NOT_STARTED', 'Not Started'),
        ('IN_PROGRESS', 'In Progress'),
        ('WAITING_DEPENDENCY', 'Waiting on Dependency'),
        ('BLOCKED', 'Blocked'),
        ('COMPLETED', 'Completed'),
        ('WAIVED', 'Waived/N/A'),
        ('FAILED', 'Failed/Rejected'),
    )

    job_card = models.ForeignKey(
        'production.JobCard',
        on_delete=models.CASCADE,
        related_name='requirements',
        help_text="Job card this requirement belongs to"
    )

    template = models.ForeignKey(
        RequirementTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='instances',
        help_text="Template this was created from (null if manually added)"
    )

    category = models.ForeignKey(
        RequirementCategory,
        on_delete=models.PROTECT,
        related_name='job_requirements',
        help_text="Requirement category"
    )

    # Requirement details
    requirement_text = models.TextField(
        help_text="Full requirement description"
    )

    is_blocking = models.BooleanField(
        default=False,
        help_text="If True, job cannot proceed until this requirement is met"
    )

    is_mandatory = models.BooleanField(
        default=True,
        help_text="If False, requirement is optional"
    )

    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='NOT_STARTED',
        db_index=True
    )

    started_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When requirement work started"
    )
    started_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='requirements_started',
        help_text="User who started working on this requirement"
    )

    completed_date = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="When requirement was completed"
    )
    completed_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='requirements_completed',
        help_text="User who completed this requirement"
    )

    verified_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When requirement completion was verified"
    )
    verified_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='requirements_verified',
        help_text="User who verified completion"
    )

    # Waiver tracking (for optional/waived requirements)
    waived_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When requirement was waived"
    )
    waived_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='requirements_waived',
        help_text="User who waived this requirement"
    )
    waiver_reason = models.TextField(
        blank=True,
        default="",
        help_text="Reason for waiving requirement"
    )

    # Links to actual artifacts (populated when requirement is met)
    linked_item = models.ForeignKey(
        'inventory.Item',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='job_requirements',
        help_text="For MATERIAL: actual item that satisfies requirement"
    )

    linked_document_path = models.CharField(
        max_length=500,
        blank=True,
        default="",
        help_text="For DOCUMENT: path to uploaded document file"
    )

    linked_instruction = models.ForeignKey(
        'TechnicalInstruction',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='job_requirements',
        help_text="For INSTRUCTION: technical instruction followed"
    )

    # Dependencies
    depends_on = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        related_name='dependent_requirements',
        help_text="Other requirements that must be completed first"
    )

    # Blocking information
    blocked_reason = models.TextField(
        blank=True,
        default="",
        help_text="If status=BLOCKED, why is it blocked?"
    )
    blocked_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When requirement became blocked"
    )

    # Timeline
    expected_completion_date = models.DateField(
        null=True,
        blank=True,
        help_text="Expected date to complete this requirement"
    )

    # Notes
    notes = models.TextField(
        blank=True,
        default="",
        help_text="Additional notes about this requirement"
    )

    # Display
    sort_order = models.IntegerField(
        default=0,
        help_text="Display order in requirements list"
    )

    class Meta:
        db_table = "planning_job_requirement"
        verbose_name = "Job Requirement"
        verbose_name_plural = "Job Requirements"
        ordering = ['job_card', 'sort_order', 'category', 'created_at']
        indexes = [
            models.Index(fields=['job_card', 'status'], name='ix_jr_job_status'),
            models.Index(fields=['status', 'is_blocking'], name='ix_jr_status_block'),
            models.Index(fields=['completed_date'], name='ix_jr_completed'),
        ]

    def __str__(self):
        return f"{self.job_card.job_card_number}: {self.category.code} - {self.requirement_text[:50]}"

    def clean(self):
        """Validation logic."""
        super().clean()

        # If status is COMPLETED, must have completed_date and completed_by
        if self.status == 'COMPLETED' and not self.completed_date:
            raise ValidationError("Completed requirements must have completed_date")

        # If status is WAIVED, must have waiver info
        if self.status == 'WAIVED' and not self.waived_date:
            raise ValidationError("Waived requirements must have waived_date and waiver_reason")

    def mark_started(self, user=None):
        """Mark requirement as started."""
        self.status = 'IN_PROGRESS'
        self.started_date = timezone.now()
        self.started_by = user
        self.save(update_fields=['status', 'started_date', 'started_by', 'updated_at'])

    def mark_completed(self, user=None):
        """Mark requirement as completed."""
        self.status = 'COMPLETED'
        self.completed_date = timezone.now()
        self.completed_by = user
        self.save(update_fields=['status', 'completed_date', 'completed_by', 'updated_at'])

    def mark_verified(self, user=None):
        """Mark requirement completion as verified."""
        if self.status != 'COMPLETED':
            raise ValidationError("Can only verify completed requirements")

        self.verified_date = timezone.now()
        self.verified_by = user
        self.save(update_fields=['verified_date', 'verified_by', 'updated_at'])

    def waive(self, reason, user=None):
        """Waive this requirement."""
        self.status = 'WAIVED'
        self.waived_date = timezone.now()
        self.waived_by = user
        self.waiver_reason = reason
        self.save(update_fields=['status', 'waived_date', 'waived_by', 'waiver_reason', 'updated_at'])

    def mark_blocked(self, reason):
        """Mark requirement as blocked."""
        self.status = 'BLOCKED'
        self.blocked_date = timezone.now()
        self.blocked_reason = reason
        self.save(update_fields=['status', 'blocked_date', 'blocked_reason', 'updated_at'])

    def check_dependencies_met(self):
        """
        Check if all dependencies are completed.

        Returns:
            bool: True if all dependencies are met
        """
        return not self.depends_on.exclude(
            status__in=['COMPLETED', 'WAIVED']
        ).exists()

    def get_pending_dependencies(self):
        """Get list of dependencies that are not yet completed."""
        return self.depends_on.exclude(
            status__in=['COMPLETED', 'WAIVED']
        )

    @property
    def is_overdue(self):
        """Check if requirement is overdue."""
        if not self.expected_completion_date:
            return False

        if self.status in ['COMPLETED', 'WAIVED']:
            return False

        from datetime import date
        return self.expected_completion_date < date.today()

    @classmethod
    def create_from_template(cls, job_card, template):
        """
        Create a JobRequirement instance from a RequirementTemplate.

        Args:
            job_card: JobCard instance
            template: RequirementTemplate instance

        Returns:
            JobRequirement instance
        """
        from datetime import timedelta

        # Calculate expected completion date
        expected_date = None
        if template.expected_days_from_start and job_card.date_created:
            expected_date = job_card.date_created.date() + timedelta(days=template.expected_days_from_start)

        # Create requirement
        requirement = cls.objects.create(
            job_card=job_card,
            template=template,
            category=template.category,
            requirement_text=template.requirement_text,
            is_blocking=template.is_blocking,
            is_mandatory=template.is_mandatory,
            linked_item=template.linked_item,
            linked_instruction=template.linked_instruction,
            expected_completion_date=expected_date,
            sort_order=template.sort_order,
        )

        return requirement

    @classmethod
    def auto_populate_for_job_card(cls, job_card):
        """
        Auto-populate requirements for a job card based on applicable templates.

        Args:
            job_card: JobCard instance

        Returns:
            list: Created JobRequirement instances
        """
        templates = RequirementTemplate.objects.filter(is_active=True)
        created_requirements = []

        for template in templates:
            if template.applies_to_job_card(job_card):
                req = cls.create_from_template(job_card, template)
                created_requirements.append(req)

        # Set up dependencies
        for req in created_requirements:
            if req.template and req.template.depends_on_templates.exists():
                # Find corresponding requirement instances
                for dep_template in req.template.depends_on_templates.all():
                    dep_req = next(
                        (r for r in created_requirements if r.template == dep_template),
                        None
                    )
                    if dep_req:
                        req.depends_on.add(dep_req)

        return created_requirements


class TechnicalInstruction(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Technical instructions and procedures for specific operations.

    Can be linked to:
    - Serial numbers (bit-specific)
    - MAT numbers (design-specific)
    - Bit types (type-specific)
    - Customers (customer-specific procedures)
    - Operations (operation-specific work instructions)

    Displayed in:
    - Evaluation page sidebar
    - Job requirement details
    - Routing step instructions
    """

    APPLIES_TO_CHOICES = (
        ('SERIAL_NUMBER', 'Specific Serial Number'),
        ('MAT_NUMBER', 'Specific MAT Number'),
        ('BIT_TYPE', 'Bit Type Family'),
        ('CUSTOMER', 'Customer'),
        ('OPERATION', 'Operation/Process'),
        ('ALL', 'All Jobs'),
    )

    title = models.CharField(
        max_length=200,
        help_text="Instruction title"
    )

    applies_to_type = models.CharField(
        max_length=20,
        choices=APPLIES_TO_CHOICES,
        default='ALL',
        db_index=True,
        help_text="What type of jobs this instruction applies to"
    )

    applies_to_value = models.CharField(
        max_length=200,
        blank=True,
        default="",
        db_index=True,
        help_text="Specific value (SN, MAT#, customer name, operation code, etc.)"
    )

    instruction_text = models.TextField(
        help_text="Full instruction text (supports markdown)"
    )

    # Priority for display when multiple instructions match
    priority = models.IntegerField(
        default=0,
        help_text="Lower number = higher priority (displayed first)"
    )

    # Categorization
    category = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Instruction category (Safety, Quality, Process, etc.)"
    )

    # Links
    document_path = models.CharField(
        max_length=500,
        blank=True,
        default="",
        help_text="Path to PDF or document file"
    )

    external_url = models.URLField(
        blank=True,
        default="",
        help_text="External URL for additional resources"
    )

    # Flags
    is_critical = models.BooleanField(
        default=False,
        help_text="Mark as critical safety or quality instruction"
    )

    requires_acknowledgement = models.BooleanField(
        default=False,
        help_text="Operator must acknowledge reading this instruction"
    )

    is_active = models.BooleanField(default=True, db_index=True)

    # Versioning
    version = models.CharField(
        max_length=20,
        default="1.0",
        help_text="Instruction version number"
    )
    effective_date = models.DateField(
        default=timezone.now,
        help_text="Date when this version becomes effective"
    )

    # Metadata
    tags = models.JSONField(
        default=list,
        blank=True,
        help_text="Tags for searching/filtering (e.g., ['welding', 'safety', 'aramco'])"
    )

    notes = models.TextField(blank=True, default="")

    class Meta:
        db_table = "planning_technical_instruction"
        verbose_name = "Technical Instruction"
        verbose_name_plural = "Technical Instructions"
        ordering = ['applies_to_type', 'priority', 'title']
        indexes = [
            models.Index(fields=['applies_to_type', 'applies_to_value'], name='ix_ti_type_value'),
            models.Index(fields=['is_active', 'priority'], name='ix_ti_active_pri'),
        ]

    def __str__(self):
        return f"{self.title} ({self.applies_to_type})"

    @classmethod
    def get_instructions_for_job_card(cls, job_card):
        """
        Get all applicable technical instructions for a job card.

        Checks in priority order:
        1. Serial number specific
        2. MAT number specific
        3. Bit type specific
        4. Customer specific
        5. General (ALL)

        Args:
            job_card: JobCard instance

        Returns:
            QuerySet: Applicable TechnicalInstruction instances, ordered by priority
        """
        from django.db.models import Q, Case, When, IntegerField

        filters = Q(is_active=True)

        # Build filter conditions
        conditions = []

        # Serial number
        if job_card.serial_unit:
            conditions.append(
                Q(applies_to_type='SERIAL_NUMBER', applies_to_value=job_card.serial_unit.serial_number)
            )

        # MAT number
        if job_card.current_mat:
            conditions.append(
                Q(applies_to_type='MAT_NUMBER', applies_to_value=job_card.current_mat.mat_number)
            )

        # Bit type
        if job_card.bit_type:
            conditions.append(
                Q(applies_to_type='BIT_TYPE', applies_to_value=job_card.bit_type)
            )

        # Customer
        if job_card.customer_name:
            conditions.append(
                Q(applies_to_type='CUSTOMER', applies_to_value=job_card.customer_name)
            )

        # All jobs
        conditions.append(Q(applies_to_type='ALL'))

        # Combine with OR
        if conditions:
            filters &= Q(*conditions, _connector='OR')

        # Annotate with specificity priority (serial > MAT > type > customer > all)
        instructions = cls.objects.filter(filters).annotate(
            specificity=Case(
                When(applies_to_type='SERIAL_NUMBER', then=1),
                When(applies_to_type='MAT_NUMBER', then=2),
                When(applies_to_type='BIT_TYPE', then=3),
                When(applies_to_type='CUSTOMER', then=4),
                When(applies_to_type='ALL', then=5),
                default=99,
                output_field=IntegerField(),
            )
        ).order_by('specificity', 'priority', 'title')

        return instructions

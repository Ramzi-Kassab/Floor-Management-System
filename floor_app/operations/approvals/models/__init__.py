"""
Approval Workflow System

Comprehensive approval system with:
- Multi-level approval chains
- Role-based approvers
- Parallel and sequential approvals
- Conditional approvals
- Auto-approval rules
- Delegation
- Escalation
- Complete audit trail
- Integration with notifications
- Visibility to all concerned parties
"""

from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.conf import settings

from floor_app.mixins import AuditMixin


class ApprovalWorkflow(AuditMixin):
    """
    Define approval workflow templates.

    Workflows specify who needs to approve what, in what order.
    """

    WORKFLOW_TYPES = (
        ('BOM_MODIFICATION', 'BOM Modification'),
        ('CUTTER_SUBSTITUTION', 'Cutter Substitution'),
        ('PURCHASE_REQUEST', 'Purchase Request'),
        ('JOB_CARD_CREATION', 'Job Card Creation'),
        ('REWORK_REQUEST', 'Rework Request'),
        ('SCRAP_APPROVAL', 'Scrap Approval'),
        ('STOCK_ADJUSTMENT', 'Stock Adjustment'),
        ('DESIGN_CHANGE', 'Design Change'),
        ('PRICE_CHANGE', 'Price Change'),
        ('CUSTOMER_COMPLAINT', 'Customer Complaint'),
        ('LEAVE_REQUEST', 'Leave Request'),
        ('OVERTIME_REQUEST', 'Overtime Request'),
        ('CUSTOM', 'Custom Workflow'),
    )

    workflow_type = models.CharField(
        max_length=50,
        choices=WORKFLOW_TYPES,
        unique=True
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)

    # Auto-approval rules
    auto_approve_conditions = models.JSONField(
        default=dict,
        help_text="Conditions for auto-approval (e.g., {'amount_less_than': 1000})"
    )

    # Escalation
    escalation_enabled = models.BooleanField(default=False)
    escalation_hours = models.PositiveIntegerField(
        default=24,
        help_text="Hours before escalation"
    )

    # Notification settings
    notify_requester_on_approval = models.BooleanField(default=True)
    notify_requester_on_rejection = models.BooleanField(default=True)
    notify_all_approvers = models.BooleanField(
        default=False,
        help_text="Notify all approvers when request is submitted?"
    )

    class Meta:
        db_table = 'approvals_workflow'
        ordering = ['workflow_type']

    def __str__(self):
        return f"{self.name} ({self.get_workflow_type_display()})"


class ApprovalLevel(models.Model):
    """
    Approval level within a workflow.

    Levels can be sequential (1→2→3) or parallel (all at same level).
    """

    APPROVAL_MODE = (
        ('SEQUENTIAL', 'Sequential (one after another)'),
        ('PARALLEL', 'Parallel (all at same time)'),
        ('ANY_ONE', 'Any One (first to approve)'),
        ('MAJORITY', 'Majority (>50% must approve)'),
        ('ALL', 'All (everyone must approve)'),
    )

    workflow = models.ForeignKey(
        ApprovalWorkflow,
        on_delete=models.CASCADE,
        related_name='levels'
    )
    level_number = models.PositiveIntegerField(
        help_text="Level in sequence (1, 2, 3, ...)"
    )
    name = models.CharField(
        max_length=100,
        help_text="Level name (e.g., 'Manager Approval', 'Director Approval')"
    )

    approval_mode = models.CharField(
        max_length=20,
        choices=APPROVAL_MODE,
        default='SEQUENTIAL'
    )

    # Approvers
    approver_roles = models.JSONField(
        default=list,
        help_text="List of role names who can approve at this level"
    )
    approver_departments = models.ManyToManyField(
        'hr.HRDepartment',
        blank=True,
        help_text="Specific departments who can approve"
    )
    approver_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        help_text="Specific users who can approve"
    )

    # Conditions
    skip_if_requester_is_approver = models.BooleanField(
        default=True,
        help_text="Skip this level if requester is in approvers list?"
    )
    required_conditions = models.JSONField(
        default=dict,
        help_text="Conditions to activate this level (e.g., {'amount_greater_than': 5000})"
    )

    # SLA
    sla_hours = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Hours to approve before escalation"
    )

    class Meta:
        db_table = 'approvals_level'
        unique_together = [('workflow', 'level_number')]
        ordering = ['workflow', 'level_number']

    def __str__(self):
        return f"{self.workflow.name} - Level {self.level_number}: {self.name}"

    def get_approvers(self, request_instance=None):
        """
        Get list of users who can approve at this level.

        Can be filtered based on request context.
        """
        from django.contrib.auth import get_user_model
        User = get_user_model()

        approvers = User.objects.none()

        # Add specific users
        if self.approver_users.exists():
            approvers = approvers | self.approver_users.all()

        # Add users from departments
        if self.approver_departments.exists():
            dept_users = User.objects.filter(
                hremployee__current_department__in=self.approver_departments.all()
            )
            approvers = approvers | dept_users

        # Add users from roles (would need role system)
        # TODO: Implement role-based filtering

        return approvers.distinct()


class ApprovalRequest(AuditMixin):
    """
    Individual approval request instance.

    Tracks request through workflow until final approval/rejection.
    """

    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('IN_PROGRESS', 'In Progress'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
        ('ESCALATED', 'Escalated'),
    )

    workflow = models.ForeignKey(
        ApprovalWorkflow,
        on_delete=models.PROTECT,
        related_name='requests'
    )

    # What is being approved
    title = models.CharField(max_length=200)
    description = models.TextField()

    # Link to the object being approved
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE
    )
    object_id = models.PositiveIntegerField()
    related_object = GenericForeignKey('content_type', 'object_id')

    # Requester
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='approval_requests_made'
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT'
    )
    current_level = models.PositiveIntegerField(
        default=1,
        help_text="Current approval level"
    )

    # Timeline
    submitted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    due_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When approval is needed by"
    )

    # Visibility - who should see this request
    visible_to_all = models.BooleanField(
        default=False,
        help_text="Visible to all users?"
    )
    visible_to_departments = models.ManyToManyField(
        'hr.HRDepartment',
        blank=True,
        related_name='visible_approval_requests'
    )
    visible_to_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='visible_approval_requests'
    )

    # Metadata
    request_data = models.JSONField(
        default=dict,
        help_text="Additional data about the request"
    )
    priority = models.CharField(
        max_length=10,
        choices=[('LOW', 'Low'), ('NORMAL', 'Normal'), ('HIGH', 'High'), ('URGENT', 'Urgent')],
        default='NORMAL'
    )

    # Attachments
    attachments = models.JSONField(
        default=list,
        help_text="List of attachment paths/URLs"
    )

    class Meta:
        db_table = 'approvals_request'
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['workflow', 'status']),
            models.Index(fields=['requester', '-created_at']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['-submitted_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    def submit(self):
        """Submit request for approval."""
        if self.status == 'DRAFT':
            self.status = 'SUBMITTED'
            self.submitted_at = timezone.now()
            self.save()

            # Create approval steps for first level
            self._create_approval_steps()

            # Send notifications
            self._send_notifications()

    def _create_approval_steps(self):
        """Create approval steps for current level."""
        from floor_app.operations.approvals.models import ApprovalStep

        level = self.workflow.levels.filter(level_number=self.current_level).first()
        if not level:
            # No more levels, auto-approve
            self.approve_final()
            return

        # Check conditions
        if not self._check_level_conditions(level):
            # Skip this level
            self.current_level += 1
            self.save()
            self._create_approval_steps()
            return

        # Get approvers
        approvers = level.get_approvers(self)

        # Create steps
        for approver in approvers:
            ApprovalStep.objects.create(
                request=self,
                level=level,
                approver=approver,
                status='PENDING'
            )

    def _check_level_conditions(self, level):
        """Check if level conditions are met."""
        # TODO: Implement condition checking logic
        return True

    def _send_notifications(self):
        """Send notifications to approvers."""
        from floor_app.operations.notifications.services import NotificationService

        # Get current level approvers
        pending_steps = self.steps.filter(status='PENDING')

        for step in pending_steps:
            NotificationService.send_approval_request(
                request=self,
                approver=step.approver
            )

    def approve_final(self):
        """Mark request as finally approved."""
        self.status = 'APPROVED'
        self.completed_at = timezone.now()
        self.save()

        # Notify requester
        from floor_app.operations.notifications.services import NotificationService
        NotificationService.send_approval_approved(self)

    def reject_final(self, rejected_by, reason):
        """Mark request as rejected."""
        self.status = 'REJECTED'
        self.completed_at = timezone.now()
        self.save()

        # Notify requester
        from floor_app.operations.notifications.services import NotificationService
        NotificationService.send_approval_rejected(self, rejected_by, reason)

    def can_user_see(self, user):
        """Check if user can see this approval request."""
        # Requester can always see
        if self.requester == user:
            return True

        # Approvers can see
        if self.steps.filter(approver=user).exists():
            return True

        # Visible to all
        if self.visible_to_all:
            return True

        # Visible to specific users
        if self.visible_to_users.filter(id=user.id).exists():
            return True

        # Visible to departments
        if hasattr(user, 'hremployee'):
            if self.visible_to_departments.filter(
                id=user.hremployee.current_department_id
            ).exists():
                return True

        return False


class ApprovalStep(AuditMixin):
    """
    Individual approval step within a request.

    One step per approver per level.
    """

    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('SKIPPED', 'Skipped'),
        ('DELEGATED', 'Delegated'),
    )

    request = models.ForeignKey(
        ApprovalRequest,
        on_delete=models.CASCADE,
        related_name='steps'
    )
    level = models.ForeignKey(
        ApprovalLevel,
        on_delete=models.CASCADE
    )
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='approval_steps'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )

    # Response
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    comments = models.TextField(blank=True)

    # Delegation
    delegated_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='delegated_approval_steps'
    )
    delegated_at = models.DateTimeField(null=True, blank=True)
    delegation_reason = models.TextField(blank=True)

    # SLA tracking
    due_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this step is due"
    )
    is_overdue = models.BooleanField(default=False)

    class Meta:
        db_table = 'approvals_step'
        indexes = [
            models.Index(fields=['request', 'status']),
            models.Index(fields=['approver', 'status', '-created_at']),
            models.Index(fields=['level']),
        ]
        ordering = ['created_at']

    def __str__(self):
        return f"{self.request.title} - {self.approver.username}: {self.status}"

    def approve(self, comments=''):
        """Approve this step."""
        self.status = 'APPROVED'
        self.approved_at = timezone.now()
        self.comments = comments
        self.save()

        # Check if level is complete
        self._check_level_completion()

    def reject(self, comments=''):
        """Reject this step."""
        self.status = 'REJECTED'
        self.rejected_at = timezone.now()
        self.comments = comments
        self.save()

        # Reject entire request
        self.request.reject_final(self.approver, comments)

    def delegate(self, delegate_to, reason=''):
        """Delegate this approval to another user."""
        self.delegated_to = delegate_to
        self.delegated_at = timezone.now()
        self.delegation_reason = reason
        self.status = 'DELEGATED'
        self.save()

        # Create new step for delegate
        ApprovalStep.objects.create(
            request=self.request,
            level=self.level,
            approver=delegate_to,
            status='PENDING'
        )

    def _check_level_completion(self):
        """Check if current level is complete and advance if needed."""
        level = self.level
        all_steps = self.request.steps.filter(level=level)

        if level.approval_mode == 'SEQUENTIAL':
            # All must approve
            if all_steps.filter(status='APPROVED').count() == all_steps.count():
                self._advance_to_next_level()
        elif level.approval_mode == 'ANY_ONE':
            # First approval is enough
            self._advance_to_next_level()
        elif level.approval_mode == 'MAJORITY':
            # >50% must approve
            approved = all_steps.filter(status='APPROVED').count()
            total = all_steps.count()
            if approved > total / 2:
                self._advance_to_next_level()
        elif level.approval_mode == 'ALL':
            # All must approve
            if all_steps.filter(status='APPROVED').count() == all_steps.count():
                self._advance_to_next_level()

    def _advance_to_next_level(self):
        """Advance request to next approval level."""
        self.request.current_level += 1
        self.request.status = 'IN_PROGRESS'
        self.request.save()

        # Create steps for next level
        self.request._create_approval_steps()


class ApprovalHistory(models.Model):
    """
    Complete audit trail of all approval actions.

    Immutable log of every action taken on approval requests.
    """

    ACTION_TYPES = (
        ('CREATED', 'Created'),
        ('SUBMITTED', 'Submitted'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('DELEGATED', 'Delegated'),
        ('ESCALATED', 'Escalated'),
        ('CANCELLED', 'Cancelled'),
        ('COMMENTED', 'Commented'),
        ('MODIFIED', 'Modified'),
    )

    request = models.ForeignKey(
        ApprovalRequest,
        on_delete=models.CASCADE,
        related_name='history'
    )
    step = models.ForeignKey(
        ApprovalStep,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='history'
    )

    action_type = models.CharField(
        max_length=20,
        choices=ACTION_TYPES
    )
    action_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    action_at = models.DateTimeField(auto_now_add=True)

    comments = models.TextField(blank=True)
    metadata = models.JSONField(
        default=dict,
        help_text="Additional action metadata"
    )

    # For visibility - who can see this history entry
    is_internal = models.BooleanField(
        default=False,
        help_text="Internal note (not visible to requester)"
    )

    class Meta:
        db_table = 'approvals_history'
        indexes = [
            models.Index(fields=['request', '-action_at']),
            models.Index(fields=['action_type', '-action_at']),
        ]
        ordering = ['-action_at']
        verbose_name_plural = 'Approval histories'

    def __str__(self):
        return f"{self.get_action_type_display()} by {self.action_by} on {self.request.title}"


class ApprovalDelegation(models.Model):
    """
    Persistent approval delegation rules.

    User A can delegate all/specific approvals to User B for a time period.
    """

    delegator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='delegations_made'
    )
    delegate = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='delegations_received'
    )

    # Scope
    workflow_types = models.JSONField(
        default=list,
        help_text="List of workflow types to delegate (empty = all)"
    )

    # Time period
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    reason = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'approvals_delegation'
        indexes = [
            models.Index(fields=['delegator', 'is_active']),
            models.Index(fields=['delegate', 'is_active']),
            models.Index(fields=['start_date', 'end_date']),
        ]

    def __str__(self):
        return f"{self.delegator.username} → {self.delegate.username} ({self.start_date} to {self.end_date})"

    @property
    def is_current(self):
        """Check if delegation is currently active."""
        now = timezone.now()
        return (
            self.is_active and
            self.start_date <= now <= self.end_date
        )

"""
Leave Management Models

Comprehensive leave management for HRMS including leave types, requests,
balances, and accruals.
"""

from django.db import models
from django.utils import timezone
from floor_app.mixins import AuditMixin, SoftDeleteMixin


def get_current_year():
    """Get current year for default value."""
    return timezone.now().year


class LeaveType:
    """Types of leave - Saudi Arabia Labor Law Compliant"""
    # Standard leave types
    ANNUAL = 'ANNUAL'
    SICK = 'SICK'
    MATERNITY = 'MATERNITY'
    PATERNITY = 'PATERNITY'
    NEWBORN = 'NEWBORN'  # KSA: 3 days for newborn
    BEREAVEMENT = 'BEREAVEMENT'  # KSA: Variable by relative degree
    BEREAVEMENT_SPOUSE = 'BEREAVEMENT_SPOUSE'  # KSA: 5 days
    BEREAVEMENT_PARENT = 'BEREAVEMENT_PARENT'  # KSA: 5 days
    BEREAVEMENT_CHILD = 'BEREAVEMENT_CHILD'  # KSA: 5 days
    BEREAVEMENT_SIBLING = 'BEREAVEMENT_SIBLING'  # KSA: 3 days
    BEREAVEMENT_GRANDPARENT = 'BEREAVEMENT_GRANDPARENT'  # KSA: 3 days
    HAJJ = 'HAJJ'  # KSA: Once during employment, unpaid unless using annual leave
    OMRA = 'OMRA'  # KSA: Umrah pilgrimage, unpaid, subject to approval
    EXIT_REENTRY = 'EXIT_REENTRY'  # KSA: Exit/re-entry visa leave, tied to visa regulations
    MARRIAGE = 'MARRIAGE'
    UNPAID = 'UNPAID'  # KSA: Employer discretion, max 20-30 days/year
    EMERGENCY = 'EMERGENCY'
    COMPENSATORY = 'COMPENSATORY'  # From overtime weekend work
    STUDY = 'STUDY'  # For education/training

    CHOICES = [
        (ANNUAL, 'Annual Leave'),
        (SICK, 'Sick Leave'),
        (MATERNITY, 'Maternity Leave (10 weeks)'),
        (PATERNITY, 'Paternity Leave'),
        (NEWBORN, 'Newborn Care Leave (3 days - KSA)'),
        (BEREAVEMENT, 'Bereavement Leave (General)'),
        (BEREAVEMENT_SPOUSE, 'Bereavement - Spouse (5 days - KSA)'),
        (BEREAVEMENT_PARENT, 'Bereavement - Parent (5 days - KSA)'),
        (BEREAVEMENT_CHILD, 'Bereavement - Child (5 days - KSA)'),
        (BEREAVEMENT_SIBLING, 'Bereavement - Sibling (3 days - KSA)'),
        (BEREAVEMENT_GRANDPARENT, 'Bereavement - Grandparent (3 days - KSA)'),
        (HAJJ, 'Hajj Pilgrimage (Once during employment - KSA)'),
        (OMRA, 'Omra/Umrah Pilgrimage (Unpaid - KSA)'),
        (EXIT_REENTRY, 'Exit/Re-entry Visa Leave (KSA)'),
        (MARRIAGE, 'Marriage Leave'),
        (UNPAID, 'Unpaid Leave'),
        (EMERGENCY, 'Emergency Leave'),
        (COMPENSATORY, 'Compensatory Time Off'),
        (STUDY, 'Study/Education Leave'),
    ]


class LeaveRequestStatus:
    """Leave request status states"""
    DRAFT = 'DRAFT'
    SUBMITTED = 'SUBMITTED'
    PENDING_APPROVAL = 'PENDING_APPROVAL'
    APPROVED = 'APPROVED'
    REJECTED = 'REJECTED'
    CANCELLED = 'CANCELLED'

    CHOICES = [
        (DRAFT, 'Draft'),
        (SUBMITTED, 'Submitted'),
        (PENDING_APPROVAL, 'Pending Approval'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected'),
        (CANCELLED, 'Cancelled'),
    ]


class LeavePolicy(AuditMixin, SoftDeleteMixin):
    """
    Leave policy defining entitlements and rules.
    """
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    leave_type = models.CharField(
        max_length=30,
        choices=LeaveType.CHOICES,
        db_index=True
    )
    description = models.TextField(blank=True)

    # Entitlement
    annual_entitlement_days = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Annual entitlement in days"
    )
    max_accumulation_days = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Maximum days that can be accumulated"
    )
    carry_forward_days = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Days that can be carried forward"
    )
    carry_forward_expiry_months = models.IntegerField(
        default=12,
        help_text="Months after which carry forward expires"
    )

    # Rules
    minimum_notice_days = models.IntegerField(
        default=0,
        help_text="Minimum days notice required"
    )
    maximum_consecutive_days = models.IntegerField(
        default=30,
        help_text="Maximum consecutive days allowed"
    )
    minimum_days_per_request = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=0.5,
        help_text="Minimum days per request (0.5 for half day)"
    )

    # Accrual
    accrual_type = models.CharField(
        max_length=20,
        default='MONTHLY',
        choices=[
            ('UPFRONT', 'Upfront at start of year'),
            ('MONTHLY', 'Monthly accrual'),
            ('QUARTERLY', 'Quarterly accrual'),
        ]
    )
    prorate_for_new_joiners = models.BooleanField(default=True)
    prorate_for_leavers = models.BooleanField(default=True)

    # Approval
    requires_approval = models.BooleanField(default=True)
    auto_approve_below_days = models.IntegerField(
        default=0,
        help_text="Auto-approve requests below this number of days (0 = always require approval)"
    )

    # Documentation
    requires_medical_certificate = models.BooleanField(default=False)
    medical_certificate_after_days = models.IntegerField(
        default=2,
        help_text="Medical certificate required after this many days"
    )

    # Encashment (Saudi Arabia)
    allows_encashment = models.BooleanField(default=False)
    max_encashment_days = models.IntegerField(default=0)

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'hr_leave_policy'
        verbose_name = 'Leave Policy'
        verbose_name_plural = 'Leave Policies'
        ordering = ['leave_type', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_leave_type_display()})"


class LeaveBalance(AuditMixin):
    """
    Employee leave balance tracking per leave type per year.
    """
    employee = models.ForeignKey(
        'HREmployee',
        on_delete=models.CASCADE,
        related_name='leave_balances'
    )
    leave_policy = models.ForeignKey(
        LeavePolicy,
        on_delete=models.CASCADE,
        related_name='balances'
    )
    year = models.IntegerField(
        default=get_current_year,
        db_index=True
    )

    # Balance Tracking
    opening_balance = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        help_text="Balance at start of year"
    )
    accrued = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        help_text="Days accrued during the year"
    )
    used = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        help_text="Days used"
    )
    pending = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        help_text="Days in pending requests"
    )
    adjustment = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        help_text="Manual adjustments"
    )
    encashed = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        help_text="Days encashed"
    )
    carry_forward_from_previous = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        help_text="Carried forward from previous year"
    )

    adjustment_reason = models.TextField(blank=True)
    last_accrual_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'hr_leave_balance'
        verbose_name = 'Leave Balance'
        verbose_name_plural = 'Leave Balances'
        unique_together = [['employee', 'leave_policy', 'year']]
        ordering = ['-year', 'employee']

    def __str__(self):
        return f"{self.employee.employee_no} - {self.leave_policy.name} ({self.year})"

    @property
    def available_balance(self):
        """Calculate available balance"""
        return (
            self.opening_balance +
            self.accrued +
            self.carry_forward_from_previous +
            self.adjustment -
            self.used -
            self.pending -
            self.encashed
        )

    def deduct(self, days):
        """Deduct days from balance"""
        self.used += days
        self.save(update_fields=['used'])

    def add_pending(self, days):
        """Add days to pending"""
        self.pending += days
        self.save(update_fields=['pending'])

    def release_pending(self, days):
        """Release pending days (when request is cancelled/rejected)"""
        self.pending = max(0, self.pending - days)
        self.save(update_fields=['pending'])

    def convert_pending_to_used(self, days):
        """Convert pending to used (when request is approved)"""
        self.pending = max(0, self.pending - days)
        self.used += days
        self.save(update_fields=['pending', 'used'])


class LeaveRequest(AuditMixin, SoftDeleteMixin):
    """
    Employee leave request.
    """
    employee = models.ForeignKey(
        'HREmployee',
        on_delete=models.CASCADE,
        related_name='leave_requests'
    )
    leave_policy = models.ForeignKey(
        LeavePolicy,
        on_delete=models.PROTECT,
        related_name='requests'
    )

    # Request Details
    request_number = models.CharField(
        max_length=30,
        unique=True,
        db_index=True
    )
    status = models.CharField(
        max_length=20,
        choices=LeaveRequestStatus.CHOICES,
        default=LeaveRequestStatus.DRAFT,
        db_index=True
    )

    # Dates
    start_date = models.DateField()
    end_date = models.DateField()
    total_days = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Total leave days requested"
    )

    # Half Day Support
    is_half_day_start = models.BooleanField(
        default=False,
        help_text="Start date is half day"
    )
    is_half_day_end = models.BooleanField(
        default=False,
        help_text="End date is half day"
    )

    # Reason
    reason = models.TextField(
        help_text="Reason for leave"
    )
    contact_during_leave = models.CharField(
        max_length=200,
        blank=True,
        help_text="Contact number during leave"
    )

    # Approval
    submitted_at = models.DateTimeField(null=True, blank=True)
    approver_id = models.BigIntegerField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approval_notes = models.TextField(blank=True)

    rejected_by_id = models.BigIntegerField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)

    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)

    # Coverage
    coverage_employee_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Employee covering during absence"
    )
    handover_notes = models.TextField(blank=True)

    # Documentation
    attachment_path = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = 'hr_leave_request'
        verbose_name = 'Leave Request'
        verbose_name_plural = 'Leave Requests'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['employee', 'status'], name='ix_leavereq_emp_status'),
            models.Index(fields=['start_date', 'end_date'], name='ix_leavereq_dates'),
        ]

    def __str__(self):
        return f"{self.request_number} - {self.employee.employee_no}"

    def submit(self):
        """Submit leave request for approval"""
        if self.status == LeaveRequestStatus.DRAFT:
            self.status = LeaveRequestStatus.PENDING_APPROVAL
            self.submitted_at = timezone.now()
            self.save(update_fields=['status', 'submitted_at'])

            # Update balance to pending
            try:
                balance = LeaveBalance.objects.get(
                    employee=self.employee,
                    leave_policy=self.leave_policy,
                    year=self.start_date.year
                )
                balance.add_pending(self.total_days)
            except LeaveBalance.DoesNotExist:
                pass

            return True
        return False

    def approve(self, approver_id, notes=''):
        """Approve leave request"""
        if self.status == LeaveRequestStatus.PENDING_APPROVAL:
            self.status = LeaveRequestStatus.APPROVED
            self.approver_id = approver_id
            self.approved_at = timezone.now()
            self.approval_notes = notes
            self.save(update_fields=[
                'status', 'approver_id', 'approved_at', 'approval_notes'
            ])

            # Convert pending to used in balance
            try:
                balance = LeaveBalance.objects.get(
                    employee=self.employee,
                    leave_policy=self.leave_policy,
                    year=self.start_date.year
                )
                balance.convert_pending_to_used(self.total_days)
            except LeaveBalance.DoesNotExist:
                pass

            return True
        return False

    def reject(self, rejector_id, reason):
        """Reject leave request"""
        if self.status == LeaveRequestStatus.PENDING_APPROVAL:
            self.status = LeaveRequestStatus.REJECTED
            self.rejected_by_id = rejector_id
            self.rejected_at = timezone.now()
            self.rejection_reason = reason
            self.save(update_fields=[
                'status', 'rejected_by_id', 'rejected_at', 'rejection_reason'
            ])

            # Release pending in balance
            try:
                balance = LeaveBalance.objects.get(
                    employee=self.employee,
                    leave_policy=self.leave_policy,
                    year=self.start_date.year
                )
                balance.release_pending(self.total_days)
            except LeaveBalance.DoesNotExist:
                pass

            return True
        return False

    @classmethod
    def generate_request_number(cls):
        """Generate next request number"""
        year = timezone.now().year
        prefix = f'LV-{year}-'
        last_req = cls.all_objects.filter(
            request_number__startswith=prefix
        ).order_by('-request_number').first()

        if last_req:
            last_num = int(last_req.request_number.split('-')[-1])
            next_num = last_num + 1
        else:
            next_num = 1

        return f"{prefix}{next_num:05d}"

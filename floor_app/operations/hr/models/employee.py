from django.conf import settings
from django.db import models

from floor_app.mixins import HRAuditMixin, HRSoftDeleteMixin
from floor_app.mixins import PublicIdMixin  # from floor_app.mixins


class HREmployee(PublicIdMixin, HRAuditMixin, HRSoftDeleteMixin):
    STATUS = (
        ("ACTIVE", "Active"),
        ("ON_LEAVE", "On leave"),
        ("SUSPENDED", "Suspended"),
        ("TERMINATED", "Terminated"),
    )

    # Changed from EMPLOYEE_TYPE to CONTRACT_TYPE
    CONTRACT_TYPE = (
        ("PERMANENT", "Permanent Employee"),
        ("FIXED_TERM", "Fixed Term Contract"),
        ("TEMPORARY", "Temporary"),
        ("PART_TIME", "Part-Time"),
        ("INTERN", "Internship"),
        ("CONSULTANT", "Consultant"),
        ("CONTRACTOR", "Contractor"),
    )

    EMPLOYMENT_STATUS = (
        ("ACTIVE", "Active"),
        ("ON_PROBATION", "On Probation"),
        ("ON_LEAVE", "On Leave"),
        ("ON_SUSPENSION", "On Suspension"),
        ("UNDER_NOTICE", "Under Notice"),
        ("TERMINATED", "Terminated"),
        ("RETIRED", "Retired"),
    )

    PROBATION_STATUS = (
        ("PENDING", "Pending"),
        ("PASSED", "Passed"),
        ("FAILED", "Failed"),
    )

    SHIFT_PATTERN = (
        ("DAY", "Day Shift"),
        ("NIGHT", "Night Shift"),
        ("ROTATING", "Rotating Shift"),
        ("FLEXIBLE", "Flexible"),
    )

    EMPLOYMENT_CATEGORY = (
        ("REGULAR", "Regular"),
        ("SEASONAL", "Seasonal"),
        ("PROJECT_BASED", "Project-Based"),
        ("RELIEF_STAFF", "Relief Staff"),
        ("CASUAL", "Casual"),
    )

    person = models.OneToOneField(
        "HRPeople",
        on_delete=models.PROTECT,
        related_name="employee",
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hr_employee",
    )

    # Basic Information
    employee_no = models.CharField(max_length=32, unique=True)
    status = models.CharField(max_length=16, choices=STATUS, default="ACTIVE")

    # Job Assignment (UPDATED: position FK instead of job_title text)
    position = models.ForeignKey(
        "Position",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employees",
        help_text="Job position/title"
    )

    # Legacy job_title field (deprecated - use position instead)
    # Kept for backward compatibility with existing database
    job_title = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        help_text="DEPRECATED: Use position field instead. Kept for backward compatibility."
    )

    department = models.ForeignKey(
        "Department",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employees",
        help_text="Department assignment"
    )

    # Contract Type (RENAMED from employee_type)
    contract_type = models.CharField(
        max_length=16,
        choices=CONTRACT_TYPE,
        default="PERMANENT",
        help_text="Type of employment contract"
    )

    # Legacy employee_type field (deprecated - use contract_type instead)
    # Kept for backward compatibility with existing database
    employee_type = models.CharField(
        max_length=16,
        null=True,
        blank=True,
        help_text="DEPRECATED: Use contract_type field instead. Kept for backward compatibility."
    )

    # Contract Duration Fields (NEW)
    contract_start_date = models.DateField(
        null=True,
        blank=True,
        help_text="Contract start date (for fixed-term contracts)"
    )

    contract_end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Contract end date (for fixed-term contracts)"
    )

    contract_renewal_date = models.DateField(
        null=True,
        blank=True,
        help_text="Next contract renewal date"
    )

    # Probation Fields (NEW)
    probation_end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Probation period end date"
    )

    probation_status = models.CharField(
        max_length=16,
        choices=PROBATION_STATUS,
        null=True,
        blank=True,
        help_text="Current probation status"
    )

    # Employment Dates
    hire_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date of hire/joining"
    )

    termination_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date of termination"
    )

    # Work Schedule (NEW)
    work_days_per_week = models.IntegerField(
        default=5,
        help_text="Number of working days per week"
    )

    hours_per_week = models.IntegerField(
        default=40,
        help_text="Total working hours per week"
    )

    shift_pattern = models.CharField(
        max_length=16,
        choices=SHIFT_PATTERN,
        default="DAY",
        help_text="Work shift pattern"
    )

    # Compensation (NEW)
    salary_grade = models.CharField(
        max_length=32,
        blank=True,
        default="",
        help_text="Salary grade classification"
    )

    monthly_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Monthly salary amount"
    )

    benefits_eligible = models.BooleanField(
        default=True,
        help_text="Eligible for company benefits"
    )

    overtime_eligible = models.BooleanField(
        default=True,
        help_text="Eligible for overtime compensation"
    )

    # Leave Entitlements (NEW)
    annual_leave_days = models.IntegerField(
        default=20,
        help_text="Annual leave days per year"
    )

    sick_leave_days = models.IntegerField(
        default=10,
        help_text="Sick leave days per year"
    )

    special_leave_days = models.IntegerField(
        default=3,
        help_text="Special leave days per year"
    )

    # Employment Details (NEW)
    employment_category = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_CATEGORY,
        default="REGULAR",
        help_text="Employment category type"
    )

    employment_status = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_STATUS,
        default="ACTIVE",
        help_text="Current employment status"
    )

    report_to = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subordinates",
        help_text="Supervisor or Manager this employee reports to"
    )

    cost_center = models.CharField(
        max_length=32,
        blank=True,
        default="",
        help_text="Cost center code for allocation"
    )

    # Legacy field (kept for backward compatibility, will be deprecated)
    team = models.CharField(
        max_length=64,
        blank=True,
        default="",
        help_text="DEPRECATED: Use department field instead"
    )

    class Meta:
        db_table = "hr_employee"
        ordering = ["employee_no"]

    def __str__(self):
        base = f"{self.employee_no}"
        if self.person_id:
            return f"{base} - {self.person}"
        return base

    @property
    def phones(self):
        return self.person.phones.all()

    @property
    def emails(self):
        return self.person.emails.all()

    @property
    def addresses(self):
        return self.person.addresses.all()
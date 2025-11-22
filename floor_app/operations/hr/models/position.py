from django.db import models
from django.contrib.auth.models import Group
from floor_app.mixins import HRAuditMixin, HRSoftDeleteMixin


class Position(HRAuditMixin, HRSoftDeleteMixin):
    """
    Position/Job title model that standardizes job positions across the organization.
    Each position is linked to a department and has a position level.
    """

    POSITION_LEVEL_CHOICES = [
        ('ENTRY', 'Entry Level'),
        ('JUNIOR', 'Junior'),
        ('SENIOR', 'Senior'),
        ('SUPERVISOR', 'Supervisor'),
        ('MANAGER', 'Manager'),
        ('DIRECTOR', 'Director'),
        ('OTHER', 'Other'),
    ]

    SALARY_GRADE_CHOICES = [
        ('GRADE_A', 'Grade A'),
        ('GRADE_B', 'Grade B'),
        ('GRADE_C', 'Grade C'),
        ('GRADE_D', 'Grade D'),
        ('GRADE_E', 'Grade E'),
        ('EXECUTIVE', 'Executive'),
    ]

    # Basic Information
    name = models.CharField(
        max_length=200,
        unique=True,
        help_text="Position title (e.g., QA Engineer, Production Operator)"
    )

    description = models.TextField(
        blank=True,
        null=True,
        help_text="Position description and main responsibilities"
    )

    # Organization
    department = models.ForeignKey(
        'Department',
        on_delete=models.PROTECT,
        related_name='positions',
        help_text="Department this position belongs to"
    )

    # Level & Grade
    position_level = models.CharField(
        max_length=16,
        choices=POSITION_LEVEL_CHOICES,
        default='ENTRY',
        help_text="Seniority level of this position"
    )

    salary_grade = models.CharField(
        max_length=16,
        choices=SALARY_GRADE_CHOICES,
        help_text="Salary grade for this position"
    )

    # Additional Info
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this position is currently available"
    )

    # RBAC: Link to Django auth Group
    auth_group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='positions',
        help_text='Django auth Group linked to this position for RBAC'
    )

    # Additional permissions as comma-separated codenames
    permission_codenames = models.TextField(
        blank=True,
        default='',
        help_text='Comma-separated list of additional permission codenames for this position'
    )

    class Meta:
        db_table = 'hr_position'
        ordering = ['department', 'name']
        verbose_name = 'Position'
        verbose_name_plural = 'Positions'
        indexes = [
            models.Index(fields=['department', 'name']),
            models.Index(fields=['position_level']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.department.name})"

    @property
    def employee_count(self):
        """Count how many employees have this position."""
        # Check if annotated value exists (from queryset annotation)
        if hasattr(self, 'num_employees'):
            return self.num_employees
        # Otherwise, perform database query
        return self.employees.filter(is_deleted=False).count()

    def get_employee_count(self):
        """Count how many employees have this position."""
        return self.employee_count

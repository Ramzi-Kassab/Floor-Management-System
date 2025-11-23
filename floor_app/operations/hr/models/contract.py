"""
HR Contract Models

Manages employee contracts, compensation, and employment terms.
"""
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from .employee import HREmployee


class HRContract(models.Model):
    """
    Employee contract model.

    Tracks employment contracts, compensation details, and contract terms.
    Finance-related fields should be displayed in a collapsible panel in the UI.
    """

    CONTRACT_TYPE_CHOICES = [
        ('permanent', 'Permanent'),
        ('temporary', 'Temporary'),
        ('contractor', 'Contractor'),
        ('intern', 'Intern'),
        ('part_time', 'Part Time'),
    ]

    # Employee relationship
    employee = models.ForeignKey(
        HREmployee,
        on_delete=models.CASCADE,
        related_name='contracts',
        help_text='Employee associated with this contract'
    )

    # Contract details
    contract_number = models.CharField(
        max_length=50,
        unique=True,
        help_text='Unique contract reference number'
    )

    contract_type = models.CharField(
        max_length=20,
        choices=CONTRACT_TYPE_CHOICES,
        help_text='Type of employment contract'
    )

    start_date = models.DateField(
        help_text='Contract start date'
    )

    end_date = models.DateField(
        null=True,
        blank=True,
        help_text='Contract end date (null for permanent contracts)'
    )

    # Compensation details (Finance panel in UI)
    basic_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Basic monthly salary'
    )

    housing_allowance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Monthly housing allowance'
    )

    transport_allowance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Monthly transport allowance'
    )

    other_allowances = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Other monthly allowances'
    )

    # Currency
    currency = models.ForeignKey(
        'core.Currency',
        on_delete=models.PROTECT,
        default='SAR',
        help_text='Currency for compensation'
    )

    # Status
    is_current = models.BooleanField(
        default=True,
        help_text='Is this the current active contract?'
    )

    # Additional details
    probation_period_months = models.IntegerField(
        null=True,
        blank=True,
        help_text='Probation period in months'
    )

    notice_period_days = models.IntegerField(
        null=True,
        blank=True,
        help_text='Notice period in days'
    )

    work_hours_per_week = models.IntegerField(
        default=40,
        help_text='Standard work hours per week'
    )

    annual_leave_days = models.IntegerField(
        default=21,
        help_text='Annual leave entitlement in days'
    )

    # Contract document
    contract_file = models.FileField(
        upload_to='hr/contracts/',
        null=True,
        blank=True,
        help_text='Scanned contract document'
    )

    notes = models.TextField(
        blank=True,
        help_text='Additional notes'
    )

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_hr_contracts'
    )

    class Meta:
        db_table = 'hr_contract'
        verbose_name = 'HR Contract'
        verbose_name_plural = 'HR Contracts'
        ordering = ['-is_current', '-start_date']
        indexes = [
            models.Index(fields=['employee', 'is_current']),
            models.Index(fields=['contract_type']),
            models.Index(fields=['start_date']),
        ]

    def __str__(self):
        return f"{self.contract_number} - {self.employee.employee_code} ({self.get_contract_type_display()})"

    @property
    def total_compensation(self):
        """Calculate total monthly compensation."""
        return (
            self.basic_salary +
            self.housing_allowance +
            self.transport_allowance +
            self.other_allowances
        )

    @property
    def is_active(self):
        """Check if contract is currently active."""
        from django.utils import timezone
        today = timezone.now().date()

        if not self.is_current:
            return False

        if self.start_date > today:
            return False

        if self.end_date and self.end_date < today:
            return False

        return True

    def save(self, *args, **kwargs):
        # Auto-generate contract number if not provided
        if not self.contract_number:
            from django.utils import timezone
            year = timezone.now().year
            count = HRContract.objects.filter(
                contract_number__startswith=f'C-{year}'
            ).count() + 1
            self.contract_number = f'C-{year}-{count:04d}'

        # If setting as current, unset other current contracts
        if self.is_current:
            HRContract.objects.filter(
                employee=self.employee,
                is_current=True
            ).exclude(pk=self.pk).update(is_current=False)

        super().save(*args, **kwargs)

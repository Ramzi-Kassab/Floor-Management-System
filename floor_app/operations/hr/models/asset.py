"""
HR Asset Management Models

Manages company assets and their assignment to employees.
"""
from django.db import models
from django.core.exceptions import ValidationError
from .employee import HREmployee


class AssetType(models.Model):
    """
    Asset type/category model.

    Defines types of assets that can be assigned to employees
    (e.g., Laptop, Phone, Vehicle, Safety Equipment, Tools).
    """

    # Asset type details
    code = models.CharField(
        max_length=20,
        unique=True,
        help_text='Unique asset type code (e.g., LAPTOP, PHONE, VEHICLE)'
    )

    name = models.CharField(
        max_length=100,
        help_text='Asset type name'
    )

    description = models.TextField(
        blank=True,
        help_text='Asset type description'
    )

    # Classification
    category = models.CharField(
        max_length=50,
        blank=True,
        help_text='Asset category (IT, Transport, Safety, Tools, etc.)'
    )

    # Tracking requirements
    requires_serial_number = models.BooleanField(
        default=True,
        help_text='Does this asset type require serial number tracking?'
    )

    requires_maintenance = models.BooleanField(
        default=False,
        help_text='Does this asset type require regular maintenance?'
    )

    maintenance_interval_days = models.IntegerField(
        null=True,
        blank=True,
        help_text='Maintenance interval in days (if applicable)'
    )

    # Depreciation
    depreciation_period_months = models.IntegerField(
        null=True,
        blank=True,
        help_text='Depreciation period in months'
    )

    # Status
    is_active = models.BooleanField(
        default=True,
        help_text='Is this asset type active?'
    )

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_asset_types'
    )

    class Meta:
        db_table = 'hr_asset_type'
        verbose_name = 'Asset Type'
        verbose_name_plural = 'Asset Types'
        ordering = ['category', 'name']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['category']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"


class HRAsset(models.Model):
    """
    Company asset model.

    Tracks individual company assets that can be assigned to employees.
    This is for generic assets; specialized assets like Vehicles are in hr_assets app.
    """

    CONDITION_CHOICES = [
        ('new', 'New'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
        ('damaged', 'Damaged'),
        ('retired', 'Retired'),
    ]

    STATUS_CHOICES = [
        ('available', 'Available'),
        ('assigned', 'Assigned'),
        ('in_maintenance', 'In Maintenance'),
        ('retired', 'Retired'),
        ('lost', 'Lost'),
        ('damaged', 'Damaged'),
    ]

    # Asset identification
    asset_tag = models.CharField(
        max_length=50,
        unique=True,
        help_text='Unique asset tag/identifier'
    )

    asset_type = models.ForeignKey(
        AssetType,
        on_delete=models.PROTECT,
        related_name='assets',
        help_text='Type of asset'
    )

    name = models.CharField(
        max_length=200,
        help_text='Asset name/description'
    )

    serial_number = models.CharField(
        max_length=100,
        blank=True,
        help_text='Manufacturer serial number'
    )

    # Details
    manufacturer = models.CharField(
        max_length=100,
        blank=True,
        help_text='Manufacturer/brand'
    )

    model = models.CharField(
        max_length=100,
        blank=True,
        help_text='Model number/name'
    )

    specifications = models.JSONField(
        default=dict,
        blank=True,
        help_text='Technical specifications (JSON)'
    )

    # Purchase/Financial details
    purchase_date = models.DateField(
        null=True,
        blank=True,
        help_text='Date of purchase'
    )

    purchase_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Purchase cost'
    )

    currency = models.ForeignKey(
        'core.Currency',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text='Purchase currency'
    )

    supplier = models.CharField(
        max_length=200,
        blank=True,
        help_text='Supplier/vendor name'
    )

    # Warranty
    warranty_expiry_date = models.DateField(
        null=True,
        blank=True,
        help_text='Warranty expiration date'
    )

    # Status and condition
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='available',
        help_text='Current status'
    )

    condition = models.CharField(
        max_length=20,
        choices=CONDITION_CHOICES,
        default='good',
        help_text='Physical condition'
    )

    # Location
    current_location = models.CharField(
        max_length=200,
        blank=True,
        help_text='Current physical location'
    )

    cost_center = models.ForeignKey(
        'core.CostCenter',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assets',
        help_text='Cost center responsible for this asset'
    )

    # Maintenance tracking
    last_maintenance_date = models.DateField(
        null=True,
        blank=True,
        help_text='Date of last maintenance'
    )

    next_maintenance_date = models.DateField(
        null=True,
        blank=True,
        help_text='Next scheduled maintenance date'
    )

    # Notes
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
        related_name='created_hr_assets'
    )

    class Meta:
        db_table = 'hr_asset'
        verbose_name = 'Asset'
        verbose_name_plural = 'Assets'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['asset_tag']),
            models.Index(fields=['asset_type', 'status']),
            models.Index(fields=['serial_number']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.asset_tag} - {self.name}"

    @property
    def is_available(self):
        """Check if asset is available for assignment."""
        return self.status == 'available'

    @property
    def is_under_warranty(self):
        """Check if asset is still under warranty."""
        if not self.warranty_expiry_date:
            return False
        from django.utils import timezone
        return self.warranty_expiry_date >= timezone.now().date()

    @property
    def needs_maintenance(self):
        """Check if asset needs maintenance."""
        if not self.next_maintenance_date:
            return False
        from django.utils import timezone
        return self.next_maintenance_date <= timezone.now().date()

    def save(self, *args, **kwargs):
        # Auto-generate asset tag if not provided
        if not self.asset_tag:
            from django.utils import timezone
            year = timezone.now().year
            type_code = self.asset_type.code[:3].upper()
            count = HRAsset.objects.filter(
                asset_tag__startswith=f'{type_code}-{year}'
            ).count() + 1
            self.asset_tag = f'{type_code}-{year}-{count:04d}'

        # Calculate next maintenance date if applicable
        if (self.asset_type.requires_maintenance and
            self.asset_type.maintenance_interval_days and
            self.last_maintenance_date and
            not self.next_maintenance_date):
            from datetime import timedelta
            self.next_maintenance_date = (
                self.last_maintenance_date +
                timedelta(days=self.asset_type.maintenance_interval_days)
            )

        super().save(*args, **kwargs)


class AssetAssignment(models.Model):
    """
    Asset assignment model.

    Tracks assignment of assets to employees, including assignment
    and return dates, and condition at handover/return.
    """

    ASSIGNMENT_STATUS_CHOICES = [
        ('active', 'Active'),
        ('returned', 'Returned'),
        ('lost', 'Lost'),
        ('damaged', 'Damaged'),
    ]

    # Assignment details
    asset = models.ForeignKey(
        HRAsset,
        on_delete=models.PROTECT,
        related_name='assignments',
        help_text='Asset being assigned'
    )

    employee = models.ForeignKey(
        HREmployee,
        on_delete=models.CASCADE,
        related_name='asset_assignments',
        help_text='Employee receiving the asset'
    )

    # Assignment period
    assignment_date = models.DateField(
        help_text='Date asset was assigned to employee'
    )

    expected_return_date = models.DateField(
        null=True,
        blank=True,
        help_text='Expected return date (for temporary assignments)'
    )

    actual_return_date = models.DateField(
        null=True,
        blank=True,
        help_text='Actual return date'
    )

    # Condition tracking
    condition_at_assignment = models.CharField(
        max_length=20,
        choices=HRAsset.CONDITION_CHOICES,
        help_text='Asset condition when assigned'
    )

    condition_at_return = models.CharField(
        max_length=20,
        choices=HRAsset.CONDITION_CHOICES,
        null=True,
        blank=True,
        help_text='Asset condition when returned'
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=ASSIGNMENT_STATUS_CHOICES,
        default='active',
        help_text='Assignment status'
    )

    # Notes
    assignment_notes = models.TextField(
        blank=True,
        help_text='Notes at time of assignment'
    )

    return_notes = models.TextField(
        blank=True,
        help_text='Notes at time of return'
    )

    # Acknowledgment
    employee_acknowledged = models.BooleanField(
        default=False,
        help_text='Employee acknowledged receipt of asset'
    )

    acknowledgment_signature = models.TextField(
        blank=True,
        help_text='Digital signature or reference'
    )

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    assigned_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='asset_assignments_created',
        help_text='User who assigned the asset'
    )
    returned_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='asset_returns_processed',
        help_text='User who processed the return'
    )

    class Meta:
        db_table = 'hr_asset_assignment'
        verbose_name = 'Asset Assignment'
        verbose_name_plural = 'Asset Assignments'
        ordering = ['-assignment_date']
        indexes = [
            models.Index(fields=['employee', 'status']),
            models.Index(fields=['asset', 'status']),
            models.Index(fields=['assignment_date']),
            models.Index(fields=['expected_return_date']),
        ]

    def __str__(self):
        return f"{self.asset.asset_tag} → {self.employee.employee_code} ({self.assignment_date})"

    def clean(self):
        """Validate assignment."""
        # Check if asset is available for assignment
        if not self.pk:  # New assignment
            if self.asset.status != 'available':
                raise ValidationError({
                    'asset': f'Asset is not available (current status: {self.asset.get_status_display()})'
                })

            # Check for active assignments
            active_assignments = AssetAssignment.objects.filter(
                asset=self.asset,
                status='active'
            ).exclude(pk=self.pk)

            if active_assignments.exists():
                raise ValidationError({
                    'asset': 'Asset is already assigned to another employee'
                })

        # Validate return date
        if self.actual_return_date and self.actual_return_date < self.assignment_date:
            raise ValidationError({
                'actual_return_date': 'Return date cannot be before assignment date'
            })

    @property
    def is_active(self):
        """Check if assignment is currently active."""
        return self.status == 'active' and not self.actual_return_date

    @property
    def is_overdue(self):
        """Check if expected return date has passed."""
        if not self.expected_return_date or self.actual_return_date:
            return False
        from django.utils import timezone
        return self.expected_return_date < timezone.now().date()

    def save(self, *args, **kwargs):
        # Update asset status based on assignment
        if self.pk:  # Existing assignment
            old_assignment = AssetAssignment.objects.get(pk=self.pk)
            # If being returned, update asset status
            if not old_assignment.actual_return_date and self.actual_return_date:
                self.status = 'returned'
                self.asset.status = 'available'
                self.asset.condition = self.condition_at_return or self.asset.condition
                self.asset.save()
        else:  # New assignment
            # Mark asset as assigned
            self.asset.status = 'assigned'
            self.asset.save()

        super().save(*args, **kwargs)

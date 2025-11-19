"""
Asset Registry models - Core CMMS master data.
"""
import uuid
from django.db import models
from django.conf import settings
from floor_app.mixins import AuditMixin, SoftDeleteMixin, PublicIdMixin


class AssetCategory(AuditMixin, SoftDeleteMixin, models.Model):
    """Category/type of asset (Grinder, Oven, Brazing Station, etc.)"""

    class DefaultCriticality(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'
        CRITICAL = 'CRITICAL', 'Critical'

    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True, help_text="Short code like GRN, OVN")
    description = models.TextField(blank=True)
    default_criticality = models.CharField(
        max_length=10, choices=DefaultCriticality.choices, default=DefaultCriticality.MEDIUM
    )
    icon = models.CharField(max_length=50, blank=True, help_text="Bootstrap icon class")
    color = models.CharField(max_length=7, default='#6366f1')
    is_active = models.BooleanField(default=True)

    # PM defaults
    default_pm_interval_days = models.PositiveIntegerField(
        null=True, blank=True, help_text="Default PM frequency in days"
    )

    class Meta:
        verbose_name = 'Asset Category'
        verbose_name_plural = 'Asset Categories'
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def asset_count(self):
        return self.assets.filter(is_deleted=False).count()


class AssetLocation(AuditMixin, SoftDeleteMixin, models.Model):
    """Physical location of assets (hierarchical: Site → Building → Area → Zone)"""

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=30, unique=True)
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, related_name='children'
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Asset Location'
        verbose_name_plural = 'Asset Locations'
        ordering = ['order', 'name']

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name

    @property
    def full_path(self):
        if self.parent:
            return f"{self.parent.full_path} > {self.name}"
        return self.name

    @property
    def depth(self):
        if self.parent:
            return self.parent.depth + 1
        return 0


class Asset(AuditMixin, SoftDeleteMixin, PublicIdMixin, models.Model):
    """Main asset/equipment registry."""

    class Status(models.TextChoices):
        IN_SERVICE = 'IN_SERVICE', 'In Service'
        UNDER_MAINTENANCE = 'UNDER_MAINTENANCE', 'Under Maintenance'
        OUT_OF_SERVICE = 'OUT_OF_SERVICE', 'Out of Service'
        STANDBY = 'STANDBY', 'Standby'
        SCRAPPED = 'SCRAPPED', 'Scrapped'

    class Criticality(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'
        CRITICAL = 'CRITICAL', 'Critical - Production Stopper'

    # Core identification
    asset_code = models.CharField(
        max_length=50, unique=True, help_text="Internal asset tag (e.g., GRN-001)"
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    # Classification
    category = models.ForeignKey(
        AssetCategory, on_delete=models.PROTECT, related_name='assets'
    )
    location = models.ForeignKey(
        AssetLocation, on_delete=models.SET_NULL, null=True, blank=True, related_name='assets'
    )

    # Status & Criticality
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.IN_SERVICE)
    criticality = models.CharField(max_length=10, choices=Criticality.choices, default=Criticality.MEDIUM)

    # Equipment details
    manufacturer = models.CharField(max_length=100, blank=True)
    model_number = models.CharField(max_length=100, blank=True)
    serial_number = models.CharField(max_length=100, blank=True)
    year_manufactured = models.PositiveIntegerField(null=True, blank=True)

    # Ownership & Warranty
    purchase_date = models.DateField(null=True, blank=True)
    purchase_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    warranty_expires = models.DateField(null=True, blank=True)
    vendor = models.CharField(max_length=255, blank=True)

    # External references
    erp_asset_number = models.CharField(max_length=50, blank=True, help_text="ERP system asset ID")
    barcode = models.CharField(max_length=100, blank=True)
    qr_token = models.CharField(
        max_length=50, unique=True, blank=True,
        help_text="Unique token for QR code scanning"
    )

    # Technical specs
    specifications = models.JSONField(default=dict, blank=True, help_text="Technical specifications")
    notes = models.TextField(blank=True)

    # Operational data
    installation_date = models.DateField(null=True, blank=True)
    last_pm_date = models.DateTimeField(null=True, blank=True)
    next_pm_date = models.DateTimeField(null=True, blank=True)
    meter_reading = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text="Current meter/hour reading"
    )
    meter_unit = models.CharField(max_length=20, default='hours', help_text="e.g., hours, cycles, km")

    # Responsible person
    responsible_department = models.ForeignKey(
        'hr.Department', on_delete=models.SET_NULL, null=True, blank=True, related_name='assets'
    )
    primary_operator = models.ForeignKey(
        'hr.HREmployee', on_delete=models.SET_NULL, null=True, blank=True, related_name='operated_assets'
    )

    # Financial tracking
    replacement_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    salvage_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    depreciation_method = models.CharField(max_length=50, blank=True)
    expected_life_years = models.PositiveIntegerField(null=True, blank=True)

    # Flags
    is_critical = models.BooleanField(default=False, help_text="Critical asset that can stop production")
    requires_certification = models.BooleanField(default=False, help_text="Operators need certification")
    has_safety_lockout = models.BooleanField(default=False, help_text="Requires LOTO procedures")

    class Meta:
        verbose_name = 'Asset'
        verbose_name_plural = 'Assets'
        ordering = ['asset_code']
        indexes = [
            models.Index(fields=['asset_code']),
            models.Index(fields=['status', 'criticality']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['location', 'status']),
            models.Index(fields=['qr_token']),
            models.Index(fields=['is_critical']),
            # Performance indexes for common queries
            models.Index(fields=['-last_maintenance_date'], name='idx_asset_last_maint'),
            models.Index(fields=['next_pm_due_date'], name='idx_asset_next_pm'),
            models.Index(fields=['manufacturer', 'model_number'], name='idx_asset_mfr_model'),
            models.Index(fields=['is_deleted', 'status'], name='idx_asset_active'),
        ]

    def __str__(self):
        return f"{self.asset_code} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.qr_token:
            self.qr_token = f"AST-{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)

    @property
    def age_years(self):
        if self.purchase_date:
            from django.utils import timezone
            delta = timezone.now().date() - self.purchase_date
            return round(delta.days / 365, 1)
        return None

    @property
    def warranty_status(self):
        if self.warranty_expires:
            from django.utils import timezone
            if timezone.now().date() > self.warranty_expires:
                return 'EXPIRED'
            days_left = (self.warranty_expires - timezone.now().date()).days
            if days_left <= 30:
                return 'EXPIRING_SOON'
            return 'ACTIVE'
        return 'UNKNOWN'

    @property
    def open_work_orders_count(self):
        return self.work_orders.exclude(
            status__in=['COMPLETED', 'CANCELLED']
        ).count()

    @property
    def total_downtime_hours(self):
        from django.db.models import Sum
        total = self.downtime_events.aggregate(total=Sum('duration_minutes'))['total']
        return (total or 0) / 60


class AssetDocument(models.Model):
    """Documents attached to assets (manuals, drawings, SOPs)."""

    class DocumentType(models.TextChoices):
        MANUAL = 'MANUAL', 'User Manual'
        OEM_GUIDE = 'OEM_GUIDE', 'OEM Guide'
        SOP = 'SOP', 'Standard Operating Procedure'
        DRAWING = 'DRAWING', 'Technical Drawing'
        WARRANTY = 'WARRANTY', 'Warranty Document'
        CERTIFICATE = 'CERTIFICATE', 'Calibration/Certificate'
        SAFETY = 'SAFETY', 'Safety Data Sheet'
        OTHER = 'OTHER', 'Other'

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='documents')
    document = models.ForeignKey(
        'knowledge.Document', on_delete=models.CASCADE, related_name='asset_usages',
        null=True, blank=True
    )
    document_type = models.CharField(max_length=20, choices=DocumentType.choices, default=DocumentType.OTHER)
    description = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False, help_text="Primary document for this type")

    class Meta:
        verbose_name = 'Asset Document'
        verbose_name_plural = 'Asset Documents'
        unique_together = [['asset', 'document']]

    def __str__(self):
        return f"{self.asset.asset_code} - {self.document.title}"


class AssetMeterReading(models.Model):
    """Track meter/counter readings for assets."""

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='meter_readings')
    reading_date = models.DateTimeField()
    reading_value = models.DecimalField(max_digits=12, decimal_places=2)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = 'Meter Reading'
        verbose_name_plural = 'Meter Readings'
        ordering = ['-reading_date']
        indexes = [
            models.Index(fields=['asset', 'reading_date']),
        ]

    def __str__(self):
        return f"{self.asset.asset_code}: {self.reading_value} @ {self.reading_date}"

"""
Asset and Equipment Registry Models

Core models for managing factory assets, equipment, and their documentation.
"""
import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from floor_app.mixins import AuditMixin, SoftDeleteMixin, PublicIdMixin


class AssetCategory(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Categories for grouping assets (e.g., Grinder, Oven, Compressor, Forklift).
    Used for filtering, PM templates, and reporting.
    """

    code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Unique category code (e.g., GRND, OVEN, COMP)"
    )
    name = models.CharField(
        max_length=100,
        help_text="Category name"
    )
    description = models.TextField(
        blank=True,
        default="",
        help_text="Detailed description of this category"
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subcategories',
        help_text="Parent category for hierarchy"
    )

    # PM defaults
    default_pm_interval_days = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Default PM interval in days for assets in this category"
    )
    requires_certification = models.BooleanField(
        default=False,
        help_text="Whether technicians need special certification to work on these assets"
    )

    # Display order
    sort_order = models.PositiveIntegerField(
        default=0,
        help_text="Display order in lists"
    )

    class Meta:
        db_table = "maintenance_asset_category"
        verbose_name = "Asset Category"
        verbose_name_plural = "Asset Categories"
        ordering = ['sort_order', 'code']
        indexes = [
            models.Index(fields=['code'], name='ix_maint_cat_code'),
            models.Index(fields=['parent'], name='ix_maint_cat_parent'),
        ]

    def __str__(self):
        if self.parent:
            return f"{self.parent.code} > {self.code} - {self.name}"
        return f"{self.code} - {self.name}"

    @property
    def full_path(self):
        """Return the full hierarchical path."""
        if self.parent:
            return f"{self.parent.full_path} > {self.name}"
        return self.name

    @property
    def asset_count(self):
        """Count of assets in this category."""
        return self.assets.filter(is_deleted=False).count()


class AssetLocation(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Hierarchical locations for assets (Site → Area → Zone).
    Examples: PDC Workshop, Roller Cone Area, Matrix Infiltration, NDT Room, Yard.
    """

    code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Unique location code (e.g., PDC-WS, RC-AREA)"
    )
    name = models.CharField(
        max_length=150,
        help_text="Location name"
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sublocations',
        help_text="Parent location for hierarchy"
    )
    description = models.TextField(
        blank=True,
        default="",
        help_text="Description of this location"
    )

    # Contact info for location
    responsible_person_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="ID of HR Employee responsible for this location"
    )
    responsible_person_name = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Name of responsible person (denormalized)"
    )
    contact_phone = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="Contact phone for this location"
    )

    # Physical details
    building = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Building name or number"
    )
    floor_level = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="Floor or level"
    )

    # Display order
    sort_order = models.PositiveIntegerField(
        default=0,
        help_text="Display order in lists"
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Whether this location is currently active"
    )

    class Meta:
        db_table = "maintenance_asset_location"
        verbose_name = "Asset Location"
        verbose_name_plural = "Asset Locations"
        ordering = ['sort_order', 'code']
        indexes = [
            models.Index(fields=['code'], name='ix_maint_loc_code'),
            models.Index(fields=['parent'], name='ix_maint_loc_parent'),
            models.Index(fields=['is_active'], name='ix_maint_loc_active'),
        ]

    def __str__(self):
        if self.parent:
            return f"{self.parent.code} > {self.code} - {self.name}"
        return f"{self.code} - {self.name}"

    @property
    def full_path(self):
        """Return the full hierarchical path."""
        if self.parent:
            return f"{self.parent.full_path} > {self.name}"
        return self.name

    @property
    def asset_count(self):
        """Count of assets in this location."""
        return self.assets.filter(is_deleted=False).count()


class Asset(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Central asset registry - the main equipment/machine master.
    Each physical piece of equipment in the factory.
    """

    STATUS_CHOICES = (
        ('IN_SERVICE', 'In Service'),
        ('UNDER_MAINTENANCE', 'Under Maintenance'),
        ('OUT_OF_SERVICE', 'Out of Service'),
        ('SCRAPPED', 'Scrapped'),
        ('DISPOSED', 'Disposed'),
    )

    CRITICALITY_CHOICES = (
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    )

    # Primary Identification
    asset_code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Internal asset tag/code (e.g., AST-2025-0001)"
    )
    name = models.CharField(
        max_length=200,
        help_text="Asset name/title"
    )
    description = models.TextField(
        blank=True,
        default="",
        help_text="Detailed description of the asset"
    )

    # Classification
    category = models.ForeignKey(
        AssetCategory,
        on_delete=models.PROTECT,
        related_name='assets',
        help_text="Asset category"
    )
    location = models.ForeignKey(
        AssetLocation,
        on_delete=models.PROTECT,
        related_name='assets',
        help_text="Physical location of the asset"
    )
    parent_asset = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sub_equipment',
        help_text="Parent asset (for sub-equipment)"
    )

    # Manufacturer Information
    manufacturer = models.CharField(
        max_length=150,
        blank=True,
        default="",
        help_text="Manufacturer name"
    )
    model_number = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Model number"
    )
    serial_number = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Serial number from manufacturer"
    )

    # Status & Criticality
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='IN_SERVICE',
        db_index=True,
        help_text="Current operational status"
    )
    criticality = models.CharField(
        max_length=10,
        choices=CRITICALITY_CHOICES,
        default='MEDIUM',
        db_index=True,
        help_text="How critical this asset is to production"
    )
    is_critical_production_asset = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Mark if this asset can stop major production when down"
    )

    # Important Dates
    installation_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date when asset was installed/commissioned"
    )
    warranty_expiry_date = models.DateField(
        null=True,
        blank=True,
        help_text="Warranty expiration date"
    )
    last_maintenance_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date of last maintenance performed"
    )
    next_pm_due_date = models.DateField(
        null=True,
        blank=True,
        help_text="Next scheduled preventive maintenance date"
    )

    # ERP Integration
    erp_asset_number = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Asset number from ERP system"
    )

    # QR/Barcode Token
    qr_token = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        db_index=True,
        help_text="Unique token for QR code scanning"
    )

    # Financial Information
    purchase_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Original purchase cost"
    )
    purchase_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date of purchase"
    )
    replacement_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Estimated replacement cost"
    )
    depreciation_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Annual depreciation rate (%)"
    )

    # Meter-Based PM Support
    current_meter_reading = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Current meter reading (hours, cycles, km, etc.)"
    )
    meter_unit = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="Unit of meter measurement (hours, cycles, km)"
    )
    last_meter_update = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When meter was last updated"
    )

    # Additional Info
    specifications = models.TextField(
        blank=True,
        default="",
        help_text="Technical specifications"
    )
    notes = models.TextField(
        blank=True,
        default="",
        help_text="Additional notes"
    )

    class Meta:
        db_table = "maintenance_asset"
        verbose_name = "Asset"
        verbose_name_plural = "Assets"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['asset_code'], name='ix_maint_asset_code'),
            models.Index(fields=['status', 'criticality'], name='ix_maint_asset_stat_crit'),
            models.Index(fields=['category', 'location'], name='ix_maint_asset_cat_loc'),
            models.Index(fields=['qr_token'], name='ix_maint_asset_qr'),
            models.Index(fields=['is_critical_production_asset'], name='ix_maint_asset_critical'),
            models.Index(fields=['next_pm_due_date'], name='ix_maint_asset_next_pm'),
        ]

    def __str__(self):
        return f"{self.asset_code} - {self.name}"

    def save(self, *args, **kwargs):
        # Auto-generate QR token if not set
        if not self.qr_token:
            self.qr_token = f"AST-{self.public_id.hex[:12].upper()}"
        super().save(*args, **kwargs)

    @property
    def is_under_warranty(self):
        """Check if asset is still under warranty."""
        if self.warranty_expiry_date:
            return self.warranty_expiry_date >= timezone.now().date()
        return False

    @property
    def days_since_last_maintenance(self):
        """Days since last maintenance."""
        if self.last_maintenance_date:
            delta = timezone.now().date() - self.last_maintenance_date
            return delta.days
        return None

    @property
    def pm_overdue(self):
        """Check if PM is overdue."""
        if self.next_pm_due_date:
            return self.next_pm_due_date < timezone.now().date()
        return False

    @property
    def status_display_class(self):
        """Bootstrap class for status badge."""
        mapping = {
            'IN_SERVICE': 'success',
            'UNDER_MAINTENANCE': 'warning',
            'OUT_OF_SERVICE': 'danger',
            'SCRAPPED': 'secondary',
            'DISPOSED': 'dark',
        }
        return mapping.get(self.status, 'secondary')

    @property
    def criticality_display_class(self):
        """Bootstrap class for criticality badge."""
        mapping = {
            'LOW': 'info',
            'MEDIUM': 'primary',
            'HIGH': 'warning',
            'CRITICAL': 'danger',
        }
        return mapping.get(self.criticality, 'secondary')


class AssetDocument(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Documents attached to assets (manuals, drawings, SOPs, OEM guides, photos).
    """

    DOC_TYPE_CHOICES = (
        ('MANUAL', 'User Manual'),
        ('DRAWING', 'Technical Drawing'),
        ('SOP', 'Standard Operating Procedure'),
        ('WARRANTY', 'Warranty Document'),
        ('CERTIFICATE', 'Certificate'),
        ('PHOTO', 'Photo'),
        ('SPEC_SHEET', 'Specification Sheet'),
        ('MAINTENANCE_GUIDE', 'Maintenance Guide'),
        ('SAFETY', 'Safety Document'),
        ('OTHER', 'Other'),
    )

    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name='documents',
        help_text="Asset this document belongs to"
    )
    title = models.CharField(
        max_length=200,
        help_text="Document title"
    )
    doc_type = models.CharField(
        max_length=20,
        choices=DOC_TYPE_CHOICES,
        default='OTHER',
        help_text="Type of document"
    )
    file = models.FileField(
        upload_to='maintenance/asset_docs/%Y/%m/',
        help_text="Uploaded file"
    )
    description = models.TextField(
        blank=True,
        default="",
        help_text="Description of this document"
    )

    # Version control
    version = models.CharField(
        max_length=50,
        blank=True,
        default="1.0",
        help_text="Document version"
    )
    is_current_version = models.BooleanField(
        default=True,
        help_text="Whether this is the current version"
    )

    class Meta:
        db_table = "maintenance_asset_document"
        verbose_name = "Asset Document"
        verbose_name_plural = "Asset Documents"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['asset', 'doc_type'], name='ix_maint_doc_asset_type'),
            models.Index(fields=['is_current_version'], name='ix_maint_doc_current'),
        ]

    def __str__(self):
        return f"{self.asset.asset_code} - {self.title} ({self.get_doc_type_display()})"

    @property
    def file_extension(self):
        """Get file extension."""
        if self.file:
            return self.file.name.split('.')[-1].upper()
        return ""

    @property
    def file_size_display(self):
        """Get human-readable file size."""
        if self.file:
            size = self.file.size
            if size < 1024:
                return f"{size} B"
            elif size < 1024 * 1024:
                return f"{size / 1024:.1f} KB"
            else:
                return f"{size / (1024 * 1024):.1f} MB"
        return "0 B"

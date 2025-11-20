"""
Bill of Materials (BOM) for Production, Retrofit, and Repair

BOMs define what components are needed to:
- Produce a new PDC bit from scratch
- Retrofit an existing bit (change configuration)
- Repair a bit (replace cutters, sleeves, etc.)

BOMs are linked to specific BitDesignRevision (MAT) targets.

MOVED FROM: floor_app.operations.inventory.models.bom
REASON: Engineering owns BOM definitions and design data
"""

from django.db import models
from django.core.exceptions import ValidationError
from floor_app.mixins import AuditMixin, SoftDeleteMixin, PublicIdMixin


class BOMHeader(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Bill of Materials header - defines what design is being produced/repaired.

    Examples:
    - Production BOM for L5 MAT HP-X123-M2
    - Retrofit BOM to convert M1 to M2
    - Repair template for replacing cutters
    """

    BOM_TYPE_CHOICES = (
        ('PRODUCTION', 'Production (New Assembly)'),
        ('RETROFIT', 'Retrofit (Design Change)'),
        ('REPAIR', 'Repair (Component Replacement)'),
        ('TEMPLATE', 'Generic Template'),
        ('DISASSEMBLY', 'Disassembly BOM'),
    )

    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('PENDING_APPROVAL', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('ACTIVE', 'Active'),
        ('OBSOLETE', 'Obsolete'),
    )

    # Identification
    bom_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="BOM number/code (e.g., BOM-HP-X123-M2-PROD)"
    )
    name = models.CharField(
        max_length=200,
        help_text="Descriptive name for this BOM"
    )
    description = models.TextField(blank=True, default="")

    # Type and target
    bom_type = models.CharField(
        max_length=20,
        choices=BOM_TYPE_CHOICES,
        default='PRODUCTION',
        help_text="Type of BOM"
    )
    target_mat = models.ForeignKey(
        'BitDesignRevision',
        on_delete=models.PROTECT,
        related_name='boms',
        help_text="Target MAT revision this BOM produces/repairs"
    )

    # Versioning
    revision = models.CharField(
        max_length=10,
        default='A',
        help_text="BOM revision (A, B, C... or 1, 2, 3...)"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT',
        db_index=True
    )

    # Effectivity
    effective_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date when this BOM becomes effective"
    )
    obsolete_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date when this BOM becomes obsolete"
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="False when superseded or obsoleted"
    )

    # Supersession
    superseded_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='supersedes',
        help_text="Newer BOM that replaces this one"
    )

    # For RETROFIT: source design
    source_mat = models.ForeignKey(
        'BitDesignRevision',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='retrofit_source_boms',
        help_text="For RETROFIT: the source MAT being converted"
    )

    # Cost and time estimates
    estimated_labor_hours = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Estimated labor hours to complete"
    )
    estimated_material_cost = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Estimated total material cost"
    )

    # ERP Integration
    erp_bom_number = models.CharField(
        max_length=50,
        blank=True,
        help_text='ERP BOM Number'
    )
    total_material_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Calculated total material cost'
    )

    notes = models.TextField(blank=True, default="")

    class Meta:
        db_table = "inventory_bom_header"  # ⚠️ KEEP original table name to preserve data
        verbose_name = "BOM Header"
        verbose_name_plural = "BOM Headers"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['bom_number'], name='ix_bom_number'),
            models.Index(fields=['target_mat', 'is_active'], name='ix_bom_target_active'),
            models.Index(fields=['bom_type', 'status'], name='ix_bom_type_status'),
        ]

    def __str__(self):
        return f"{self.bom_number} ({self.bom_type}) -> {self.target_mat.mat_number}"

    def clean(self):
        """Validate BOM data."""
        super().clean()

        # RETROFIT BOM must have source_mat
        if self.bom_type == 'RETROFIT' and not self.source_mat:
            raise ValidationError({
                'source_mat': "Retrofit BOMs must specify the source MAT."
            })

        # Source and target should be different for RETROFIT
        if self.bom_type == 'RETROFIT' and self.source_mat == self.target_mat:
            raise ValidationError({
                'target_mat': "Source and target MAT must be different for retrofit."
            })

    @property
    def total_component_count(self):
        """Total number of component lines in this BOM."""
        return self.lines.count()

    @property
    def total_material_cost(self):
        """Calculate total material cost from component lines."""
        from django.db.models import Sum, F
        result = self.lines.aggregate(
            total=Sum(F('quantity_required') * F('unit_cost'))
        )
        return result['total'] or 0

    def get_active_lines(self):
        """Get all active (non-deleted) BOM lines."""
        return self.lines.filter(is_active=True).order_by('line_number')

    def copy_as_new_revision(self, new_revision_code):
        """
        Create a copy of this BOM with a new revision code.

        Returns the new BOMHeader instance.
        """
        new_bom = BOMHeader.objects.create(
            bom_number=f"{self.bom_number}-{new_revision_code}",
            name=self.name,
            description=self.description,
            bom_type=self.bom_type,
            target_mat=self.target_mat,
            revision=new_revision_code,
            status='DRAFT',
            source_mat=self.source_mat,
            estimated_labor_hours=self.estimated_labor_hours,
            notes=f"Copied from {self.bom_number}"
        )

        # Copy all lines
        for line in self.get_active_lines():
            BOMLine.objects.create(
                bom_header=new_bom,
                line_number=line.line_number,
                component_item=line.component_item,
                quantity_required=line.quantity_required,
                uom=line.uom,
                required_condition=line.required_condition,
                required_ownership=line.required_ownership,
                is_optional=line.is_optional,
                scrap_factor=line.scrap_factor,
                position_reference=line.position_reference,
                unit_cost=line.unit_cost,
                notes=line.notes
            )

        return new_bom


class BOMLine(AuditMixin, SoftDeleteMixin):
    """
    Individual component line in a BOM.

    Specifies what item, how much, and under what conditions.
    """

    bom_header = models.ForeignKey(
        BOMHeader,
        on_delete=models.CASCADE,
        related_name='lines',
        help_text="Parent BOM header"
    )
    line_number = models.IntegerField(
        help_text="Line sequence number within the BOM"
    )

    # Component specification
    component_item = models.ForeignKey(
        'inventory.Item',  # ⚠️ Using string reference for cross-app reference
        on_delete=models.PROTECT,
        related_name='bom_usages',
        help_text="Item to be used as component"
    )
    quantity_required = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        help_text="Quantity of component required per unit"
    )
    uom = models.ForeignKey(
        'inventory.UnitOfMeasure',  # ⚠️ Using string reference for cross-app reference
        on_delete=models.PROTECT,
        related_name='bom_lines',
        help_text="Unit of measure for quantity"
    )

    # Optional constraints on source stock
    required_condition = models.ForeignKey(
        'inventory.ConditionType',  # ⚠️ Using string reference for cross-app reference
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bom_line_requirements',
        help_text="Component must be in this condition (e.g., NEW only)"
    )
    required_ownership = models.ForeignKey(
        'inventory.OwnershipType',  # ⚠️ Using string reference for cross-app reference
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bom_line_requirements',
        help_text="Component must have this ownership"
    )

    # Flexibility flags
    is_optional = models.BooleanField(
        default=False,
        help_text="True if this component is optional"
    )
    is_alternative = models.BooleanField(
        default=False,
        help_text="True if this is an alternative to another line"
    )
    alternative_group = models.CharField(
        max_length=20,
        blank=True,
        default="",
        help_text="Group ID for alternative components (choose one from group)"
    )

    # Waste/scrap factor
    scrap_factor = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Extra percentage for scrap/waste (e.g., 5.00 for 5%)"
    )

    # Position in assembly (for PDC bits)
    position_reference = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="Position reference in assembly (e.g., 'Blade 1 Position 3')"
    )

    # Cost tracking
    unit_cost = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Unit cost for this component"
    )

    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, default="")

    class Meta:
        db_table = "inventory_bom_line"  # ⚠️ KEEP original table name to preserve data
        verbose_name = "BOM Line"
        verbose_name_plural = "BOM Lines"
        ordering = ['bom_header', 'line_number']
        constraints = [
            models.UniqueConstraint(
                fields=['bom_header', 'line_number'],
                name='uq_bom_line_number'
            ),
        ]
        indexes = [
            models.Index(fields=['bom_header', 'line_number'], name='ix_bl_header_line'),
            models.Index(fields=['component_item'], name='ix_bl_component'),
        ]

    def __str__(self):
        return f"{self.bom_header.bom_number} L{self.line_number}: {self.component_item.sku} x {self.quantity_required}"

    @property
    def extended_quantity(self):
        """Quantity including scrap factor."""
        return self.quantity_required * (1 + self.scrap_factor / 100)

    @property
    def extended_cost(self):
        """Total cost including scrap factor."""
        if self.unit_cost:
            return self.extended_quantity * self.unit_cost
        return None

    @property
    def is_available(self):
        """
        Check if required quantity is available in stock.

        Considers condition and ownership constraints if specified.
        """
        if self.component_item.is_serialized:
            # For serialized items, check available count
            query = self.component_item.serial_units.filter(status='IN_STOCK')
            if self.required_condition:
                query = query.filter(condition=self.required_condition)
            if self.required_ownership:
                query = query.filter(ownership=self.required_ownership)
            return query.count() >= self.quantity_required
        else:
            # For non-serialized, check stock quantities
            from django.db.models import Sum
            query = self.component_item.inventory_stocks.all()
            if self.required_condition:
                query = query.filter(condition=self.required_condition)
            if self.required_ownership:
                query = query.filter(ownership=self.required_ownership)

            result = query.aggregate(available=Sum('quantity_on_hand') - Sum('quantity_reserved'))
            available = result['available'] or 0
            return available >= self.extended_quantity

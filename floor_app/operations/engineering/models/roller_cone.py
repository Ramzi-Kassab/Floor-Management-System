"""
Roller Cone Bit Models

Models for roller cone (tricone/bicone) drilling bits - a different technology from PDC bits.
Roller cone bits use rotating cones with teeth or tungsten carbide inserts instead of fixed PDC cutters.

Key Differences from PDC:
- Uses rotating cones instead of fixed cutters
- Bearings and seals are critical components
- Teeth can be milled (steel tooth) or insert type (tungsten carbide)
- Different BOM structure (cones, bearings, seals, nozzles)

MOVED FROM: floor_app.operations.inventory.models.roller_cone
REASON: Engineering owns design and BOM definitions, not inventory
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from floor_app.mixins import AuditMixin, SoftDeleteMixin


class RollerConeBitType(models.Model):
    """
    Types of roller cone bits (Rock Bit Types per IADC classification)

    IADC Classification System:
    - Series 1-3: Soft formations (long tooth, widely spaced)
    - Series 4-5: Medium formations
    - Series 6-7: Medium-hard formations
    - Series 8: Hard formations (short tooth, closely spaced)

    Examples:
    - 111: Soft, low compressive strength formations
    - 437: Medium formations, medium compressive strength
    - 537: Medium-hard formations with insert teeth
    - 617: Hard, abrasive formations
    """

    iadc_code = models.CharField(
        max_length=10,
        unique=True,
        db_index=True,
        help_text="IADC classification code (e.g., 111, 437, 537, 617)"
    )
    name = models.CharField(
        max_length=200,
        help_text="Descriptive name"
    )
    formation_type = models.CharField(
        max_length=100,
        help_text="Formation type description (e.g., Soft, Medium, Hard)"
    )

    # Classification details
    series = models.CharField(
        max_length=10,
        help_text="Series number (1-8)"
    )
    tooth_type = models.CharField(
        max_length=50,
        choices=[
            ('MILLED', 'Milled Steel Tooth'),
            ('INSERT', 'Tungsten Carbide Insert'),
        ],
        help_text="Type of cutting structure"
    )

    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        db_table = "inventory_roller_cone_bit_type"  # ⚠️ KEEP original table name to preserve data
        verbose_name = "Roller Cone Bit Type"
        verbose_name_plural = "Roller Cone Bit Types"
        ordering = ['series', 'iadc_code']

    def __str__(self):
        return f"{self.iadc_code} - {self.name}"


class RollerConeBearing(models.Model):
    """
    Bearing types for roller cone bits

    Common Types:
    - Open Roller Bearing: Traditional, lubricant from mud
    - Sealed Roller Bearing: Grease-sealed system
    - Journal Bearing: Friction bearing with lubrication
    - Sealed Journal: Journal bearing with seal system
    """

    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Bearing code"
    )
    name = models.CharField(max_length=100)

    bearing_type = models.CharField(
        max_length=50,
        choices=[
            ('OPEN_ROLLER', 'Open Roller Bearing'),
            ('SEALED_ROLLER', 'Sealed Roller Bearing'),
            ('JOURNAL', 'Journal Bearing'),
            ('SEALED_JOURNAL', 'Sealed Journal Bearing'),
            ('BALL', 'Ball Bearing'),
        ]
    )

    is_sealed = models.BooleanField(
        default=False,
        help_text="Whether bearing has seal system"
    )

    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "inventory_roller_cone_bearing"  # ⚠️ KEEP original table name to preserve data
        verbose_name = "Roller Cone Bearing Type"
        verbose_name_plural = "Roller Cone Bearing Types"
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"


class RollerConeSeal(models.Model):
    """
    Seal types for sealed bearing systems

    Common Seal Systems:
    - Metal Face Seal
    - O-Ring Seal
    - Hybrid Seal (multiple sealing elements)
    - No Seal (open bearing)
    """

    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)

    seal_type = models.CharField(
        max_length=50,
        choices=[
            ('METAL_FACE', 'Metal Face Seal'),
            ('O_RING', 'O-Ring Seal'),
            ('HYBRID', 'Hybrid Seal System'),
            ('NONE', 'No Seal (Open Bearing)'),
        ]
    )

    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "inventory_roller_cone_seal"  # ⚠️ KEEP original table name to preserve data
        verbose_name = "Roller Cone Seal Type"
        verbose_name_plural = "Roller Cone Seal Types"
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"


class RollerConeDesign(AuditMixin, SoftDeleteMixin):
    """
    Roller cone bit design specifications

    Links to BitDesign and provides roller cone specific attributes.
    """

    # Link to main bit design
    bit_design = models.OneToOneField(
        'inventory.BitDesign',
        on_delete=models.CASCADE,
        related_name='roller_cone_design',
        help_text="Parent bit design (must be roller cone type)"
    )

    # Cone configuration
    number_of_cones = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(4)],
        default=3,
        help_text="Number of cones (typically 3 for tricone, 2 for bicone)"
    )

    # IADC Classification
    bit_type = models.ForeignKey(
        RollerConeBitType,
        on_delete=models.PROTECT,
        related_name='designs',
        help_text="IADC bit type classification"
    )

    # Bearing and Seal
    bearing_type = models.ForeignKey(
        RollerConeBearing,
        on_delete=models.PROTECT,
        related_name='designs'
    )
    seal_type = models.ForeignKey(
        RollerConeSeal,
        on_delete=models.PROTECT,
        related_name='designs',
        null=True,
        blank=True
    )

    # Cutting Structure
    tooth_structure = models.CharField(
        max_length=50,
        choices=[
            ('MILLED', 'Milled Steel Tooth'),
            ('INSERT', 'Tungsten Carbide Insert'),
            ('HYBRID', 'Hybrid (Mixed)'),
        ],
        help_text="Type of cutting elements on cones"
    )

    # Insert details (if applicable)
    insert_type = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Type of inserts if insert bit (e.g., Chisel, Conical, Wedge)"
    )
    insert_size_range = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Size range of inserts"
    )
    total_insert_count = models.IntegerField(
        null=True,
        blank=True,
        help_text="Total number of inserts per bit"
    )

    # Nozzle configuration
    nozzle_count = models.IntegerField(
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
        help_text="Number of nozzle ports"
    )
    nozzle_configuration = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Standard nozzle setup (e.g., 3x12, 4x14)"
    )

    # Journal angles (cone offset angles)
    journal_angle_1 = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Journal angle for cone 1 (degrees)"
    )
    journal_angle_2 = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Journal angle for cone 2 (degrees)"
    )
    journal_angle_3 = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Journal angle for cone 3 (degrees)"
    )

    # Offset (how much cones are offset from bit center)
    cone_offset_inches = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        null=True,
        blank=True,
        help_text="Cone offset from center (inches)"
    )

    # Gage protection
    gage_protection = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Gage protection features (hardfacing, inserts, etc.)"
    )

    # Hydraulics
    jet_velocity_optimized = models.BooleanField(
        default=False,
        help_text="Whether bit is optimized for jet velocity"
    )
    extended_nozzles = models.BooleanField(
        default=False,
        help_text="Whether bit has extended nozzles"
    )

    # Performance characteristics
    recommended_rpm_min = models.IntegerField(
        null=True,
        blank=True,
        help_text="Minimum recommended RPM"
    )
    recommended_rpm_max = models.IntegerField(
        null=True,
        blank=True,
        help_text="Maximum recommended RPM"
    )
    recommended_wob_min_klbs = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Minimum recommended weight on bit (1000 lbs)"
    )
    recommended_wob_max_klbs = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maximum recommended weight on bit (1000 lbs)"
    )

    # Application notes
    recommended_formations = models.TextField(
        blank=True,
        default="",
        help_text="Recommended formation types and drilling conditions"
    )
    special_features = models.TextField(
        blank=True,
        default="",
        help_text="Special features or design innovations"
    )
    notes = models.TextField(blank=True, default="")

    class Meta:
        db_table = "inventory_roller_cone_design"  # ⚠️ KEEP original table name to preserve data
        verbose_name = "Roller Cone Design"
        verbose_name_plural = "Roller Cone Designs"
        ordering = ['-created_at']

    def __str__(self):
        return f"Roller Cone: {self.bit_design.design_code} ({self.number_of_cones}-Cone)"


class RollerConeComponent(AuditMixin):
    """
    Individual components for roller cone bits

    Unlike PDC cutters, roller cone bits have different component types:
    - Cones (complete cone assemblies)
    - Bearings
    - Seals
    - Inserts (for insert bits)
    - Nozzles
    - Shanks
    - Locking elements (ball plugs, snaprings)
    """

    COMPONENT_TYPE_CHOICES = [
        ('CONE', 'Cone Assembly'),
        ('BEARING_KIT', 'Bearing Kit'),
        ('SEAL_KIT', 'Seal Kit'),
        ('INSERT', 'Tungsten Carbide Insert'),
        ('NOZZLE', 'Nozzle'),
        ('SHANK', 'Bit Shank/Body'),
        ('LOCKING', 'Locking Element (Ball/Snapring)'),
        ('HARDFACING', 'Hardfacing Material'),
        ('OTHER', 'Other Component'),
    ]

    # Identification
    part_number = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Manufacturer part number"
    )
    component_type = models.CharField(
        max_length=50,
        choices=COMPONENT_TYPE_CHOICES,
        db_index=True
    )

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")

    # Manufacturer info
    manufacturer = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Component manufacturer"
    )
    oem_part_number = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="OEM/original part number if aftermarket"
    )

    # Specifications (flexible JSON for component-specific attributes)
    specifications = models.JSONField(
        default=dict,
        help_text="Component-specific specifications (size, material, etc.)"
    )

    # Pricing
    unit_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    # Inventory link
    inventory_item_id = models.BigIntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Reference to inventory.Item if stocked"
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "inventory_roller_cone_component"  # ⚠️ KEEP original table name to preserve data
        verbose_name = "Roller Cone Component"
        verbose_name_plural = "Roller Cone Components"
        ordering = ['component_type', 'part_number']
        indexes = [
            models.Index(fields=['component_type', 'is_active'], name='ix_rc_comp_type'),
            models.Index(fields=['part_number'], name='ix_rc_comp_part'),
        ]

    def __str__(self):
        return f"{self.part_number} - {self.name}"


class RollerConeBOM(AuditMixin):
    """
    Bill of Materials for Roller Cone bits

    Links components to specific bit design revisions.
    Different structure from PDC cutter BOM.
    """

    bit_design_revision = models.ForeignKey(
        'inventory.BitDesignRevision',
        on_delete=models.CASCADE,
        related_name='roller_cone_bom_lines',
        help_text="MAT number this BOM applies to"
    )

    component = models.ForeignKey(
        RollerConeComponent,
        on_delete=models.PROTECT,
        related_name='bom_usages'
    )

    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(0)],
        help_text="Quantity per bit"
    )

    # Position/location (e.g., "Cone 1", "Cone 2", "Seal - Inner")
    position = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Position or location of component in assembly"
    )

    # Alternative components
    is_optional = models.BooleanField(
        default=False,
        help_text="Whether this component is optional"
    )
    alternate_component = models.ForeignKey(
        RollerConeComponent,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alternate_for',
        help_text="Alternate/substitute component"
    )

    notes = models.TextField(blank=True, default="")

    class Meta:
        db_table = "inventory_roller_cone_bom"  # ⚠️ KEEP original table name to preserve data
        verbose_name = "Roller Cone BOM Line"
        verbose_name_plural = "Roller Cone BOM Lines"
        ordering = ['bit_design_revision', 'component__component_type', 'position']
        unique_together = [['bit_design_revision', 'component', 'position']]

    def __str__(self):
        return f"{self.bit_design_revision.mat_number} - {self.component.part_number} x{self.quantity}"

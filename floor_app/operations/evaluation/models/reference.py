"""
Reference/Lookup Tables for Evaluation & Technical Instructions

These are the foundational tables that provide controlled vocabularies
for cutter evaluation codes, feature codes, bit sections, and bit types.
"""

from django.db import models


class CutterEvaluationCode(models.Model):
    """
    Defines evaluation codes for cutter condition assessment.

    Examples:
    - X: Damaged/Replace - Cutter needs replacement
    - O: OK/Keep - Cutter is in good condition
    - S: Braze Fill - Needs braze fill repair
    - R: Rotate - Cutter can be rotated to fresh cutting face
    - L: Lost - Cutter is missing/lost
    """

    ACTION_CHOICES = (
        ('REPLACE', 'Replace Cutter'),
        ('KEEP', 'Keep As Is'),
        ('BRAZE_FILL', 'Braze Fill Repair'),
        ('ROTATE', 'Rotate Cutter'),
        ('LOST', 'Lost/Missing'),
    )

    code = models.CharField(
        max_length=10,
        unique=True,
        help_text="Single character code (e.g., X, O, S, R, L)"
    )
    name = models.CharField(
        max_length=100,
        help_text="Full name of the evaluation code"
    )
    description = models.TextField(
        blank=True,
        default="",
        help_text="Detailed description of what this code means"
    )
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        help_text="Required action for this evaluation code"
    )
    color_code = models.CharField(
        max_length=7,
        default="#FFFFFF",
        help_text="Hex color for UI display (e.g., #FF0000 for red)"
    )
    sort_order = models.IntegerField(
        default=0,
        help_text="Display order in UI"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "evaluation_cutter_evaluation_code"
        verbose_name = "Cutter Evaluation Code"
        verbose_name_plural = "Cutter Evaluation Codes"
        ordering = ['sort_order', 'code']

    def __str__(self):
        return f"{self.code} - {self.name}"


class FeatureCode(models.Model):
    """
    Defines feature codes for special conditions on bit geometry.

    Examples:
    - V: Fin Build-up - Material build-up on fin geometry
    - P: Pocket Damage - Damage to cutter pocket
    - I: Impact Arrestor Issue - Problem with impact arrestor
    - B: Body Build-up - Material build-up on body
    """

    GEOMETRY_TYPE_CHOICES = (
        ('FIN', 'Fin/Blade Geometry'),
        ('POCKET', 'Cutter Pocket'),
        ('BODY', 'Bit Body'),
        ('OTHER', 'Other Feature'),
    )

    code = models.CharField(
        max_length=10,
        unique=True,
        help_text="Feature code (e.g., V, P, I, B)"
    )
    name = models.CharField(
        max_length=100,
        help_text="Full name of the feature code"
    )
    description = models.TextField(
        blank=True,
        default="",
        help_text="Detailed description of the feature issue"
    )
    geometry_type = models.CharField(
        max_length=20,
        choices=GEOMETRY_TYPE_CHOICES,
        help_text="Type of geometry this feature relates to"
    )
    color_code = models.CharField(
        max_length=7,
        default="#FFFF00",
        help_text="Hex color for UI display"
    )
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "evaluation_feature_code"
        verbose_name = "Feature Code"
        verbose_name_plural = "Feature Codes"
        ordering = ['sort_order', 'code']

    def __str__(self):
        return f"{self.code} - {self.name}"


class BitSection(models.Model):
    """
    Defines standard sections of a PDC bit.

    Sections from center to outer:
    - CONE: Center/cone area
    - NOSE: Nose section
    - TAPER: Tapered section
    - SHOULDER: Shoulder area
    - GAUGE: Gauge/outer section
    """

    code = models.CharField(
        max_length=20,
        unique=True,
        help_text="Section code (e.g., CONE, NOSE, TAPER)"
    )
    name = models.CharField(
        max_length=100,
        help_text="Full name of the section"
    )
    description = models.TextField(
        blank=True,
        default="",
        help_text="Description of this section's location and characteristics"
    )
    sequence = models.IntegerField(
        unique=True,
        help_text="Order from center (1) to outer edge (5)"
    )
    color_code = models.CharField(
        max_length=7,
        default="#808080",
        help_text="Hex color for UI display"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "evaluation_bit_section"
        verbose_name = "Bit Section"
        verbose_name_plural = "Bit Sections"
        ordering = ['sequence']

    def __str__(self):
        return f"{self.sequence}. {self.name}"


class BitType(models.Model):
    """
    Defines bit types/designs.

    Examples:
    - HDBS: High Durability Bit System
    - SMI: Standard Matrix Impregnated
    - TSP: Thermally Stable Polycrystalline
    """

    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Bit type code (e.g., HDBS, SMI)"
    )
    name = models.CharField(
        max_length=200,
        help_text="Full name of the bit type"
    )
    description = models.TextField(
        blank=True,
        default="",
        help_text="Description of this bit type and its characteristics"
    )
    manufacturer = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Original manufacturer/designer"
    )
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "evaluation_bit_type"
        verbose_name = "Bit Type"
        verbose_name_plural = "Bit Types"
        ordering = ['sort_order', 'code']

    def __str__(self):
        return f"{self.code} - {self.name}"

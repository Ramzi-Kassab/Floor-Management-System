"""
Flexible Attributes (Controlled EAV) System

Provides extensible attributes for items without schema changes.

Use this for:
- Less common attributes (not every item needs them)
- Highly variable attributes across categories
- Attributes that change requirements over time

Do NOT use this for core/stable attributes like bit size, connection type, etc.
Those should be fixed fields for query performance.
"""

from django.db import models
from django.core.exceptions import ValidationError


class AttributeDefinition(models.Model):
    """
    Definition of a custom attribute.

    Examples:
    - Cutter diameter (NUMBER)
    - Cutter chamfer angle (NUMBER)
    - Material grade (TEXT/CHOICE)
    - Is certified (BOOLEAN)
    - Certification date (DATE)
    """

    DATA_TYPE_CHOICES = (
        ('TEXT', 'Text'),
        ('NUMBER', 'Number'),
        ('INTEGER', 'Integer'),
        ('BOOLEAN', 'Boolean'),
        ('DATE', 'Date'),
        ('DATETIME', 'Date & Time'),
        ('CHOICE', 'Choice from List'),
        ('URL', 'URL'),
    )

    code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Unique attribute code (e.g., CUTTER_DIAMETER)"
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default="")

    data_type = models.CharField(
        max_length=20,
        choices=DATA_TYPE_CHOICES,
        help_text="Type of data this attribute holds"
    )

    # For CHOICE type: list of valid options
    choice_options = models.JSONField(
        blank=True,
        null=True,
        help_text="For CHOICE type: list of valid options ['option1', 'option2']"
    )

    # For NUMBER type: optional unit of measure
    default_uom = models.ForeignKey(
        'UnitOfMeasure',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='attributes',
        help_text="Default unit of measure for NUMBER attributes"
    )

    # Validation rules (JSON object)
    validation_rules = models.JSONField(
        blank=True,
        null=True,
        help_text=(
            "Validation rules as JSON: "
            "{'min': 0, 'max': 100, 'pattern': 'regex', 'required_chars': 5}"
        )
    )

    # Display settings
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "inventory_attribute_definition"
        verbose_name = "Attribute Definition"
        verbose_name_plural = "Attribute Definitions"
        ordering = ['sort_order', 'name']

    def __str__(self):
        return f"{self.code} ({self.data_type})"

    def validate_value(self, value):
        """
        Validate that a value conforms to this attribute's type and rules.

        Returns: (is_valid, error_message)
        """
        if value is None:
            return True, None

        # Type validation
        if self.data_type == 'NUMBER':
            try:
                float(value)
            except (ValueError, TypeError):
                return False, f"Value must be a number"

        elif self.data_type == 'INTEGER':
            try:
                int(value)
            except (ValueError, TypeError):
                return False, f"Value must be an integer"

        elif self.data_type == 'BOOLEAN':
            if not isinstance(value, bool) and value not in ('true', 'false', '1', '0', True, False):
                return False, f"Value must be a boolean"

        elif self.data_type == 'CHOICE':
            if self.choice_options and value not in self.choice_options:
                return False, f"Value must be one of: {', '.join(self.choice_options)}"

        # Custom validation rules
        if self.validation_rules:
            if 'min' in self.validation_rules:
                if float(value) < self.validation_rules['min']:
                    return False, f"Value must be >= {self.validation_rules['min']}"

            if 'max' in self.validation_rules:
                if float(value) > self.validation_rules['max']:
                    return False, f"Value must be <= {self.validation_rules['max']}"

            if 'pattern' in self.validation_rules:
                import re
                if not re.match(self.validation_rules['pattern'], str(value)):
                    return False, f"Value does not match required pattern"

            if 'min_length' in self.validation_rules:
                if len(str(value)) < self.validation_rules['min_length']:
                    return False, f"Value must be at least {self.validation_rules['min_length']} characters"

        return True, None


class CategoryAttributeMap(models.Model):
    """
    Maps which attributes are applicable to which item categories.

    This controls which custom attributes are available/required for items
    in a given category.
    """

    category = models.ForeignKey(
        'ItemCategory',
        on_delete=models.CASCADE,
        related_name='attribute_mappings',
        help_text="Item category"
    )
    attribute = models.ForeignKey(
        AttributeDefinition,
        on_delete=models.CASCADE,
        related_name='category_mappings',
        help_text="Attribute to map to this category"
    )

    is_required = models.BooleanField(
        default=False,
        help_text="True if this attribute is mandatory for items in this category"
    )
    default_value = models.TextField(
        blank=True,
        default="",
        help_text="Default value for new items (if applicable)"
    )
    sort_order = models.IntegerField(
        default=0,
        help_text="Display order within the category"
    )

    class Meta:
        db_table = "inventory_category_attribute_map"
        verbose_name = "Category Attribute Map"
        verbose_name_plural = "Category Attribute Maps"
        ordering = ['category', 'sort_order']
        constraints = [
            models.UniqueConstraint(
                fields=['category', 'attribute'],
                name='uq_cat_attr_map'
            ),
        ]

    def __str__(self):
        req = " (Required)" if self.is_required else ""
        return f"{self.category.code} -> {self.attribute.code}{req}"


class ItemAttributeValue(models.Model):
    """
    Actual attribute values for items.

    Stores the value in the appropriate typed field based on the attribute's data type.
    """

    item = models.ForeignKey(
        'Item',
        on_delete=models.CASCADE,
        related_name='attribute_values',
        help_text="Item this value belongs to"
    )
    attribute = models.ForeignKey(
        AttributeDefinition,
        on_delete=models.CASCADE,
        related_name='item_values',
        help_text="Attribute definition"
    )

    # Typed value storage (only one is used based on attribute.data_type)
    value_text = models.TextField(
        blank=True,
        default="",
        help_text="Value for TEXT, CHOICE, URL types"
    )
    value_number = models.DecimalField(
        max_digits=15,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Value for NUMBER type"
    )
    value_integer = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Value for INTEGER type"
    )
    value_boolean = models.BooleanField(
        null=True,
        blank=True,
        help_text="Value for BOOLEAN type"
    )
    value_date = models.DateField(
        null=True,
        blank=True,
        help_text="Value for DATE type"
    )
    value_datetime = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Value for DATETIME type"
    )

    class Meta:
        db_table = "inventory_item_attribute_value"
        verbose_name = "Item Attribute Value"
        verbose_name_plural = "Item Attribute Values"
        constraints = [
            models.UniqueConstraint(
                fields=['item', 'attribute'],
                name='uq_item_attr_value'
            ),
        ]
        indexes = [
            models.Index(fields=['item'], name='ix_iav_item'),
            models.Index(fields=['attribute'], name='ix_iav_attribute'),
        ]

    def __str__(self):
        return f"{self.item.sku}.{self.attribute.code} = {self.get_value()}"

    def get_value(self):
        """Get the value from the appropriate typed field."""
        if self.attribute.data_type == 'TEXT':
            return self.value_text
        elif self.attribute.data_type == 'NUMBER':
            return self.value_number
        elif self.attribute.data_type == 'INTEGER':
            return self.value_integer
        elif self.attribute.data_type == 'BOOLEAN':
            return self.value_boolean
        elif self.attribute.data_type == 'DATE':
            return self.value_date
        elif self.attribute.data_type == 'DATETIME':
            return self.value_datetime
        elif self.attribute.data_type == 'CHOICE':
            return self.value_text
        elif self.attribute.data_type == 'URL':
            return self.value_text
        return None

    def set_value(self, value):
        """Set the value in the appropriate typed field."""
        # Clear all fields first
        self.value_text = ""
        self.value_number = None
        self.value_integer = None
        self.value_boolean = None
        self.value_date = None
        self.value_datetime = None

        if value is None:
            return

        if self.attribute.data_type == 'TEXT':
            self.value_text = str(value)
        elif self.attribute.data_type == 'NUMBER':
            self.value_number = float(value)
        elif self.attribute.data_type == 'INTEGER':
            self.value_integer = int(value)
        elif self.attribute.data_type == 'BOOLEAN':
            if isinstance(value, bool):
                self.value_boolean = value
            else:
                self.value_boolean = str(value).lower() in ('true', '1', 'yes')
        elif self.attribute.data_type == 'DATE':
            self.value_date = value  # Expects date object
        elif self.attribute.data_type == 'DATETIME':
            self.value_datetime = value  # Expects datetime object
        elif self.attribute.data_type == 'CHOICE':
            self.value_text = str(value)
        elif self.attribute.data_type == 'URL':
            self.value_text = str(value)

    def clean(self):
        """Validate the value against attribute rules."""
        super().clean()
        value = self.get_value()
        is_valid, error = self.attribute.validate_value(value)
        if not is_valid:
            raise ValidationError({'value': error})

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

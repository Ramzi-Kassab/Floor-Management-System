"""
Sales & Lifecycle - Customer and Operator Models
Tracks customers, operators, and their relationships.
"""
from django.db import models
from floor_app.mixins import PublicIdMixin, AuditMixin, SoftDeleteMixin


class Customer(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Customer/Operator entity.
    Represents oil companies, drilling contractors, and service companies.
    """
    CUSTOMER_TYPE_CHOICES = [
        ('OPERATOR', 'Oil & Gas Operator'),
        ('DRILLING_CONTRACTOR', 'Drilling Contractor'),
        ('SERVICE_COMPANY', 'Service Company'),
        ('DISTRIBUTOR', 'Distributor'),
        ('JV_PARTNER', 'Joint Venture Partner'),
        ('END_USER', 'End User'),
        ('OTHER', 'Other'),
    ]

    ACCOUNT_STATUS_CHOICES = [
        ('ACTIVE', 'Active Account'),
        ('INACTIVE', 'Inactive'),
        ('PROSPECT', 'Prospect'),
        ('SUSPENDED', 'Suspended'),
    ]

    # Identification
    customer_code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Short code (e.g., ARAMCO, ADC, NOC)"
    )
    name = models.CharField(max_length=200)
    legal_name = models.CharField(
        max_length=300,
        blank=True,
        default="",
        help_text="Full legal entity name"
    )
    customer_type = models.CharField(
        max_length=30,
        choices=CUSTOMER_TYPE_CHOICES,
        default='OPERATOR'
    )

    # Account Status
    account_status = models.CharField(
        max_length=20,
        choices=ACCOUNT_STATUS_CHOICES,
        default='ACTIVE'
    )

    # Parent/Subsidiary Relationship
    parent_company = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='subsidiaries',
        help_text="Parent company if this is a subsidiary"
    )

    # Billing vs Operating (often different)
    is_billing_entity = models.BooleanField(
        default=True,
        help_text="Can receive invoices"
    )
    is_operating_entity = models.BooleanField(
        default=True,
        help_text="Operates rigs/wells"
    )
    billing_customer = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='operating_entities',
        help_text="If different, who to bill"
    )

    # Contact Information
    primary_contact_name = models.CharField(max_length=100, blank=True, default="")
    primary_contact_email = models.EmailField(blank=True, default="")
    primary_contact_phone = models.CharField(max_length=50, blank=True, default="")
    address = models.TextField(blank=True, default="")
    city = models.CharField(max_length=100, blank=True, default="")
    country = models.CharField(max_length=100, blank=True, default="")

    # Business Terms
    payment_terms_days = models.PositiveIntegerField(
        default=30,
        help_text="Standard payment terms in days"
    )
    credit_limit = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Credit limit in SAR"
    )
    currency = models.CharField(max_length=3, default='SAR')

    # Preferences
    requires_coc = models.BooleanField(
        default=True,
        help_text="Requires Certificate of Conformance"
    )
    requires_dull_grade = models.BooleanField(
        default=True,
        help_text="Requires dull grade evaluation after each run"
    )
    custom_report_format = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Customer-specific report format (e.g., ARAMCO_COMPACT)"
    )

    # Integration
    external_id = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="ID in external system (ERP, etc.)"
    )

    notes = models.TextField(blank=True, default="")

    class Meta:
        db_table = "sales_customer"
        verbose_name = "Customer"
        verbose_name_plural = "Customers"
        ordering = ['customer_code']
        indexes = [
            models.Index(fields=['customer_code'], name='ix_sales_cust_code'),
            models.Index(fields=['customer_type'], name='ix_sales_cust_type'),
            models.Index(fields=['account_status'], name='ix_sales_cust_status'),
        ]

    def __str__(self):
        return f"{self.customer_code} - {self.name}"

    @property
    def is_active(self):
        return self.account_status == 'ACTIVE'


class Rig(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Drilling rig entity.
    Tracks rigs owned/operated by customers.
    """
    RIG_TYPE_CHOICES = [
        ('LAND', 'Land Rig'),
        ('OFFSHORE_FIXED', 'Offshore Fixed Platform'),
        ('JACKUP', 'Jack-up Rig'),
        ('SEMI_SUBMERSIBLE', 'Semi-submersible'),
        ('DRILLSHIP', 'Drillship'),
        ('BARGE', 'Drilling Barge'),
        ('COILED_TUBING', 'Coiled Tubing Unit'),
        ('WORKOVER', 'Workover Rig'),
        ('OTHER', 'Other'),
    ]

    STATUS_CHOICES = [
        ('ACTIVE', 'Active - Drilling'),
        ('STANDBY', 'Standby'),
        ('MOBILIZING', 'Mobilizing'),
        ('DEMOBILIZING', 'Demobilizing'),
        ('STACKED', 'Stacked'),
        ('UNDER_MAINTENANCE', 'Under Maintenance'),
        ('RETIRED', 'Retired'),
    ]

    rig_code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Rig identifier (e.g., RIG-101, ARAMCO-45)"
    )
    name = models.CharField(max_length=200)
    rig_type = models.CharField(max_length=30, choices=RIG_TYPE_CHOICES)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ACTIVE'
    )

    # Ownership
    owner_customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name='owned_rigs',
        help_text="Company that owns the rig"
    )
    operator_customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name='operated_rigs',
        null=True,
        blank=True,
        help_text="Company operating the rig (if different)"
    )
    drilling_contractor = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contracted_rigs',
        help_text="Drilling contractor if applicable"
    )

    # Technical Specs
    max_depth_ft = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Maximum depth capability in feet"
    )
    top_drive = models.BooleanField(default=True)
    mud_pump_capacity = models.CharField(max_length=100, blank=True, default="")

    # Location
    current_location = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Current location or field"
    )
    gps_coordinates = models.CharField(max_length=100, blank=True, default="")

    # Contacts
    rig_manager = models.CharField(max_length=100, blank=True, default="")
    toolpusher = models.CharField(max_length=100, blank=True, default="")
    contact_phone = models.CharField(max_length=50, blank=True, default="")

    notes = models.TextField(blank=True, default="")

    class Meta:
        db_table = "sales_rig"
        verbose_name = "Rig"
        verbose_name_plural = "Rigs"
        ordering = ['rig_code']
        indexes = [
            models.Index(fields=['rig_code'], name='ix_sales_rig_code'),
            models.Index(fields=['status'], name='ix_sales_rig_status'),
            models.Index(fields=['rig_type'], name='ix_sales_rig_type'),
        ]

    def __str__(self):
        return f"{self.rig_code} - {self.name}"


class Well(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Well / Wellbore entity.
    Tracks wells where bits are used.
    """
    WELL_TYPE_CHOICES = [
        ('EXPLORATION', 'Exploration'),
        ('DEVELOPMENT', 'Development'),
        ('APPRAISAL', 'Appraisal'),
        ('INJECTION', 'Injection'),
        ('WORKOVER', 'Workover'),
        ('SIDETRACK', 'Sidetrack'),
        ('OTHER', 'Other'),
    ]

    STATUS_CHOICES = [
        ('PLANNED', 'Planned'),
        ('DRILLING', 'Drilling'),
        ('COMPLETING', 'Completing'),
        ('PRODUCING', 'Producing'),
        ('SUSPENDED', 'Suspended'),
        ('ABANDONED', 'Abandoned'),
    ]

    well_name = models.CharField(
        max_length=100,
        unique=True,
        db_index=True
    )
    uwi = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="Unique Well Identifier"
    )
    api_number = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="API Well Number"
    )

    well_type = models.CharField(max_length=20, choices=WELL_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PLANNED')

    # Operator
    operator_customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name='wells'
    )
    current_rig = models.ForeignKey(
        Rig,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='wells'
    )

    # Location
    field_name = models.CharField(max_length=100)
    block_name = models.CharField(max_length=100, blank=True, default="")
    country = models.CharField(max_length=100, default='Saudi Arabia')
    gps_latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True
    )
    gps_longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True
    )

    # Well Details
    spud_date = models.DateField(null=True, blank=True)
    planned_td_ft = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Planned Total Depth in feet"
    )
    current_depth_ft = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Current depth in feet"
    )

    notes = models.TextField(blank=True, default="")

    class Meta:
        db_table = "sales_well"
        verbose_name = "Well"
        verbose_name_plural = "Wells"
        ordering = ['well_name']
        indexes = [
            models.Index(fields=['well_name'], name='ix_sales_well_name'),
            models.Index(fields=['status'], name='ix_sales_well_status'),
            models.Index(fields=['field_name'], name='ix_sales_well_field'),
        ]

    def __str__(self):
        return f"{self.well_name} ({self.field_name})"

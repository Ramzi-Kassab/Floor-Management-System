"""
Sales & Lifecycle - Bit Lifecycle Event Tracking
Central event log for tracking complete bit lifecycle from manufacture to scrap.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from floor_app.mixins import PublicIdMixin, AuditMixin, SoftDeleteMixin
from .customer import Customer, Rig, Well


class BitLifecycleEvent(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Event log entry for bit lifecycle tracking.
    Provides chronological history of all events for a serialized bit.
    """
    EVENT_TYPE_CHOICES = [
        # Manufacturing/Production Events
        ('MANUFACTURED', 'Manufactured (New)'),
        ('REPAIR_STARTED', 'Repair Job Started'),
        ('REPAIR_COMPLETED', 'Repair Job Completed'),
        ('RETROFIT', 'Retrofit/MAT Change'),
        ('QC_PASSED', 'Quality Control Passed'),
        ('QC_FAILED', 'Quality Control Failed'),

        # Inventory Events
        ('RECEIVED', 'Received into Inventory'),
        ('STOCKED', 'Stocked in Warehouse'),
        ('ALLOCATED', 'Allocated to Order'),
        ('DEALLOCATED', 'Deallocated from Order'),

        # Shipment Events
        ('SHIPPED_TO_CUSTOMER', 'Shipped to Customer'),
        ('SHIPPED_TO_RIG', 'Shipped to Rig'),
        ('SHIPPED_TO_WAREHOUSE', 'Shipped to Warehouse'),
        ('IN_TRANSIT', 'In Transit'),
        ('DELIVERED', 'Delivered'),
        ('RETURNED', 'Returned from Field'),

        # Drilling Operations
        ('RUN_IN_HOLE', 'Run In Hole'),
        ('PULLED_OUT', 'Pulled Out of Hole'),
        ('DULL_GRADED', 'Dull Grade Evaluation'),

        # Quality/Disposition
        ('INSPECTION', 'Inspection Performed'),
        ('REWORK_REQUIRED', 'Rework Required'),
        ('APPROVED_FOR_RERUN', 'Approved for Rerun'),
        ('CONDEMNED', 'Condemned'),

        # End of Life
        ('SCRAPPED', 'Scrapped'),
        ('JUNKED', 'Junked/Sold as Scrap'),
        ('LOST_IN_HOLE', 'Lost in Hole'),

        # Administrative
        ('OWNERSHIP_TRANSFER', 'Ownership Transferred'),
        ('LOCATION_UPDATE', 'Location Updated'),
        ('STATUS_CHANGE', 'Status Changed'),
        ('NOTE_ADDED', 'Note Added'),
    ]

    # Identification
    event_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True
    )

    # Bit Reference (loose coupling to inventory.SerialUnit)
    serial_unit_id = models.BigIntegerField(
        db_index=True,
        help_text="Reference to inventory.SerialUnit"
    )
    bit_serial_number = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Bit serial number (denormalized for quick access)"
    )

    # MAT at time of event
    mat_number = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="MAT number at time of event"
    )

    # Event Details
    event_type = models.CharField(
        max_length=30,
        choices=EVENT_TYPE_CHOICES,
        db_index=True
    )
    event_datetime = models.DateTimeField(
        default=timezone.now,
        db_index=True
    )

    # Context - Where did this event occur?
    customer = models.ForeignKey(
        Customer,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='lifecycle_events'
    )
    well = models.ForeignKey(
        Well,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='lifecycle_events'
    )
    rig = models.ForeignKey(
        Rig,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='lifecycle_events'
    )
    location_description = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Physical location (warehouse, rig name, etc.)"
    )

    # Related Records (loose coupling)
    job_card_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Reference to production.JobCard"
    )
    sales_order_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Reference to sales.SalesOrder"
    )
    drilling_run_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Reference to sales.DrillingRun"
    )
    dull_grade_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Reference to sales.DullGradeEvaluation"
    )
    shipment_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Reference to sales.Shipment"
    )
    ncr_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Reference to quality.NonconformanceReport"
    )
    junk_sale_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Reference to sales.JunkSale"
    )

    # Event Data
    description = models.TextField(
        blank=True,
        default="",
        help_text="Human-readable event description"
    )
    notes = models.TextField(blank=True, default="")

    # Before/After State
    previous_status = models.CharField(
        max_length=50,
        blank=True,
        default=""
    )
    new_status = models.CharField(
        max_length=50,
        blank=True,
        default=""
    )
    previous_location = models.CharField(
        max_length=200,
        blank=True,
        default=""
    )
    new_location = models.CharField(
        max_length=200,
        blank=True,
        default=""
    )

    # Metrics at time of event
    cumulative_footage = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total footage drilled to date"
    )
    cumulative_hours = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total hours on bottom to date"
    )
    run_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of runs completed to date"
    )

    # Recorded By
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='recorded_lifecycle_events'
    )
    recorded_by_name = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Name if not system user"
    )

    # Attachments
    attachments_json = models.JSONField(
        default=list,
        help_text="List of attachment URLs/paths"
    )

    class Meta:
        db_table = "sales_bit_lifecycle_event"
        verbose_name = "Bit Lifecycle Event"
        verbose_name_plural = "Bit Lifecycle Events"
        ordering = ['bit_serial_number', '-event_datetime']
        indexes = [
            models.Index(fields=['event_number'], name='ix_sales_ble_number'),
            models.Index(fields=['serial_unit_id'], name='ix_sales_ble_serial'),
            models.Index(fields=['bit_serial_number'], name='ix_sales_ble_bitsn'),
            models.Index(fields=['event_type'], name='ix_sales_ble_type'),
            models.Index(fields=['event_datetime'], name='ix_sales_ble_datetime'),
            models.Index(
                fields=['bit_serial_number', 'event_datetime'],
                name='ix_sales_ble_bit_time'
            ),
            models.Index(
                fields=['customer', 'event_datetime'],
                name='ix_sales_ble_cust_time'
            ),
        ]

    def __str__(self):
        return f"{self.event_number} - {self.bit_serial_number} - {self.get_event_type_display()}"

    @classmethod
    def generate_event_number(cls):
        """Generate unique event number."""
        year = timezone.now().year
        prefix = f"BLE-{year}-"
        last_event = cls.all_objects.filter(
            event_number__startswith=prefix
        ).order_by('-event_number').first()
        if last_event:
            try:
                last_num = int(last_event.event_number.split('-')[-1])
                next_num = last_num + 1
            except ValueError:
                next_num = 1
        else:
            next_num = 1
        return f"{prefix}{next_num:06d}"

    @classmethod
    def create_event(cls, serial_unit_id, bit_serial_number, event_type, **kwargs):
        """
        Factory method to create a lifecycle event.
        Automatically generates event number.
        """
        event = cls(
            event_number=cls.generate_event_number(),
            serial_unit_id=serial_unit_id,
            bit_serial_number=bit_serial_number,
            event_type=event_type,
            **kwargs
        )
        event.save()
        return event

    @property
    def event_category(self):
        """Group event types into categories for display."""
        production_events = ['MANUFACTURED', 'REPAIR_STARTED', 'REPAIR_COMPLETED',
                            'RETROFIT', 'QC_PASSED', 'QC_FAILED']
        inventory_events = ['RECEIVED', 'STOCKED', 'ALLOCATED', 'DEALLOCATED']
        shipment_events = ['SHIPPED_TO_CUSTOMER', 'SHIPPED_TO_RIG', 'SHIPPED_TO_WAREHOUSE',
                          'IN_TRANSIT', 'DELIVERED', 'RETURNED']
        drilling_events = ['RUN_IN_HOLE', 'PULLED_OUT', 'DULL_GRADED']
        quality_events = ['INSPECTION', 'REWORK_REQUIRED', 'APPROVED_FOR_RERUN', 'CONDEMNED']
        eol_events = ['SCRAPPED', 'JUNKED', 'LOST_IN_HOLE']

        if self.event_type in production_events:
            return 'Production'
        elif self.event_type in inventory_events:
            return 'Inventory'
        elif self.event_type in shipment_events:
            return 'Shipment'
        elif self.event_type in drilling_events:
            return 'Drilling'
        elif self.event_type in quality_events:
            return 'Quality'
        elif self.event_type in eol_events:
            return 'End of Life'
        else:
            return 'Administrative'


class Shipment(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Track shipments of bits and equipment.
    """
    SHIPMENT_TYPE_CHOICES = [
        ('OUTBOUND', 'Outbound to Customer'),
        ('RETURN', 'Return from Field'),
        ('TRANSFER', 'Inter-location Transfer'),
        ('REPAIR_DELIVERY', 'Repair Delivery'),
    ]

    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PENDING', 'Pending Shipment'),
        ('SHIPPED', 'Shipped'),
        ('IN_TRANSIT', 'In Transit'),
        ('DELIVERED', 'Delivered'),
        ('PARTIAL', 'Partially Delivered'),
        ('CANCELLED', 'Cancelled'),
    ]

    CARRIER_CHOICES = [
        ('FEDEX', 'FedEx'),
        ('UPS', 'UPS'),
        ('DHL', 'DHL'),
        ('TRUCK', 'Truck Freight'),
        ('AIR', 'Air Freight'),
        ('SEA', 'Sea Freight'),
        ('COURIER', 'Local Courier'),
        ('CUSTOMER_PICKUP', 'Customer Pickup'),
        ('OWN_FLEET', 'Own Fleet'),
        ('OTHER', 'Other'),
    ]

    # Identification
    shipment_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True
    )

    # Related Order
    sales_order_id = models.BigIntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Reference to SalesOrder"
    )

    # Type and Status
    shipment_type = models.CharField(
        max_length=20,
        choices=SHIPMENT_TYPE_CHOICES,
        default='OUTBOUND'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT'
    )

    # Origin
    from_location = models.CharField(max_length=200)
    from_customer = models.ForeignKey(
        Customer,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='shipments_from'
    )
    from_rig = models.ForeignKey(
        Rig,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='shipments_from'
    )

    # Destination
    to_location = models.CharField(max_length=200)
    to_customer = models.ForeignKey(
        Customer,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='shipments_to'
    )
    to_rig = models.ForeignKey(
        Rig,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='shipments_to'
    )
    to_well = models.ForeignKey(
        Well,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='shipments'
    )

    # Shipping Details
    carrier = models.CharField(
        max_length=20,
        choices=CARRIER_CHOICES,
        blank=True,
        default=""
    )
    tracking_number = models.CharField(max_length=100, blank=True, default="")
    waybill_number = models.CharField(max_length=100, blank=True, default="")

    # Dates
    ship_date = models.DateField(null=True, blank=True)
    expected_delivery_date = models.DateField(null=True, blank=True)
    actual_delivery_date = models.DateField(null=True, blank=True)

    # Shipping Costs
    shipping_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    insurance_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    # Contents
    bit_serial_numbers = models.TextField(
        blank=True,
        default="",
        help_text="Comma-separated list of bit serial numbers"
    )
    contents_description = models.TextField(
        blank=True,
        default="",
        help_text="Description of shipment contents"
    )

    # Weight and Dimensions
    total_weight_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    number_of_packages = models.PositiveIntegerField(default=1)

    # Documentation
    packing_list_url = models.URLField(blank=True, default="")
    commercial_invoice_url = models.URLField(blank=True, default="")
    customs_documents_json = models.JSONField(default=dict)

    # Contacts
    shipper_name = models.CharField(max_length=100, blank=True, default="")
    receiver_name = models.CharField(max_length=100, blank=True, default="")
    receiver_phone = models.CharField(max_length=30, blank=True, default="")

    # Special Instructions
    handling_instructions = models.TextField(blank=True, default="")
    notes = models.TextField(blank=True, default="")

    # Confirmation
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='confirmed_shipments'
    )
    confirmation_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "sales_shipment"
        verbose_name = "Shipment"
        verbose_name_plural = "Shipments"
        ordering = ['-ship_date', '-created_at']
        indexes = [
            models.Index(fields=['shipment_number'], name='ix_sales_ship_number'),
            models.Index(fields=['status'], name='ix_sales_ship_status'),
            models.Index(fields=['ship_date'], name='ix_sales_ship_date'),
            models.Index(fields=['tracking_number'], name='ix_sales_ship_tracking'),
        ]

    def __str__(self):
        return f"{self.shipment_number} - {self.get_shipment_type_display()}"

    @classmethod
    def generate_shipment_number(cls):
        """Generate unique shipment number."""
        year = timezone.now().year
        prefix = f"SHP-{year}-"
        last_ship = cls.all_objects.filter(
            shipment_number__startswith=prefix
        ).order_by('-shipment_number').first()
        if last_ship:
            try:
                last_num = int(last_ship.shipment_number.split('-')[-1])
                next_num = last_num + 1
            except ValueError:
                next_num = 1
        else:
            next_num = 1
        return f"{prefix}{next_num:06d}"

    @property
    def is_overdue(self):
        """Check if shipment delivery is overdue."""
        if self.status not in ['DELIVERED', 'CANCELLED'] and self.expected_delivery_date:
            return timezone.now().date() > self.expected_delivery_date
        return False


class JunkSale(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Track final disposition of bits sold as scrap/junk.
    Records weight sold and value recovered.
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending Sale'),
        ('QUOTED', 'Quote Received'),
        ('SOLD', 'Sold'),
        ('CANCELLED', 'Cancelled'),
    ]

    # Identification
    junk_sale_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True
    )

    # Bit Reference
    serial_unit_id = models.BigIntegerField(
        db_index=True,
        help_text="Reference to inventory.SerialUnit"
    )
    bit_serial_number = models.CharField(
        max_length=100,
        db_index=True
    )
    mat_number = models.CharField(max_length=50, blank=True, default="")

    # Weight
    gross_weight_kg = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        help_text="Total weight before processing"
    )
    net_weight_kg = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        help_text="Net weight sold"
    )
    carbide_weight_kg = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        help_text="Weight of carbide recovered"
    )
    steel_weight_kg = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        help_text="Weight of steel body"
    )

    # Pricing
    price_per_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Price per kg for scrap"
    )
    carbide_price_per_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Special price for carbide if separated"
    )
    total_sale_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Total value recovered"
    )

    # Buyer Information
    buyer_name = models.CharField(max_length=200)
    buyer_contact = models.CharField(max_length=100, blank=True, default="")
    buyer_reference = models.CharField(max_length=100, blank=True, default="")

    # Transaction Details
    sale_date = models.DateField(default=timezone.now)
    invoice_number = models.CharField(max_length=100, blank=True, default="")
    payment_status = models.CharField(
        max_length=20,
        choices=[
            ('UNPAID', 'Unpaid'),
            ('PARTIAL', 'Partially Paid'),
            ('PAID', 'Paid'),
        ],
        default='UNPAID'
    )
    payment_date = models.DateField(null=True, blank=True)

    # Reason for Scrapping
    scrap_reason = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Why bit was scrapped (wear, damage, obsolete)"
    )
    last_dull_grade = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="Final dull grade before scrapping"
    )

    # Lifecycle Metrics
    total_footage_drilled = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total footage drilled in lifetime"
    )
    total_hours_drilled = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total hours on bottom in lifetime"
    )
    total_runs = models.PositiveIntegerField(
        default=0,
        help_text="Total number of runs in lifetime"
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )

    # Documentation
    weight_certificate_url = models.URLField(blank=True, default="")
    photos_json = models.JSONField(default=list)

    # Approval
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='approved_junk_sales'
    )
    approval_date = models.DateTimeField(null=True, blank=True)

    notes = models.TextField(blank=True, default="")

    class Meta:
        db_table = "sales_junk_sale"
        verbose_name = "Junk Sale"
        verbose_name_plural = "Junk Sales"
        ordering = ['-sale_date']
        indexes = [
            models.Index(fields=['junk_sale_number'], name='ix_sales_junk_number'),
            models.Index(fields=['serial_unit_id'], name='ix_sales_junk_serial'),
            models.Index(fields=['bit_serial_number'], name='ix_sales_junk_bitsn'),
            models.Index(fields=['sale_date'], name='ix_sales_junk_date'),
            models.Index(fields=['status'], name='ix_sales_junk_status'),
        ]

    def __str__(self):
        return f"{self.junk_sale_number} - {self.bit_serial_number} ({self.net_weight_kg} kg)"

    @classmethod
    def generate_junk_sale_number(cls):
        """Generate unique junk sale number."""
        year = timezone.now().year
        prefix = f"JNK-{year}-"
        last_sale = cls.all_objects.filter(
            junk_sale_number__startswith=prefix
        ).order_by('-junk_sale_number').first()
        if last_sale:
            try:
                last_num = int(last_sale.junk_sale_number.split('-')[-1])
                next_num = last_num + 1
            except ValueError:
                next_num = 1
        else:
            next_num = 1
        return f"{prefix}{next_num:06d}"

    def save(self, *args, **kwargs):
        """Calculate total sale value before saving."""
        if self.carbide_weight_kg and self.carbide_price_per_kg:
            carbide_value = float(self.carbide_weight_kg) * float(self.carbide_price_per_kg)
            steel_weight = float(self.net_weight_kg) - float(self.carbide_weight_kg)
            steel_value = steel_weight * float(self.price_per_kg)
            self.total_sale_value = carbide_value + steel_value
        else:
            self.total_sale_value = float(self.net_weight_kg) * float(self.price_per_kg)
        super().save(*args, **kwargs)

    @property
    def cost_per_foot(self):
        """Calculate cost per foot drilled in lifetime."""
        if self.total_footage_drilled and float(self.total_footage_drilled) > 0:
            # This would need original bit cost from SerialUnit
            # Return None for now, calculate in view with full data
            return None
        return None

    @property
    def recovery_rate(self):
        """Calculate scrap recovery rate percentage."""
        if self.gross_weight_kg and float(self.gross_weight_kg) > 0:
            return (float(self.net_weight_kg) / float(self.gross_weight_kg)) * 100
        return 100.0

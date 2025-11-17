"""
Outbound Shipment and Customer Returns Models

Manages shipments to customers/rigs and handling of customer returns.
"""

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone
from floor_app.mixins import PublicIdMixin, AuditMixin, SoftDeleteMixin
from .supplier import Currency, Incoterms


class ShipmentStatus:
    """Outbound Shipment status states"""
    DRAFT = 'DRAFT'
    PICKING = 'PICKING'
    PACKED = 'PACKED'
    READY_TO_SHIP = 'READY_TO_SHIP'
    SHIPPED = 'SHIPPED'
    IN_TRANSIT = 'IN_TRANSIT'
    DELIVERED = 'DELIVERED'
    CANCELLED = 'CANCELLED'

    CHOICES = [
        (DRAFT, 'Draft'),
        (PICKING, 'Picking in Progress'),
        (PACKED, 'Packed'),
        (READY_TO_SHIP, 'Ready to Ship'),
        (SHIPPED, 'Shipped'),
        (IN_TRANSIT, 'In Transit'),
        (DELIVERED, 'Delivered'),
        (CANCELLED, 'Cancelled'),
    ]


class ShipmentType:
    """Types of outbound shipments"""
    SALES_ORDER = 'SALES'
    RIG_DELIVERY = 'RIG'
    REPAIR_RETURN = 'REPAIR'
    SAMPLE = 'SAMPLE'
    CONSIGNMENT = 'CONSIGN'
    INTERNAL = 'INTERNAL'

    CHOICES = [
        (SALES_ORDER, 'Sales Order'),
        (RIG_DELIVERY, 'Rig Delivery'),
        (REPAIR_RETURN, 'Repair Return'),
        (SAMPLE, 'Sample Shipment'),
        (CONSIGNMENT, 'Consignment'),
        (INTERNAL, 'Internal Transfer'),
    ]


class CustomerReturnStatus:
    """Customer Return status states"""
    REQUESTED = 'REQUESTED'
    APPROVED = 'APPROVED'
    SHIPPED_BY_CUSTOMER = 'SHIPPED'
    RECEIVED = 'RECEIVED'
    UNDER_INSPECTION = 'INSPECTING'
    INSPECTION_COMPLETE = 'INSPECTED'
    PROCESSED = 'PROCESSED'
    CLOSED = 'CLOSED'
    REJECTED = 'REJECTED'

    CHOICES = [
        (REQUESTED, 'Return Requested'),
        (APPROVED, 'Return Approved'),
        (SHIPPED_BY_CUSTOMER, 'Shipped by Customer'),
        (RECEIVED, 'Received'),
        (UNDER_INSPECTION, 'Under Inspection'),
        (INSPECTION_COMPLETE, 'Inspection Complete'),
        (PROCESSED, 'Processed'),
        (CLOSED, 'Closed'),
        (REJECTED, 'Return Rejected'),
    ]


class OutboundShipment(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Outbound Shipment to customers, rigs, or other destinations.
    """
    # Identification
    shipment_number = models.CharField(
        max_length=30,
        unique=True,
        db_index=True,
        help_text="Auto-generated shipment number"
    )
    shipment_type = models.CharField(
        max_length=10,
        choices=ShipmentType.CHOICES,
        default=ShipmentType.SALES_ORDER
    )
    status = models.CharField(
        max_length=15,
        choices=ShipmentStatus.CHOICES,
        default=ShipmentStatus.DRAFT,
        db_index=True
    )

    # Customer/Destination
    customer_id = models.BigIntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Customer ID if customer shipment"
    )
    customer_name = models.CharField(max_length=200)
    customer_reference = models.CharField(
        max_length=100,
        blank=True,
        help_text="Customer's PO or reference number"
    )

    # Delivery Address
    delivery_contact_name = models.CharField(max_length=200, blank=True)
    delivery_contact_phone = models.CharField(max_length=30, blank=True)
    delivery_address_line1 = models.CharField(max_length=255)
    delivery_address_line2 = models.CharField(max_length=255, blank=True)
    delivery_city = models.CharField(max_length=100)
    delivery_state = models.CharField(max_length=100, blank=True)
    delivery_postal_code = models.CharField(max_length=20, blank=True)
    delivery_country = models.CharField(max_length=100, default='Saudi Arabia')

    # For Rig Deliveries
    rig_name = models.CharField(max_length=200, blank=True)
    rig_location = models.CharField(max_length=200, blank=True)
    well_name = models.CharField(max_length=200, blank=True)
    field_name = models.CharField(max_length=200, blank=True)

    # Source Warehouse
    source_warehouse_id = models.BigIntegerField(
        db_index=True,
        help_text="Warehouse from which items are shipped"
    )

    # Dates
    created_date = models.DateField(default=timezone.now)
    scheduled_ship_date = models.DateField(
        null=True,
        blank=True,
        help_text="Planned shipping date"
    )
    actual_ship_date = models.DateTimeField(null=True, blank=True)
    expected_delivery_date = models.DateField(null=True, blank=True)
    actual_delivery_date = models.DateTimeField(null=True, blank=True)

    # Shipping Details
    carrier_name = models.CharField(max_length=200, blank=True)
    shipping_method = models.CharField(max_length=100, blank=True)
    tracking_number = models.CharField(max_length=100, blank=True)
    waybill_number = models.CharField(max_length=100, blank=True)
    vehicle_number = models.CharField(max_length=50, blank=True)
    driver_name = models.CharField(max_length=200, blank=True)
    driver_phone = models.CharField(max_length=30, blank=True)

    # Terms
    incoterm = models.CharField(
        max_length=3,
        choices=Incoterms.CHOICES,
        default=Incoterms.DAP
    )
    currency = models.CharField(
        max_length=3,
        choices=Currency.CHOICES,
        default=Currency.SAR
    )

    # Package Information
    total_packages = models.IntegerField(default=0)
    total_weight_kg = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=0
    )
    total_volume_cbm = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=0,
        help_text="Total volume in cubic meters"
    )

    # Handlers
    picker_id = models.BigIntegerField(null=True, blank=True)
    packer_id = models.BigIntegerField(null=True, blank=True)
    shipper_id = models.BigIntegerField(null=True, blank=True)

    # Financials
    shipping_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    insurance_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    total_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Total value of shipped goods"
    )

    # Export Documentation (Saudi Arabia)
    export_declaration_number = models.CharField(max_length=100, blank=True)
    certificate_of_origin = models.CharField(max_length=100, blank=True)
    commercial_invoice_number = models.CharField(max_length=100, blank=True)
    packing_list_number = models.CharField(max_length=100, blank=True)

    # Delivery Confirmation
    delivery_confirmed = models.BooleanField(default=False)
    delivered_to = models.CharField(max_length=200, blank=True)
    delivery_signature = models.CharField(max_length=500, blank=True)
    delivery_notes = models.TextField(blank=True)
    delivery_photos = models.JSONField(default=list, blank=True)

    # Inventory Transaction
    inventory_transaction_id = models.BigIntegerField(
        null=True,
        blank=True
    )

    # References
    sales_order_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Related sales order"
    )
    job_card_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Related job card"
    )

    special_instructions = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)

    class Meta:
        db_table = 'purchasing_outbound_shipment'
        verbose_name = 'Outbound Shipment'
        verbose_name_plural = 'Outbound Shipments'
        ordering = ['-created_date', '-shipment_number']
        indexes = [
            models.Index(fields=['shipment_number'], name='ix_shipment_number'),
            models.Index(fields=['status'], name='ix_shipment_status'),
            models.Index(fields=['customer_id'], name='ix_shipment_customer'),
        ]

    def __str__(self):
        return f"{self.shipment_number} - {self.customer_name}"

    def start_picking(self, picker_id):
        """Start picking process"""
        if self.status == ShipmentStatus.DRAFT:
            self.status = ShipmentStatus.PICKING
            self.picker_id = picker_id
            self.save(update_fields=['status', 'picker_id'])
            return True
        return False

    def mark_packed(self, packer_id):
        """Mark shipment as packed"""
        if self.status == ShipmentStatus.PICKING:
            self.status = ShipmentStatus.PACKED
            self.packer_id = packer_id
            self.save(update_fields=['status', 'packer_id'])
            return True
        return False

    def ship(self, shipper_id, tracking_number='', carrier=''):
        """Mark shipment as shipped"""
        if self.status in [ShipmentStatus.PACKED, ShipmentStatus.READY_TO_SHIP]:
            self.status = ShipmentStatus.SHIPPED
            self.shipper_id = shipper_id
            self.actual_ship_date = timezone.now()
            self.tracking_number = tracking_number
            self.carrier_name = carrier
            self.save(update_fields=[
                'status', 'shipper_id', 'actual_ship_date',
                'tracking_number', 'carrier_name'
            ])
            return True
        return False

    def confirm_delivery(self, delivered_to='', notes=''):
        """Confirm delivery"""
        if self.status in [ShipmentStatus.SHIPPED, ShipmentStatus.IN_TRANSIT]:
            self.status = ShipmentStatus.DELIVERED
            self.delivery_confirmed = True
            self.actual_delivery_date = timezone.now()
            self.delivered_to = delivered_to
            self.delivery_notes = notes
            self.save(update_fields=[
                'status', 'delivery_confirmed', 'actual_delivery_date',
                'delivered_to', 'delivery_notes'
            ])
            return True
        return False

    def calculate_totals(self):
        """Calculate totals from lines"""
        lines = self.lines.all()
        self.total_packages = lines.count()
        self.total_weight_kg = sum(line.weight_kg for line in lines)
        self.total_value = sum(line.total_value for line in lines)
        self.save(update_fields=[
            'total_packages', 'total_weight_kg', 'total_value'
        ])

    @classmethod
    def generate_shipment_number(cls):
        """Generate next shipment number"""
        year = timezone.now().year
        prefix = f'SHP-{year}-'
        last_shp = cls.all_objects.filter(
            shipment_number__startswith=prefix
        ).order_by('-shipment_number').first()

        if last_shp:
            last_num = int(last_shp.shipment_number.split('-')[-1])
            next_num = last_num + 1
        else:
            next_num = 1

        return f"{prefix}{next_num:05d}"


class ShipmentLine(AuditMixin):
    """
    Individual line item in an Outbound Shipment.
    """
    shipment = models.ForeignKey(
        OutboundShipment,
        on_delete=models.CASCADE,
        related_name='lines'
    )
    line_number = models.PositiveIntegerField()

    # Item Reference
    item_id = models.BigIntegerField(db_index=True)
    item_code = models.CharField(max_length=50)
    description = models.CharField(max_length=500)

    # Quantities
    quantity_ordered = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        help_text="Quantity ordered by customer"
    )
    quantity_picked = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=0
    )
    quantity_shipped = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=0
    )
    uom = models.CharField(max_length=20, default='EA')

    # Value
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=0
    )
    total_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )

    # Package Details
    package_number = models.CharField(max_length=50, blank=True)
    weight_kg = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=0
    )
    dimensions = models.CharField(
        max_length=100,
        blank=True,
        help_text="L x W x H in cm"
    )

    # Serial/Batch
    serial_numbers = models.JSONField(
        default=list,
        blank=True,
        help_text="Serial numbers being shipped"
    )
    batch_number = models.CharField(max_length=50, blank=True)

    # Storage
    picked_from_location_id = models.BigIntegerField(
        null=True,
        blank=True
    )
    picked_from_bin = models.CharField(max_length=50, blank=True)

    # QR Code
    qcode_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="QR Code for tracking"
    )

    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'purchasing_shipment_line'
        verbose_name = 'Shipment Line'
        verbose_name_plural = 'Shipment Lines'
        ordering = ['shipment', 'line_number']
        unique_together = [['shipment', 'line_number']]
        indexes = [
            models.Index(fields=['item_id'], name='ix_shpline_item'),
        ]

    def __str__(self):
        return f"{self.shipment.shipment_number} Line {self.line_number}"

    def save(self, *args, **kwargs):
        # Calculate total value
        self.total_value = self.quantity_shipped * self.unit_price
        super().save(*args, **kwargs)


class CustomerReturn(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Customer Return - handling returns from customers.
    """
    # Identification
    return_number = models.CharField(
        max_length=30,
        unique=True,
        db_index=True,
        help_text="Auto-generated return number"
    )
    status = models.CharField(
        max_length=15,
        choices=CustomerReturnStatus.CHOICES,
        default=CustomerReturnStatus.REQUESTED,
        db_index=True
    )

    # Customer
    customer_id = models.BigIntegerField(
        db_index=True,
        help_text="Customer ID"
    )
    customer_name = models.CharField(max_length=200)
    customer_contact = models.CharField(max_length=200, blank=True)
    customer_phone = models.CharField(max_length=30, blank=True)

    # Reference
    original_shipment = models.ForeignKey(
        OutboundShipment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='customer_returns'
    )
    sales_order_id = models.BigIntegerField(null=True, blank=True)

    # Return Details
    return_request_date = models.DateField(default=timezone.now)
    reason = models.CharField(
        max_length=30,
        choices=[
            ('DEFECTIVE', 'Defective Product'),
            ('WRONG_ITEM', 'Wrong Item'),
            ('DAMAGED', 'Damaged'),
            ('NOT_AS_DESCRIBED', 'Not as Described'),
            ('PERFORMANCE', 'Performance Issue'),
            ('WEAR_PATTERN', 'Abnormal Wear Pattern'),
            ('WARRANTY', 'Warranty Claim'),
            ('OTHER', 'Other'),
        ]
    )
    reason_detail = models.TextField(blank=True)

    # Authorization
    rma_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Return Merchandise Authorization number"
    )
    approved_by_id = models.BigIntegerField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    # Shipping
    customer_tracking_number = models.CharField(max_length=100, blank=True)
    received_date = models.DateTimeField(null=True, blank=True)
    received_by_id = models.BigIntegerField(null=True, blank=True)

    # Receiving Location
    receiving_warehouse_id = models.BigIntegerField(
        null=True,
        blank=True
    )
    qa_hold_location_id = models.BigIntegerField(
        null=True,
        blank=True
    )

    # Inspection
    inspection_required = models.BooleanField(default=True)
    inspected_by_id = models.BigIntegerField(null=True, blank=True)
    inspection_date = models.DateTimeField(null=True, blank=True)
    inspection_result = models.CharField(
        max_length=20,
        blank=True,
        choices=[
            ('CONFIRMED_DEFECT', 'Confirmed Defect'),
            ('NO_DEFECT', 'No Defect Found'),
            ('WEAR_NORMAL', 'Normal Wear'),
            ('MISUSE', 'Customer Misuse'),
            ('REPAIRABLE', 'Repairable'),
            ('SCRAP', 'Scrap'),
        ]
    )
    inspection_notes = models.TextField(blank=True)

    # Resolution
    resolution_type = models.CharField(
        max_length=20,
        blank=True,
        choices=[
            ('REPLACE', 'Replace'),
            ('REFUND', 'Refund'),
            ('CREDIT', 'Credit Note'),
            ('REPAIR', 'Repair'),
            ('REJECT', 'Return Rejected'),
            ('NO_ACTION', 'No Action Required'),
        ]
    )
    resolution_notes = models.TextField(blank=True)
    credit_note_number = models.CharField(max_length=100, blank=True)
    credit_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )

    # Inventory
    restock_to_inventory = models.BooleanField(default=False)
    inventory_transaction_id = models.BigIntegerField(
        null=True,
        blank=True
    )

    # Totals
    total_items = models.IntegerField(default=0)
    total_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )

    # Attachments
    photos = models.JSONField(default=list, blank=True)
    documents = models.JSONField(default=list, blank=True)

    notes = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)

    class Meta:
        db_table = 'purchasing_customer_return'
        verbose_name = 'Customer Return'
        verbose_name_plural = 'Customer Returns'
        ordering = ['-return_request_date', '-return_number']
        indexes = [
            models.Index(fields=['return_number'], name='ix_custret_number'),
            models.Index(fields=['status'], name='ix_custret_status'),
            models.Index(fields=['customer_id'], name='ix_custret_customer'),
        ]

    def __str__(self):
        return f"{self.return_number} - {self.customer_name}"

    def approve(self, approver_id, rma_number=''):
        """Approve the return request"""
        if self.status == CustomerReturnStatus.REQUESTED:
            self.status = CustomerReturnStatus.APPROVED
            self.approved_by_id = approver_id
            self.approved_at = timezone.now()
            if rma_number:
                self.rma_number = rma_number
            else:
                self.rma_number = f"RMA-{self.return_number}"
            self.save(update_fields=[
                'status', 'approved_by_id', 'approved_at', 'rma_number'
            ])
            return True
        return False

    def receive(self, receiver_id):
        """Mark return as received"""
        if self.status in [CustomerReturnStatus.APPROVED, CustomerReturnStatus.SHIPPED_BY_CUSTOMER]:
            self.status = CustomerReturnStatus.RECEIVED
            self.received_by_id = receiver_id
            self.received_date = timezone.now()
            self.save(update_fields=['status', 'received_by_id', 'received_date'])
            return True
        return False

    def complete_inspection(self, inspector_id, result, notes=''):
        """Complete inspection of returned items"""
        if self.status in [CustomerReturnStatus.RECEIVED, CustomerReturnStatus.UNDER_INSPECTION]:
            self.status = CustomerReturnStatus.INSPECTION_COMPLETE
            self.inspected_by_id = inspector_id
            self.inspection_date = timezone.now()
            self.inspection_result = result
            self.inspection_notes = notes
            self.save(update_fields=[
                'status', 'inspected_by_id', 'inspection_date',
                'inspection_result', 'inspection_notes'
            ])
            return True
        return False

    def calculate_totals(self):
        """Calculate totals from lines"""
        lines = self.lines.all()
        self.total_items = lines.count()
        self.total_value = sum(line.total_value for line in lines)
        self.save(update_fields=['total_items', 'total_value'])

    @classmethod
    def generate_return_number(cls):
        """Generate next customer return number"""
        year = timezone.now().year
        prefix = f'CR-{year}-'
        last_cr = cls.all_objects.filter(
            return_number__startswith=prefix
        ).order_by('-return_number').first()

        if last_cr:
            last_num = int(last_cr.return_number.split('-')[-1])
            next_num = last_num + 1
        else:
            next_num = 1

        return f"{prefix}{next_num:05d}"


class CustomerReturnLine(AuditMixin):
    """
    Individual line item in a Customer Return.
    """
    customer_return = models.ForeignKey(
        CustomerReturn,
        on_delete=models.CASCADE,
        related_name='lines'
    )
    line_number = models.PositiveIntegerField()

    # Item Reference
    item_id = models.BigIntegerField(db_index=True)
    item_code = models.CharField(max_length=50)
    description = models.CharField(max_length=500)

    # Original Shipment Reference
    shipment_line = models.ForeignKey(
        ShipmentLine,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='return_lines'
    )

    # Quantities
    quantity_returned = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        validators=[MinValueValidator(0)]
    )
    uom = models.CharField(max_length=20, default='EA')

    # Value
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=0
    )
    total_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )

    # Condition
    condition = models.CharField(
        max_length=20,
        choices=[
            ('NEW', 'New/Unused'),
            ('USED', 'Used'),
            ('DAMAGED', 'Damaged'),
            ('DEFECTIVE', 'Defective'),
        ]
    )
    condition_notes = models.TextField(blank=True)

    # Serial/Batch
    serial_numbers = models.JSONField(
        default=list,
        blank=True,
        help_text="Serial numbers being returned"
    )
    batch_number = models.CharField(max_length=50, blank=True)

    # Inspection Result
    line_inspection_result = models.CharField(
        max_length=20,
        blank=True,
        choices=[
            ('RESTOCK', 'Restock'),
            ('REPAIR', 'Repair'),
            ('SCRAP', 'Scrap'),
            ('QUARANTINE', 'Quarantine'),
        ]
    )

    # Storage
    storage_location_id = models.BigIntegerField(
        null=True,
        blank=True
    )

    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'purchasing_customer_return_line'
        verbose_name = 'Customer Return Line'
        verbose_name_plural = 'Customer Return Lines'
        ordering = ['customer_return', 'line_number']
        unique_together = [['customer_return', 'line_number']]

    def __str__(self):
        return f"{self.customer_return.return_number} Line {self.line_number}"

    def save(self, *args, **kwargs):
        # Calculate total value
        self.total_value = self.quantity_returned * self.unit_price
        super().save(*args, **kwargs)

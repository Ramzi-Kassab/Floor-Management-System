from django.db import models
from django.db.models.expressions import OrderBy
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.conf import settings
from django.contrib.auth.models import Group, User
from decimal import Decimal
from typing import Optional, cast, Type, Any
from datetime import date
from .managers import BaseManager
from django.db.models import F, Q, ExpressionWrapper, DecimalField as DDecimalField, UniqueConstraint
from .mixins import (
    # SoftDeleteMixin,
    # PublicIdMixin,
    DocumentReferenceMixin,
    PartyReferenceMixin,
    # PartyType,  # Import from mixins now
    PostingMixin,
    GenericPartyReferenceMixin
)
from django.core.validators import RegexValidator
import hashlib
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
# from django.utils.translation import gettext_lazy as _   # ← keep commented unless you actually use _()
# import uuid                                              # ← remove (only needed if you use PublicIdMixin)
# from .utils import require_if                             # ← comment out if not used yet


# ============================================================================
# ENUM CHOICES
# ============================================================================

class PocketShapeEnumChoices(models.TextChoices):
    ROUND = 'ROUND', 'Round'
    BULLET = 'BULLET', 'Bullet'


class ProfileZoneEnumChoices(models.TextChoices):
    CONE = 'CONE', 'Cone'
    NOSE = 'NOSE', 'Nose'
    TAPER = 'TAPER', 'Taper'
    SHOULDER = 'SHOULDER', 'Shoulder'
    GAUGE = 'GAUGE', 'Gauge'


class BOMKindEnumChoices(models.TextChoices):
    PRODUCTION = 'PRODUCTION', 'Production'
    RETROFIT = 'RETROFIT', 'Retrofit'
    REPAIR = 'REPAIR', 'Repair'


class CutterDecisionEnumChoices(models.TextChoices):
    OKAY = 'OKAY', 'Okay'
    REPLACE = 'REPLACE', 'Replace'
    ROTATE = 'ROTATE', 'Rotate'


class CutterVariantEnumChoices(models.TextChoices):
    NEW = 'NEW', 'New'
    ENO = 'ENO', 'ENO'
    ADT_RECLAIM = 'ADT_RECLAIM', 'ADT Reclaim'
    LSTK_RECLAIM = 'LSTK_RECLAIM', 'LSTK Reclaim'


class PocketConditionEnumChoices(models.TextChoices):
    OK = 'OK', 'OK'
    DAMAGED = 'DAMAGED', 'Damaged'
    ERODED = 'ERODED', 'Eroded'
    OVERSIZED = 'OVERSIZED', 'Oversized'
    CRACKED = 'CRACKED', 'Cracked'


class CutterConditionEnumChoices(models.TextChoices):
    OK = 'OK', 'OK'
    CRACKED_REPLACE = 'CRACKED_REPLACE', 'Cracked - Replace'
    CRACKED_ACCEPTABLE = 'CRACKED_ACCEPTABLE', 'Cracked - Acceptable'
    ROTATE = 'ROTATE', 'Rotate'
    BRAZE_ERODED = 'BRAZE_ERODED', 'Braze Eroded'


class FinConditionEnumChoices(models.TextChoices):
    OK = 'OK', 'OK'
    BROKEN = 'BROKEN', 'Broken'
    ERODED = 'ERODED', 'Eroded'
    NEEDS_BUILDUP = 'NEEDS_BUILDUP', 'Needs Buildup'


# ============================================================================
# STATUS CHOICES
# ============================================================================

class WorkOrderStatus(models.TextChoices):
    DRAFT = 'Draft', 'Draft'
    RELEASED = 'Released', 'Released'
    IN_PROGRESS = 'In Progress', 'In Progress'
    COMPLETED = 'Completed', 'Completed'
    CANCELLED = 'Cancelled', 'Cancelled'


class JobCardStatus(models.TextChoices):
    DRAFT = 'Draft', 'Draft'
    PENDING = 'Pending', 'Pending'
    IN_PROGRESS = 'In Progress', 'In Progress'
    COMPLETED = 'Completed', 'Completed'
    ON_HOLD = 'On Hold', 'On Hold'


class OrderStatus(models.TextChoices):
    DRAFT = 'Draft', 'Draft'
    SUBMITTED = 'Submitted', 'Submitted'
    CONFIRMED = 'Confirmed', 'Confirmed'
    INVOICED = 'Invoiced', 'Invoiced'
    IN_PROGRESS = 'In Progress', 'In Progress'
    COMPLETED = 'Completed', 'Completed'
    CANCELLED = 'Cancelled', 'Cancelled'


class InvoiceStatus(models.TextChoices):
    DRAFT = 'Draft', 'Draft'
    SUBMITTED = 'Submitted', 'Submitted'
    PAID = 'Paid', 'Paid'
    PARTIALLY_PAID = 'Partially Paid', 'Partially Paid'
    OVERDUE = 'Overdue', 'Overdue'
    CANCELLED = 'Cancelled', 'Cancelled'


class PaymentStatus(models.TextChoices):
    DRAFT = 'Draft', 'Draft'
    SUBMITTED = 'Submitted', 'Submitted'
    CLEARED = 'Cleared', 'Cleared'
    CANCELLED = 'Cancelled', 'Cancelled'


class ShipmentStatus(models.TextChoices):
    DRAFT = 'Draft', 'Draft'
    READY = 'Ready', 'Ready'
    IN_TRANSIT = 'In Transit', 'In Transit'
    DELIVERED = 'Delivered', 'Delivered'
    CANCELLED = 'Cancelled', 'Cancelled'


class ItemStatus(models.TextChoices):
    ACTIVE = 'Active', 'Active'
    INACTIVE = 'Inactive', 'Inactive'
    DISCONTINUED = 'Discontinued', 'Discontinued'


class PartyStatus(models.TextChoices):
    """Status choices for Customer and Supplier"""
    ACTIVE = 'Active', 'Active'
    INACTIVE = 'Inactive', 'Inactive'
    SUSPENDED = 'Suspended', 'Suspended'


class EmploymentStatus(models.TextChoices):
    ACTIVE = 'Active', 'Active'
    ON_LEAVE = 'On Leave', 'On Leave'
    RESIGNED = 'Resigned', 'Resigned'
    TERMINATED = 'Terminated', 'Terminated'


class StockEntryStatus(models.TextChoices):
    DRAFT = 'Draft', 'Draft'
    SUBMITTED = 'Submitted', 'Submitted'
    COMPLETED = 'Completed', 'Completed'
    CANCELLED = 'Cancelled', 'Cancelled'


class QCStatus(models.TextChoices):
    PENDING = 'Pending', 'Pending'
    IN_PROGRESS = 'In Progress', 'In Progress'
    PASSED = 'Passed', 'Passed'
    FAILED = 'Failed', 'Failed'
    PARTIAL = 'Partial', 'Partial'


class AssetStatus(models.TextChoices):
    ACTIVE = 'Active', 'Active'
    IDLE = 'Idle', 'Idle'
    MAINTENANCE = 'Maintenance', 'Maintenance'
    BROKEN = 'Broken', 'Broken'
    RETIRED = 'Retired', 'Retired'


class MaintenanceStatus(models.TextChoices):
    DRAFT = 'Draft', 'Draft'
    SCHEDULED = 'Scheduled', 'Scheduled'
    IN_PROGRESS = 'In Progress', 'In Progress'
    COMPLETED = 'Completed', 'Completed'
    CANCELLED = 'Cancelled', 'Cancelled'


class IncidentStatus(models.TextChoices):
    REPORTED = 'Reported', 'Reported'
    INVESTIGATING = 'Investigating', 'Investigating'
    RESOLVED = 'Resolved', 'Resolved'
    CLOSED = 'Closed', 'Closed'


class ApprovalStatus(models.TextChoices):
    PENDING = 'Pending', 'Pending'
    APPROVED = 'Approved', 'Approved'
    REJECTED = 'Rejected', 'Rejected'
    CANCELLED = 'Cancelled', 'Cancelled'


class MaritalStatus(models.TextChoices):
    SINGLE = 'single',  'Single'
    MARRIED = 'married', 'Married'


class Designation(models.TextChoices):
    GRINDING_OPERATOR     = 'grinding_operator',     'Grinding Operator'
    WELDER                = 'usr_tech',              'Welder'
    BRAZER                = 'brazing_tech',          'Brazer'
    MACHINIST             = 'machinist',             'Machinist'
    QC_INSPECTOR          = 'qc_inspector',          'QC Inspector'
    REPAIR_TECH           = 'repair_tech',          'Repair Tech'
    SANDBLAST_OPERATOR    = 'sandblast_operator',    'Sandblast Operator'
    STOREKEEPER           = 'storekeeper',           'Storekeeper'
    LOGISTICS_COORDINATOR = 'logistics_coordinator', 'Logistics Coordinator'
    LOGISTICS_SUPERVISOR  = 'logistics_supervisor', 'Logistics Supervisor'
    PLANNER               = 'planner',               'Planner'
    PRODUCTION_SUPERVISOR = 'production_supervisor', 'Production Supervisor'
    MAINTENANCE_TECH      = 'maintenance_tech',      'Maintenance Tech'
    EVALUATION_ENGINEER   = 'evaluation_engineer',   'Evaluation Engineer'
    HSE_OFFICER           = 'hse_officer',           'HSE Officer'
    ADMIN_ASSISTANT       = 'admin_assistant',       'Admin Assistant'
    OTHER                 = 'other',                 'Other'


# ============================================================================
# TYPE CHOICES
# ============================================================================


class DocType(models.TextChoices):
    """Centralized document type choices"""
    WORK_ORDER = 'WorkOrder', 'Work Order'
    SALES_ORDER = 'SalesOrder', 'Sales Order'
    PURCHASE_ORDER = 'PurchaseOrder', 'Purchase Order'
    SALES_INVOICE = 'SalesInvoice', 'Sales Invoice'
    PURCHASE_INVOICE = 'PurchaseInvoice', 'Purchase Invoice'
    DELIVERY_NOTE = 'DeliveryNote', 'Delivery Note'
    PURCHASE_RECEIPT = 'PurchaseReceipt', 'Purchase Receipt'
    STOCK_ENTRY = 'StockEntry', 'Stock Entry'
    MATERIAL_REQUEST = 'MaterialRequest', 'Material Request'
    PAYMENT = 'Payment', 'Payment'
    SHIPMENT = 'Shipment', 'Shipment'


# ============================================================================
# BASE MIXINS
# ============================================================================


# floor_app/audit_mixin.py
# floor_app/models.py - Replace the AuditMixin class

# ============================================================================
# FIXED: Traditional AuditMixin (no dynamic field addition)
# ============================================================================

class AuditMixin(models.Model):
    """
    Base audit fields for all models:
    - created_at / updated_at: timestamps (auto)
    - created_by / updated_by: user (auto, non-editable in forms)
    - remarks: free text (editable)
    """
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="%(app_label)s_%(class)s_created",
        editable=False,           # <-- keep non-editable in admin/forms
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="%(app_label)s_%(class)s_updated",
        editable=False,           # <-- keep non-editable in admin/forms
    )

    remarks = models.TextField(blank=True, default="")

    # fields to ignore when computing diffs (used by signals)
    audit_exclude = ("created_at", "updated_at", "created_by", "updated_by")

    class Meta:
        abstract = True


# ============================================================================
# CORE MODELS
# ============================================================================



class Position(AuditMixin):
    """Organizational position/hierarchy"""
    position_id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=64, unique=True)
    title = models.CharField(max_length=200)
    department = models.CharField(max_length=120, blank=True)
    grade = models.CharField(max_length=32, blank=True)
    reports_to = models.ForeignKey('Position', null=True, blank=True, on_delete=models.SET_NULL,
                                   db_column='reports_to_id', related_name='subordinates')
    is_active = models.BooleanField(default=True)

    objects = BaseManager()

    class Meta:
        db_table = 'positions'
        verbose_name = 'Position'
        verbose_name_plural = 'Positions'
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.title}"


class Currency(AuditMixin):
    currency_code = models.CharField(max_length=3, primary_key=True)
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=10)
    decimal_places = models.IntegerField(default=2)
    is_active = models.BooleanField(default=True)

    objects = BaseManager()

    class Meta:
        db_table = 'currencies'
        verbose_name = 'Currency'
        verbose_name_plural = 'Currencies'
        constraints = [
            models.CheckConstraint(
                check=models.Q(decimal_places__gte=0, decimal_places__lte=6),
                name='ck_currency_decimals_range'
            ),
        ]

    def __str__(self):
        return f"{self.currency_code} - {self.name}"


class ExchangeRate(AuditMixin):
    rate_id = models.BigAutoField(primary_key=True)
    from_currency = models.ForeignKey('Currency', on_delete=models.PROTECT,
                                      db_column='from_currency', related_name='rates_from')
    to_currency = models.ForeignKey('Currency', on_delete=models.PROTECT,
                                    db_column='to_currency', related_name='rates_to')
    rate = models.DecimalField(max_digits=18, decimal_places=6)
    valid_date = models.DateField()

    class Meta:
        db_table = 'exchange_rates'
        verbose_name = 'Exchange Rate'
        verbose_name_plural = 'Exchange Rates'
        indexes = [
            models.Index(fields=['valid_date'], name='ix_exchange_rate_date')
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['from_currency', 'to_currency', 'valid_date'],
                name='uq_exchange_rate_currencies_date'
            ),
            models.CheckConstraint(check=models.Q(rate__gt=0), name='ck_fx_rate_pos'),
            models.CheckConstraint(
                check=~models.Q(from_currency=models.F('to_currency')),
                name='ck_fx_currency_pair_distinct'
            ),
        ]

    def __str__(self):
        return f"{self.from_currency}/{self.to_currency} = {self.rate} on {self.valid_date}"


class UOM(models.Model):
    uom_code = models.CharField(max_length=32, primary_key=True)
    label = models.CharField(max_length=64)
    category = models.CharField(max_length=32)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'uom'
        verbose_name = 'Unit of Measure'
        verbose_name_plural = 'Units of Measure'
        ordering = ['category', 'label']

    def __str__(self):
        return f"{self.label} ({self.uom_code})"


class CostCenter(AuditMixin):
    cc_id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=200)
    company = models.ForeignKey('Company', on_delete=models.PROTECT,
                                db_column='company_id', related_name='cost_centers')
    parent_cc = models.ForeignKey('CostCenter', null=True, blank=True, on_delete=models.SET_NULL,
                                  db_column='parent_cc_id', related_name='children')
    is_active = models.BooleanField(default=True)

    objects = BaseManager()

    class Meta:
        db_table = 'cost_centers'
        verbose_name = 'Cost Center'
        verbose_name_plural = 'Cost Centers'
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"


class DocNumberSeries(AuditMixin):
    series_id = models.BigAutoField(primary_key=True)
    company = models.ForeignKey('Company', null=True, blank=True, on_delete=models.SET_NULL,
                                db_column='company_id', related_name='doc_series')
    doc_type = models.CharField(max_length=32, choices=DocType.choices)
    prefix = models.CharField(max_length=32)
    next_int = models.IntegerField(default=1)
    pad_to = models.IntegerField(default=5)
    active = models.BooleanField(default=True)

    objects = BaseManager()

    class Meta:
        db_table = 'doc_number_series'
        verbose_name = 'Document Number Series'
        verbose_name_plural = 'Document Number Series'
        constraints = [
            models.UniqueConstraint(
                fields=['company', 'doc_type', 'prefix'],
                name='uq_doc_series_company_type_prefix'
            ),
            models.CheckConstraint(check=Q(next_int__gte=1), name='ck_docseries_nextint_ge_1'),
            models.CheckConstraint(check=Q(pad_to__gte=1), name='ck_docseries_padto_ge_1'),
        ]

    def __str__(self):
        return f"{self.doc_type} - {self.prefix}"


# ============================================================================
# ATTACHMENT & EXTERNAL REFERENCES
# ============================================================================

class Attachment(models.Model):
    file_id = models.BigAutoField(primary_key=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                              db_column='owner_id', related_name='attachments')
    category = models.CharField(max_length=32, blank=True)
    caption = models.CharField(max_length=255, blank=True)
    table_name = models.CharField(max_length=120)
    record_id = models.BigIntegerField()
    filename = models.CharField(max_length=255)
    url = models.URLField(max_length=500)
    file_size = models.BigIntegerField(null=True, blank=True)
    mime_type = models.CharField(max_length=100, blank=True)
    uploaded_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'attachments'
        verbose_name = 'Attachment'
        verbose_name_plural = 'Attachments'
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['table_name', 'record_id'], name='ix_attachment_doc')
        ]

    def __str__(self):
        return f"{self.filename} ({self.table_name})"


class ExternalSystemRef(AuditMixin):
    extref_id = models.BigAutoField(primary_key=True)
    system = models.CharField(max_length=32)
    doc_type = models.CharField(max_length=32, choices=DocType.choices)
    local_id = models.BigIntegerField()
    external_id = models.CharField(max_length=128)
    notes = models.CharField(max_length=255, blank=True)
    synced_ts = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    objects = BaseManager()

    class Meta:
        db_table = 'external_system_refs'
        verbose_name = 'External System Reference'
        verbose_name_plural = 'External System References'
        ordering = ['-synced_ts']
        indexes = [
            models.Index(fields=['doc_type', 'local_id'], name='ix_extref_doctype_local')
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['system', 'doc_type', 'external_id'],
                name='uq_extref_system_type_id'
            )
        ]

    def __str__(self):
        return f"{self.system}:{self.external_id} -> {self.doc_type}({self.local_id})"


# ============================================================================
# ITEM MANAGEMENT
# ============================================================================

class ItemGroup(AuditMixin):
    item_group_id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=120, unique=True)
    parent = models.ForeignKey('ItemGroup', null=True, blank=True, on_delete=models.SET_NULL,
                               db_column='parent_id', related_name='children')
    path = models.CharField(max_length=512, blank=True)
    depth = models.IntegerField(default=0)
    is_serialized = models.BooleanField(default=False)

    objects = BaseManager()

    class Meta:
        db_table = 'item_groups'
        verbose_name = 'Item Group'
        verbose_name_plural = 'Item Groups'
        ordering = ['path', 'code']
        indexes = [
            models.Index(fields=['path'], name='ix_item_group_path')
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"


class Item(AuditMixin):
    item_id = models.BigAutoField(primary_key=True)
    item_code = models.CharField(max_length=120, unique=True)
    item_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    item_group = models.ForeignKey('ItemGroup', null=True, blank=True, on_delete=models.SET_NULL,
                                   db_column='item_group_id', related_name='items')
    hs_code = models.CharField(max_length=20, blank=True)
    barcode = models.CharField(max_length=128, blank=True)
    uom_code = models.ForeignKey('UOM', null=True, blank=True, on_delete=models.SET_NULL,
                                 db_column='uom_code', related_name='items')
    package_size = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    package_uom = models.ForeignKey('UOM', null=True, blank=True, on_delete=models.SET_NULL,
                                    db_column='package_uom', related_name='package_items')
    weight = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    weight_uom = models.ForeignKey('UOM', null=True, blank=True, on_delete=models.SET_NULL,
                                   db_column='weight_uom', related_name='weight_items')
    dimensions = models.CharField(max_length=120, blank=True)
    manufacturer = models.ForeignKey('Company', null=True, blank=True, on_delete=models.SET_NULL,
                                     db_column='manufacturer_id', related_name='manufactured_items')
    brand = models.CharField(max_length=120, blank=True)
    model = models.CharField(max_length=120, blank=True)
    is_stock_item = models.BooleanField(default=True)
    is_purchase_item = models.BooleanField(default=True)
    is_sales_item = models.BooleanField(default=False)
    is_fixed_asset = models.BooleanField(default=False)
    is_batch_tracked = models.BooleanField(default=False)
    is_serial_tracked = models.BooleanField(default=False)
    has_shelf_life = models.BooleanField(default=False)
    shelf_life_days = models.IntegerField(null=True, blank=True)
    min_order_qty = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    reorder_level = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    reorder_qty = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    default_supplier = models.ForeignKey('Supplier', null=True, blank=True, on_delete=models.SET_NULL,
                                         db_column='default_supplier_id', related_name='default_items')
    default_warehouse = models.ForeignKey('Warehouse', null=True, blank=True, on_delete=models.SET_NULL,
                                          db_column='default_wh_id', related_name='default_items')
    lead_time_days = models.IntegerField(null=True, blank=True)
    valuation_method = models.CharField(max_length=16, default='FIFO')
    status = models.CharField(max_length=16, choices=ItemStatus.choices, default=ItemStatus.ACTIVE, db_index=True)

    objects = BaseManager()

    def clean(self):
        super().clean()
        if getattr(self, 'has_shelf_life', False):
            if not getattr(self, 'shelf_life_days', None):
                raise ValidationError({'shelf_life_days': 'Required when shelf life is enabled.'})
            if getattr(self, 'shelf_life_days', 0) <= 0:
                raise ValidationError({'shelf_life_days': 'Must be greater than zero.'})

    class Meta:
        db_table = 'items'
        verbose_name = 'Item'
        verbose_name_plural = 'Items'
        ordering = ['item_code']
        indexes = [
            models.Index(fields=['status', 'item_group'], name='ix_item_status_group')
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(lead_time_days__gte=0) | models.Q(lead_time_days__isnull=True),
                name='ck_item_lead_time_nonneg'
            ),
            models.CheckConstraint(
                check=models.Q(shelf_life_days__gt=0) | models.Q(shelf_life_days__isnull=True),
                name='ck_item_shelf_life_pos'
            ),
            models.CheckConstraint(
                check=models.Q(package_size__gt=0) | models.Q(package_size__isnull=True),
                name='ck_item_package_size_pos'
            ),
        ]

    def __str__(self):
        return f"{self.item_code} - {self.item_name}"


class ItemAttribute(AuditMixin):
    attr_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=120, unique=True)
    data_type = models.CharField(max_length=16, default='text')

    class Meta:
        db_table = 'item_attributes'
        verbose_name = 'Item Attribute'
        verbose_name_plural = 'Item Attributes'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.data_type})"


class ItemAttributeValue(AuditMixin):
    attr_val_id = models.BigAutoField(primary_key=True)
    attr = models.ForeignKey('ItemAttribute', on_delete=models.CASCADE,
                             db_column='attr_id', related_name='values')
    value = models.CharField(max_length=120)
    sort_order = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'item_attribute_values'
        verbose_name = 'Item Attribute Value'
        verbose_name_plural = 'Item Attribute Values'
        ordering = ['attr', 'sort_order', 'value']
        constraints = [
            models.UniqueConstraint(fields=['attr', 'value'], name='uq_item_attr_value')
        ]

    def __str__(self):
        return f"{self.attr.name}: {self.value}"


class ItemAttrData(AuditMixin):
    iad_id = models.BigAutoField(primary_key=True)
    item = models.ForeignKey('Item', on_delete=models.CASCADE,
                             db_column='item_id', related_name='attributes')
    attr = models.ForeignKey('ItemAttribute', on_delete=models.CASCADE,
                             db_column='attr_id', related_name='item_data')
    attr_val = models.ForeignKey('ItemAttributeValue', null=True, blank=True, on_delete=models.SET_NULL,
                                 db_column='attr_val_id', related_name='item_data')
    value_num = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    value_text = models.CharField(max_length=255, blank=True)
    value_date = models.DateField(null=True, blank=True)
    uom_code = models.ForeignKey('UOM', null=True, blank=True, on_delete=models.SET_NULL,
                                 db_column='uom_code', related_name='attr_data')

    class Meta:
        db_table = 'item_attr_data'
        verbose_name = 'Item Attribute Data'
        verbose_name_plural = 'Item Attribute Data'
        constraints = [
            models.UniqueConstraint(fields=['item', 'attr'], name='uq_item_attr_data'),
            models.CheckConstraint(
                check=(
                        models.Q(attr_val_id__isnull=False) |
                        models.Q(value_num__isnull=False) |
                        ~models.Q(value_text='') |
                        models.Q(value_date__isnull=False)
                ),
                name='ck_iad_has_some_value'
            ),
        ]


class ItemUOM(models.Model):
    item_uom_id = models.BigAutoField(primary_key=True)
    item: 'Item' = models.ForeignKey('Item', on_delete=models.CASCADE,
                                     db_column='item_id', related_name='uom_conversions')
    uom_code: 'UOM' = models.ForeignKey('UOM', on_delete=models.PROTECT,
                                        db_column='uom_code', related_name='item_conversions')
    conversion_factor = models.DecimalField(max_digits=18, decimal_places=6, default=1)

    class Meta:
        db_table = 'item_uom'
        verbose_name = 'Item UOM Conversion'
        verbose_name_plural = 'Item UOM Conversions'
        constraints = [
            models.UniqueConstraint(fields=['item', 'uom_code'], name='uq_item_uom'),
            models.CheckConstraint(check=models.Q(conversion_factor__gt=0), name='ck_item_uom_factor_pos')
        ]

    def __str__(self):
        return f"{self.item.item_code} - {self.uom_code.uom_code} (x{self.conversion_factor})"


# -----------------------------
# Contact (person or company)
# -----------------------------


# models.py (imports you’ll need)
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Q, UniqueConstraint
from .mixins import GenericPartyReferenceMixin
from .mixins import SoftDeleteMixin, PublicIdMixin  # if you use them elsewhere
from .models import AuditMixin  # your existing AuditMixin (already in your project)


# ----------------------------------------------------------------------
# CONTACTS (NEW)
# ----------------------------------------------------------------------

class Contact(GenericPartyReferenceMixin, AuditMixin):
    """
    Person or Company contact that belongs to any owner (employee, customer, supplier, carrier, company, ...).
    Exactly one contact per owner may be flagged 'is_primary=True'.
    """
    contact_id = models.BigAutoField(primary_key=True)

    CONTACT_KIND = (('person', 'Person'), ('company', 'Company'))
    kind        = models.CharField(max_length=16, choices=CONTACT_KIND, default='person', db_index=True)

    # Person
    first_name  = models.CharField(max_length=120, blank=True)
    middle_name = models.CharField(max_length=120, blank=True)
    last_name   = models.CharField(max_length=120, blank=True)

    # Company
    company_name = models.CharField(max_length=200, blank=True)

    job_title   = models.CharField(max_length=120, blank=True)
    notes       = models.TextField(blank=True)

    # “primary contact for this owner”
    is_primary  = models.BooleanField(default=False, db_index=True)

    class Meta:
        db_table = 'contacts'
        ordering = ['party_type', 'party_id', '-is_primary', 'kind', 'last_name', 'first_name', 'company_name']
        constraints = [
            UniqueConstraint(
                fields=['party_type', 'party_id'],
                condition=Q(is_primary=True),
                name='uq_contact_primary_per_party',
            )
        ]
        indexes = [
            models.Index(fields=['party_type', 'party_id', 'is_primary'], name='ix_contact_party_primary'),
            models.Index(fields=['kind', 'last_name', 'first_name'], name='ix_contact_person_name'),
            models.Index(fields=['kind', 'company_name'], name='ix_contact_company_name'),
        ]

    def clean(self):
        if self.kind == 'person':
            if not (self.first_name or '').strip():
                raise ValidationError("First name is required for a person contact.")
        elif self.kind == 'company':
            if not (self.company_name or '').strip():
                raise ValidationError("Company name is required for a company contact.")
        else:
            raise ValidationError("Unknown contact kind.")

    @property
    def display_name(self) -> str:
        if self.kind == 'company':
            return self.company_name or "(Company)"
        parts = [self.first_name, self.middle_name, self.last_name]
        name = " ".join(p for p in parts if p).strip()
        return name or "(Person)"

    def __str__(self):
        return self.display_name


e164_validator = RegexValidator(
    r'^\+[1-9]\d{6,14}$',
    "Use E.164 format, e.g., +966512345678"
)


class ContactMethod(models.Model):
    """
    Multiple methods per contact: email and/or phone.
    - Exactly one 'primary' per kind per contact
    - For phone rows, can flag is_whatsapp=True (no duplication)
    """
    METHOD = (('email', 'Email'), ('phone', 'Phone'))

    method_id  = models.BigAutoField(primary_key=True)
    contact    = models.ForeignKey('Contact', on_delete=models.CASCADE, related_name='methods')
    kind       = models.CharField(max_length=16, choices=METHOD)

    email      = models.EmailField(max_length=254, blank=True)                   # for kind='email'
    e164_phone = models.CharField(max_length=20, blank=True, validators=[e164_validator])  # for kind='phone'

    is_whatsapp = models.BooleanField(default=False)  # for phone only
    is_primary  = models.BooleanField(default=False)  # primary per kind
    label       = models.CharField(max_length=32, blank=True)  # Work/Personal/etc.

    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'contact_methods'
        ordering = ['contact_id', 'kind', '-is_primary', '-is_whatsapp', 'label']
        constraints = [
            # one primary of each kind per contact
            models.UniqueConstraint(
                fields=['contact', 'kind'],
                condition=Q(is_primary=True),
                name='uq_contactmethod_primary_per_kind'
            ),
            # avoid exact duplicates
            models.UniqueConstraint(
                fields=['contact', 'kind', 'e164_phone', 'email'],
                name='uq_contactmethod_unique_value'
            ),
        ]
        indexes = [
            models.Index(fields=['contact', 'kind']),
            models.Index(fields=['kind']),
        ]

    def clean(self):
        if self.kind == 'email':
            if not self.email:
                raise ValidationError("Email is required when kind='email'.")
            self.e164_phone = ''
            self.is_whatsapp = False
        elif self.kind == 'phone':
            if not self.e164_phone:
                raise ValidationError("Phone is required (E.164) when kind='phone'.")
            self.email = ''
        else:
            raise ValidationError("Unknown method kind.")

    def __str__(self):
        val = self.email if self.kind == 'email' else self.e164_phone
        w   = " (WhatsApp)" if (self.kind == 'phone' and self.is_whatsapp) else ""
        return f"{self.get_kind_display()}: {val}{w}"


# ----------------------------------------------------------------------
# OWNER MODELS — only the parts that change (remove old contact columns)
# ----------------------------------------------------------------------
# NOTE:
#   Delete any of these old columns if they exist on your owners:
#     contact, phone, mobile, email (EXCEPT Employee.email which you already use for login)
#   Optionally add 'primary_contact' FK for quick access (shown below).
#   All owners get helper properties: contacts, primary_contact (resolve).

# ============================================================================
# CUSTOMERS & SUPPLIERS
# ============================================================================


class Customer(AuditMixin):
    customer_id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=200, unique=True)
    company = models.ForeignKey('Company', on_delete=models.PROTECT,
                                db_column='company_id', related_name='customers')
    tax_no = models.CharField(max_length=64, blank=True)
    credit_limit = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    payment_terms = models.IntegerField(null=True, blank=True, help_text="Payment terms in days")
    currency_code = models.ForeignKey('Currency', on_delete=models.PROTECT,
                                      db_column='currency_code', related_name='customers')
    price_list = models.ForeignKey('PriceList', null=True, blank=True, on_delete=models.PROTECT,
                                   db_column='price_list_id', related_name='customers')
    status = models.CharField(max_length=32, choices=PartyStatus.choices, default=PartyStatus.ACTIVE)

    objects = BaseManager()
    # Optional: a fast pointer to the primary contact (nice in reporting/admin)
    primary_contact = models.ForeignKey(
        Contact, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='customers_as_primary',
        db_column='primary_contact_id'
    )

    class Meta:
        db_table = 'customers'
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'
        ordering = ['code']
        constraints = [
            models.CheckConstraint(
                check=models.Q(credit_limit__gte=0) | models.Q(credit_limit__isnull=True),
                name='ck_customer_credit_nonneg'
            ),
            models.CheckConstraint(
                check=models.Q(payment_terms__gte=0) | models.Q(payment_terms__isnull=True),
                name='ck_customer_terms_nonneg'
            ),
        ]

    @property
    def contacts(self):
        ct = ContentType.objects.get_for_model(self.__class__)
        return Contact.objects.filter(party_type=ct, party_id=self.pk)

    @property
    def resolved_primary_contact(self):
        return self.primary_contact or self.contacts.filter(is_primary=True).first()

    def __str__(self):
        return f"{self.code} - {self.name}"


class Supplier(AuditMixin):
    supplier_id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=200, unique=True)
    company = models.ForeignKey('Company', on_delete=models.PROTECT,
                                db_column='company_id', related_name='suppliers')
    tax_no = models.CharField(max_length=64, blank=True)
    credit_limit = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    payment_terms = models.IntegerField(null=True, blank=True, help_text="Payment terms in days")
    currency_code = models.ForeignKey('Currency', on_delete=models.PROTECT,
                                      db_column='currency_code', related_name='suppliers')
    status = models.CharField(max_length=32, choices=PartyStatus.choices, default=PartyStatus.ACTIVE)

    objects = BaseManager()
    primary_contact = models.ForeignKey(
        Contact, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='suppliers_as_primary',
        db_column='primary_contact_id'
    )
    class Meta:
        db_table = 'suppliers'
        verbose_name = 'Supplier'
        verbose_name_plural = 'Suppliers'
        ordering = ['code']
        constraints = [
            models.CheckConstraint(
                check=models.Q(credit_limit__gte=0) | models.Q(credit_limit__isnull=True),
                name='ck_supplier_credit_nonneg'
            ),
            models.CheckConstraint(
                check=models.Q(payment_terms__gte=0) | models.Q(payment_terms__isnull=True),
                name='ck_supplier_terms_nonneg'
            ),
        ]
    @property
    def contacts(self):
        ct = ContentType.objects.get_for_model(self.__class__)
        return Contact.objects.filter(party_type=ct, party_id=self.pk)

    @property
    def resolved_primary_contact(self):
        return self.primary_contact or self.contacts.filter(is_primary=True).first()

    def __str__(self):
        return f"{self.code} - {self.name}"


class Address(AuditMixin):
    """Normalized physical/mailing address. No owner/phone/email here."""
    address_id = models.BigAutoField(primary_key=True)

    # ISO country (e.g., SA, JO, US)
    country_code = models.CharField(
        max_length=2,
        validators=[RegexValidator(r'^[A-Z]{2}$', 'Must be ISO 3166-1 alpha-2 (e.g., SA, JO, US).')],
        help_text="ISO 3166-1 alpha-2 (e.g., 'SA' for Saudi Arabia).",
        null=True, blank=True,  # TEMPORARY to allow migration without prompts
    )

    # Regionals
    region       = models.CharField(max_length=64, blank=True)   # state/province/region
    city         = models.CharField(max_length=64)
    neighborhood = models.CharField(max_length=64, blank=True)   # حي / district
    street_name  = models.CharField(max_length=128, blank=True)

    # KSA National Address specifics (optional → global-safe)
    building_no   = models.CharField(max_length=10, blank=True)
    additional_no = models.CharField(max_length=10, blank=True)
    unit_no       = models.CharField(max_length=10, blank=True)
    postal_code   = models.CharField(
        max_length=12, blank=True,
        help_text="KSA: 5 digits (e.g., 12345). Other formats accepted.",
    )

    # Free-form fallbacks (for odd international formats)
    line1  = models.CharField(max_length=128, blank=True)
    line2  = models.CharField(max_length=128, blank=True)
    po_box = models.CharField(max_length=32,  blank=True)

    # Optional geo
    latitude  = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # Dedupe helpers
    normalized_text = models.TextField(editable=False, blank=True)
    fingerprint     = models.CharField(max_length=40, editable=False, blank=True, db_index=True)  # SHA1

    class Meta:
        db_table = "addresses"
        ordering = ["country_code", "region", "city", "neighborhood", "street_name", "building_no"]
        indexes = [
            models.Index(fields=["country_code", "region", "city"], name="ix_addr_cc_region_city"),
            models.Index(fields=["neighborhood"], name="ix_addr_neighborhood"),
            models.Index(fields=["postal_code"], name="ix_addr_postal"),
            models.Index(fields=["fingerprint"], name="ix_addr_fingerprint"),
        ]
        constraints = [
            # Soft exact-tuple uniqueness to discourage accidental duplicates
            models.UniqueConstraint(
                fields=[
                    "country_code","region","city","neighborhood",
                    "street_name","building_no","additional_no","unit_no","postal_code",
                    "line1","line2","po_box",
                ],
                name="uq_addr_exact_tuple",
            ),
        ]

    def save(self, *args, **kwargs):
        parts = [
            (self.line1 or "").strip(), (self.line2 or "").strip(), (self.po_box or "").strip(),
            (self.street_name or "").strip(), (self.building_no or "").strip(),
            (self.additional_no or "").strip(), (self.unit_no or "").strip(),
            (self.neighborhood or "").strip(), (self.city or "").strip(),
            (self.region or "").strip(), (self.postal_code or "").strip(),
            (self.country_code or "").strip(),
        ]
        self.normalized_text = " | ".join(p for p in parts if p).lower()
        self.fingerprint = hashlib.sha1(self.normalized_text.encode("utf-8")).hexdigest() if self.normalized_text else ""
        super().save(*args, **kwargs)

    def __str__(self):
        bits = [self.line1, self.line2, self.po_box, self.street_name, self.building_no,
                self.additional_no, self.unit_no, self.neighborhood, self.city,
                self.region, self.postal_code, self.country_code]
        return ", ".join([b for b in bits if b])


class AddressType(models.TextChoices):
    HOME      = "home", "Home"
    OFFICE    = "office", "Office/HQ"
    WAREHOUSE = "warehouse", "Warehouse/Site"
    BILLING   = "billing", "Billing"
    SHIPPING  = "shipping", "Shipping"
    OTHER     = "other", "Other"


class AddressLink(AuditMixin):
    link_id = models.BigAutoField(primary_key=True)

    owner_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name="address_links")
    owner_object_id    = models.BigIntegerField()
    owner              = GenericForeignKey("owner_content_type", "owner_object_id")

    address    = models.ForeignKey(Address, on_delete=models.CASCADE, related_name="links")
    label      = models.CharField(max_length=120, blank=True)          # e.g., "Address 1", "Head Office"
    type       = models.CharField(max_length=16, choices=AddressType.choices, default=AddressType.OTHER, db_index=True)
    is_primary = models.BooleanField(default=False, db_index=True)
    sequence   = models.PositiveSmallIntegerField(default=1)

    class Meta:
        db_table = "addresses_link"
        ordering = ["owner_content_type", "owner_object_id", "type", "sequence"]
        indexes  = [
            models.Index(fields=["owner_content_type", "owner_object_id", "type"], name="ix_addr_owner_type"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["owner_content_type", "owner_object_id", "address"],
                name="uq_addr_link_owner_address",
            ),
            models.UniqueConstraint(
                fields=["owner_content_type", "owner_object_id", "type"],
                condition=models.Q(is_primary=True),
                name="uq_addr_primary_per_owner_type",
            ),
        ]

    def save(self, *args, **kwargs):
        if not self.sequence:
            qs = AddressLink.objects.filter(
                owner_content_type=self.owner_content_type,
                owner_object_id=self.owner_object_id,
            )
            self.sequence = (qs.aggregate(models.Max("sequence"))["sequence__max"] or 0) + 1
        if not self.label:
            count = AddressLink.objects.filter(
                owner_content_type=self.owner_content_type,
                owner_object_id=self.owner_object_id,
            ).count() + (0 if self.pk else 1)
            self.label = f"Address {count}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.owner_content_type.model}:{self.owner_object_id} • {self.get_type_display()} • {self.label}"



# Logistics
class Carrier(AuditMixin):
    carrier_id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=200)
    mode = models.CharField(max_length=16, blank=True)
    is_active = models.BooleanField(default=True)

    objects = BaseManager()
    primary_contact = models.ForeignKey(
        Contact, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='carriers_as_primary',
        db_column='primary_contact_id'
    )

    class Meta:
        db_table = 'carriers'
        verbose_name = 'Carrier'
        verbose_name_plural = 'Carriers'
        ordering = ['code']

    @property
    def contacts(self):
        ct = ContentType.objects.get_for_model(self.__class__)
        return Contact.objects.filter(party_type=ct, party_id=self.pk)

    @property
    def resolved_primary_contact(self):
        return self.primary_contact or self.contacts.filter(is_primary=True).first()

    def __str__(self):
        return f"{self.code} - {self.name}"

class Company(AuditMixin):
    company_id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=200, unique=True)
    tax_no = models.CharField(max_length=64, blank=True)
    base_currency = models.ForeignKey('Currency', on_delete=models.PROTECT,
                                      db_column='base_currency', related_name='companies')
    fiscal_year_start_month = models.IntegerField(help_text="Month when fiscal year starts (1-12)")
    is_active = models.BooleanField(default=True)
    primary_contact = models.ForeignKey(
        Contact, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='companies_as_primary',
        db_column='primary_contact_id'
    )
    objects = BaseManager()

    class Meta:
        db_table = 'companies'
        verbose_name = 'Company'
        verbose_name_plural = 'Companies'
        ordering = ['code']
        constraints = [
            models.CheckConstraint(
                check=models.Q(fiscal_year_start_month__gte=1, fiscal_year_start_month__lte=12),
                name='ck_company_fy_month_1_12'
            ),
        ]

    @property
    def contacts(self):
        ct = ContentType.objects.get_for_model(self.__class__)
        return Contact.objects.filter(party_type=ct, party_id=self.pk)

    @property
    def resolved_primary_contact(self):
        return self.primary_contact or self.contacts.filter(is_primary=True).first()

    def __str__(self):
        return f"{self.code} - {self.name}"








# ============================================================================
# WAREHOUSE & INVENTORY
# ============================================================================


class Warehouse(models.Model):
    wh_id = models.BigAutoField(primary_key=True)
    warehouse_code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=120, unique=True)
    warehouse_type = models.CharField(max_length=32, blank=True)
    parent_wh = models.ForeignKey('Warehouse', null=True, blank=True, on_delete=models.SET_NULL,
                                  db_column='parent_wh_id', related_name='sub_warehouses')
    company = models.ForeignKey('Company', on_delete=models.PROTECT,
                                db_column='company_id', related_name='warehouses')
    address = models.ForeignKey('Address', null=True, blank=True, on_delete=models.SET_NULL,
                                db_column='address_id', related_name='warehouses')
    is_active = models.BooleanField(default=True)

    objects = BaseManager()

    class Meta:
        db_table = 'warehouses'
        verbose_name = 'Warehouse'
        verbose_name_plural = 'Warehouses'
        ordering = ['warehouse_code']

    def __str__(self):
        return f"{self.warehouse_code} - {self.name}"


class Location(models.Model):
    loc_id = models.BigAutoField(primary_key=True)
    wh: 'Warehouse' = models.ForeignKey('Warehouse', on_delete=models.PROTECT,
                                        db_column='wh_id', related_name='locations')
    code = models.CharField(max_length=64)
    bin_type = models.CharField(max_length=64, blank=True)
    capacity = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    objects = BaseManager()

    class Meta:
        db_table = 'locations'
        verbose_name = 'Location'
        verbose_name_plural = 'Locations'
        ordering = ['wh', 'code']
        constraints = [
            models.UniqueConstraint(fields=['wh', 'code'], name='uq_location_wh_code')
        ]

    def __str__(self):
        return f"{self.wh.warehouse_code}/{self.code}"


class Batch(models.Model):
    batch_id = models.BigAutoField(primary_key=True)
    item: 'Item' = models.ForeignKey('Item', on_delete=models.PROTECT,
                                     db_column='item_id', related_name='batches')
    batch_code = models.CharField(max_length=120, unique=True)
    mfg_date = models.DateField(null=True, blank=True)
    exp_date = models.DateField(null=True, blank=True)
    supplier_batch = models.CharField(max_length=120, blank=True)

    class Meta:
        db_table = 'batches'
        verbose_name = 'Batch'
        verbose_name_plural = 'Batches'
        ordering = ['batch_code']
        indexes = [
            models.Index(fields=['item'], name='ix_batch_item'),
            models.Index(fields=['exp_date'], name='ix_batch_exp')
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(exp_date__gte=models.F('mfg_date')) | models.Q(exp_date__isnull=True) | models.Q(
                    mfg_date__isnull=True),
                name='ck_batch_exp_ge_mfg'
            )
        ]

    def __str__(self):
        return f"{self.batch_code} ({self.item.item_code})"


class Serial(models.Model):
    serial_id = models.BigAutoField(primary_key=True)
    item: 'Item' = models.ForeignKey('Item', on_delete=models.PROTECT,
                                     db_column='item_id', related_name='serials')
    serial_no = models.CharField(max_length=120, unique=True)
    batch = models.ForeignKey('Batch', null=True, blank=True, on_delete=models.SET_NULL,
                              db_column='batch_id', related_name='serials')
    status = models.CharField(max_length=32, blank=True)
    warranty_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'serials'
        verbose_name = 'Serial Number'
        verbose_name_plural = 'Serial Numbers'
        ordering = ['serial_no']
        indexes = [
            models.Index(fields=['item'], name='ix_serial_item'),
            models.Index(fields=['status'], name='ix_serial_status')
        ]

    def __str__(self):
        return f"{self.serial_no} ({self.item.item_code})"


class StockLedger(PostingMixin, DocumentReferenceMixin):
    sle_id = models.BigAutoField(primary_key=True)
    item = models.ForeignKey('Item', on_delete=models.PROTECT,
                             db_column='item_id', related_name='stock_ledger_entries')
    wh = models.ForeignKey('Warehouse', on_delete=models.PROTECT,
                           db_column='wh_id', related_name='stock_ledger_entries')
    loc = models.ForeignKey('Location', null=True, blank=True, on_delete=models.SET_NULL,
                            db_column='loc_id', related_name='stock_ledger_entries')
    qty_in = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    qty_out = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    balance_qty = models.DecimalField(max_digits=18, decimal_places=6)
    uom_code = models.ForeignKey('UOM', null=True, blank=True, on_delete=models.SET_NULL,
                                 db_column='uom_code', related_name='stock_ledger_entries')
    batch = models.ForeignKey('Batch', null=True, blank=True, on_delete=models.SET_NULL,
                              db_column='batch_id', related_name='stock_ledger_entries')
    serial = models.ForeignKey('Serial', null=True, blank=True, on_delete=models.SET_NULL,
                               db_column='serial_id', related_name='stock_ledger_entries')
    company = models.ForeignKey('Company', on_delete=models.PROTECT,
                                db_column='company_id', related_name='stock_ledger_entries')
    rate = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    value = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)

    class Meta:
        db_table = 'stock_ledger'
        verbose_name = 'Stock Ledger Entry'
        verbose_name_plural = 'Stock Ledger Entries'
        indexes = [
            models.Index(fields=['item', 'wh', 'posting_ts'], name='ix_sle_item_wh_date'),
            models.Index(fields=['posting_ts'], name='ix_sle_posting'),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(qty_in__gte=0) & models.Q(qty_out__gte=0),
                name='ck_sle_qty_nonneg'
            ),
            models.CheckConstraint(
                check=(models.Q(qty_in__gt=0) & models.Q(qty_out=0)) | (models.Q(qty_out__gt=0) & models.Q(qty_in=0)),
                name='ck_sle_one_direction_only'
            ),
        ]


class InventoryBalance(models.Model):
    invbal_id = models.BigAutoField(primary_key=True)
    item = models.ForeignKey('Item', on_delete=models.CASCADE,
                             db_column='item_id', related_name='balances')
    wh = models.ForeignKey('Warehouse', on_delete=models.CASCADE,
                           db_column='wh_id', related_name='balances')
    loc = models.ForeignKey('Location', on_delete=models.CASCADE,
                            db_column='loc_id', related_name='balances')
    batch = models.ForeignKey('Batch', null=True, blank=True, on_delete=models.SET_NULL,
                              db_column='batch_id', related_name='balances')
    serial = models.ForeignKey('Serial', null=True, blank=True, on_delete=models.SET_NULL,
                               db_column='serial_id', related_name='balances')
    qty_on_hand = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    qty_reserved = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    qty_available = models.DecimalField(max_digits=18, decimal_places=6, default=0)

    class Meta:
        db_table = 'inventory_balances'
        verbose_name = 'Inventory Balance'
        verbose_name_plural = 'Inventory Balances'
        indexes = [
            models.Index(fields=['item', 'wh', 'loc'], name='ix_invbal_item_wh_loc'),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['item', 'wh', 'loc', 'batch', 'serial'],
                name='uq_invbal_item_wh_loc_batch_serial'
            ),
            models.CheckConstraint(check=models.Q(qty_on_hand__gte=0), name='ck_invbal_qty_nonneg'),
            models.CheckConstraint(
                check=models.Q(qty_reserved__lte=models.F('qty_on_hand')),
                name='ck_invbal_reserved_le_onhand'
            ),
            models.CheckConstraint(
                check=models.Q(qty_available=models.F('qty_on_hand') - models.F('qty_reserved')),
                name='ck_invbal_avail_eq_onhand_minus_reserved'
            ),
        ]


class StockEntryPurpose(models.TextChoices):
    MATERIAL_ISSUE = 'Material Issue', 'Material Issue'
    MATERIAL_RECEIPT = 'Material Receipt', 'Material Receipt'
    MATERIAL_TRANSFER = 'Material Transfer', 'Material Transfer'
    MANUFACTURING = 'Manufacturing', 'Manufacturing'
    ADJUSTMENT = 'Adjustment', 'Adjustment'


class StockEntry(AuditMixin, PostingMixin):
    se_id = models.BigAutoField(primary_key=True)
    se_no = models.CharField(max_length=64, unique=True)
    purpose = models.CharField(max_length=24, choices=StockEntryPurpose.choices)
    status = models.CharField(max_length=32, choices=StockEntryStatus.choices, default=StockEntryStatus.DRAFT)
    company = models.ForeignKey('Company', on_delete=models.PROTECT,
                                db_column='company_id', related_name='stock_entries')
    wo = models.ForeignKey('WorkOrder', null=True, blank=True, on_delete=models.SET_NULL,
                           db_column='wo_id', related_name='stock_entries')
    cost_center = models.ForeignKey('CostCenter', null=True, blank=True, on_delete=models.SET_NULL,
                                    db_column='cost_center_id', related_name='stock_entries')

    objects = BaseManager()

    class Meta:
        db_table = 'stock_entries'
        verbose_name = 'Stock Entry'
        verbose_name_plural = 'Stock Entries'

    def __str__(self):
        return f"{self.se_no} ({self.status})"


class StockEntryItem(models.Model):
    sei_id = models.BigAutoField(primary_key=True)
    se = models.ForeignKey('StockEntry', on_delete=models.CASCADE,
                           db_column='se_id', related_name='items')
    item = models.ForeignKey('Item', on_delete=models.PROTECT,
                             db_column='item_id', related_name='stock_entry_items')
    s_warehouse = models.ForeignKey('Warehouse', null=True, blank=True, on_delete=models.SET_NULL,
                                    db_column='s_warehouse_id', related_name='source_entries')
    s_location = models.ForeignKey('Location', null=True, blank=True, on_delete=models.SET_NULL,
                                   db_column='s_location_id', related_name='source_entries')
    t_warehouse = models.ForeignKey('Warehouse', null=True, blank=True, on_delete=models.SET_NULL,
                                    db_column='t_warehouse_id', related_name='target_entries')
    t_location = models.ForeignKey('Location', null=True, blank=True, on_delete=models.SET_NULL,
                                   db_column='t_location_id', related_name='target_entries')
    qty = models.DecimalField(max_digits=18, decimal_places=6)
    uom_code = models.ForeignKey('UOM', null=True, blank=True, on_delete=models.SET_NULL,
                                 db_column='uom_code', related_name='stock_entry_items')
    batch = models.ForeignKey('Batch', null=True, blank=True, on_delete=models.SET_NULL,
                              db_column='batch_id', related_name='stock_entry_items')
    serial = models.ForeignKey('Serial', null=True, blank=True, on_delete=models.SET_NULL,
                               db_column='serial_id', related_name='stock_entry_items')
    basic_rate = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    basic_amount = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)

    class Meta:
        db_table = 'stock_entry_items'
        verbose_name = 'Stock Entry Item'
        verbose_name_plural = 'Stock Entry Items'
        constraints = [
            models.CheckConstraint(check=models.Q(qty__gt=0), name='ck_sei_qty_pos'),
            models.CheckConstraint(
                check=models.Q(basic_rate__gte=0) | models.Q(basic_rate__isnull=True),
                name='ck_sei_rate_nonneg'
            ),
            models.CheckConstraint(
                name='ck_sei_source_or_target_present',
                check=(
                        Q(s_warehouse__isnull=False) |
                        Q(t_warehouse__isnull=False)
                ),
            ),

        ]


# ============================================================================
# BOM & MANUFACTURING
# ============================================================================

class BOM(AuditMixin):
    bom_id = models.BigAutoField(primary_key=True)
    bom_no = models.CharField(max_length=64, unique=True)
    item: 'Item' = models.ForeignKey('Item', on_delete=models.PROTECT,
                                     db_column='item_id', related_name='boms')
    revision = models.CharField(max_length=32, blank=True)
    qty = models.DecimalField(max_digits=18, decimal_places=6, default=1)
    uom_code = models.ForeignKey('UOM', null=True, blank=True, on_delete=models.SET_NULL,
                                 db_column='uom_code', related_name='boms')
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)

    objects = BaseManager()

    class Meta:
        db_table = 'boms'
        verbose_name = 'BOM'
        verbose_name_plural = 'BOMs'
        ordering = ['bom_no']
        indexes = [
            models.Index(fields=['item', 'is_active'], name='ix_bom_item_active')
        ]
        constraints = [
            models.CheckConstraint(check=models.Q(qty__gt=0), name='ck_bom_qty_pos')
        ]

    def __str__(self):
        return f"{self.bom_no} - {self.item.item_code}"


class BOMItem(models.Model):
    bom_item_id = models.BigAutoField(primary_key=True)
    bom = models.ForeignKey('BOM', on_delete=models.CASCADE,
                            db_column='bom_id', related_name='components')
    component_item = models.ForeignKey('Item', on_delete=models.PROTECT,
                                       db_column='component_item_id', related_name='used_in_boms')
    qty = models.DecimalField(max_digits=18, decimal_places=6, default=1)
    uom_code = models.ForeignKey('UOM', null=True, blank=True, on_delete=models.SET_NULL,
                                 db_column='uom_code', related_name='bom_items')
    scrap_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    operation_seq = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'bom_items'
        verbose_name = 'BOM Item'
        verbose_name_plural = 'BOM Items'
        constraints = [
            models.CheckConstraint(check=models.Q(qty__gt=0), name='ck_bomitem_qty_pos'),
            models.CheckConstraint(
                check=models.Q(scrap_pct__gte=0, scrap_pct__lte=100) | models.Q(scrap_pct__isnull=True),
                name='ck_bomitem_scrap_pct'
            ),
        ]


class Operation(AuditMixin):
    operation_id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    default_workstation = models.ForeignKey('Workstation', null=True, blank=True, on_delete=models.SET_NULL,
                                            db_column='default_workstation_id', related_name='default_operations')
    std_time_min = models.IntegerField(null=True, blank=True, help_text="Standard time in minutes")
    std_setup_min = models.IntegerField(null=True, blank=True, help_text="Standard setup time in minutes")

    objects = BaseManager()

    class Meta:
        db_table = 'operations'
        verbose_name = 'Operation'
        verbose_name_plural = 'Operations'
        ordering = ['code']
        constraints = [
            models.CheckConstraint(
                check=models.Q(std_time_min__gt=0) | models.Q(std_time_min__isnull=True),
                name='ck_op_time_pos'
            ),
            models.CheckConstraint(
                check=models.Q(std_setup_min__gte=0) | models.Q(std_setup_min__isnull=True),
                name='ck_op_setup_nonneg'
            ),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"


class Workstation(AuditMixin):
    workstation_id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=120, unique=True)
    dept = models.CharField(max_length=120, blank=True)
    cost_center = models.ForeignKey('CostCenter', null=True, blank=True, on_delete=models.SET_NULL,
                                    db_column='cost_center_id', related_name='workstations')
    capacity_per_shift = models.IntegerField(null=True, blank=True)
    hour_rate = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'workstations'
        verbose_name = 'Workstation'
        verbose_name_plural = 'Workstations'
        ordering = ['code']
        constraints = [
            models.CheckConstraint(
                check=models.Q(capacity_per_shift__isnull=True) | models.Q(capacity_per_shift__gte=0),
                name='ck_ws_capacity_nonneg'
            ),
            models.CheckConstraint(
                check=models.Q(hour_rate__isnull=True) | models.Q(hour_rate__gte=0),
                name='ck_ws_hour_rate_nonneg'
            ),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"


class Route(AuditMixin):
    route_id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=120, unique=True)
    item = models.ForeignKey('Item', null=True, blank=True, on_delete=models.SET_NULL,
                             db_column='item_id', related_name='routes')
    is_active = models.BooleanField(default=True)

    objects = BaseManager()

    class Meta:
        db_table = 'routes'
        verbose_name = 'Route'
        verbose_name_plural = 'Routes'
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"


class RouteOperation(models.Model):
    route_op_id = models.BigAutoField(primary_key=True)
    route: 'Route' = models.ForeignKey('Route', on_delete=models.CASCADE,
                                       db_column='route_id', related_name='operations')
    op_seq = models.IntegerField(help_text="Operation sequence number within the route")
    operation = models.ForeignKey('Operation', null=True, blank=True, on_delete=models.SET_NULL,
                                  db_column='operation_id', related_name='route_operations')
    workstation = models.ForeignKey('Workstation', on_delete=models.PROTECT,
                                    db_column='workstation_id', related_name='route_operations')
    std_time_min = models.IntegerField(null=True, blank=True,
                                       help_text="Standard processing time per unit in minutes")
    std_setup_min = models.IntegerField(null=True, blank=True,
                                        help_text="Standard setup time in minutes")

    class Meta:
        db_table = 'route_operations'
        ordering = ['route', 'op_seq']
        verbose_name = 'Route Operation'
        verbose_name_plural = 'Route Operations'
        indexes = [
            models.Index(fields=['route', 'op_seq'], name='ix_route_op_route_seq'),
            models.Index(fields=['workstation'], name='ix_route_op_workstation'),
        ]
        constraints = [
            models.UniqueConstraint(fields=['route', 'op_seq'], name='uq_route_op_route_seq'),
            models.CheckConstraint(check=models.Q(op_seq__gte=1), name='ck_route_op_seq_ge_1'),
            models.CheckConstraint(
                check=models.Q(std_time_min__gt=0) | models.Q(std_time_min__isnull=True),
                name='ck_route_op_time_pos'
            ),
            models.CheckConstraint(
                check=models.Q(std_setup_min__gte=0) | models.Q(std_setup_min__isnull=True),
                name='ck_route_op_setup_nonneg'
            ),
        ]

    def __str__(self):
        op_name = self.operation.name if self.operation else "Custom Op"
        return f"{self.route.code} - #{self.op_seq}: {op_name}"

    @property
    def total_time_min(self):
        """Calculate total time including setup and processing"""
        setup = self.std_setup_min or 0
        process = self.std_time_min or 0
        return setup + process


# ============================================================================
# BIT MAP & CUTTER MODELS
# ============================================================================


class BitMap(AuditMixin):
    map_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    cutters_count = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'bit_maps'
        verbose_name = 'Bit Map'
        verbose_name_plural = 'Bit Maps'
        ordering = ['name']

    def __str__(self):
        return self.name


class BitPocket(AuditMixin):
    pocket_id = models.BigAutoField(primary_key=True)
    map = models.ForeignKey('BitMap', on_delete=models.CASCADE,
                            db_column='map_id', related_name='pockets')
    blade_no = models.IntegerField(db_index=True)
    row_no = models.IntegerField(db_index=True)
    row_code = models.CharField(max_length=2, db_index=True)
    pocket_seq_blade = models.IntegerField(db_index=True)
    pocket_seq_blade_row = models.IntegerField(db_index=True)
    pocket_seq_global = models.IntegerField(db_index=True)
    engagement_order = models.IntegerField(db_index=True, null=True, blank=True)
    code = models.CharField(max_length=32, db_index=True)
    pocket_length = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    pocket_diameter = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    pocket_shape = models.CharField(max_length=6, choices=PocketShapeEnumChoices.choices, blank=True)
    profile_zone = models.CharField(max_length=8, choices=ProfileZoneEnumChoices.choices, blank=True)
    insert_material = models.CharField(max_length=64, blank=True)
    meta_json = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = 'bit_pockets'
        verbose_name = 'Bit Pocket'
        verbose_name_plural = 'Bit Pockets'
        indexes = [
            models.Index(fields=['map', 'blade_no', 'row_no', 'pocket_seq_blade_row'],
                         name='ix_pocket_map_blade_row_seq')
        ]
        constraints = [
            models.UniqueConstraint(fields=['map', 'code'], name='uq_pocket_map_code'),
            models.UniqueConstraint(fields=['map', 'blade_no', 'pocket_seq_blade'],
                                    name='uq_pocket_map_blade_seq'),
            models.UniqueConstraint(fields=['map', 'blade_no', 'row_no', 'pocket_seq_blade_row'],
                                    name='uq_pocket_map_blade_row_seq')
        ]

    def __str__(self):
        return f"{self.code} (Blade {self.blade_no}, Row {self.row_code})"


class BitFin(AuditMixin):
    """Fin segments per blade/row for a BitMap"""
    fin_id = models.BigAutoField(primary_key=True)
    map = models.ForeignKey('BitMap', on_delete=models.CASCADE,
                            db_column='map_id', related_name='fins')
    blade_no = models.IntegerField(db_index=True)
    row_label = models.CharField(max_length=8, db_index=True)
    fin_seq = models.IntegerField(db_index=True)
    before_pocket_seq = models.IntegerField(null=True, blank=True)
    after_pocket_seq = models.IntegerField(null=True, blank=True)
    thickness = models.CharField(max_length=16, default='MEDIUM')
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'bit_fins'
        verbose_name = 'Bit Fin'
        verbose_name_plural = 'Bit Fins'
        indexes = [
            models.Index(fields=['map', 'blade_no', 'row_label'], name='ix_bitfin_scope')
        ]
        constraints = [
            models.UniqueConstraint(fields=['map', 'blade_no', 'row_label', 'fin_seq'],
                                    name='uq_bitfin_map_blade_row_seq'),
            models.CheckConstraint(check=models.Q(fin_seq__gte=1), name='ck_bitfin_seq_pos')
        ]


class CutterBOM(AuditMixin, DocumentReferenceMixin):
    cutter_bom_id = models.BigAutoField(primary_key=True)
    bit_map = models.ForeignKey('BitMap', on_delete=models.PROTECT,
                                db_column='bit_map_id', related_name='cutter_boms')
    version = models.CharField(max_length=32, db_index=True)
    kind = models.CharField(default='PRODUCTION', max_length=10, choices=BOMKindEnumChoices.choices)
    is_active = models.BooleanField(default=True)
    parent_bom = models.ForeignKey('CutterBOM', null=True, blank=True, on_delete=models.SET_NULL,
                                   db_column='parent_bom_id', related_name='children')
    baseline_bom = models.ForeignKey('CutterBOM', null=True, blank=True, on_delete=models.SET_NULL,
                                     db_column='baseline_bom_id', related_name='derived_boms')
    source_evaluation = models.ForeignKey('BitEvaluation', null=True, blank=True, on_delete=models.SET_NULL,
                                          db_column='source_evaluation_id', related_name='produced_boms')
    notes = models.TextField(blank=True)

    objects = BaseManager()

    class Meta:
        db_table = 'cutter_boms'
        verbose_name = 'Cutter BOM'
        verbose_name_plural = 'Cutter BOMs'
        constraints = [
            models.UniqueConstraint(fields=['bit_map', 'version'], name='uq_cutter_bom_map_version')
        ]

    def __str__(self):
        return f"{self.bit_map.name} v{self.version} ({self.kind})"


class CutterBOMMap(AuditMixin):
    bom_map_id = models.BigAutoField(primary_key=True)
    cutter_bom = models.ForeignKey('CutterBOM', on_delete=models.CASCADE,
                                   db_column='cutter_bom_id', related_name='pocket_lines')
    pocket = models.ForeignKey('BitPocket', on_delete=models.PROTECT,
                               db_column='pocket_id', related_name='bom_mappings')
    original_item = models.ForeignKey('Item', null=True, blank=True, on_delete=models.SET_NULL,
                                      db_column='original_item_id', related_name='original_mappings')
    decision = models.CharField(default='OKAY', max_length=7, choices=CutterDecisionEnumChoices.choices)
    replacement_item = models.ForeignKey('Item', null=True, blank=True, on_delete=models.SET_NULL,
                                         db_column='replacement_item_id', related_name='replacement_mappings')
    rotate_stage = models.IntegerField(null=True, blank=True)
    cutter_variant = models.CharField(max_length=12, choices=CutterVariantEnumChoices.choices, blank=True)
    required_spec_json = models.JSONField(null=True, blank=True)
    qty = models.DecimalField(max_digits=18, decimal_places=6, default=1)

    class Meta:
        db_table = 'cutter_bom_map'
        verbose_name = 'Cutter BOM Mapping'
        verbose_name_plural = 'Cutter BOM Mappings'
        constraints = [
            models.UniqueConstraint(fields=['cutter_bom', 'pocket_id'], name='uq_cutter_bom_map'),
            models.CheckConstraint(check=models.Q(qty__gte=0), name='ck_cutter_bom_map_qty_nonneg'),
            models.CheckConstraint(
                check=models.Q(rotate_stage__range=(0, 2)) | models.Q(rotate_stage__isnull=True),
                name='ck_rotate_stage_0_2'
            ),
        ]


class BitEvaluation(AuditMixin, DocumentReferenceMixin):
    evaluation_id = models.BigAutoField(primary_key=True)
    bit_map = models.ForeignKey('BitMap', on_delete=models.PROTECT,
                                db_column='bit_map_id', related_name='evaluations')
    eval_stage = models.CharField(max_length=24, blank=True)
    reference_bom = models.ForeignKey('CutterBOM', null=True, blank=True, on_delete=models.SET_NULL,
                                      db_column='reference_bom_id', related_name='reference_evaluations')
    produced_bom = models.ForeignKey('CutterBOM', null=True, blank=True, on_delete=models.SET_NULL,
                                     db_column='produced_bom_id', related_name='result_evaluations')
    summary = models.TextField(blank=True)

    class Meta:
        db_table = 'bit_evaluations'
        verbose_name = 'Bit Evaluation'
        verbose_name_plural = 'Bit Evaluations'
        ordering = ['-created_at']

    def __str__(self):
        return f"Evaluation {self.evaluation_id} - {self.bit_map.name}"


# ============================================================================
# PURCHASE & SALES
# ============================================================================

class PurchaseOrder(AuditMixin):
    po_id = models.BigAutoField(primary_key=True)
    po_no = models.CharField(max_length=64, unique=True)
    revision = models.IntegerField(default=0)
    supplier: 'Supplier' = models.ForeignKey('Supplier', on_delete=models.PROTECT,
                                             db_column='supplier_id', related_name='purchase_orders')
    po_date = models.DateField()
    required_date = models.DateField(null=True, blank=True)
    company = models.ForeignKey('Company', on_delete=models.PROTECT,
                                db_column='company_id', related_name='purchase_orders')
    cost_center = models.ForeignKey('CostCenter', null=True, blank=True, on_delete=models.SET_NULL,
                                    db_column='cost_center_id', related_name='purchase_orders')
    currency_code = models.ForeignKey('Currency', on_delete=models.PROTECT,
                                      db_column='currency_code', related_name='purchase_orders')
    conversion_rate = models.DecimalField(max_digits=18, decimal_places=6, default=1)
    net_total = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    tax_total = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    grand_total = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    status = models.CharField(max_length=16, choices=OrderStatus.choices, default=OrderStatus.DRAFT, db_index=True)

    objects = BaseManager()

    class Meta:
        db_table = 'purchase_orders'
        ordering = ['-po_date', 'po_no']
        verbose_name = 'Purchase Order'
        verbose_name_plural = 'Purchase Orders'
        indexes = [
            models.Index(fields=['status', 'po_date'], name='ix_po_status_date'),
            models.Index(fields=['supplier'], name='ix_po_supplier'),
            models.Index(  # ✅ expressions passed positionally (no 'expressions=' kw)
                F('supplier'),
                F('status'),
                OrderBy(F('po_date'), descending=True),
                name='ix_po_supp_status_date',
            ),
        ]
        constraints = [
            models.CheckConstraint(check=models.Q(conversion_rate__gt=0), name='ck_po_rate_pos'),
            models.CheckConstraint(
                check=models.Q(grand_total__gte=0) | models.Q(grand_total__isnull=True),
                name='ck_po_gt_nonneg'
            ),
        ]

    def __str__(self):
        return f"{self.po_no} - {self.supplier.code} ({self.status})"


class PurchaseOrderItem(models.Model):
    poi_id = models.BigAutoField(primary_key=True)
    po = models.ForeignKey('PurchaseOrder', on_delete=models.CASCADE,
                           db_column='po_id', related_name='items')
    item = models.ForeignKey('Item', on_delete=models.PROTECT,
                             db_column='item_id', related_name='po_items')
    qty = models.DecimalField(max_digits=18, decimal_places=6)
    received_qty = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    uom_code = models.ForeignKey('UOM', null=True, blank=True, on_delete=models.SET_NULL,
                                 db_column='uom_code', related_name='po_items')
    rate = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    amount = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    need_by_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'purchase_order_items'
        verbose_name = 'Purchase Order Item'
        verbose_name_plural = 'Purchase Order Items'
        constraints = [
            models.CheckConstraint(check=models.Q(qty__gt=0), name='ck_poi_qty_pos'),
            models.CheckConstraint(
                check=models.Q(rate__gte=0) | models.Q(rate__isnull=True),
                name='ck_poi_rate_nonneg'
            ),
            models.CheckConstraint(check=models.Q(received_qty__gte=0), name='ck_poi_received_nonneg'),
            models.CheckConstraint(
                check=models.Q(received_qty__lte=models.F('qty')),
                name='ck_poi_received_le_qty'
            ),
        ]


class PurchaseReceiptStatus(models.TextChoices):
    DRAFT = 'Draft', 'Draft'
    SUBMITTED = 'Submitted', 'Submitted'
    COMPLETED = 'Completed', 'Completed'
    CANCELLED = 'Cancelled', 'Cancelled'


class PurchaseReceipt(AuditMixin, PostingMixin):
    pr_id = models.BigAutoField(primary_key=True)
    receipt_no = models.CharField(max_length=64, unique=True)
    po = models.ForeignKey('PurchaseOrder', null=True, blank=True, on_delete=models.SET_NULL,
                           db_column='po_id', related_name='receipts')
    supplier = models.ForeignKey('Supplier', on_delete=models.PROTECT,
                                 db_column='supplier_id', related_name='receipts')
    status = models.CharField(max_length=32, choices=PurchaseReceiptStatus.choices, default=PurchaseReceiptStatus.DRAFT)

    objects = BaseManager()

    class Meta:
        db_table = 'purchase_receipts'
        verbose_name = 'Purchase Receipt'
        verbose_name_plural = 'Purchase Receipts'

    def __str__(self):
        return f"{self.receipt_no} ({self.status})"


class PurchaseReceiptItem(models.Model):
    pri_id = models.BigAutoField(primary_key=True)
    pr = models.ForeignKey('PurchaseReceipt', on_delete=models.CASCADE,
                           db_column='pr_id', related_name='items')
    poi = models.ForeignKey('PurchaseOrderItem', null=True, blank=True, on_delete=models.SET_NULL,
                            db_column='poi_id', related_name='receipts')
    item = models.ForeignKey('Item', on_delete=models.PROTECT,
                             db_column='item_id', related_name='receipt_items')
    qty = models.DecimalField(max_digits=18, decimal_places=6)
    accepted_qty = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    rejected_qty = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    uom_code = models.ForeignKey('UOM', null=True, blank=True, on_delete=models.SET_NULL,
                                 db_column='uom_code', related_name='receipt_items')
    wh = models.ForeignKey('Warehouse', on_delete=models.PROTECT,
                           db_column='wh_id', related_name='receipt_items')
    loc = models.ForeignKey('Location', on_delete=models.PROTECT,
                            db_column='loc_id', related_name='receipt_items')
    batch = models.ForeignKey('Batch', null=True, blank=True, on_delete=models.SET_NULL,
                              db_column='batch_id', related_name='receipt_items')
    serial = models.ForeignKey('Serial', null=True, blank=True, on_delete=models.SET_NULL,
                               db_column='serial_id', related_name='receipt_items')

    class Meta:
        db_table = 'purchase_receipt_items'
        verbose_name = 'Purchase Receipt Item'
        verbose_name_plural = 'Purchase Receipt Items'
        constraints = [
            models.CheckConstraint(check=models.Q(qty__gt=0), name='ck_pri_qty_pos'),
            models.CheckConstraint(
                check=models.Q(accepted_qty__gte=0) | models.Q(accepted_qty__isnull=True),
                name='ck_pri_accepted_nonneg'
            ),
            models.CheckConstraint(
                check=models.Q(rejected_qty__gte=0) | models.Q(rejected_qty__isnull=True),
                name='ck_pri_rejected_nonneg'
            ),
            models.CheckConstraint(
                check=(
                        models.Q(accepted_qty__isnull=True, rejected_qty__isnull=True) |
                        models.Q(qty__gte=(models.F('accepted_qty') + models.F('rejected_qty')))
                ),
                name='ck_pri_sum_le_qty'
            ),
        ]


class MaterialRequestStatus(models.TextChoices):
    DRAFT = 'Draft', 'Draft'
    SUBMITTED = 'Submitted', 'Submitted'
    ORDERED = 'Ordered', 'Ordered'
    COMPLETED = 'Completed', 'Completed'
    CANCELLED = 'Cancelled', 'Cancelled'


class MaterialRequest(AuditMixin):
    mr_id = models.BigAutoField(primary_key=True)
    mr_no = models.CharField(max_length=64, unique=True)
    purpose = models.CharField(max_length=16)
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                     db_column='requested_by', related_name='material_requests')
    schedule_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=32, choices=MaterialRequestStatus.choices, default=MaterialRequestStatus.DRAFT)

    objects = BaseManager()

    class Meta:
        db_table = 'material_requests'
        verbose_name = 'Material Request'
        verbose_name_plural = 'Material Requests'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.mr_no} ({self.status})"


class MaterialRequestItem(models.Model):
    mri_id = models.BigAutoField(primary_key=True)
    mr = models.ForeignKey('MaterialRequest', on_delete=models.CASCADE,
                           db_column='mr_id', related_name='items')
    item = models.ForeignKey('Item', on_delete=models.PROTECT,
                             db_column='item_id', related_name='mr_items')
    qty = models.DecimalField(max_digits=18, decimal_places=6)
    ordered_qty = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    uom_code = models.ForeignKey('UOM', null=True, blank=True, on_delete=models.SET_NULL,
                                 db_column='uom_code', related_name='mr_items')
    required_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'material_request_items'
        verbose_name = 'Material Request Item'
        verbose_name_plural = 'Material Request Items'
        constraints = [
            models.CheckConstraint(check=models.Q(qty__gt=0), name='ck_mri_qty_pos'),
            models.CheckConstraint(check=models.Q(ordered_qty__gte=0), name='ck_mri_ordered_nonneg'),
            models.CheckConstraint(
                check=models.Q(ordered_qty__lte=models.F('qty')),
                name='ck_mri_ordered_le_qty'
            ),
        ]


class SalesOrder(AuditMixin):
    so_id = models.BigAutoField(primary_key=True)
    so_no = models.CharField(max_length=64, unique=True)
    revision = models.IntegerField(default=0)
    customer: 'Customer' = models.ForeignKey('Customer', on_delete=models.PROTECT,
                                             db_column='customer_id', related_name='sales_orders')
    so_date = models.DateField()
    delivery_date = models.DateField(null=True, blank=True)
    company = models.ForeignKey('Company', on_delete=models.PROTECT,
                                db_column='company_id', related_name='sales_orders')
    cost_center = models.ForeignKey('CostCenter', null=True, blank=True, on_delete=models.SET_NULL,
                                    db_column='cost_center_id', related_name='sales_orders')
    currency_code = models.ForeignKey('Currency', on_delete=models.PROTECT,
                                      db_column='currency_code', related_name='sales_orders')
    conversion_rate = models.DecimalField(max_digits=18, decimal_places=6, default=1)
    net_total = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    tax_total = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    grand_total = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    status = models.CharField(max_length=16, choices=OrderStatus.choices, default=OrderStatus.DRAFT, db_index=True)

    objects = BaseManager()

    class Meta:
        db_table = 'sales_orders'
        ordering = ['-so_date', 'so_no']
        verbose_name = 'Sales Order'
        verbose_name_plural = 'Sales Orders'
        indexes = [
            models.Index(fields=['status', 'so_date'], name='ix_so_status_date'),
            models.Index(fields=['customer'], name='ix_so_customer'),
            models.Index(
                F('customer'),
                F('status'),
                OrderBy(F('so_date'), descending=True),
                name='ix_so_cust_status_date',
            ),
        ]
        constraints = [
            models.CheckConstraint(check=models.Q(conversion_rate__gt=0), name='ck_so_rate_pos'),
            models.CheckConstraint(
                check=models.Q(grand_total__gte=0) | models.Q(grand_total__isnull=True),
                name='ck_so_gt_nonneg'
            ),
        ]

    def __str__(self):
        return f"{self.so_no} - {self.customer.code} ({self.status})"


# ============================================================================
# SALES ITEMS & DELIVERY
# ============================================================================


class SalesOrderItem(models.Model):
    soi_id = models.BigAutoField(primary_key=True)
    so = models.ForeignKey('SalesOrder', on_delete=models.CASCADE,
                           db_column='so_id', related_name='items')
    item = models.ForeignKey('Item', on_delete=models.PROTECT,
                             db_column='item_id', related_name='so_items')
    qty = models.DecimalField(max_digits=18, decimal_places=6)
    delivered_qty = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    uom_code = models.ForeignKey('UOM', null=True, blank=True, on_delete=models.SET_NULL,
                                 db_column='uom_code', related_name='so_items')
    rate = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    amount = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    promised_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'sales_order_items'
        verbose_name = 'Sales Order Item'
        verbose_name_plural = 'Sales Order Items'
        constraints = [
            models.CheckConstraint(check=models.Q(qty__gt=0), name='ck_soi_qty_pos'),
            models.CheckConstraint(
                check=models.Q(rate__gte=0) | models.Q(rate__isnull=True),
                name='ck_soi_rate_nonneg'
            ),
            models.CheckConstraint(check=models.Q(delivered_qty__gte=0), name='ck_soi_delivered_nonneg'),
            models.CheckConstraint(
                check=models.Q(delivered_qty__lte=models.F('qty')),
                name='ck_soi_delivered_le_qty'
            ),
        ]


class DeliveryNoteStatus(models.TextChoices):
    DRAFT = 'Draft', 'Draft'
    SUBMITTED = 'Submitted', 'Submitted'
    DELIVERED = 'Delivered', 'Delivered'
    CANCELLED = 'Cancelled', 'Cancelled'


class DeliveryNote(AuditMixin, PostingMixin):
    dn_id = models.BigAutoField(primary_key=True)
    dn_no = models.CharField(max_length=64, unique=True)
    so = models.ForeignKey('SalesOrder', null=True, blank=True, on_delete=models.SET_NULL,
                           db_column='so_id', related_name='deliveries')
    customer = models.ForeignKey('Customer', on_delete=models.PROTECT,
                                 db_column='customer_id', related_name='deliveries')
    status = models.CharField(max_length=32, choices=DeliveryNoteStatus.choices, default=DeliveryNoteStatus.DRAFT)

    objects = BaseManager()

    class Meta:
        db_table = 'delivery_notes'
        verbose_name = 'Delivery Note'
        verbose_name_plural = 'Delivery Notes'

    def __str__(self):
        return f"{self.dn_no} ({self.status})"


class DeliveryNoteItem(models.Model):
    dni_id = models.BigAutoField(primary_key=True)
    dn = models.ForeignKey('DeliveryNote', on_delete=models.CASCADE,
                           db_column='dn_id', related_name='items')
    soi = models.ForeignKey('SalesOrderItem', null=True, blank=True, on_delete=models.SET_NULL,
                            db_column='soi_id', related_name='deliveries')
    item = models.ForeignKey('Item', on_delete=models.PROTECT,
                             db_column='item_id', related_name='delivery_items')
    qty = models.DecimalField(max_digits=18, decimal_places=6)
    uom_code = models.ForeignKey('UOM', null=True, blank=True, on_delete=models.SET_NULL,
                                 db_column='uom_code', related_name='delivery_items')
    wh = models.ForeignKey('Warehouse', on_delete=models.PROTECT,
                           db_column='wh_id', related_name='delivery_items')
    loc = models.ForeignKey('Location', on_delete=models.PROTECT,
                            db_column='loc_id', related_name='delivery_items')
    batch = models.ForeignKey('Batch', null=True, blank=True, on_delete=models.SET_NULL,
                              db_column='batch_id', related_name='delivery_items')
    serial = models.ForeignKey('Serial', null=True, blank=True, on_delete=models.SET_NULL,
                               db_column='serial_id', related_name='delivery_items')

    class Meta:
        db_table = 'delivery_note_items'
        verbose_name = 'Delivery Note Item'
        verbose_name_plural = 'Delivery Note Items'
        constraints = [
            models.CheckConstraint(check=models.Q(qty__gt=0), name='ck_dni_qty_pos')
        ]


# ============================================================================
# PRICING
# ============================================================================

class PriceList(AuditMixin):
    price_list_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=120, unique=True)
    company = models.ForeignKey('Company', on_delete=models.PROTECT,
                                db_column='company_id', related_name='price_lists')
    currency_code = models.ForeignKey('Currency', on_delete=models.PROTECT,
                                      db_column='currency_code', related_name='price_lists')
    selling = models.BooleanField(default=True)
    buying = models.BooleanField(default=False)
    enabled = models.BooleanField(default=True)

    objects = BaseManager()

    class Meta:
        db_table = 'price_lists'
        verbose_name = 'Price List'
        verbose_name_plural = 'Price Lists'
        ordering = ['name']
        constraints = [
            models.CheckConstraint(
                check=models.Q(selling=True) | models.Q(buying=True),
                name='ck_pricelist_has_role'
            ),
        ]

    def __str__(self):
        return self.name


class ItemPrice(AuditMixin):
    item_price_id = models.BigAutoField(primary_key=True)
    item = models.ForeignKey('Item', on_delete=models.CASCADE,
                             db_column='item_id', related_name='prices')
    price_list = models.ForeignKey('PriceList', on_delete=models.CASCADE,
                                   db_column='price_list_id', related_name='items')
    uom_code = models.ForeignKey('UOM', null=True, blank=True, on_delete=models.SET_NULL,
                                 db_column='uom_code', related_name='prices')
    rate = models.DecimalField(max_digits=18, decimal_places=6)
    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)

    def clean(self):
        super().clean()
        if self.valid_from and self.valid_to and self.valid_from > self.valid_to:
            raise ValidationError({'valid_to': 'valid_to must be on/after valid_from.'})

    class Meta:
        db_table = 'item_prices'
        verbose_name = 'Item Price'
        verbose_name_plural = 'Item Prices'
        constraints = [
            models.UniqueConstraint(fields=['item', 'price_list', 'uom_code'],
                                    name='uq_item_price'),
            models.UniqueConstraint(
                fields=['item', 'price_list'],
                condition=models.Q(uom_code__isnull=True),
                name='uq_item_price_null_uom'
            ),
            models.CheckConstraint(check=models.Q(rate__gte=0), name='ck_item_price_rate_nonneg')
        ]


# ============================================================================
# WORK ORDERS & JOB CARDS
# ============================================================================
class WorkOrder(AuditMixin):
    wo_id = models.BigAutoField(primary_key=True)
    wo_no = models.CharField(max_length=64, unique=True)
    revision = models.IntegerField(default=0)

    fg_item = models.ForeignKey(
        'Item', on_delete=models.PROTECT,
        db_column='fg_item_id', related_name='work_orders'
    )
    bom: 'BOM' = models.ForeignKey(
        'BOM', on_delete=models.PROTECT,
        db_column='bom_id', related_name='work_orders'
    )
    route = models.ForeignKey(
        'Route', null=True, blank=True, on_delete=models.SET_NULL,
        db_column='route_id', related_name='work_orders'
    )

    qty_to_make = models.DecimalField(
        max_digits=18, decimal_places=6,
        help_text="Target quantity to manufacture in this work order"
    )
    qty_completed = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    qty_rejected = models.DecimalField(max_digits=18, decimal_places=6, default=0)

    start_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)

    company = models.ForeignKey(
        'Company', on_delete=models.PROTECT,
        db_column='company_id', related_name='work_orders'
    )
    cost_center = models.ForeignKey(
        'CostCenter', null=True, blank=True, on_delete=models.SET_NULL,
        db_column='cost_center_id', related_name='work_orders'
    )
    status = models.CharField(
        max_length=16, choices=WorkOrderStatus.choices,
        default=WorkOrderStatus.DRAFT, db_index=True
    )

    objects = BaseManager()

    @property
    def qty_remaining(self):
        return (self.qty_to_make or 0) - (self.qty_completed or 0) - (self.qty_rejected or 0)

    def clean(self):
        super().clean()

        # --- BOM item must match WO FG item ---
        # Compare using related objects' .pk so the IDE doesn't complain about *_id
        if self.bom and self.fg_item:
            bom_item_id: int | None = cast(int | None, getattr(self.bom, 'item_id', None))
            fg_pk: int | None = cast(int | None, getattr(self.fg_item, 'pk', None))
            if bom_item_id is not None and fg_pk is not None and bom_item_id != fg_pk:
                raise ValidationError({'bom': 'BOM item must match Work Order FG item.'})

        # --- date sanity ---
        if self.start_date and self.due_date and self.due_date < self.start_date:
            raise ValidationError({'due_date': 'Due date must be on/after the start date.'})

    class Meta:
        db_table = 'work_orders'
        verbose_name = 'Work Order'
        verbose_name_plural = 'Work Orders'
        ordering = ['-created_at', 'wo_no']
        indexes = [
            models.Index(fields=['status', 'due_date'], name='ix_wo_status_due'),
            models.Index(
                F('company'), F('status'),
                OrderBy(F('created_at'), descending=True),
                name='ix_wo_company_status_date',
            ),
        ]
        constraints = [
            models.CheckConstraint(check=Q(qty_to_make__gt=0), name='ck_wo_qty_pos'),
            models.CheckConstraint(check=Q(qty_completed__gte=0), name='ck_wo_completed_nonneg'),
            models.CheckConstraint(check=Q(qty_rejected__gte=0), name='ck_wo_rejected_nonneg'),
            models.CheckConstraint(
                check=Q(
                    qty_to_make__gte=ExpressionWrapper(
                        F('qty_completed') + F('qty_rejected'),
                        output_field=DDecimalField(max_digits=18, decimal_places=6),
                    )
                ),
                name='ck_wo_outcome_le_to_make',
            ),
        ]

    def __str__(self):
        return f"{self.wo_no} ({self.status})"

    @property
    def is_overdue(self):
        return (
                self.due_date
                and self.due_date < timezone.now().date()
                and self.status not in [WorkOrderStatus.COMPLETED, WorkOrderStatus.CANCELLED]
        )


class WOOperationStatus(models.TextChoices):
    PENDING = 'Pending', 'Pending'
    SCHEDULED = 'Scheduled', 'Scheduled'
    IN_PROGRESS = 'In Progress', 'In Progress'
    ON_HOLD = 'On Hold', 'On Hold'
    COMPLETED = 'Completed', 'Completed'
    CANCELLED = 'Cancelled', 'Cancelled'


class WOOperation(models.Model):
    wo_op_id = models.BigAutoField(primary_key=True)
    wo = models.ForeignKey('WorkOrder', on_delete=models.CASCADE,
                           db_column='wo_id', related_name='operations')
    op_seq = models.IntegerField()
    operation = models.ForeignKey('Operation', null=True, blank=True, on_delete=models.SET_NULL,
                                  db_column='operation_id', related_name='wo_operations')
    op_code = models.CharField(max_length=64, blank=True)
    op_name = models.CharField(max_length=200, blank=True)
    workstation = models.ForeignKey('Workstation', on_delete=models.PROTECT,
                                    db_column='workstation_id', related_name='wo_operations')
    planned_start = models.DateTimeField(null=True, blank=True)
    planned_end = models.DateTimeField(null=True, blank=True)
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=32, choices=WOOperationStatus.choices, default=WOOperationStatus.PENDING, )
    qty_completed = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    qty_rejected = models.DecimalField(max_digits=18, decimal_places=6, default=0)

    objects = BaseManager()

    class Meta:
        db_table = 'wo_operations'
        verbose_name = 'Work Order Operation'
        verbose_name_plural = 'Work Order Operations'
        indexes = [
            models.Index(fields=['status'], name='ix_wo_op_status')
        ]
        constraints = [
            models.UniqueConstraint(fields=['wo', 'op_seq'], name='uq_wo_op_wo_seq'),
            models.CheckConstraint(check=models.Q(op_seq__gte=1), name='ck_woop_seq_ge_1'),
            models.CheckConstraint(check=models.Q(qty_completed__gte=0), name='ck_wo_op_completed_nonneg'),
            models.CheckConstraint(check=models.Q(qty_rejected__gte=0), name='ck_wo_op_rejected_nonneg'),
            models.CheckConstraint(
                check=(
                        models.Q(planned_end__isnull=True) |
                        (models.Q(planned_start__isnull=False) & models.Q(planned_end__gte=models.F('planned_start')))
                ),
                name='ck_woop_planned_end_ge_start'
            ),
            models.CheckConstraint(
                check=(
                        models.Q(actual_end__isnull=True) |
                        (models.Q(actual_start__isnull=False) & models.Q(actual_end__gte=models.F('actual_start')))
                ),
                name='ck_woop_actual_end_ge_start'
            ),
        ]


class WOMaterial(models.Model):
    wo_mat_id = models.BigAutoField(primary_key=True)
    wo = models.ForeignKey('WorkOrder', on_delete=models.CASCADE,
                           db_column='wo_id', related_name='materials')
    component_item = models.ForeignKey('Item', on_delete=models.PROTECT,
                                       db_column='component_item_id', related_name='wo_materials')
    required_qty = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    issued_qty = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    consumed_qty = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    returned_qty = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    uom_code = models.ForeignKey('UOM', null=True, blank=True, on_delete=models.SET_NULL,
                                 db_column='uom_code', related_name='wo_materials')
    used_substitute_item = models.ForeignKey('Item', null=True, blank=True, on_delete=models.SET_NULL,
                                             db_column='used_substitute_item_id', related_name='wo_substitutes')

    class Meta:
        db_table = 'wo_materials'
        verbose_name = 'Work Order Material'
        verbose_name_plural = 'Work Order Materials'
        constraints = [
            models.UniqueConstraint(fields=['wo', 'component_item'], name='uq_womat_wo_component'),
            models.CheckConstraint(check=models.Q(required_qty__gte=0), name='ck_womat_required_nonneg'),
            models.CheckConstraint(check=models.Q(issued_qty__gte=0), name='ck_womat_issued_nonneg'),
            models.CheckConstraint(check=models.Q(consumed_qty__gte=0), name='ck_womat_consumed_nonneg'),
            models.CheckConstraint(check=models.Q(returned_qty__gte=0), name='ck_womat_returned_nonneg'),
            models.CheckConstraint(
                check=models.Q(issued_qty__gte=models.F('consumed_qty')),
                name='ck_womat_issued_ge_consumed'
            ),
            models.CheckConstraint(
                check=models.Q(issued_qty__gte=models.F('returned_qty')),
                name='ck_womat_issued_ge_returned'
            ),
            models.CheckConstraint(
                check=models.Q(issued_qty__gte=models.F('consumed_qty') + models.F('returned_qty')),
                name='ck_womat_consumed_plus_returned_le_issued'
            ),
        ]


class JobCard(AuditMixin):
    job_card_id = models.BigAutoField(primary_key=True)
    job_card_no = models.CharField(max_length=64, unique=True)
    wo_op = models.ForeignKey('WOOperation', on_delete=models.CASCADE,
                              db_column='wo_op_id', related_name='job_cards')
    workstation = models.ForeignKey('Workstation', null=True, blank=True, on_delete=models.SET_NULL,
                                    db_column='workstation_id', related_name='job_cards')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                    db_column='assigned_to', related_name='job_cards')
    qty_to_process = models.DecimalField(max_digits=18, decimal_places=6)
    qty_good = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    qty_reject = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    scheduled_start = models.DateTimeField(null=True, blank=True)
    scheduled_end = models.DateTimeField(null=True, blank=True)
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=JobCardStatus.choices, default=JobCardStatus.DRAFT, db_index=True)
    priority = models.IntegerField(default=3)
    company = models.ForeignKey('Company', null=True, blank=True, on_delete=models.SET_NULL,
                                db_column='company_id', related_name='job_cards')

    objects = BaseManager()

    class Meta:
        db_table = 'job_cards'
        ordering = ['-created_at', 'job_card_no']
        verbose_name = 'Job Card'
        verbose_name_plural = 'Job Cards'
        indexes = [
            models.Index(fields=['status'], name='ix_job_card_status'),
            models.Index(fields=['assigned_to'], name='ix_job_card_assigned'),
            models.Index(fields=['status', 'assigned_to'], name='ix_job_card_status_assigned'),
        ]
        constraints = [
            models.CheckConstraint(check=models.Q(qty_to_process__gt=0), name='ck_jc_qty_pos'),
            models.CheckConstraint(check=models.Q(qty_good__gte=0), name='ck_jc_good_nonneg'),
            models.CheckConstraint(check=models.Q(qty_reject__gte=0), name='ck_jc_reject_nonneg'),
            models.CheckConstraint(
                check=models.Q(qty_to_process__gte=models.F('qty_good') + models.F('qty_reject')),
                name='ck_jc_outcome_le_to_process'
            ),
            models.CheckConstraint(
                check=(
                        models.Q(scheduled_end__isnull=True) |
                        (models.Q(scheduled_start__isnull=False) & models.Q(
                            scheduled_end__gte=models.F('scheduled_start')))
                ),
                name='ck_jc_scheduled_end_ge_start'
            ),
            models.CheckConstraint(
                check=(
                        models.Q(actual_end__isnull=True) |
                        (models.Q(actual_start__isnull=False) & models.Q(actual_end__gte=models.F('actual_start')))
                ),
                name='ck_jc_actual_end_ge_start'
            ),
        ]

    def __str__(self):
        return f"{self.job_card_no} ({self.status})"


class JobCardTime(models.Model):
    jct_id = models.BigAutoField(primary_key=True)
    job_card = models.ForeignKey('JobCard', on_delete=models.CASCADE,
                                 db_column='job_card_id', related_name='times')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                             db_column='user_id', related_name='job_card_times')
    start_ts = models.DateTimeField()
    end_ts = models.DateTimeField(null=True, blank=True)
    minutes = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'job_card_times'
        verbose_name = 'Job Card Time'
        verbose_name_plural = 'Job Card Times'
        constraints = [
            models.CheckConstraint(
                check=models.Q(end_ts__isnull=True) | models.Q(end_ts__gte=models.F('start_ts')),
                name='ck_jct_end_ge_start'
            ),
            models.CheckConstraint(
                check=models.Q(minutes__isnull=True) | models.Q(minutes__gte=0),
                name='ck_jct_minutes_nonneg'
            ),
        ]


class JobCardMaterial(models.Model):
    jcm_id = models.BigAutoField(primary_key=True)
    job_card = models.ForeignKey('JobCard', on_delete=models.CASCADE,
                                 db_column='job_card_id', related_name='materials')
    item = models.ForeignKey('Item', on_delete=models.PROTECT,
                             db_column='item_id', related_name='job_card_materials')
    qty = models.DecimalField(max_digits=18, decimal_places=6)
    uom_code = models.ForeignKey('UOM', null=True, blank=True, on_delete=models.SET_NULL,
                                 db_column='uom_code', related_name='job_card_materials')

    class Meta:
        db_table = 'job_card_materials'
        verbose_name = 'Job Card Material'
        verbose_name_plural = 'Job Card Materials'
        constraints = [
            models.CheckConstraint(check=models.Q(qty__gt=0), name='ck_jcm_qty_pos')
        ]


class TimeLog(models.Model):
    time_log_id = models.BigAutoField(primary_key=True)
    wo_op = models.ForeignKey('WOOperation', on_delete=models.CASCADE,
                              db_column='wo_op_id', related_name='time_logs')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                             db_column='user_id', related_name='time_logs')
    start_ts = models.DateTimeField()
    end_ts = models.DateTimeField(null=True, blank=True)
    minutes = models.IntegerField(null=True, blank=True)
    activity = models.CharField(max_length=32, blank=True)
    remark = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'time_logs'
        verbose_name = 'Time Log'
        verbose_name_plural = 'Time Logs'
        ordering = ['-start_ts']
        indexes = [
            models.Index(fields=['user'], name='ix_time_log_user'),
            models.Index(fields=['wo_op'], name='ix_time_log_wo_op')
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(end_ts__isnull=True) | models.Q(end_ts__gte=models.F('start_ts')),
                name='ck_timelog_end_ge_start'
            ),
            models.CheckConstraint(
                check=models.Q(minutes__isnull=True) | models.Q(minutes__gte=0),
                name='ck_timelog_minutes_nonneg'
            ),
        ]

    def __str__(self):
        return f"Time Log {self.time_log_id} - {self.user}"


# Quality Control
class QCPlan(AuditMixin):
    qc_plan_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=120, unique=True)
    doc_type_target = models.CharField(max_length=32, choices=DocType.choices)
    item_group = models.ForeignKey('ItemGroup', null=True, blank=True, on_delete=models.SET_NULL,
                                   db_column='item_group_id', related_name='qc_plans')
    is_active = models.BooleanField(default=True)

    objects = BaseManager()

    class Meta:
        db_table = 'qc_plans'
        ordering = ['name']
        verbose_name = 'QC Plan'
        verbose_name_plural = 'QC Plans'

    def __str__(self):
        return self.name


class QCCheck(models.Model):
    qc_check_id = models.BigAutoField(primary_key=True)
    qc_plan = models.ForeignKey('QCPlan', on_delete=models.CASCADE,
                                db_column='qc_plan_id', related_name='checks')
    check_name = models.CharField(max_length=200)
    check_type = models.CharField(max_length=32)
    method = models.CharField(max_length=120, blank=True)
    tol_min = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    tol_max = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    target_value = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    uom_code = models.ForeignKey('UOM', null=True, blank=True, on_delete=models.SET_NULL,
                                 db_column='uom_code', related_name='qc_checks')
    sample_size = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'qc_checks'
        verbose_name = 'QC Check'
        verbose_name_plural = 'QC Checks'
        ordering = ['qc_plan', 'check_name']
        constraints = [
            models.CheckConstraint(
                check=models.Q(tol_min__lte=models.F('tol_max')) | models.Q(tol_min__isnull=True) | models.Q(
                    tol_max__isnull=True),
                name='ck_qc_tol_min_le_max'
            ),
            models.CheckConstraint(
                check=models.Q(sample_size__isnull=True) | models.Q(sample_size__gt=0),
                name='ck_qc_sample_size_pos'
            ),
        ]

    def __str__(self):
        return f"{self.qc_plan.name} - {self.check_name}"


class QCInspectionStatus(models.TextChoices):
    DRAFT = 'Draft', 'Draft'
    IN_PROGRESS = 'In Progress', 'In Progress'
    COMPLETED = 'Completed', 'Completed'
    APPROVED = 'Approved', 'Approved'
    REJECTED = 'Rejected', 'Rejected'


class QCInspection(AuditMixin):
    qci_id = models.BigAutoField(primary_key=True)
    inspection_no = models.CharField(max_length=64, unique=True)
    doc_type = models.CharField(max_length=32)
    doc_id = models.BigIntegerField()
    qc_plan = models.ForeignKey('QCPlan', null=True, blank=True, on_delete=models.SET_NULL,
                                db_column='qc_plan_id', related_name='inspections')
    inspector = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                  db_column='inspector_id', related_name='qc_inspections')
    inspection_date = models.DateField()
    sample_size = models.IntegerField(null=True, blank=True)
    passed_qty = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    rejected_qty = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    status = models.CharField(max_length=32, choices=QCInspectionStatus.choices, db_index=True,
                              default=QCInspectionStatus.DRAFT)

    def clean(self):
        super().clean()
        # Require all three to be present
        if self.sample_size is None or self.passed_qty is None or self.rejected_qty is None:
            return
        # Be explicit about types for the IDE/type checker
        passed: Decimal = cast(Decimal, self.passed_qty)
        rejected: Decimal = cast(Decimal, self.rejected_qty)
        sample_size_value: int = int(cast(Any, self.sample_size))
        sample: Decimal = Decimal(sample_size_value)
        if (passed + rejected) != sample:
            raise ValidationError('passed_qty + rejected_qty must equal sample_size.')

    objects = BaseManager()

    class Meta:
        db_table = 'qc_inspections'  # ← FIX THIS (was 'job_cards')
        ordering = ['-inspection_date', 'inspection_no']  # ← FIX THIS
        verbose_name = 'QC Inspection'
        verbose_name_plural = 'QC Inspections'
        indexes = [
            models.Index(fields=['status'], name='ix_qci_status'),
            models.Index(fields=['inspector'], name='ix_qci_inspector'),
            models.Index(fields=['doc_type', 'doc_id'], name='ix_qci_doc'),
        ]
        constraints = [
            models.CheckConstraint(
                check=Q(sample_size__isnull=True) | Q(sample_size__gt=0),
                name='ck_qci_sample_size_pos'
            ),
            models.CheckConstraint(
                check=Q(passed_qty__isnull=True) | Q(passed_qty__gte=0),
                name='ck_qci_passed_nonneg'
            ),
            models.CheckConstraint(
                check=Q(rejected_qty__isnull=True) | Q(rejected_qty__gte=0),
                name='ck_qci_rejected_nonneg'
            ),
            # ← ADD THIS NEW CONSTRAINT:
            models.CheckConstraint(
                check=(
                    # If any field is NULL, don't enforce the check
                    Q(sample_size__isnull=True) |
                    Q(passed_qty__isnull=True) |
                    Q(rejected_qty__isnull=True) |
                    # Otherwise, enforce passed + rejected = sample_size
                    Q(sample_size=ExpressionWrapper(
                        F('passed_qty') + F('rejected_qty'),
                        output_field=DDecimalField(max_digits=18, decimal_places=6)
                    ))
                ),
                name='ck_qci_passed_plus_rejected_eq_sample'
            ),
        ]

    def __str__(self):
        return f"{self.inspection_no} ({self.status})"


class QCResult(models.Model):
    qcr_id = models.BigAutoField(primary_key=True)
    qci = models.ForeignKey('QCInspection', on_delete=models.CASCADE,
                            db_column='qci_id', related_name='results')
    qc_check: 'QCCheck' = models.ForeignKey('QCCheck', on_delete=models.PROTECT,
                                            db_column='qc_check_id', related_name='results')
    sample_no = models.IntegerField(null=True, blank=True)
    measured_value = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    text_result = models.CharField(max_length=255, blank=True)
    passed = models.BooleanField(default=False)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'qc_results'
        verbose_name = 'QC Result'
        verbose_name_plural = 'QC Results'
        ordering = ['qci', 'qc_check', 'sample_no']

    def __str__(self):
        return f"Result for {self.qc_check.check_name} - Sample {self.sample_no}"


class Inspection(AuditMixin, DocumentReferenceMixin):
    inspection_id = models.BigAutoField(primary_key=True)
    stage = models.CharField(max_length=32, db_index=True)
    map = models.ForeignKey('BitMap', on_delete=models.PROTECT,
                            db_column='map_id', related_name='inspections')
    inspector = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                  db_column='inspector_id', related_name='inspections')
    status = models.CharField(max_length=32, db_index=True)
    total_nodes = models.IntegerField(null=True, blank=True)
    nodes_ok = models.IntegerField(null=True, blank=True)
    nodes_issue = models.IntegerField(null=True, blank=True)

    objects = BaseManager()

    class Meta:
        db_table = 'inspections'
        verbose_name = 'Inspection'
        verbose_name_plural = 'Inspections'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['stage', 'status'], name='ix_inspection_stage_status'),
            models.Index(fields=['map'], name='ix_inspection_map'),
        ]

    def __str__(self):
        return f"Inspection {self.inspection_id} - {self.stage} ({self.status})"


class InspectionObservation(AuditMixin):
    obs_id = models.BigAutoField(primary_key=True)
    inspection = models.ForeignKey('Inspection', on_delete=models.CASCADE,
                                   db_column='inspection_id', related_name='observations')
    node_id = models.IntegerField(db_column='node_id')
    element_type = models.CharField(max_length=32, blank=True)
    pocket_condition = models.CharField(max_length=16, blank=True)
    cutter_condition = models.CharField(max_length=32, blank=True)
    fin_condition = models.CharField(max_length=16, blank=True)
    severity = models.CharField(max_length=16, default='NONE')
    decision = models.CharField(max_length=32, blank=True)
    decision_params = models.JSONField(null=True, blank=True)
    measures_json = models.JSONField(null=True, blank=True)
    notes = models.TextField(blank=True)
    grid_code = models.CharField(max_length=32, db_index=True, blank=True)
    blade_no = models.IntegerField(null=True, blank=True)
    row_no = models.IntegerField(null=True, blank=True)
    col_no = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'inspection_observations'
        verbose_name = 'Inspection Observation'
        verbose_name_plural = 'Inspection Observations'
        ordering = ['inspection_id', 'node_id']
        indexes = [
            models.Index(fields=['element_type', 'grid_code'], name='ix_obs_element_grid')
        ]

    def __str__(self):
        return f"Observation {self.obs_id} - Node {self.node_id}"


# Accounting
class Account(AuditMixin):
    account_id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=200)
    account_type = models.CharField(max_length=16)
    parent = models.ForeignKey('Account', null=True, blank=True, on_delete=models.SET_NULL,
                               db_column='parent_id', related_name='children')
    is_active = models.BooleanField(default=True)

    objects = BaseManager()

    class Meta:
        db_table = 'accounts'
        verbose_name = 'Account'
        verbose_name_plural = 'Accounts'
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"


class JournalStatus(models.TextChoices):
    DRAFT = 'Draft', 'Draft'
    SUBMITTED = 'Submitted', 'Submitted'
    POSTED = 'Posted', 'Posted'
    CANCELLED = 'Cancelled', 'Cancelled'


class Journal(AuditMixin):
    jv_id = models.BigAutoField(primary_key=True)
    jv_no = models.CharField(max_length=64, unique=True)
    posting_date = models.DateField()
    memo = models.CharField(max_length=255, blank=True)
    company = models.ForeignKey('Company', on_delete=models.PROTECT,
                                db_column='company_id', related_name='journals')
    total_debit = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    total_credit = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    status = models.CharField(max_length=32, choices=JournalStatus.choices, default=JournalStatus.DRAFT)

    objects = BaseManager()

    class Meta:
        db_table = 'journals'
        ordering = ['-posting_date', 'jv_no']
        verbose_name = 'Journal Entry'
        verbose_name_plural = 'Journal Entries'

    def __str__(self):
        return f"{self.jv_no} - {self.posting_date}"

    def clean(self):
        super().clean()
        # If totals are provided on header, validate equality
        if self.total_debit is not None and self.total_credit is not None:
            if self.total_debit != self.total_credit:
                raise ValidationError('Total debit must equal total credit.')


class JournalLine(DocumentReferenceMixin):
    jv_line_id = models.BigAutoField(primary_key=True)
    jv: 'Journal' = models.ForeignKey('Journal', on_delete=models.CASCADE,
                                      db_column='jv_id', related_name='lines')
    account: 'Account' = models.ForeignKey('Account', on_delete=models.PROTECT,
                                           db_column='account_id', related_name='journal_lines')
    cost_center = models.ForeignKey('CostCenter', null=True, blank=True, on_delete=models.SET_NULL,
                                    db_column='cost_center_id', related_name='journal_lines')
    debit = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    credit = models.DecimalField(max_digits=18, decimal_places=6, default=0)

    class Meta:
        db_table = 'journal_lines'
        verbose_name = 'Journal Line'
        verbose_name_plural = 'Journal Lines'
        ordering = ['jv', 'jv_line_id']
        constraints = [
            models.CheckConstraint(
                check=models.Q(debit__gte=0) & models.Q(credit__gte=0),
                name='ck_jl_nonneg'
            ),
            models.CheckConstraint(
                check=models.Q(debit=0) | models.Q(credit=0),
                name='ck_jl_one_side_zero'
            ),
            models.CheckConstraint(
                check=models.Q(debit__gt=0) | models.Q(credit__gt=0),
                name='ck_jl_nonzero'
            ),
        ]

    def __str__(self):
        return f"{self.jv.jv_no} - {self.account.code}"


# Invoicing
class SalesInvoice(AuditMixin):
    si_id = models.BigAutoField(primary_key=True)
    si_no = models.CharField(max_length=64, unique=True)
    so = models.ForeignKey('SalesOrder', null=True, blank=True, on_delete=models.SET_NULL,
                           db_column='so_id', related_name='invoices')
    customer = models.ForeignKey('Customer', on_delete=models.PROTECT,
                                 db_column='customer_id', related_name='invoices')
    posting_date = models.DateField()
    due_date = models.DateField(null=True, blank=True)
    currency_code = models.ForeignKey('Currency', on_delete=models.PROTECT,
                                      db_column='currency_code', related_name='sales_invoices')
    conversion_rate = models.DecimalField(max_digits=18, decimal_places=6, default=1)
    total = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    tax = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    grand_total = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    grand_total_base = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    outstanding_amount = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    status = models.CharField(max_length=32, choices=InvoiceStatus.choices, default=InvoiceStatus.DRAFT)

    objects = BaseManager()

    class Meta:
        db_table = 'sales_invoices'
        ordering = ['-posting_date', 'si_no']
        verbose_name = 'Sales Invoice'
        verbose_name_plural = 'Sales Invoices'
        indexes = [
            models.Index(fields=['customer', 'posting_date'], name='ix_si_customer_date'),
            models.Index(fields=['status'], name='ix_si_status'),
        ]
        constraints = [
            models.CheckConstraint(check=models.Q(conversion_rate__gt=0), name='ck_si_rate_pos'),
            models.CheckConstraint(
                check=models.Q(grand_total__gte=0) | models.Q(grand_total__isnull=True),
                name='ck_si_gt_nonneg'
            ),
        ]

    def __str__(self):
        return f"{self.si_no} - {self.customer.name} ({self.status})"


class SalesInvoiceItem(models.Model):
    sii_id = models.BigAutoField(primary_key=True)
    si: 'SalesInvoice' = models.ForeignKey('SalesInvoice', on_delete=models.CASCADE,
                                           db_column='si_id', related_name='items')
    item: 'Item' = models.ForeignKey('Item', on_delete=models.PROTECT,
                                     db_column='item_id', related_name='invoice_items')
    qty = models.DecimalField(max_digits=18, decimal_places=6)
    uom_code = models.ForeignKey('UOM', null=True, blank=True, on_delete=models.SET_NULL,
                                 db_column='uom_code', related_name='invoice_items')
    rate = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    amount = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)

    class Meta:
        db_table = 'sales_invoice_items'
        verbose_name = 'Sales Invoice Item'
        verbose_name_plural = 'Sales Invoice Items'
        ordering = ['si', 'sii_id']
        constraints = [
            models.CheckConstraint(check=models.Q(qty__gt=0), name='ck_sii_qty_pos'),
            models.CheckConstraint(
                check=models.Q(rate__gte=0) | models.Q(rate__isnull=True),
                name='ck_sii_rate_nonneg'
            ),
        ]

    def __str__(self):
        return f"{self.si.si_no} - {self.item.item_code}"


class PurchaseInvoice(AuditMixin):
    pi_id = models.BigAutoField(primary_key=True)
    pi_no = models.CharField(max_length=64, unique=True)
    pr = models.ForeignKey('PurchaseReceipt', null=True, blank=True, on_delete=models.SET_NULL,
                           db_column='pr_id', related_name='invoices')
    supplier = models.ForeignKey('Supplier', on_delete=models.PROTECT,
                                 db_column='supplier_id', related_name='invoices')
    posting_date = models.DateField()
    due_date = models.DateField(null=True, blank=True)
    currency_code = models.ForeignKey('Currency', on_delete=models.PROTECT,
                                      db_column='currency_code', related_name='purchase_invoices')
    conversion_rate = models.DecimalField(max_digits=18, decimal_places=6, default=1)
    total = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    tax = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    grand_total = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    grand_total_base = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    outstanding_amount = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    status = models.CharField(max_length=32, choices=InvoiceStatus.choices, default=InvoiceStatus.DRAFT)

    objects = BaseManager()

    class Meta:
        db_table = 'purchase_invoices'
        ordering = ['-posting_date', 'pi_no']
        verbose_name = 'Purchase Invoice'
        verbose_name_plural = 'Purchase Invoices'
        indexes = [
            models.Index(fields=['supplier', 'posting_date'], name='ix_pi_supplier_date'),
            models.Index(fields=['status'], name='ix_pi_status'),
        ]
        constraints = [
            models.CheckConstraint(check=models.Q(conversion_rate__gt=0), name='ck_pi_rate_pos'),
            models.CheckConstraint(
                check=models.Q(grand_total__gte=0) | models.Q(grand_total__isnull=True),
                name='ck_pi_gt_nonneg'
            ),
        ]

    def __str__(self):
        return f"{self.pi_no} - {self.supplier.name} ({self.status})"


class Payment(AuditMixin, PartyReferenceMixin, DocumentReferenceMixin):
    pay_id = models.BigAutoField(primary_key=True)
    payment_no = models.CharField(max_length=64, unique=True)
    payment_date = models.DateField()
    method = models.CharField(max_length=32, blank=True)
    reference = models.CharField(max_length=100, blank=True)
    currency_code = models.ForeignKey('Currency', on_delete=models.PROTECT,
                                      db_column='currency_code', related_name='payments')
    conversion_rate = models.DecimalField(max_digits=18, decimal_places=6, default=1)
    amount = models.DecimalField(max_digits=18, decimal_places=6)
    amount_base = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    status = models.CharField(max_length=32, choices=PaymentStatus.choices, default=PaymentStatus.DRAFT)

    objects = BaseManager()

    class Meta:
        db_table = 'payments'
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        ordering = ['-payment_date', 'payment_no']
        indexes = [

            models.Index(fields=['payment_date'], name='ix_payment_date'),
            models.Index(fields=['status'], name='ix_payment_status'),
        ]
        constraints = [
            models.CheckConstraint(check=models.Q(amount__gt=0), name='ck_pay_amount_pos'),
            models.CheckConstraint(check=models.Q(conversion_rate__gt=0), name='ck_pay_rate_pos'),
        ]

    def __str__(self):
        return f"{self.payment_no} - {self.amount} ({self.status})"





class VehicleStatus(models.TextChoices):
    AVAILABLE = 'Available', 'Available'
    IN_USE = 'In Use', 'In Use'
    MAINTENANCE = 'Maintenance', 'Maintenance'
    OUT_OF_SERVICE = 'Out of Service', 'Out of Service'


class Vehicle(AuditMixin):
    vehicle_id = models.BigAutoField(primary_key=True)
    plate_no = models.CharField(max_length=32, unique=True)
    vehicle_type = models.CharField(max_length=64, blank=True)
    make_model = models.CharField(max_length=100, blank=True)
    year = models.IntegerField(null=True, blank=True)
    color = models.CharField(max_length=32, blank=True)
    capacity_kg = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    capacity_volume = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    capacity_passengers = models.PositiveSmallIntegerField(null=True, blank=True)
    status = models.CharField(max_length=32, choices=VehicleStatus.choices, default=VehicleStatus.AVAILABLE)

    objects = BaseManager()

    class Meta:
        db_table = 'vehicles'
        verbose_name = 'Vehicle'
        verbose_name_plural = 'Vehicles'
        ordering = ['plate_no']
        constraints = [
            models.CheckConstraint(
                check=models.Q(year__isnull=True) | models.Q(year__gte=1886),
                name='ck_vehicle_year_valid'
            ),
            models.CheckConstraint(
                check=models.Q(capacity_kg__isnull=True) | models.Q(capacity_kg__gt=0),
                name='ck_vehicle_capacitykg_pos'
            ),
            models.CheckConstraint(
                check=models.Q(capacity_volume__isnull=True) | models.Q(capacity_volume__gt=0),
                name='ck_vehicle_capacityvol_pos'
            ),
            # NEW: passengers must be > 0 when provided
            models.CheckConstraint(
                check=models.Q(capacity_passengers__isnull=True) | models.Q(capacity_passengers__gt=0),
                name='ck_vehicle_capacitypass_pos'
            ),
        ]

    def __str__(self):
        return f"{self.plate_no} - {self.make_model}"


class PickListStatus(models.TextChoices):
    DRAFT = 'Draft', 'Draft'
    OPEN = 'Open', 'Open'
    IN_PROGRESS = 'In Progress', 'In Progress'
    COMPLETED = 'Completed', 'Completed'


class PickList(AuditMixin):
    pick_id = models.BigAutoField(primary_key=True)
    pick_no = models.CharField(max_length=64, unique=True)
    source_wh = models.ForeignKey('Warehouse', on_delete=models.PROTECT,
                                  db_column='source_wh_id', related_name='pick_lists')
    order_type = models.CharField(max_length=32)
    order_id = models.BigIntegerField(null=True, blank=True)
    picker = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                               db_column='picker_id', related_name='pick_lists')
    status = models.CharField(max_length=32, choices=PickListStatus.choices, default=PickListStatus.DRAFT)

    objects = BaseManager()

    class Meta:
        db_table = 'pick_lists'
        ordering = ['-created_at', 'pick_no']
        verbose_name = 'Pick List'
        verbose_name_plural = 'Pick Lists'

    def __str__(self):
        return f"{self.pick_no} ({self.status})"


class PickListItem(models.Model):
    pick_item_id = models.BigAutoField(primary_key=True)
    pick: 'PickList' = models.ForeignKey('PickList', on_delete=models.CASCADE,
                                         db_column='pick_id', related_name='items')
    item: 'Item' = models.ForeignKey('Item', on_delete=models.PROTECT,
                                     db_column='item_id', related_name='pick_items')
    qty_requested = models.DecimalField(max_digits=18, decimal_places=6)
    qty_picked = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    uom_code = models.ForeignKey('UOM', null=True, blank=True, on_delete=models.SET_NULL,
                                 db_column='uom_code', related_name='pick_items')
    loc = models.ForeignKey('Location', on_delete=models.PROTECT,
                            db_column='loc_id', related_name='pick_items')
    batch = models.ForeignKey('Batch', null=True, blank=True, on_delete=models.SET_NULL,
                              db_column='batch_id', related_name='pick_items')
    serial = models.ForeignKey('Serial', null=True, blank=True, on_delete=models.SET_NULL,
                               db_column='serial_id', related_name='pick_items')

    class Meta:
        db_table = 'pick_list_items'
        verbose_name = 'Pick List Item'
        verbose_name_plural = 'Pick List Items'
        ordering = ['pick', 'pick_item_id']
        constraints = [
            models.CheckConstraint(check=models.Q(qty_requested__gt=0), name='ck_pick_qtyreq_pos'),
            models.CheckConstraint(check=models.Q(qty_picked__gte=0), name='ck_pick_qtypicked_nonneg'),
            models.CheckConstraint(
                check=models.Q(qty_picked__lte=models.F('qty_requested')),
                name='ck_pick_picked_le_requested'
            ),
            models.UniqueConstraint(
                fields=['pick', 'item', 'loc', 'batch', 'serial'],
                name='uq_pick_item_unique_combo'
            ),

        ]

    def __str__(self):
        return f"{self.pick.pick_no} - {self.item.item_code}"


class Shipment(AuditMixin):
    ship_id = models.BigAutoField(primary_key=True)
    shipment_no = models.CharField(max_length=64, unique=True)
    doc_type = models.CharField(max_length=32, choices=DocType.choices)
    doc_id = models.BigIntegerField(null=True, blank=True)
    carrier = models.ForeignKey('Carrier', null=True, blank=True, on_delete=models.SET_NULL,
                                db_column='carrier_id', related_name='shipments')
    tracking_no = models.CharField(max_length=120, blank=True)
    ship_date = models.DateField(null=True, blank=True)
    est_delivery_date = models.DateField(null=True, blank=True)
    actual_delivery_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=32, choices=ShipmentStatus.choices, default=ShipmentStatus.DRAFT)
    ship_from_addr = models.ForeignKey('Address', null=True, blank=True, on_delete=models.SET_NULL,
                                       db_column='ship_from_addr_id', related_name='shipments_from')
    ship_to_addr = models.ForeignKey('Address', null=True, blank=True, on_delete=models.SET_NULL,
                                     db_column='ship_to_addr_id', related_name='shipments_to')

    objects = BaseManager()

    class Meta:
        db_table = 'shipments'
        verbose_name = 'Shipment'
        verbose_name_plural = 'Shipments'
        ordering = ['-ship_date', 'shipment_no']
        indexes = [
            models.Index(fields=['tracking_no'], name='ix_shipment_tracking'),
            models.Index(fields=['status'], name='ix_shipment_status'),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(est_delivery_date__isnull=True) | (
                            models.Q(ship_date__isnull=False) & models.Q(est_delivery_date__gte=models.F('ship_date'))),
                name='ck_ship_est_ge_shipdate'
            ),
            models.CheckConstraint(
                check=models.Q(actual_delivery_date__isnull=True) | (models.Q(ship_date__isnull=False) & models.Q(
                    actual_delivery_date__gte=models.F('ship_date'))),
                name='ck_ship_actual_ge_shipdate'
            ),
        ]

    def __str__(self):
        return f"{self.shipment_no} ({self.status})"


class ShipmentItem(DocumentReferenceMixin):
    ship_item_id = models.BigAutoField(primary_key=True)
    ship: 'Shipment' = models.ForeignKey('Shipment', on_delete=models.CASCADE,
                                         db_column='ship_id', related_name='items')
    item: 'Item' = models.ForeignKey('Item', on_delete=models.PROTECT,
                                     db_column='item_id', related_name='shipment_items')
    qty = models.DecimalField(max_digits=18, decimal_places=6)
    uom_code = models.ForeignKey('UOM', null=True, blank=True, on_delete=models.SET_NULL,
                                 db_column='uom_code', related_name='shipment_items')
    batch = models.ForeignKey('Batch', null=True, blank=True, on_delete=models.SET_NULL,
                              db_column='batch_id', related_name='shipment_items')
    serial = models.ForeignKey('Serial', null=True, blank=True, on_delete=models.SET_NULL,
                               db_column='serial_id', related_name='shipment_items')

    class Meta:
        db_table = 'shipment_items'
        verbose_name = 'Shipment Item'
        verbose_name_plural = 'Shipment Items'
        ordering = ['ship', 'ship_item_id']
        constraints = [
            models.CheckConstraint(check=models.Q(qty__gt=0), name='ck_shipitem_qty_pos')
        ]

    def __str__(self):
        return f"{self.ship.shipment_no} - {self.item.item_code}"

    def clean(self):
        super().clean()
        if self.ship:
            parent = self.ship  # this is a Shipment object
            if self.ref_doctype and self.ref_doctype != parent.doc_type:
                raise ValidationError({'ref_doctype': 'ref_doctype must match parent Shipment.doc_type'})
            if self.ref_id and parent.doc_id and self.ref_id != parent.doc_id:
                raise ValidationError({'ref_id': 'ref_id must match parent Shipment.doc_id'})


# Maintenance & Assets
class Asset(AuditMixin):
    asset_id = models.BigAutoField(primary_key=True)
    asset_code = models.CharField(max_length=64, unique=True)
    asset_name = models.CharField(max_length=200)
    asset_category = models.CharField(max_length=64, blank=True)
    workstation = models.ForeignKey('Workstation', null=True, blank=True, on_delete=models.SET_NULL,
                                    db_column='workstation_id', related_name='assets')
    location_text = models.CharField(max_length=255, blank=True)
    purchase_date = models.DateField(null=True, blank=True)
    warranty_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=32, choices=AssetStatus.choices, default=AssetStatus.ACTIVE)

    objects = BaseManager()

    class Meta:
        db_table = 'assets'
        verbose_name = 'Asset'
        verbose_name_plural = 'Assets'
        ordering = ['asset_code']

    def __str__(self):
        return f"{self.asset_code} - {self.asset_name}"


class PMSchedule(AuditMixin):
    pm_id = models.BigAutoField(primary_key=True)
    asset: 'Asset' = models.ForeignKey('Asset', on_delete=models.CASCADE,
                                       db_column='asset_id', related_name='pm_schedules')
    schedule_name = models.CharField(max_length=120)
    schedule_type = models.CharField(max_length=16)
    interval_days = models.IntegerField(null=True, blank=True)
    interval_hours = models.IntegerField(null=True, blank=True)
    last_done_date = models.DateField(null=True, blank=True)
    next_due_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    objects = BaseManager()

    class Meta:
        db_table = 'pm_schedules'
        ordering = ['asset', 'next_due_date']
        verbose_name = 'PM Schedule'
        verbose_name_plural = 'PM Schedules'
        constraints = [
            models.CheckConstraint(
                check=models.Q(interval_days__isnull=True) | models.Q(interval_days__gt=0),
                name='ck_pm_interval_days_pos'
            ),
            models.CheckConstraint(
                check=models.Q(interval_hours__isnull=True) | models.Q(interval_hours__gt=0),
                name='ck_pm_interval_hours_pos'
            ),
            models.CheckConstraint(
                check=models.Q(next_due_date__isnull=True) | models.Q(last_done_date__isnull=True) | models.Q(
                    next_due_date__gte=models.F('last_done_date')),
                name='ck_pm_next_ge_last'
            ),
        ]

    def __str__(self):
        return f"{self.asset.asset_code} - {self.schedule_name}"


class MaintenanceRequestStatus(models.TextChoices):
    OPEN = 'Open', 'Open'
    IN_PROGRESS = 'In Progress', 'In Progress'
    COMPLETED = 'Completed', 'Completed'
    CANCELLED = 'Cancelled', 'Cancelled'


class MaintenanceRequest(AuditMixin):
    maint_req_id = models.BigAutoField(primary_key=True)
    request_no = models.CharField(max_length=64, unique=True)
    asset = models.ForeignKey('Asset', null=True, blank=True, on_delete=models.SET_NULL,
                              db_column='asset_id', related_name='maintenance_requests')
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                    db_column='reported_by', related_name='maintenance_reports')
    request_date = models.DateField()
    severity = models.CharField(max_length=16, blank=True)
    issue_type = models.CharField(max_length=32, blank=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=32, choices=MaintenanceRequestStatus.choices,
                              default=MaintenanceRequestStatus.OPEN)

    objects = BaseManager()

    class Meta:
        db_table = 'maintenance_requests'
        verbose_name = 'Maintenance Request'
        verbose_name_plural = 'Maintenance Requests'
        ordering = ['-request_date', 'request_no']

    def __str__(self):
        return f"{self.request_no} ({self.status})"


class MaintenanceWorkorderStatus(models.TextChoices):
    PENDING = 'Pending', 'Pending'
    IN_PROGRESS = 'In Progress', 'In Progress'
    COMPLETED = 'Completed', 'Completed'
    CANCELLED = 'Cancelled', 'Cancelled'


class MaintenanceWorkorder(AuditMixin):
    mwo_id = models.BigAutoField(primary_key=True)
    mwo_no = models.CharField(max_length=64, unique=True)
    maint_req = models.ForeignKey('MaintenanceRequest', null=True, blank=True, on_delete=models.SET_NULL,
                                  db_column='maint_req_id', related_name='workorders')
    asset = models.ForeignKey('Asset', null=True, blank=True, on_delete=models.SET_NULL,
                              db_column='asset_id', related_name='workorders')
    pm = models.ForeignKey('PMSchedule', null=True, blank=True, on_delete=models.SET_NULL,
                           db_column='pm_id', related_name='workorders')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                    db_column='assigned_to', related_name='maintenance_assignments')
    planned_start = models.DateTimeField(null=True, blank=True)
    planned_end = models.DateTimeField(null=True, blank=True)
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=32, choices=MaintenanceWorkorderStatus.choices,
                              default=MaintenanceWorkorderStatus.PENDING)
    notes = models.TextField(blank=True)

    objects = BaseManager()

    class Meta:
        db_table = 'maintenance_workorders'
        ordering = ['-created_at', 'mwo_no']
        verbose_name = 'Maintenance Work Order'
        verbose_name_plural = 'Maintenance Work Orders'
        constraints = [
            models.CheckConstraint(
                check=(
                        models.Q(planned_end__isnull=True) |
                        (models.Q(planned_start__isnull=False) & models.Q(planned_end__gte=models.F('planned_start')))
                ),
                name='ck_mwo_planned_end_ge_start'
            ),
            models.CheckConstraint(
                check=(
                        models.Q(actual_end__isnull=True) |
                        (models.Q(actual_start__isnull=False) & models.Q(actual_end__gte=models.F('actual_start')))
                ),
                name='ck_mwo_actual_end_ge_start'
            ),
        ]

    def __str__(self):
        return f"{self.mwo_no} ({self.status})"


# Safety & Training
class SafetyTraining(AuditMixin):
    training_id = models.BigAutoField(primary_key=True)
    training_code = models.CharField(max_length=32, unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    training_type = models.CharField(max_length=32, blank=True)
    required_for_group = models.ForeignKey(Group, null=True, blank=True, on_delete=models.SET_NULL,
                                           db_column='required_for_group_id', related_name='required_trainings')
    valid_months = models.IntegerField(null=True, blank=True,
                                       help_text="Number of months this training is valid for")

    objects = BaseManager()

    class Meta:
        db_table = 'safety_training'
        ordering = ['training_code']
        verbose_name = 'Safety Training'
        verbose_name_plural = 'Safety Training'
        constraints = [
            models.CheckConstraint(
                check=models.Q(valid_months__isnull=True) | models.Q(valid_months__gt=0),
                name='ck_training_valid_months_pos'
            ),
        ]

    def __str__(self):
        return f"{self.training_code} - {self.title}"


class UserTrainingStatus(models.TextChoices):
    SCHEDULED = 'Scheduled', 'Scheduled'
    COMPLETED = 'Completed', 'Completed'
    EXPIRED = 'Expired', 'Expired'
    FAILED = 'Failed', 'Failed'


class UserTraining(AuditMixin):
    user_training_id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             db_column='user_id', related_name='trainings')
    training: 'SafetyTraining' = models.ForeignKey('SafetyTraining', on_delete=models.CASCADE,
                                                   db_column='training_id', related_name='user_trainings')
    training_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    certificate_no = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=32, choices=UserTrainingStatus.choices, default=UserTrainingStatus.COMPLETED)

    class Meta:
        db_table = 'user_training'
        verbose_name = 'User Training'
        verbose_name_plural = 'User Training Records'
        ordering = ['-training_date']
        constraints = [
            models.UniqueConstraint(fields=['user', 'training'], name='uq_user_training'),
            models.CheckConstraint(
                check=models.Q(expiry_date__gte=models.F('training_date')) | models.Q(expiry_date__isnull=True),
                name='ck_user_training_expiry_ge_training'
            ),
            models.CheckConstraint(
                check=models.Q(score__isnull=True) | (models.Q(score__gte=0) & models.Q(score__lte=100)),
                name='ck_training_score_0_100'
            ),
        ]

    def __str__(self):
        user = cast(User, self.user)  # tell the IDE it's a User
        name = user.get_full_name() or user.username
        return f"{name} - {self.training.title}"


class UserCertificate(AuditMixin):
    cert_id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             db_column='user_id', related_name='certificates')
    cert_code = models.CharField(max_length=64)
    cert_name = models.CharField(max_length=200)
    issuing_authority = models.CharField(max_length=200, blank=True)
    issue_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    objects = BaseManager()

    class Meta:
        db_table = 'user_certificates'
        verbose_name = 'User Certificate'
        verbose_name_plural = 'User Certificates'
        ordering = ['-issue_date']
        constraints = [
            models.UniqueConstraint(fields=['user', 'cert_code'], name='uq_user_certificate'),
            models.CheckConstraint(
                check=models.Q(expiry_date__gte=models.F('issue_date')) | models.Q(expiry_date__isnull=True),
                name='ck_user_cert_expiry_ge_issue'
            ),
        ]

    def __str__(self):
        user = cast(User, self.user)  # tell the IDE it's a User
        name = user.get_full_name() or user.username
        return f"{name} - {self.cert_name}"


class PPEType(models.Model):
    ppe_id = models.BigAutoField(primary_key=True)
    ppe_code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=120, unique=True)
    category = models.CharField(max_length=64, blank=True)
    standard_ref = models.CharField(max_length=120, blank=True)
    replacement_days = models.IntegerField(null=True, blank=True,
                                           help_text="Standard replacement interval in days")

    class Meta:
        db_table = 'ppe_types'
        ordering = ['ppe_code']
        verbose_name = 'PPE Type'
        verbose_name_plural = 'PPE Types'
        constraints = [
            models.CheckConstraint(
                check=models.Q(replacement_days__isnull=True) | models.Q(replacement_days__gt=0),
                name='ck_ppe_replacement_days_pos'
            ),
        ]

    def __str__(self):
        return f"{self.ppe_code} - {self.name}"


class PPEIssuance(models.Model):
    ppe_issue_id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                             db_column='user_id', related_name='ppe_issuances')
    ppe = models.ForeignKey('PPEType', null=True, blank=True, on_delete=models.SET_NULL,
                            db_column='ppe_id', related_name='issuances')
    issue_date = models.DateField()
    qty = models.DecimalField(max_digits=18, decimal_places=6)
    return_date = models.DateField(null=True, blank=True)
    condition_on_return = models.CharField(max_length=32, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'ppe_issuance'
        ordering = ['-issue_date']
        verbose_name = 'PPE Issuance'
        verbose_name_plural = 'PPE Issuances'
        constraints = [
            models.CheckConstraint(check=models.Q(qty__gt=0), name='ck_ppe_qty_pos'),
            models.CheckConstraint(
                check=models.Q(return_date__gte=models.F('issue_date')) | models.Q(return_date__isnull=True),
                name='ck_ppe_return_ge_issue'
            ),
        ]

    def __str__(self):
        user = cast(User, self.user) if self.user else None
        name = user.get_full_name() or user.username if user else "—"
        ppe = self.ppe.name if self.ppe else "—"
        return f"{name} - {ppe} ({self.issue_date})"


# Safety & Training (Enhanced)
class Incident(AuditMixin):
    incident_id = models.BigAutoField(primary_key=True)
    incident_no = models.CharField(max_length=64, unique=True)
    incident_date = models.DateField()
    reported_date = models.DateField()
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                    db_column='reported_by', related_name='incident_reports')
    incident_type = models.CharField(max_length=32, blank=True)
    severity = models.CharField(max_length=16, blank=True)
    location_text = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    root_cause = models.TextField(blank=True)
    corrective_action = models.TextField(blank=True)
    status = models.CharField(max_length=32, choices=IncidentStatus.choices, default=IncidentStatus.REPORTED)

    objects = BaseManager()

    class Meta:
        db_table = 'incidents'
        ordering = ['-incident_date', 'incident_no']
        verbose_name = 'Incident'
        verbose_name_plural = 'Incidents'
        constraints = [
            models.CheckConstraint(
                check=models.Q(reported_date__gte=models.F('incident_date')),
                name='ck_incident_reported_ge_occurred'
            )
        ]

    def __str__(self):
        return f"{self.incident_no} - {self.incident_type} ({self.severity})"


class RiskAssessment(AuditMixin):
    ra_id = models.BigAutoField(primary_key=True)
    ra_code = models.CharField(max_length=64, unique=True)
    area_or_process = models.CharField(max_length=200)
    hazard = models.CharField(max_length=200)
    risk_before = models.CharField(max_length=32, blank=True)
    likelihood = models.IntegerField(null=True, blank=True)
    severity = models.IntegerField(null=True, blank=True)
    risk_score = models.IntegerField(null=True, blank=True)
    controls = models.TextField(blank=True)
    risk_after = models.CharField(max_length=32, blank=True)
    review_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'risk_assessments'
        ordering = ['-created_at', 'ra_code']
        verbose_name = 'Risk Assessment'
        verbose_name_plural = 'Risk Assessments'
        constraints = [
            models.CheckConstraint(
                check=models.Q(likelihood__isnull=True) | models.Q(likelihood__range=(1, 5)),
                name='ck_ra_likelihood_1_5'
            ),
            models.CheckConstraint(
                check=models.Q(severity__isnull=True) | models.Q(severity__range=(1, 5)),
                name='ck_ra_severity_1_5'
            ),
            models.CheckConstraint(
                check=models.Q(risk_score__isnull=True) | models.Q(risk_score__gte=0),
                name='ck_ra_score_nonneg'
            ),
        ]

    def __str__(self):
        return f"{self.ra_code} - {self.area_or_process}"


# HR & Employee (Enhanced)
class Employee(AuditMixin):
    emp_id = models.BigAutoField(primary_key=True)
    employee_code = models.CharField(max_length=50, unique=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, db_column="user_id",
        related_name="employee_record",
        help_text="Login account for this employee (auto-created if empty).",
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, blank=True)
    marital_status = models.CharField(
        max_length=10,
        choices=MaritalStatus.choices,
        default=MaritalStatus.SINGLE,
        db_index=True
    )
    allow_admin_login = models.BooleanField(
        default=False,
        db_index=True,
        help_text="If checked, the linked user can sign in to Django admin (sets is_staff)."
    )
    department = models.CharField(max_length=100, blank=True)
    designation = models.CharField(
        max_length=40,
        choices=Designation.choices,
        default=Designation.OTHER,
        db_index=True
    )
    email = models.EmailField(unique=True, null=True, blank=True)
    auth_group = models.ForeignKey(
        Group, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="employees",
        help_text="Permissions group for this employee."
    )
    joining_date = models.DateField()
    confirmation_date = models.DateField(null=True, blank=True)
    resignation_date = models.DateField(null=True, blank=True)
    base_salary = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    salary_currency = models.ForeignKey('Currency', on_delete=models.PROTECT,
                                        db_column='salary_currency', related_name='employees')
    bank_account = models.CharField(max_length=50, blank=True)
    employment_status = models.CharField(max_length=32, choices=EmploymentStatus.choices,
                                         default=EmploymentStatus.ACTIVE)

    objects = BaseManager()

    class Meta:
        db_table = 'employees'
        ordering = ['employee_code']
        verbose_name = 'Employee'
        verbose_name_plural = 'Employees'
        indexes = [
            models.Index(fields=['employment_status'], name='ix_employee_status')
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(base_salary__gt=0) | models.Q(base_salary__isnull=True),
                name='ck_emp_salary_pos'
            ),
            models.CheckConstraint(
                check=models.Q(confirmation_date__isnull=True) | models.Q(
                    confirmation_date__gte=models.F('joining_date')),
                name='ck_emp_confirm_ge_join'
            ),
            models.CheckConstraint(
                check=models.Q(resignation_date__isnull=True) | models.Q(
                    resignation_date__gte=models.F('joining_date')),
                name='ck_emp_resign_ge_join'
            ),
        ]

    def __str__(self):
        return f"{self.employee_code} - {self.full_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    # Helpers to reach Contact records for this employee:
    @property
    def contacts(self):
        ct = ContentType.objects.get_for_model(self.__class__)
        return Contact.objects.filter(party_type=ct, party_id=self.pk)

    @property
    def primary_contact(self):
        return self.contacts.filter(is_primary=True).first()


class Responsibility(AuditMixin):
    responsibility_id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'responsibilities'
        verbose_name = 'Responsibility'
        verbose_name_plural = 'Responsibilities'
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"


class UserResponsibility(AuditMixin):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             db_column='user_id', related_name='responsibilities')
    responsibility = models.ForeignKey('Responsibility', on_delete=models.CASCADE,
                                       db_column='responsibility_id', related_name='users')
    is_primary = models.BooleanField(default=False)
    assigned_date = models.DateField()

    class Meta:
        db_table = 'user_responsibilities'
        ordering = ['-is_primary', 'assigned_date']
        verbose_name = 'User Responsibility'
        verbose_name_plural = 'User Responsibilities'
        constraints = [
            models.UniqueConstraint(fields=['user', 'responsibility'],
                                    name='uq_user_responsibility')
        ]

    def __str__(self):
        return f"{self.user} - {self.responsibility}"


# KPI & Metrics (Enhanced)
class KPIDefinition(AuditMixin):
    kpi_id = models.BigAutoField(primary_key=True)
    kpi_code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=200, unique=True)
    category = models.CharField(max_length=64, blank=True)
    formula_text = models.TextField(blank=True)
    target_value = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    uom = models.CharField(max_length=32, blank=True)
    frequency = models.CharField(max_length=32, blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                              db_column='owner_id', related_name='owned_kpis')

    class Meta:
        db_table = 'kpi_definitions'
        ordering = ['category', 'kpi_code']
        verbose_name = 'KPI Definition'
        verbose_name_plural = 'KPI Definitions'

    def __str__(self):
        return f"{self.kpi_code} - {self.name}"


class KPIValue(AuditMixin):
    kpi_val_id = models.BigAutoField(primary_key=True)
    kpi: 'KPIDefinition' = models.ForeignKey('KPIDefinition', on_delete=models.CASCADE,
                                             db_column='kpi_id', related_name='values')
    period_date = models.DateField()
    value_num = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    target_value = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    variance = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)

    class Meta:
        db_table = 'kpi_values'
        ordering = ['-period_date']
        verbose_name = 'KPI Value'
        verbose_name_plural = 'KPI Values'
        indexes = [
            models.Index(fields=['period_date'], name='ix_kpi_value_period'),
            models.Index(
                F('kpi'),
                OrderBy(F('period_date'), descending=True),
                name='ix_kpi_value_kpi_period',
            ),
        ]
        constraints = [
            models.UniqueConstraint(fields=['kpi', 'period_date'], name='uq_kpi_value')
        ]

    def __str__(self):
        return f"{self.kpi} - {self.period_date}: {self.value_num}"


# Audit & System (Enhanced)
class AuditLog(models.Model):
    log_id = models.BigAutoField(primary_key=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                             db_column='user_id', related_name='audit_logs')
    table_name = models.CharField(max_length=120)
    record_id = models.BigIntegerField()
    action = models.CharField(max_length=16)
    old_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'audit_log'
        ordering = ['-timestamp']
        verbose_name = 'Audit Log Entry'
        verbose_name_plural = 'Audit Log Entries'
        indexes = [
            models.Index(fields=['table_name', 'record_id'], name='ix_audit_table_record'),
            models.Index(fields=['user'], name='ix_audit_user'),
            models.Index(fields=['timestamp'], name='ix_audit_timestamp')
        ]

    def __str__(self):
        return f"{self.action} on {self.table_name}#{self.record_id} at {self.timestamp}"


class Instruction(AuditMixin):
    instruction_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=200)
    trigger_domain = models.CharField(max_length=24)
    trigger_name = models.CharField(max_length=48)
    trigger_phase = models.CharField(max_length=8, default='on')
    time_kind = models.CharField(max_length=24, blank=True)
    time_sec = models.IntegerField(null=True, blank=True)
    enabled = models.BooleanField(default=True)
    priority = models.IntegerField(default=10)
    description = models.TextField(blank=True)

    objects = BaseManager()

    class Meta:
        db_table = 'instructions'
        ordering = ['priority', 'name']
        verbose_name = 'Instruction'
        verbose_name_plural = 'Instructions'
        indexes = [
            models.Index(fields=['trigger_domain', 'trigger_phase', 'trigger_name'],
                         name='ix_instruction_trigger'),
            models.Index(fields=['enabled', 'priority'], name='ix_instr_en_pr')
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(time_sec__isnull=True) | models.Q(time_sec__gt=0),
                name='ck_instruction_time_pos'
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.trigger_domain}.{self.trigger_name})"


class InstructionCondition(AuditMixin):
    cond_id = models.BigAutoField(primary_key=True)
    instruction = models.ForeignKey('Instruction', on_delete=models.CASCADE,
                                    db_column='instruction_id', related_name='conditions')
    group_no = models.IntegerField(default=1)
    joiner = models.CharField(max_length=3, default='AND')
    left_operand = models.CharField(max_length=128)
    operator = models.CharField(max_length=16)
    right_value = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = 'instruction_conditions'
        ordering = ['instruction', 'group_no']
        verbose_name = 'Instruction Condition'
        verbose_name_plural = 'Instruction Conditions'

    def __str__(self):
        return f"{self.instruction} - {self.left_operand} {self.operator}"


class InstructionAction(AuditMixin):
    act_id = models.BigAutoField(primary_key=True)
    instruction = models.ForeignKey('Instruction', on_delete=models.CASCADE,
                                    db_column='instruction_id', related_name='actions')
    action_type = models.CharField(max_length=24)
    params_json = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = 'instruction_actions'
        ordering = ['instruction']
        verbose_name = 'Instruction Action'
        verbose_name_plural = 'Instruction Actions'

    def __str__(self):
        return f"{self.instruction} - {self.action_type}"


class NotificationSubscription(AuditMixin):
    sub_id = models.BigAutoField(primary_key=True)
    topic = models.CharField(max_length=64)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE,
                             db_column='user_id', related_name='notification_subscriptions')
    role = models.ForeignKey(Group, null=True, blank=True, on_delete=models.CASCADE,
                             db_column='role_id', related_name='notification_subscriptions')
    channel = models.CharField(max_length=32, blank=True)
    filter_expr = models.JSONField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    objects = BaseManager()

    class Meta:
        db_table = 'notification_subscriptions'
        ordering = ['topic']
        verbose_name = 'Notification Subscription'
        verbose_name_plural = 'Notification Subscriptions'
        constraints = [
            # Exactly one of user or role must be set (XOR)
            models.CheckConstraint(
                check=(models.Q(user__isnull=False) & models.Q(role__isnull=True)) | (
                            models.Q(user__isnull=True) & models.Q(role__isnull=False)),
                name='ck_sub_exactly_one_principal'
            ),
        ]

    def __str__(self):
        principal = self.user or self.role
        return f"{self.topic} - {principal}"


class TimerStatus(models.TextChoices):
    PENDING = 'PENDING', 'PENDING'
    FIRED = 'FIRED', 'FIRED'
    EXPIRED = 'EXPIRED', 'EXPIRED'
    CANCELLED = 'CANCELLED', 'CANCELLED'


class Timer(AuditMixin, DocumentReferenceMixin):
    timer_id = models.BigAutoField(primary_key=True)
    topic = models.CharField(max_length=64)
    due_ts = models.DateTimeField(db_index=True)
    payload_json = models.JSONField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=TimerStatus.choices, default=TimerStatus.PENDING)

    class Meta:
        db_table = 'timers'
        ordering = ['due_ts']
        verbose_name = 'Timer'
        verbose_name_plural = 'Timers'
        indexes = [
            models.Index(fields=['due_ts', 'status'], name='ix_timer_due_status')
        ]

    def __str__(self):
        return f"{self.topic} - Due: {self.due_ts}"


class ApprovalTemplate(AuditMixin):
    template_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=120, unique=True)
    doc_type = models.CharField(max_length=32, choices=DocType.choices)
    condition_field = models.CharField(max_length=64, blank=True)
    threshold_value = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    approver_role = models.ForeignKey(Group, null=True, blank=True, on_delete=models.SET_NULL,
                                      db_column='approver_role_id', related_name='approval_templates')
    approver_user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                      db_column='approver_user_id', related_name='approval_templates')
    approval_level = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True)

    objects = BaseManager()

    class Meta:
        db_table = 'approval_templates'
        ordering = ['doc_type', 'approval_level']
        verbose_name = 'Approval Template'
        verbose_name_plural = 'Approval Templates'
        constraints = [
            # Exactly one of approver_role or approver_user_id must be set
            models.CheckConstraint(
                check=(models.Q(approver_role__isnull=False) & models.Q(approver_user__isnull=True)) | (
                            models.Q(approver_role__isnull=True) & models.Q(approver_user__isnull=False)),
                name='ck_approval_template_one_approver'
            ),
            models.CheckConstraint(
                check=models.Q(approval_level__gte=1),
                name='ck_approval_level_pos'
            )
        ]

    def __str__(self):
        return f"{self.name} - Level {self.approval_level}"


class DocumentApprovalStatus(models.TextChoices):
    PENDING = 'Pending', 'Pending'
    APPROVED = 'Approved', 'Approved'
    REJECTED = 'Rejected', 'Rejected'
    CANCELLED = 'Cancelled', 'Cancelled'


class DocumentApproval(AuditMixin):
    approval_id = models.BigAutoField(primary_key=True)
    doc_type = models.CharField(max_length=32, choices=DocType.choices)
    doc_id = models.BigIntegerField()
    template = models.ForeignKey('ApprovalTemplate', null=True, blank=True, on_delete=models.SET_NULL,
                                 db_column='template_id', related_name='approvals')
    approval_level = models.IntegerField(default=1)
    approver = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                 db_column='approver_id', related_name='document_approvals')
    status = models.CharField(max_length=16, choices=DocumentApprovalStatus.choices,
                              default=DocumentApprovalStatus.PENDING)
    comments = models.TextField(blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    objects = BaseManager()

    class Meta:
        db_table = 'document_approvals'
        ordering = ['-created_at']
        verbose_name = 'Document Approval'
        verbose_name_plural = 'Document Approvals'
        indexes = [
            models.Index(fields=['doc_type', 'doc_id'], name='ix_doc_approval'),
            models.Index(fields=['status'], name='ix_approval_status'),
            models.Index(fields=['approver', 'status'], name='ix_approval_approver_status')
        ]

    def __str__(self):
        return f"{self.doc_type}#{self.doc_id} - Level {self.approval_level} ({self.status})"


# Item Substitutes (Enhanced)
class ItemSubstitute(AuditMixin):
    subs_id = models.BigAutoField(primary_key=True)
    item = models.ForeignKey('Item', on_delete=models.CASCADE,
                             db_column='item_id', related_name='substitutes')
    substitute_item = models.ForeignKey('Item', on_delete=models.PROTECT,
                                        db_column='substitute_item_id', related_name='substitute_for')
    reason = models.CharField(max_length=200, blank=True)
    is_approved = models.BooleanField(default=True)
    effective_from = models.DateField(null=True, blank=True)
    effective_to = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'item_substitutes'
        ordering = ['item_id', 'effective_from']
        verbose_name = 'Item Substitute'
        verbose_name_plural = 'Item Substitutes'
        constraints = [
            models.UniqueConstraint(fields=['item', 'substitute_item'], name='uq_item_substitute'),
            models.CheckConstraint(
                check=models.Q(effective_to__isnull=True) | models.Q(effective_from__isnull=True) | models.Q(
                    effective_to__gte=models.F('effective_from')),
                name='ck_itemsub_to_ge_from'
            ),
        ]

    def __str__(self):
        return f"{self.item} → {self.substitute_item}"


class BOMSubstitute(models.Model):
    bom_sub_id = models.BigAutoField(primary_key=True)
    bom_item = models.ForeignKey('BOMItem', on_delete=models.CASCADE,
                                 db_column='bom_item_id', related_name='substitutes')
    substitute_item = models.ForeignKey('Item', on_delete=models.PROTECT,
                                        db_column='substitute_item_id', related_name='bom_substitutes')
    priority = models.IntegerField(default=10, help_text="Lower number = higher priority")
    condition_expr = models.CharField(max_length=255, blank=True)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'bom_substitutes'
        ordering = ['bom_item', 'priority']
        verbose_name = 'BOM Substitute'
        verbose_name_plural = 'BOM Substitutes'
        indexes = [
            models.Index(fields=['bom_item', 'priority'], name='ix_bomsub_bomitem_priority')
        ]
        constraints = [
            models.UniqueConstraint(fields=['bom_item', 'substitute_item'],
                                    name='uq_bom_substitute'),
            models.CheckConstraint(
                check=models.Q(priority__range=(1, 100)),
                name='ck_bomsub_priority_range'
            )
        ]

    def __str__(self):
        return f"{self.bom_item} → {self.substitute_item} (P{self.priority})"


class StockReservationStatus(models.TextChoices):
    DRAFT = 'Draft', 'Draft'
    RESERVED = 'Reserved', 'Reserved'
    RELEASED = 'Released', 'Released'
    CANCELLED = 'Cancelled', 'Cancelled'


class StockReservation(AuditMixin):
    res_id = models.BigAutoField(primary_key=True)
    item = models.ForeignKey('Item', on_delete=models.PROTECT,
                             db_column='item_id', related_name='reservations')
    wh = models.ForeignKey('Warehouse', on_delete=models.PROTECT,
                           db_column='wh_id', related_name='reservations')
    qty = models.DecimalField(max_digits=18, decimal_places=6)
    uom_code = models.ForeignKey('UOM', null=True, blank=True, on_delete=models.SET_NULL,
                                 db_column='uom_code', related_name='reservations')
    demand_doctype = models.CharField(max_length=32, blank=True)
    demand_id = models.BigIntegerField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=StockReservationStatus.choices,
                              default=StockReservationStatus.DRAFT)

    objects = BaseManager()

    class Meta:
        db_table = 'stock_reservations'
        ordering = ['-created_at']
        verbose_name = 'Stock Reservation'
        verbose_name_plural = 'Stock Reservations'
        indexes = [
            models.Index(fields=['demand_doctype', 'demand_id'], name='ix_reservation_demand'),
            models.Index(fields=['item', 'wh', 'status'], name='ix_reservation_item_wh_status')
        ]
        constraints = [
            models.CheckConstraint(check=models.Q(qty__gt=0), name='ck_res_qty_pos')
        ]

    def __str__(self):
        return f"{self.item} @ {self.wh}: {self.qty} ({self.status})"


class NonConformanceStatus(models.TextChoices):
    DRAFT = 'Draft', 'Draft'
    OPEN = 'Open', 'Open'
    IN_PROGRESS = 'In Progress', 'In Progress'
    CLOSED = 'Closed', 'Closed'
    CANCELLED = 'Cancelled', 'Cancelled'


class NonConformance(AuditMixin):
    ncr_id = models.BigAutoField(primary_key=True)
    source_doc_type = models.CharField(max_length=32)
    source_doc_id = models.BigIntegerField(null=True, blank=True)
    defect_code = models.CharField(max_length=64, blank=True)
    description = models.TextField(blank=True)
    raised_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                  db_column='raised_by', related_name='non_conformances')
    status = models.CharField(max_length=16, choices=NonConformanceStatus.choices, default=NonConformanceStatus.DRAFT)

    objects = BaseManager()

    class Meta:
        db_table = 'non_conformances'
        ordering = ['-created_at']
        verbose_name = 'Non-Conformance Report'
        verbose_name_plural = 'Non-Conformance Reports'
        indexes = [
            models.Index(fields=['source_doc_type', 'source_doc_id'], name='ix_ncr_source'),
            models.Index(fields=['status'], name='ix_ncr_status'),
        ]
        constraints = [
            models.CheckConstraint(
                name='ck_ncr_source_pair',
                check=(
                        (models.Q(source_doc_id__isnull=True) & models.Q(source_doc_type='')) |
                        (models.Q(source_doc_id__isnull=False) & ~models.Q(source_doc_type=''))
                )
            ),
        ]

    def __str__(self):
        return f"NCR#{self.ncr_id} - {self.defect_code} ({self.status})"


class ReworkOrderStatus(models.TextChoices):
    DRAFT = 'Draft', 'Draft'
    IN_PROGRESS = 'InProgress', 'In Progress'
    DONE = 'Done', 'Done'
    CANCELED = 'Canceled', 'Canceled'


class ReworkOrder(AuditMixin):
    rw_id = models.BigAutoField(primary_key=True)
    ncr = models.ForeignKey('NonConformance', on_delete=models.CASCADE,
                            db_column='ncr_id', related_name='rework_orders')
    wo = models.ForeignKey('WorkOrder', null=True, blank=True, on_delete=models.SET_NULL,
                           db_column='wo_id', related_name='rework_orders')
    action_plan = models.TextField(blank=True)
    status = models.CharField(max_length=16, choices=ReworkOrderStatus.choices, default=ReworkOrderStatus.DRAFT)

    objects = BaseManager()

    class Meta:
        db_table = 'rework_orders'
        ordering = ['-created_at']
        verbose_name = 'Rework Order'
        verbose_name_plural = 'Rework Orders'
        indexes = [
            models.Index(fields=['ncr'], name='ix_rw_ncr'),
            models.Index(fields=['status'], name='ix_rw_status'),
            models.Index(fields=['wo'], name='ix_rw_wo'),
        ]

    def __str__(self):
        return f"RW#{self.rw_id} for NCR#{self.ncr} ({self.status})"


class PaymentAllocation(models.Model):
    alloc_id = models.BigAutoField(primary_key=True)

    pay: 'Payment' = models.ForeignKey(
        'Payment', on_delete=models.CASCADE,
        db_column='pay_id', related_name='allocations'
    )
    si: Optional['SalesInvoice'] = models.ForeignKey(
        'SalesInvoice', null=True, blank=True,
        on_delete=models.SET_NULL, db_column='si_id',
        related_name='payment_allocations'
    )
    pi: Optional['PurchaseInvoice'] = models.ForeignKey(
        'PurchaseInvoice', null=True, blank=True,
        on_delete=models.SET_NULL, db_column='pi_id',
        related_name='payment_allocations'
    )

    allocated_amount = models.DecimalField(max_digits=18, decimal_places=6)

    class Meta:
        db_table = 'payment_allocations'
        ordering = ['pay']
        verbose_name = 'Payment Allocation'
        verbose_name_plural = 'Payment Allocations'
        constraints = [
            # Use Decimal('0') so linters/mypy see a Decimal on RHS
            models.CheckConstraint(
                check=Q(allocated_amount__gt=Decimal('0')),
                name='ck_pa_amount_pos'
            ),
            models.CheckConstraint(
                check=(Q(si__isnull=False, pi__isnull=True) |
                       Q(si__isnull=True, pi__isnull=False)),
                name='ck_pa_exactly_one_target'
            ),
        ]

    def __str__(self):
        si = cast(Optional['SalesInvoice'], self.si)
        pi = cast(Optional['PurchaseInvoice'], self.pi)
        target = f"SI#{si.pk}" if si else (f"PI#{pi.pk}" if pi else "N/A")
        return f"Alloc: {self.allocated_amount} to {target}"

    def clean(self):
        super().clean()

        # Ensure a Payment is chosen
        if not self.pay:
            raise ValidationError({'pay': 'Payment must be selected.'})

        # Check allocated_amount is set (defensive even for non-nullable field)
        if self.allocated_amount is None:
            raise ValidationError({'allocated_amount': 'Allocated amount is required.'})

        alloc = cast(Decimal, self.allocated_amount)

        # Be defensive with Payment.amount
        pay_amount = getattr(self.pay, 'amount', None)
        if pay_amount is None:
            raise ValidationError({'pay': 'Payment has no amount defined.'})

        pay_amount = cast(Decimal, pay_amount)  # Redundant cast, but harmless

        if alloc <= Decimal('0'):
            raise ValidationError({'allocated_amount': 'Allocated amount must be > 0.'})

        if alloc > pay_amount:
            raise ValidationError({'allocated_amount': 'Allocation exceeds payment amount.'})


class Tax(AuditMixin):
    tax_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=120, unique=True)
    rate_pct = models.DecimalField(max_digits=6, decimal_places=3,
                                   help_text="Tax rate as percentage (e.g., 15.000 for 15%)")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'taxes'
        verbose_name = 'Tax'
        verbose_name_plural = 'Taxes'
        ordering = ['name']
        constraints = [
            models.CheckConstraint(
                check=models.Q(rate_pct__gte=0) & models.Q(rate_pct__lte=100),
                name='ck_tax_rate_0_100'
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.rate_pct}%)"


class DocTax(models.Model):
    doc_tax_id = models.BigAutoField(primary_key=True)
    doc_type = models.CharField(max_length=32, choices=DocType.choices)
    doc_id = models.BigIntegerField()
    tax = models.ForeignKey('Tax', on_delete=models.PROTECT,
                            db_column='tax_id', related_name='document_taxes')
    base_amount = models.DecimalField(max_digits=18, decimal_places=6)
    tax_amount = models.DecimalField(max_digits=18, decimal_places=6)
    currency_code = models.ForeignKey('Currency', on_delete=models.PROTECT,
                                      db_column='currency_code', related_name='doc_taxes')

    class Meta:
        db_table = 'doc_taxes'
        ordering = ['doc_type', 'doc_id']
        verbose_name = 'Document Tax'
        verbose_name_plural = 'Document Taxes'
        indexes = [
            models.Index(fields=['doc_type', 'doc_id'], name='ix_doctax_doc')
        ]
        constraints = [
            models.CheckConstraint(check=models.Q(base_amount__gte=0), name='ck_doctax_base_nonneg'),
            models.CheckConstraint(check=models.Q(tax_amount__gte=0), name='ck_doctax_tax_nonneg'),
        ]

    def __str__(self):
        return f"{self.doc_type}#{self.doc_id} - {self.tax}: {self.tax_amount}"


# HR Additional Models (Enhanced)
class Attendance(AuditMixin):
    att_id = models.BigAutoField(primary_key=True)
    emp = models.ForeignKey('Employee', on_delete=models.CASCADE,
                            db_column='emp_id', related_name='attendance')
    date = models.DateField()
    status = models.CharField(max_length=16)
    minutes_late = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'attendance'
        ordering = ['-date', 'emp']
        verbose_name = 'Attendance Record'
        verbose_name_plural = 'Attendance Records'
        indexes = [
            models.Index(fields=['emp', 'date'], name='ix_att_emp_date'),
            models.Index(fields=['date', 'status'], name='ix_att_date_status')
        ]
        constraints = [
            models.UniqueConstraint(fields=['emp', 'date'], name='uq_att_emp_date'),
            models.CheckConstraint(
                check=models.Q(minutes_late__isnull=True) | models.Q(minutes_late__gte=0),
                name='ck_att_minutes_late_nonneg'
            )
        ]

    def __str__(self):
        return f"{self.emp} - {self.date}: {self.status}"


class LeaveStatus(models.TextChoices):
    DRAFT = 'Draft', 'Draft'
    SUBMITTED = 'Submitted', 'Submitted'
    APPROVED = 'Approved', 'Approved'
    REJECTED = 'Rejected', 'Rejected'
    CANCELLED = 'Cancelled', 'Cancelled'


class Leave(AuditMixin):
    leave_id = models.BigAutoField(primary_key=True)
    emp = models.ForeignKey('Employee', on_delete=models.CASCADE,
                            db_column='emp_id', related_name='leaves')
    from_date = models.DateField()
    to_date = models.DateField()
    leave_type = models.CharField(max_length=32)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                    db_column='approved_by', related_name='leave_approvals')
    status = models.CharField(max_length=16, choices=LeaveStatus.choices, default=LeaveStatus.DRAFT)

    objects = BaseManager()

    class Meta:
        db_table = 'leaves'
        ordering = ['-from_date']
        verbose_name = 'Leave Request'
        verbose_name_plural = 'Leave Requests'
        indexes = [
            models.Index(fields=['emp', 'status'], name='ix_leave_emp_status')
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(to_date__gte=models.F('from_date')),
                name='ck_leave_to_ge_from'
            )
        ]

    def __str__(self):
        return f"{self.emp} - {self.leave_type}: {self.from_date} to {self.to_date}"

    @property
    def duration_days(self) -> int:
        """Calculate leave duration in days"""
        from_date = cast(date, self.from_date)
        to_date = cast(date, self.to_date)
        return (to_date - from_date).days + 1 if from_date and to_date else 0


class Qualification(AuditMixin):
    qual_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'qualifications'
        ordering = ['name']
        verbose_name = 'Qualification'
        verbose_name_plural = 'Qualifications'

    def __str__(self):
        return self.name


class EmployeeQualification(models.Model):
    emp_qual_id = models.BigAutoField(primary_key=True)
    emp = models.ForeignKey('Employee', on_delete=models.CASCADE,
                            db_column='emp_id', related_name='qualifications')
    qual = models.ForeignKey('Qualification', on_delete=models.PROTECT,
                             db_column='qual_id', related_name='employees')
    valid_from = models.DateField()
    valid_to = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'employee_qualifications'
        ordering = ['emp', '-valid_from']
        verbose_name = 'Employee Qualification'
        verbose_name_plural = 'Employee Qualifications'
        constraints = [
            models.UniqueConstraint(fields=['emp', 'qual'], name='uq_employee_qualification'),
            models.CheckConstraint(
                check=models.Q(valid_to__isnull=True) | models.Q(valid_to__gte=models.F('valid_from')),
                name='ck_empqual_to_ge_from'
            ),
        ]

    def __str__(self):
        return f"{self.emp} - {self.qual}"


class UserAvailability(AuditMixin):
    avail_id = models.BigAutoField(primary_key=True)
    emp = models.ForeignKey('Employee', on_delete=models.CASCADE,
                            db_column='emp_id', related_name='availability')
    date = models.DateField()
    available = models.BooleanField(default=True)

    class Meta:
        db_table = 'user_availability'
        ordering = ['-date']
        verbose_name = 'User Availability'
        verbose_name_plural = 'User Availability'
        indexes = [
            models.Index(fields=['emp', 'date'], name='ix_avail_emp_date')
        ]
        constraints = [
            models.UniqueConstraint(fields=['emp', 'date'], name='uq_avail_emp_date')
        ]

    def __str__(self):
        status = "Available" if self.available else "Unavailable"
        return f"{self.emp} - {self.date}: {status}"


class UserKPI(AuditMixin):
    user_kpi_id = models.BigAutoField(primary_key=True)
    emp = models.ForeignKey('Employee', on_delete=models.CASCADE,
                            db_column='emp_id', related_name='kpis')
    period = models.CharField(max_length=7, help_text="Format: YYYY-MM")
    kpi_name = models.CharField(max_length=120)
    kpi_value = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)

    class Meta:
        db_table = 'user_kpi'
        ordering = ['-period', 'emp']
        verbose_name = 'User KPI'
        verbose_name_plural = 'User KPIs'
        indexes = [
            models.Index(fields=['emp', 'period'], name='ix_kpi_emp_period')
        ]
        constraints = [
            models.UniqueConstraint(fields=['emp', 'period', 'kpi_name'],
                                    name='uq_userkpi_emp_period_name')
        ]

    def __str__(self):
        return f"{self.emp} - {self.kpi_name} ({self.period}): {self.kpi_value}"

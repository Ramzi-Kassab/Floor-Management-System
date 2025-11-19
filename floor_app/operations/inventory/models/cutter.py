"""
Cutter-Specific Models for PDC Bit Manufacturing

These models extend the generic inventory system with cutter-specific functionality
matching the Excel "Cutter Inventory" workbook structure:
- CutterOwnershipCategory: ENO As New, ENO Ground, ARDT Reclaim, LSTK Reclaim, New Stock, Retrofit
- CutterDetail: Extension of Item with cutter-specific attributes (SAP#, type, size, grade, chamfer)
- CutterPriceHistory: Time-based pricing for quotations
- CutterInventorySummary: Computed inventory levels and forecasting
"""

from django.db import models
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from floor_app.mixins import AuditMixin, SoftDeleteMixin


class CutterOwnershipCategory(models.Model):
    """
    Cutter-specific ownership categories matching Excel "Cutter Inventory" structure.

    Excel categories:
    - ENO As New: Reclaimed cutters in as-new condition (external new original)
    - ENO Ground: ENO cutters that have been reground
    - ARDT Reclaim: Cutters reclaimed by ARDT facility
    - LSTK Reclaim: Cutters reclaimed from LSTK customer bits
    - New Stock: Brand new purchased cutters
    - Retrofit: Cutters for retrofit/redesign projects

    Priority determines consumption order (lower = consumed first).
    """

    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Category code (e.g., ENO_AS_NEW, ENO_GROUND)"
    )
    name = models.CharField(
        max_length=100,
        help_text="Display name (e.g., 'ENO As New Cutter')"
    )
    short_name = models.CharField(
        max_length=30,
        help_text="Abbreviated name for column headers (e.g., 'ENO As New')"
    )

    # Consumption priority (lower number = consumed first)
    # Typical order: 1=New Stock, 2=ENO As New, 3=ENO Ground, 4=ARDT Reclaim, 5=LSTK Reclaim
    consumption_priority = models.IntegerField(
        default=50,
        help_text="Lower priority consumed first (1-99)"
    )

    # Flags
    is_new_stock = models.BooleanField(
        default=False,
        help_text="True if this is brand new purchased stock"
    )
    is_reclaimed = models.BooleanField(
        default=False,
        help_text="True if reclaimed from used bits"
    )
    is_ground = models.BooleanField(
        default=False,
        help_text="True if cutters have been reground"
    )

    # Excel sheet column reference (for migration/reconciliation)
    excel_column_label = models.CharField(
        max_length=50,
        blank=True,
        help_text="Excel sheet column label for reference (e.g., 'ENO As New Cutter')"
    )

    description = models.TextField(blank=True, default="")
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "inventory_cutter_ownership_category"
        verbose_name = "Cutter Ownership Category"
        verbose_name_plural = "Cutter Ownership Categories"
        ordering = ['sort_order', 'consumption_priority']

    def __str__(self):
        return f"{self.code} - {self.name}"


class CutterDetail(models.Model):
    """
    Cutter-specific attributes extension for Item model.

    Maps to Excel "Cutters Inventory" columns:
    - SAPNo: SAP/ERP material number
    - Type: Round, IA-STL, Shyfter, Short Bullet, etc.
    - Cutter size: 1313, 1308, 13MM Long, 1613, 19MM
    - Type (Grade): CT97, ELITE RC, M1, CT62, CT36
    - Chamfer: 0.010", 0.018", 0.012R
    - Category: P-Premium, O-Other, D-Depth of Cut, B-Standard, S-Super Premium

    This is a OneToOne extension of Item (only for cutter items).
    """

    item = models.OneToOneField(
        'Item',
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='cutter_detail',
        help_text="Link to parent Item record"
    )

    # SAP Number (from Excel "SAPNo" column)
    sap_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="SAP/ERP material number (e.g., 802065, 179692)"
    )

    # Cutter Type (from Excel "Type" column - Round, IA-STL, etc.)
    cutter_type = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Cutter type: Round, IA-STL, Shyfter, Short Bullet, etc."
    )

    # Cutter Size (from Excel "Cutter size" column)
    cutter_size = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Cutter size: 1313, 1308, 13MM Long, 1613, 19MM, etc."
    )

    # Grade (from Excel "Type" column - confusingly labeled)
    grade = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Cutter grade: CT97, ELITE RC, M1, CT62, CT36, etc."
    )

    # Chamfer (from Excel "Chamfer" column)
    chamfer = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="Chamfer size: 0.010\", 0.018\", 0.012R, etc."
    )

    # Category (from Excel "Category" column)
    CATEGORY_CHOICES = (
        ('P', 'P-Premium'),
        ('S', 'S-Super Premium'),
        ('B', 'B-Standard'),
        ('O', 'O-Other'),
        ('D', 'D-Depth of Cut'),
    )
    category = models.CharField(
        max_length=1,
        choices=CATEGORY_CHOICES,
        db_index=True,
        help_text="Cutter category classification"
    )

    # Additional description from Excel "More Description" column
    more_description = models.TextField(
        blank=True,
        default="",
        help_text="Additional description from Excel"
    )

    # Replacement cutter (from Excel "Replacement" column)
    replacement_cutter = models.ForeignKey(
        'Item',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='replaces_cutters',
        help_text="Replacement cutter if this one is obsolete"
    )

    # Obsolete flag
    is_obsolete = models.BooleanField(
        default=False,
        db_index=True,
        help_text="True if cutter is obsolete (see replacement_cutter)"
    )

    class Meta:
        db_table = "inventory_cutter_detail"
        verbose_name = "Cutter Detail"
        verbose_name_plural = "Cutter Details"
        ordering = ['sap_number']
        indexes = [
            models.Index(fields=['sap_number'], name='ix_cd_sap_number'),
            models.Index(fields=['cutter_type', 'cutter_size'], name='ix_cd_type_size'),
            models.Index(fields=['category', 'is_obsolete'], name='ix_cd_cat_obs'),
        ]

    def __str__(self):
        return f"{self.sap_number} - {self.cutter_type} {self.cutter_size} {self.grade}"


class CutterPriceHistory(AuditMixin):
    """
    Historical pricing for cutters (per Excel quotation logic).

    Preserves price changes over time so historical quotations remain accurate.
    """

    item = models.ForeignKey(
        'Item',
        on_delete=models.CASCADE,
        related_name='price_history',
        help_text="Cutter item"
    )

    effective_date = models.DateField(
        db_index=True,
        help_text="Date when this price becomes effective"
    )

    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        help_text="Price per unit in specified currency"
    )

    currency = models.CharField(
        max_length=3,
        default='SAR',
        help_text="Currency code (ISO 4217)"
    )

    # Source of price change
    SOURCE_CHOICES = (
        ('PO', 'Purchase Order'),
        ('MANUAL', 'Manual Adjustment'),
        ('IMPORT', 'Excel Import'),
        ('CONTRACT', 'Contract Agreement'),
    )
    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default='MANUAL'
    )

    reference_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="PO number, contract reference, etc."
    )

    notes = models.TextField(blank=True, default="")

    class Meta:
        db_table = "inventory_cutter_price_history"
        verbose_name = "Cutter Price History"
        verbose_name_plural = "Cutter Price Histories"
        ordering = ['-effective_date']
        unique_together = ['item', 'effective_date']
        indexes = [
            models.Index(fields=['item', '-effective_date'], name='ix_cph_item_date'),
        ]

    def __str__(self):
        return f"{self.item.sku} @ {self.unit_price} {self.currency} (effective {self.effective_date})"

    @classmethod
    def get_price_at_date(cls, item, as_of_date=None):
        """
        Get the effective price for a cutter at a specific date.

        Args:
            item: Item instance or ID
            as_of_date: Date to check (default: today)

        Returns:
            Decimal: Unit price, or None if no price history
        """
        if as_of_date is None:
            as_of_date = timezone.now().date()

        price_record = cls.objects.filter(
            item=item,
            effective_date__lte=as_of_date
        ).order_by('-effective_date').first()

        return price_record.unit_price if price_record else None


class CutterInventorySummary(models.Model):
    """
    Computed/materialized inventory summary per cutter per ownership category.

    Replaces Excel formulas with database-computed values:
    - Current balance by ownership category (ENO As New, ENO Ground, etc.)
    - Consumption metrics (6-month, 3-month, 2-month)
    - Safety stock calculation (tiered based on consumption)
    - BOM requirement (sum from active jobs)
    - On order (sum from open POs)
    - Forecast = current_balance - bom_requirement + on_order

    This table can be populated by:
    1. Database trigger on transaction insert/update
    2. Scheduled job (hourly/daily)
    3. Manual refresh via management command

    Note: For MVP, we'll use computed properties on Item model or a view.
    This model definition is for future materialization optimization.
    """

    item = models.ForeignKey(
        'Item',
        on_delete=models.CASCADE,
        related_name='inventory_summaries'
    )

    ownership_category = models.ForeignKey(
        CutterOwnershipCategory,
        on_delete=models.CASCADE,
        related_name='inventory_summaries'
    )

    # Current balance
    current_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Current stock quantity"
    )

    # Consumption metrics
    consumption_6month = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Total consumed in last 6 months (182 days)"
    )

    consumption_3month = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Total consumed in last 3 months (91 days)"
    )

    consumption_2month = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Estimated 2-month consumption (6mo / 3, rounded up)"
    )

    # Safety stock (calculated based on consumption_2month)
    safety_stock = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Tiered safety buffer based on consumption"
    )

    # BOM requirement
    bom_requirement = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Total quantity needed for bits in production"
    )

    # On order
    on_order = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Total quantity on open purchase orders"
    )

    # Forecast
    forecast = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Projected balance: current - BOM + on_order"
    )

    # Status
    STATUS_CHOICES = (
        ('OK', 'OK - Stock Adequate'),
        ('LOW', 'Low - Below Safety Stock'),
        ('SHORTAGE', 'Shortage - Below BOM Requirement'),
        ('EXCESS', 'Excess - High Inventory'),
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='OK'
    )

    # Last update
    last_calculated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "inventory_cutter_summary"
        verbose_name = "Cutter Inventory Summary"
        verbose_name_plural = "Cutter Inventory Summaries"
        unique_together = ['item', 'ownership_category']
        ordering = ['item__sku', 'ownership_category__consumption_priority']
        indexes = [
            models.Index(fields=['item', 'ownership_category'], name='ix_cis_item_cat'),
            models.Index(fields=['status'], name='ix_cis_status'),
        ]

    def __str__(self):
        return f"{self.item.sku} - {self.ownership_category.short_name}: {self.current_balance}"

    @staticmethod
    def calculate_safety_stock(consumption_2month):
        """
        Calculate tiered safety stock based on 2-month consumption.

        Excel formula logic:
        =IF(Q2<=1, 0,
           CEILING(
              IF(Q2>=300, Q2+10,
              IF(Q2>=200, Q2+5,
              IF(Q2>=100, Q2+5,
              IF(Q2>=50, Q2+2,
              IF(Q2>=20, Q2+2,
              IF(Q2>=10, Q2+2,
              IF(Q2>=5, Q2+2,
              Q2+1))))))), 5))

        Args:
            consumption_2month: Decimal - 2-month consumption quantity

        Returns:
            Decimal: Safety stock quantity
        """
        import math

        if consumption_2month <= 1:
            return Decimal('0.00')

        # Tiered buffer logic
        if consumption_2month >= 300:
            buffer = consumption_2month + 10
        elif consumption_2month >= 200:
            buffer = consumption_2month + 5
        elif consumption_2month >= 100:
            buffer = consumption_2month + 5
        elif consumption_2month >= 50:
            buffer = consumption_2month + 2
        elif consumption_2month >= 20:
            buffer = consumption_2month + 2
        elif consumption_2month >= 10:
            buffer = consumption_2month + 2
        elif consumption_2month >= 5:
            buffer = consumption_2month + 2
        else:
            buffer = consumption_2month + 1

        # Round up to nearest 5 (Excel CEILING function)
        return Decimal(math.ceil(float(buffer) / 5) * 5)

    def refresh(self):
        """
        Recalculate all computed fields for this summary record.

        This method queries InventoryTransaction to compute:
        - current_balance
        - consumption metrics
        - BOM requirement (from active job cards)
        - on_order (from open POs)
        - forecast
        - status
        """
        from .transactions import InventoryTransaction
        from django.db.models import Sum, Q
        from datetime import timedelta

        # Calculate current balance
        # Sum(additions) - Sum(subtractions) for this item + ownership category
        transactions = InventoryTransaction.objects.filter(
            item=self.item,
            ownership_category=self.ownership_category
        )

        additions = transactions.aggregate(total=Sum('quantity_in'))['total'] or Decimal('0.00')
        subtractions = transactions.aggregate(total=Sum('quantity_out'))['total'] or Decimal('0.00')
        self.current_balance = additions - subtractions

        # Calculate consumption metrics
        today = timezone.now().date()

        # 6-month consumption
        date_6mo_ago = today - timedelta(days=182)
        self.consumption_6month = transactions.filter(
            transaction_date__gte=date_6mo_ago,
            quantity_out__gt=0
        ).aggregate(total=Sum('quantity_out'))['total'] or Decimal('0.00')

        # 3-month consumption
        date_3mo_ago = today - timedelta(days=91)
        self.consumption_3month = transactions.filter(
            transaction_date__gte=date_3mo_ago,
            quantity_out__gt=0
        ).aggregate(total=Sum('quantity_out'))['total'] or Decimal('0.00')

        # 2-month consumption (6mo / 3, rounded up)
        self.consumption_2month = (self.consumption_6month / Decimal('3.0')).quantize(Decimal('0.01'))
        if self.consumption_2month > 0:
            import math
            self.consumption_2month = Decimal(math.ceil(float(self.consumption_2month)))

        # Calculate safety stock
        self.safety_stock = self.calculate_safety_stock(self.consumption_2month)

        # TODO: Calculate BOM requirement (sum from active job cards)
        # This requires querying JobCard -> JobCutterEvaluationDetail
        # For now, set to 0
        self.bom_requirement = Decimal('0.00')

        # TODO: Calculate on_order (sum from open POs)
        # This requires querying purchasing.PurchaseOrderLine
        # For now, set to 0
        self.on_order = Decimal('0.00')

        # Calculate forecast
        self.forecast = self.current_balance - self.bom_requirement + self.on_order

        # Determine status
        if self.forecast < self.bom_requirement:
            self.status = 'SHORTAGE'
        elif self.forecast < self.safety_stock:
            self.status = 'LOW'
        elif self.forecast > self.safety_stock * Decimal('2.0'):
            self.status = 'EXCESS'
        else:
            self.status = 'OK'

        self.save()

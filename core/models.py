"""
Core models for Floor Management System.

Includes:
- User Preferences (themes, table settings, UI customization)
- ERP Reference mapping (generic and specific)
- Cost Centers and organizational units
- Loss of Sale tracking
- Finance integration support
"""
from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MinValueValidator
from decimal import Decimal


# ============================================================================
# USER PREFERENCES
# ============================================================================

class UserPreference(models.Model):
    """
    Stores user-specific UI preferences including themes, font sizes,
    table density, and column visibility configurations.
    """

    THEME_CHOICES = [
        ('light', 'Light Mode'),
        ('dark', 'Dark Mode'),
        ('high_contrast', 'High Contrast'),
    ]

    FONT_SIZE_CHOICES = [
        ('small', 'Small'),
        ('normal', 'Normal'),
        ('large', 'Large'),
    ]

    TABLE_DENSITY_CHOICES = [
        ('compact', 'Compact'),
        ('normal', 'Normal'),
        ('relaxed', 'Relaxed'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='preferences',
        primary_key=True
    )

    # Theme and appearance
    theme = models.CharField(
        max_length=20,
        choices=THEME_CHOICES,
        default='light',
        help_text='UI theme preference'
    )

    font_size = models.CharField(
        max_length=10,
        choices=FONT_SIZE_CHOICES,
        default='normal',
        help_text='Text size preference'
    )

    table_density = models.CharField(
        max_length=10,
        choices=TABLE_DENSITY_CHOICES,
        default='normal',
        help_text='Table row spacing preference'
    )

    # Landing page preference
    default_landing_page = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text='URL name of preferred landing page after login'
    )

    # Per-view column visibility (JSON field)
    table_columns_config = models.JSONField(
        default=dict,
        blank=True,
        help_text='Stores column visibility preferences per table view'
    )

    # Sidebar preferences
    sidebar_collapsed = models.BooleanField(default=False)
    sidebar_sections = models.JSONField(
        default=dict,
        blank=True,
        help_text='Stores expanded/collapsed state of sidebar sections'
    )

    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    desktop_notifications = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'core_user_preference'
        verbose_name = 'User Preference'
        verbose_name_plural = 'User Preferences'

    def __str__(self):
        return f"Preferences for {self.user.username}"

    def get_table_columns(self, view_name):
        """Get column configuration for a specific view."""
        return self.table_columns_config.get(view_name, [])

    def set_table_columns(self, view_name, columns):
        """Set column configuration for a specific view."""
        self.table_columns_config[view_name] = columns
        self.save(update_fields=['table_columns_config', 'updated_at'])

    @classmethod
    def get_or_create_for_user(cls, user):
        """Get existing preferences or create with defaults."""
        preference, created = cls.objects.get_or_create(user=user)
        return preference


# ============================================================================
# COST CENTER / ORGANIZATIONAL UNITS
# ============================================================================

class CostCenter(models.Model):
    """
    Cost center for financial tracking and KPI analysis.
    Links to departments, employees, assets, and job cards.
    """

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('archived', 'Archived'),
    ]

    code = models.CharField(
        max_length=20,
        unique=True,
        help_text='Cost center code (e.g., CC-001, PROD-01)'
    )

    name = models.CharField(
        max_length=100,
        help_text='Cost center name'
    )

    description = models.TextField(
        blank=True,
        help_text='Description of cost center purpose'
    )

    # ERP integration
    erp_cost_center_code = models.CharField(
        max_length=50,
        blank=True,
        help_text='ERP system cost center code'
    )

    # Hierarchy
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        help_text='Parent cost center for hierarchical structure'
    )

    # Manager/responsible person
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_cost_centers',
        help_text='Manager responsible for this cost center'
    )

    # Budget information
    annual_budget = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Annual budget allocation'
    )

    currency = models.CharField(
        max_length=3,
        default='SAR',
        help_text='Currency code (ISO 4217)'
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='active'
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_cost_centers'
    )

    class Meta:
        db_table = 'core_cost_center'
        verbose_name = 'Cost Center'
        verbose_name_plural = 'Cost Centers'
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def full_path(self):
        """Get full hierarchical path."""
        if self.parent:
            return f"{self.parent.full_path} > {self.code}"
        return self.code


# ============================================================================
# ERP REFERENCE MAPPING
# ============================================================================

class ERPDocumentType(models.Model):
    """
    Defines types of ERP documents that can be linked.
    """

    code = models.CharField(
        max_length=20,
        unique=True,
        help_text='Document type code (e.g., PR, PO, GRN, TO)'
    )

    name = models.CharField(
        max_length=100,
        help_text='Document type name'
    )

    description = models.TextField(
        blank=True
    )

    # ERP system info
    erp_system = models.CharField(
        max_length=50,
        default='Microsoft Dynamics',
        help_text='ERP system name'
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'core_erp_document_type'
        verbose_name = 'ERP Document Type'
        verbose_name_plural = 'ERP Document Types'
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"


class ERPReference(models.Model):
    """
    Generic ERP reference that can be attached to any internal object.
    Uses ContentType framework for polymorphic linking.
    """

    STATUS_CHOICES = [
        ('pending', 'Pending Sync'),
        ('synced', 'Synced'),
        ('error', 'Sync Error'),
        ('manual', 'Manual Entry'),
    ]

    # Generic foreign key to any model
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        help_text='Type of internal object'
    )

    object_id = models.BigIntegerField(
        help_text='ID of internal object'
    )

    content_object = GenericForeignKey('content_type', 'object_id')

    # ERP reference details
    document_type = models.ForeignKey(
        ERPDocumentType,
        on_delete=models.PROTECT,
        related_name='references',
        help_text='Type of ERP document'
    )

    erp_number = models.CharField(
        max_length=100,
        db_index=True,
        help_text='ERP document number'
    )

    erp_line_number = models.IntegerField(
        null=True,
        blank=True,
        help_text='Line number within ERP document (if applicable)'
    )

    # Additional ERP metadata
    erp_date = models.DateField(
        null=True,
        blank=True,
        help_text='Date of ERP document'
    )

    erp_status = models.CharField(
        max_length=50,
        blank=True,
        help_text='Status in ERP system'
    )

    erp_json_data = models.JSONField(
        default=dict,
        blank=True,
        help_text='Additional ERP metadata as JSON'
    )

    # Sync status
    sync_status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='manual'
    )

    last_synced = models.DateTimeField(
        null=True,
        blank=True
    )

    sync_error_message = models.TextField(
        blank=True
    )

    # Notes
    notes = models.TextField(
        blank=True,
        help_text='Additional notes about this reference'
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_erp_references'
    )

    class Meta:
        db_table = 'core_erp_reference'
        verbose_name = 'ERP Reference'
        verbose_name_plural = 'ERP References'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['erp_number']),
            models.Index(fields=['document_type', 'erp_number']),
        ]
        # Ensure unique ERP number per document type
        constraints = [
            models.UniqueConstraint(
                fields=['document_type', 'erp_number', 'erp_line_number'],
                name='unique_erp_reference'
            )
        ]

    def __str__(self):
        line = f"/{self.erp_line_number}" if self.erp_line_number else ""
        return f"{self.document_type.code}: {self.erp_number}{line}"


# ============================================================================
# LOSS OF SALE TRACKING
# ============================================================================

class LossOfSaleCause(models.Model):
    """
    Categorizes causes for loss of sale events.
    """

    CATEGORY_CHOICES = [
        ('stockout', 'Stock Out'),
        ('breakdown', 'Equipment Breakdown'),
        ('delay', 'Production Delay'),
        ('quality', 'Quality Issue'),
        ('logistics', 'Logistics Issue'),
        ('external', 'External Factor'),
        ('other', 'Other'),
    ]

    code = models.CharField(
        max_length=20,
        unique=True
    )

    name = models.CharField(
        max_length=100
    )

    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='other'
    )

    description = models.TextField(
        blank=True
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'core_loss_of_sale_cause'
        verbose_name = 'Loss of Sale Cause'
        verbose_name_plural = 'Loss of Sale Causes'
        ordering = ['category', 'code']

    def __str__(self):
        return f"{self.code} - {self.name}"


class LossOfSaleEvent(models.Model):
    """
    Records loss of sale incidents with estimated financial impact.
    """

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('reviewed', 'Reviewed'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    # Event identification
    reference_number = models.CharField(
        max_length=50,
        unique=True,
        help_text='Internal reference number for this event'
    )

    title = models.CharField(
        max_length=200,
        help_text='Brief description of the event'
    )

    # Cause and details
    cause = models.ForeignKey(
        LossOfSaleCause,
        on_delete=models.PROTECT,
        related_name='events'
    )

    description = models.TextField(
        help_text='Detailed description of what happened'
    )

    # Timing
    event_date = models.DateField(
        help_text='Date when the loss event occurred'
    )

    event_time = models.TimeField(
        null=True,
        blank=True,
        help_text='Time when the loss event occurred'
    )

    duration_hours = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Duration of the impact in hours'
    )

    # Financial impact
    estimated_loss_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Estimated financial loss in local currency'
    )

    currency = models.CharField(
        max_length=3,
        default='SAR'
    )

    calculation_method = models.TextField(
        blank=True,
        help_text='How the estimated loss was calculated'
    )

    # Linked objects (Generic FK for flexibility)
    # Can link to Job Card, Asset, Stock Item, etc.
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text='Type of related object'
    )

    object_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text='ID of related object'
    )

    related_object = GenericForeignKey('content_type', 'object_id')

    # Cost center affected
    cost_center = models.ForeignKey(
        CostCenter,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='loss_events'
    )

    # Affected customer/order (denormalized for reporting)
    affected_customer_name = models.CharField(
        max_length=200,
        blank=True
    )

    affected_order_number = models.CharField(
        max_length=100,
        blank=True
    )

    # Root cause analysis
    root_cause_analysis = models.TextField(
        blank=True,
        help_text='Root cause analysis results'
    )

    corrective_actions = models.TextField(
        blank=True,
        help_text='Corrective actions taken or planned'
    )

    preventive_measures = models.TextField(
        blank=True,
        help_text='Preventive measures to avoid recurrence'
    )

    # Status and workflow
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='draft'
    )

    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='reported_loss_events'
    )

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_loss_events'
    )

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_loss_events'
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'core_loss_of_sale_event'
        verbose_name = 'Loss of Sale Event'
        verbose_name_plural = 'Loss of Sale Events'
        ordering = ['-event_date', '-created_at']
        indexes = [
            models.Index(fields=['event_date']),
            models.Index(fields=['cause']),
            models.Index(fields=['status']),
            models.Index(fields=['cost_center']),
        ]

    def __str__(self):
        return f"{self.reference_number}: {self.title}"


# ============================================================================
# APPROVAL ROUTING
# ============================================================================

class ApprovalType(models.Model):
    """
    Defines types of approvals (PR, PO, Job Card, Maintenance, etc.)
    """

    code = models.CharField(
        max_length=20,
        unique=True
    )

    name = models.CharField(
        max_length=100
    )

    description = models.TextField(
        blank=True
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'core_approval_type'
        verbose_name = 'Approval Type'
        verbose_name_plural = 'Approval Types'
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"


class ApprovalAuthority(models.Model):
    """
    Defines who can approve what based on position, department, or specific user.
    """

    approval_type = models.ForeignKey(
        ApprovalType,
        on_delete=models.CASCADE,
        related_name='authorities'
    )

    # Can be linked to specific user, group, or position
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='approval_authorities',
        help_text='Specific user with approval authority'
    )

    # Or linked to a group
    group = models.ForeignKey(
        'auth.Group',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='approval_authorities',
        help_text='Group with approval authority'
    )

    # Or linked to HR Position (if HR module is available)
    position_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text='HR Position ID with approval authority'
    )

    # Approval limits
    min_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Minimum amount for this approval authority'
    )

    max_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Maximum amount (null = unlimited)'
    )

    # Scope
    cost_center = models.ForeignKey(
        CostCenter,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approval_authorities',
        help_text='Limit authority to specific cost center'
    )

    # Priority (for routing)
    priority = models.IntegerField(
        default=0,
        help_text='Lower number = higher priority in routing'
    )

    is_active = models.BooleanField(default=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'core_approval_authority'
        verbose_name = 'Approval Authority'
        verbose_name_plural = 'Approval Authorities'
        ordering = ['approval_type', 'priority']

    def __str__(self):
        approver = self.user or self.group or f"Position {self.position_id}"
        return f"{self.approval_type.code}: {approver}"


# ============================================================================
# CURRENCY AND EXCHANGE RATES
# ============================================================================

class Currency(models.Model):
    """
    Currency master data.
    """

    code = models.CharField(
        max_length=3,
        unique=True,
        primary_key=True,
        help_text='ISO 4217 currency code'
    )

    name = models.CharField(
        max_length=50
    )

    symbol = models.CharField(
        max_length=10
    )

    decimal_places = models.IntegerField(
        default=2
    )

    is_base_currency = models.BooleanField(
        default=False,
        help_text='Is this the base/home currency'
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'core_currency'
        verbose_name = 'Currency'
        verbose_name_plural = 'Currencies'
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"


class ExchangeRate(models.Model):
    """
    Exchange rates for currency conversion.
    """

    from_currency = models.ForeignKey(
        Currency,
        on_delete=models.CASCADE,
        related_name='rates_from'
    )

    to_currency = models.ForeignKey(
        Currency,
        on_delete=models.CASCADE,
        related_name='rates_to'
    )

    rate = models.DecimalField(
        max_digits=18,
        decimal_places=8
    )

    effective_date = models.DateField()

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        db_table = 'core_exchange_rate'
        verbose_name = 'Exchange Rate'
        verbose_name_plural = 'Exchange Rates'
        ordering = ['-effective_date']
        unique_together = ['from_currency', 'to_currency', 'effective_date']

    def __str__(self):
        return f"{self.from_currency} to {self.to_currency}: {self.rate} ({self.effective_date})"


# ============================================================================
# NOTIFICATIONS AND ACTIVITY LOGGING
# ============================================================================

class Notification(models.Model):
    """
    User notifications for important events, approvals, tasks, etc.

    Supports:
    - Multiple notification types (info, success, warning, error, task, approval, system)
    - Priority levels (low, normal, high, urgent)
    - Related object linking via GenericForeignKey
    - Action URLs for quick navigation
    - Read/Unread tracking
    - Expiration dates
    """

    NOTIFICATION_TYPES = [
        ('INFO', 'Information'),
        ('SUCCESS', 'Success'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('TASK', 'Task'),
        ('APPROVAL', 'Approval Required'),
        ('SYSTEM', 'System'),
    ]

    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('NORMAL', 'Normal'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]

    # Recipient
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        help_text='User who receives this notification'
    )

    # Notification details
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        default='INFO',
        help_text='Type of notification'
    )

    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='NORMAL',
        help_text='Notification priority'
    )

    title = models.CharField(
        max_length=200,
        help_text='Notification title'
    )

    message = models.TextField(
        help_text='Notification message'
    )

    # Related object (optional)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text='Type of related object'
    )

    object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='ID of related object'
    )

    content_object = GenericForeignKey('content_type', 'object_id')

    # Action URL (optional)
    action_url = models.CharField(
        max_length=500,
        blank=True,
        default='',
        help_text='URL for the primary action'
    )

    action_text = models.CharField(
        max_length=50,
        blank=True,
        default='View',
        help_text='Text for the action button'
    )

    # Status
    is_read = models.BooleanField(
        default=False,
        help_text='Whether user has read this notification'
    )

    read_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When notification was read'
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)

    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When notification expires (optional)'
    )

    # Sender (optional)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications_sent',
        help_text='User who created this notification'
    )

    class Meta:
        db_table = 'core_notification'
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', '-created_at']),
            models.Index(fields=['user', 'notification_type']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.title} - {self.user.username}"

    def mark_as_read(self):
        """Mark notification as read."""
        from django.utils import timezone
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])

    def mark_as_unread(self):
        """Mark notification as unread."""
        if self.is_read:
            self.is_read = False
            self.read_at = None
            self.save(update_fields=['is_read', 'read_at'])

    def get_icon(self):
        """Get Bootstrap icon class for notification type."""
        icons = {
            'INFO': 'bi-info-circle-fill',
            'SUCCESS': 'bi-check-circle-fill',
            'WARNING': 'bi-exclamation-triangle-fill',
            'ERROR': 'bi-x-circle-fill',
            'TASK': 'bi-clipboard-check',
            'APPROVAL': 'bi-hand-thumbs-up',
            'SYSTEM': 'bi-gear-fill',
        }
        return icons.get(self.notification_type, 'bi-bell-fill')


class ActivityLog(models.Model):
    """
    Activity logging for audit trail across all modules.

    Tracks:
    - CRUD operations
    - Status changes
    - Important business events
    - User actions
    """

    ACTION_CHOICES = [
        ('CREATE', 'Created'),
        ('UPDATE', 'Updated'),
        ('DELETE', 'Deleted'),
        ('VIEW', 'Viewed'),
        ('EXPORT', 'Exported'),
        ('IMPORT', 'Imported'),
        ('APPROVE', 'Approved'),
        ('REJECT', 'Rejected'),
        ('SUBMIT', 'Submitted'),
        ('CANCEL', 'Cancelled'),
        ('COMPLETE', 'Completed'),
        ('ASSIGN', 'Assigned'),
        ('COMMENT', 'Commented'),
        ('OTHER', 'Other'),
    ]

    # Actor
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activity_logs',
        help_text='User who performed the action'
    )

    # Action details
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        help_text='Type of action performed'
    )

    description = models.TextField(
        help_text='Description of the action'
    )

    # Related object
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text='Type of object affected'
    )

    object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='ID of object affected'
    )

    content_object = GenericForeignKey('content_type', 'object_id')

    # Optional extra data
    extra_data = models.JSONField(
        default=dict,
        blank=True,
        help_text='Additional context data (changes, metadata, etc.)'
    )

    # IP address and session info
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text='IP address of the user'
    )

    user_agent = models.TextField(
        blank=True,
        default='',
        help_text='Browser user agent string'
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'core_activity_log'
        verbose_name = 'Activity Log'
        verbose_name_plural = 'Activity Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['action', '-created_at']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        username = self.user.username if self.user else 'System'
        return f"{username} {self.action} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

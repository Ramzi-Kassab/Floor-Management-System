"""
User Preferences Models

Models for managing user preferences, view customizations, and personalization settings.
"""

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from floor_app.mixins import AuditMixin


class UserPreference(AuditMixin):
    """
    Core user preferences for system-wide settings.
    """

    THEME_CHOICES = (
        ('LIGHT', 'Light Theme'),
        ('DARK', 'Dark Theme'),
        ('AUTO', 'Auto (System)'),
    )

    LANGUAGE_CHOICES = (
        ('en', 'English'),
        ('ar', 'Arabic'),
    )

    DENSITY_CHOICES = (
        ('COMPACT', 'Compact'),
        ('COMFORTABLE', 'Comfortable'),
        ('SPACIOUS', 'Spacious'),
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='floor_preferences',
        help_text="User who owns these preferences"
    )

    # Appearance Settings
    theme = models.CharField(
        max_length=10,
        choices=THEME_CHOICES,
        default='LIGHT',
        help_text="UI theme preference"
    )

    language = models.CharField(
        max_length=5,
        choices=LANGUAGE_CHOICES,
        default='en',
        help_text="Preferred language"
    )

    density = models.CharField(
        max_length=15,
        choices=DENSITY_CHOICES,
        default='COMFORTABLE',
        help_text="UI density/spacing"
    )

    # Dashboard Settings
    dashboard_layout = models.JSONField(
        default=dict,
        blank=True,
        help_text="Custom dashboard widget layout configuration"
    )

    default_dashboard = models.CharField(
        max_length=100,
        blank=True,
        help_text="Default dashboard to show on login"
    )

    # Notification Settings
    enable_email_notifications = models.BooleanField(
        default=True,
        help_text="Receive email notifications"
    )

    enable_push_notifications = models.BooleanField(
        default=True,
        help_text="Receive push notifications"
    )

    enable_sound = models.BooleanField(
        default=True,
        help_text="Play notification sounds"
    )

    notification_position = models.CharField(
        max_length=20,
        choices=(
            ('TOP_RIGHT', 'Top Right'),
            ('TOP_LEFT', 'Top Left'),
            ('BOTTOM_RIGHT', 'Bottom Right'),
            ('BOTTOM_LEFT', 'Bottom Left'),
        ),
        default='TOP_RIGHT',
        help_text="Position of notification popups"
    )

    # Table Settings
    default_page_size = models.IntegerField(
        default=25,
        validators=[MinValueValidator(5), MaxValueValidator(100)],
        help_text="Default number of rows per page in tables"
    )

    enable_row_numbers = models.BooleanField(
        default=True,
        help_text="Show row numbers in tables"
    )

    enable_zebra_striping = models.BooleanField(
        default=True,
        help_text="Alternate row colors in tables"
    )

    enable_hover_highlight = models.BooleanField(
        default=True,
        help_text="Highlight rows on hover"
    )

    # Date/Time Settings
    date_format = models.CharField(
        max_length=20,
        choices=(
            ('YYYY-MM-DD', 'YYYY-MM-DD (2025-01-18)'),
            ('DD-MM-YYYY', 'DD-MM-YYYY (18-01-2025)'),
            ('MM-DD-YYYY', 'MM-DD-YYYY (01-18-2025)'),
            ('DD/MM/YYYY', 'DD/MM/YYYY (18/01/2025)'),
            ('MM/DD/YYYY', 'MM/DD/YYYY (01/18/2025)'),
        ),
        default='YYYY-MM-DD',
        help_text="Preferred date format"
    )

    time_format = models.CharField(
        max_length=10,
        choices=(
            ('24H', '24 Hour (13:00)'),
            ('12H', '12 Hour (1:00 PM)'),
        ),
        default='24H',
        help_text="Preferred time format"
    )

    timezone = models.CharField(
        max_length=50,
        default='UTC',
        help_text="User's timezone"
    )

    # Other Settings
    auto_save_forms = models.BooleanField(
        default=True,
        help_text="Automatically save form drafts"
    )

    confirm_before_delete = models.BooleanField(
        default=True,
        help_text="Show confirmation dialog before deleting"
    )

    show_tooltips = models.BooleanField(
        default=True,
        help_text="Show helpful tooltips"
    )

    custom_settings = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional custom settings"
    )

    class Meta:
        db_table = 'user_preferences'
        verbose_name = 'User Preference'
        verbose_name_plural = 'User Preferences'
        ordering = ['user__username']

    def __str__(self):
        return f"Preferences for {self.user.username}"


class TableViewPreference(AuditMixin):
    """
    User preferences for specific table views.
    Allows customization of column visibility, order, filters, and sorting.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='table_preferences',
        help_text="User who owns these preferences"
    )

    table_identifier = models.CharField(
        max_length=100,
        help_text="Unique identifier for the table (e.g., 'employee_list', 'bom_grid')"
    )

    # Column Configuration
    visible_columns = models.JSONField(
        default=list,
        help_text="List of visible column identifiers in order"
    )

    column_widths = models.JSONField(
        default=dict,
        blank=True,
        help_text="Custom column widths {column_id: width_px}"
    )

    frozen_columns = models.JSONField(
        default=list,
        blank=True,
        help_text="List of frozen/pinned column identifiers"
    )

    # Sorting Configuration
    sort_by = models.JSONField(
        default=list,
        blank=True,
        help_text="Sorting configuration [{column: 'name', direction: 'asc'}]"
    )

    # Filter Configuration
    saved_filters = models.JSONField(
        default=dict,
        blank=True,
        help_text="Saved filter configurations"
    )

    active_filters = models.JSONField(
        default=dict,
        blank=True,
        help_text="Currently active filters"
    )

    # Pagination
    page_size = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(5), MaxValueValidator(100)],
        help_text="Custom page size for this table (overrides default)"
    )

    # Grouping
    group_by = models.JSONField(
        default=list,
        blank=True,
        help_text="Grouping configuration [column_ids]"
    )

    # Display Options
    show_totals = models.BooleanField(
        default=False,
        help_text="Show totals row"
    )

    show_filters_row = models.BooleanField(
        default=False,
        help_text="Show filters in header row"
    )

    enable_quick_filters = models.BooleanField(
        default=True,
        help_text="Enable quick filter chips"
    )

    # View Name
    view_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Custom name for this view configuration"
    )

    is_default = models.BooleanField(
        default=False,
        help_text="Use as default view for this table"
    )

    is_shared = models.BooleanField(
        default=False,
        help_text="Share this view with other users"
    )

    class Meta:
        db_table = 'table_view_preferences'
        verbose_name = 'Table View Preference'
        verbose_name_plural = 'Table View Preferences'
        unique_together = [['user', 'table_identifier', 'view_name']]
        ordering = ['user__username', 'table_identifier']

    def __str__(self):
        view_name = self.view_name or 'Default'
        return f"{self.user.username} - {self.table_identifier} ({view_name})"


class PageFeaturePreference(AuditMixin):
    """
    User preferences for page-level features and widgets.
    Controls visibility and configuration of page sections.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='page_preferences',
        help_text="User who owns these preferences"
    )

    page_identifier = models.CharField(
        max_length=100,
        help_text="Unique identifier for the page (e.g., 'dashboard', 'employee_detail')"
    )

    # Feature Visibility
    visible_features = models.JSONField(
        default=list,
        help_text="List of visible feature/widget identifiers"
    )

    hidden_features = models.JSONField(
        default=list,
        blank=True,
        help_text="List of hidden feature/widget identifiers"
    )

    # Feature Configuration
    feature_configs = models.JSONField(
        default=dict,
        blank=True,
        help_text="Configuration for each feature {feature_id: {config}}"
    )

    # Layout
    layout_config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Page layout configuration (grid positions, sizes, etc.)"
    )

    # Widget Specific Settings
    widget_settings = models.JSONField(
        default=dict,
        blank=True,
        help_text="Widget-specific settings {widget_id: {settings}}"
    )

    # Shortcuts and Quick Actions
    pinned_actions = models.JSONField(
        default=list,
        blank=True,
        help_text="Pinned quick actions for this page"
    )

    class Meta:
        db_table = 'page_feature_preferences'
        verbose_name = 'Page Feature Preference'
        verbose_name_plural = 'Page Feature Preferences'
        unique_together = [['user', 'page_identifier']]
        ordering = ['user__username', 'page_identifier']

    def __str__(self):
        return f"{self.user.username} - {self.page_identifier}"


class SavedView(AuditMixin):
    """
    Saved views that can be shared across users or teams.
    Allows users to save and share custom view configurations.
    """

    SCOPE_CHOICES = (
        ('PRIVATE', 'Private (Only Me)'),
        ('SHARED', 'Shared (Specific Users)'),
        ('TEAM', 'Team'),
        ('DEPARTMENT', 'Department'),
        ('PUBLIC', 'Public (All Users)'),
    )

    name = models.CharField(
        max_length=100,
        help_text="Name of the saved view"
    )

    description = models.TextField(
        blank=True,
        help_text="Description of what this view shows"
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_views',
        help_text="User who created this view"
    )

    scope = models.CharField(
        max_length=15,
        choices=SCOPE_CHOICES,
        default='PRIVATE',
        help_text="Sharing scope of this view"
    )

    # What this view applies to
    table_identifier = models.CharField(
        max_length=100,
        blank=True,
        help_text="Table this view applies to (if applicable)"
    )

    page_identifier = models.CharField(
        max_length=100,
        blank=True,
        help_text="Page this view applies to (if applicable)"
    )

    # View Configuration
    view_config = models.JSONField(
        default=dict,
        help_text="Complete view configuration"
    )

    # Sharing
    shared_with_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='shared_views',
        help_text="Specific users this view is shared with"
    )

    shared_with_teams = models.JSONField(
        default=list,
        blank=True,
        help_text="Team IDs this view is shared with"
    )

    shared_with_departments = models.JSONField(
        default=list,
        blank=True,
        help_text="Department IDs this view is shared with"
    )

    # Usage Statistics
    usage_count = models.IntegerField(
        default=0,
        help_text="Number of times this view has been used"
    )

    last_used = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last time this view was used"
    )

    # Favorites
    favorited_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='favorite_views',
        help_text="Users who have favorited this view"
    )

    is_system_view = models.BooleanField(
        default=False,
        help_text="System-provided view (cannot be deleted)"
    )

    class Meta:
        db_table = 'saved_views'
        verbose_name = 'Saved View'
        verbose_name_plural = 'Saved Views'
        ordering = ['-usage_count', 'name']

    def __str__(self):
        return f"{self.name} by {self.owner.username}"


class QuickFilter(AuditMixin):
    """
    Saved quick filters for tables and lists.
    Allows users to save commonly used filter combinations.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='quick_filters',
        help_text="User who owns this filter"
    )

    name = models.CharField(
        max_length=100,
        help_text="Name of the quick filter"
    )

    table_identifier = models.CharField(
        max_length=100,
        help_text="Table this filter applies to"
    )

    filter_config = models.JSONField(
        default=dict,
        help_text="Filter configuration"
    )

    icon = models.CharField(
        max_length=50,
        blank=True,
        help_text="Icon identifier for this filter"
    )

    color = models.CharField(
        max_length=20,
        blank=True,
        help_text="Color tag for this filter"
    )

    is_pinned = models.BooleanField(
        default=False,
        help_text="Pin to quick access bar"
    )

    usage_count = models.IntegerField(
        default=0,
        help_text="Number of times this filter has been used"
    )

    class Meta:
        db_table = 'quick_filters'
        verbose_name = 'Quick Filter'
        verbose_name_plural = 'Quick Filters'
        unique_together = [['user', 'table_identifier', 'name']]
        ordering = ['user__username', '-is_pinned', '-usage_count']

    def __str__(self):
        return f"{self.name} - {self.table_identifier}"


class UserShortcut(AuditMixin):
    """
    User-defined keyboard shortcuts and quick actions.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='shortcuts',
        help_text="User who owns this shortcut"
    )

    name = models.CharField(
        max_length=100,
        help_text="Name of the shortcut"
    )

    description = models.TextField(
        blank=True,
        help_text="Description of what this shortcut does"
    )

    # Shortcut Key
    key_combination = models.CharField(
        max_length=50,
        help_text="Keyboard shortcut (e.g., 'Ctrl+Shift+N')"
    )

    # Action
    action_type = models.CharField(
        max_length=50,
        choices=(
            ('NAVIGATE', 'Navigate to Page'),
            ('OPEN_MODAL', 'Open Modal/Dialog'),
            ('EXECUTE_FUNCTION', 'Execute Function'),
            ('FILTER', 'Apply Filter'),
            ('SEARCH', 'Quick Search'),
            ('CREATE', 'Create New Record'),
        ),
        help_text="Type of action to perform"
    )

    action_config = models.JSONField(
        default=dict,
        help_text="Configuration for the action"
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Enable/disable this shortcut"
    )

    scope = models.CharField(
        max_length=50,
        default='GLOBAL',
        help_text="Where this shortcut is active (GLOBAL, page_identifier, etc.)"
    )

    class Meta:
        db_table = 'user_shortcuts'
        verbose_name = 'User Shortcut'
        verbose_name_plural = 'User Shortcuts'
        unique_together = [['user', 'key_combination', 'scope']]
        ordering = ['user__username', 'name']

    def __str__(self):
        return f"{self.name} ({self.key_combination})"


class RecentActivity(AuditMixin):
    """
    Track user's recent activities for quick access.
    """

    ACTIVITY_TYPES = (
        ('VIEW', 'Viewed Record'),
        ('EDIT', 'Edited Record'),
        ('CREATE', 'Created Record'),
        ('DELETE', 'Deleted Record'),
        ('SEARCH', 'Search Query'),
        ('REPORT', 'Generated Report'),
        ('EXPORT', 'Exported Data'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recent_activities',
        help_text="User who performed the activity"
    )

    activity_type = models.CharField(
        max_length=20,
        choices=ACTIVITY_TYPES,
        help_text="Type of activity"
    )

    entity_type = models.CharField(
        max_length=100,
        help_text="Type of entity (model name, page, etc.)"
    )

    entity_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="ID of the entity (if applicable)"
    )

    entity_display = models.CharField(
        max_length=200,
        help_text="Display name/title of the entity"
    )

    url = models.CharField(
        max_length=500,
        blank=True,
        help_text="URL to access this entity"
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional metadata about the activity"
    )

    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text="When the activity occurred"
    )

    class Meta:
        db_table = 'recent_activities'
        verbose_name = 'Recent Activity'
        verbose_name_plural = 'Recent Activities'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['user', 'entity_type', '-timestamp']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.get_activity_type_display()} - {self.entity_display}"

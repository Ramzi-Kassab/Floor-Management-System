"""
User Preferences API Serializers

Serializers for user preferences REST API.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from floor_app.operations.user_preferences.models import (
    UserPreference,
    TableViewPreference,
    PageFeaturePreference,
    SavedView,
    QuickFilter,
    UserShortcut,
    RecentActivity
)

User = get_user_model()


# ============================================================================
# User Preference Serializers
# ============================================================================

class UserPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for user preferences."""

    class Meta:
        model = UserPreference
        fields = [
            'id', 'user', 'theme', 'language', 'density',
            'dashboard_layout', 'default_dashboard',
            'enable_email_notifications', 'enable_push_notifications',
            'enable_sound', 'notification_position',
            'default_page_size', 'enable_row_numbers',
            'enable_zebra_striping', 'enable_hover_highlight',
            'date_format', 'time_format', 'timezone',
            'auto_save_forms', 'confirm_before_delete', 'show_tooltips',
            'custom_settings', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class UserPreferenceUpdateSerializer(serializers.Serializer):
    """Serializer for updating user preferences."""

    theme = serializers.ChoiceField(
        choices=UserPreference.THEME_CHOICES,
        required=False
    )
    language = serializers.ChoiceField(
        choices=UserPreference.LANGUAGE_CHOICES,
        required=False
    )
    density = serializers.ChoiceField(
        choices=UserPreference.DENSITY_CHOICES,
        required=False
    )
    dashboard_layout = serializers.JSONField(required=False)
    default_dashboard = serializers.CharField(max_length=100, required=False, allow_blank=True)
    enable_email_notifications = serializers.BooleanField(required=False)
    enable_push_notifications = serializers.BooleanField(required=False)
    enable_sound = serializers.BooleanField(required=False)
    notification_position = serializers.CharField(max_length=20, required=False)
    default_page_size = serializers.IntegerField(min_value=5, max_value=100, required=False)
    enable_row_numbers = serializers.BooleanField(required=False)
    enable_zebra_striping = serializers.BooleanField(required=False)
    enable_hover_highlight = serializers.BooleanField(required=False)
    date_format = serializers.CharField(max_length=20, required=False)
    time_format = serializers.CharField(max_length=10, required=False)
    timezone = serializers.CharField(max_length=50, required=False)
    auto_save_forms = serializers.BooleanField(required=False)
    confirm_before_delete = serializers.BooleanField(required=False)
    show_tooltips = serializers.BooleanField(required=False)
    custom_settings = serializers.JSONField(required=False)


# ============================================================================
# Table View Preference Serializers
# ============================================================================

class TableViewPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for table view preferences."""

    class Meta:
        model = TableViewPreference
        fields = [
            'id', 'user', 'table_identifier', 'visible_columns',
            'column_widths', 'frozen_columns', 'sort_by',
            'saved_filters', 'active_filters', 'page_size',
            'group_by', 'show_totals', 'show_filters_row',
            'enable_quick_filters', 'view_name', 'is_default',
            'is_shared', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class TableViewPreferenceCreateSerializer(serializers.Serializer):
    """Serializer for creating table view preferences."""

    table_identifier = serializers.CharField(max_length=100)
    view_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    visible_columns = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )
    column_widths = serializers.JSONField(required=False, default=dict)
    frozen_columns = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )
    sort_by = serializers.JSONField(required=False, default=list)
    saved_filters = serializers.JSONField(required=False, default=dict)
    active_filters = serializers.JSONField(required=False, default=dict)
    page_size = serializers.IntegerField(min_value=5, max_value=100, required=False, allow_null=True)
    group_by = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )
    show_totals = serializers.BooleanField(default=False)
    show_filters_row = serializers.BooleanField(default=False)
    enable_quick_filters = serializers.BooleanField(default=True)
    is_default = serializers.BooleanField(default=False)
    is_shared = serializers.BooleanField(default=False)


class TableViewPreferenceListSerializer(serializers.Serializer):
    """Serializer for listing table views."""

    table_identifier = serializers.CharField(max_length=100)


# ============================================================================
# Page Feature Preference Serializers
# ============================================================================

class PageFeaturePreferenceSerializer(serializers.ModelSerializer):
    """Serializer for page feature preferences."""

    class Meta:
        model = PageFeaturePreference
        fields = [
            'id', 'user', 'page_identifier', 'visible_features',
            'hidden_features', 'feature_configs', 'layout_config',
            'widget_settings', 'pinned_actions', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class PageFeaturePreferenceSaveSerializer(serializers.Serializer):
    """Serializer for saving page feature preferences."""

    page_identifier = serializers.CharField(max_length=100)
    visible_features = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )
    hidden_features = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )
    feature_configs = serializers.JSONField(required=False, default=dict)
    layout_config = serializers.JSONField(required=False, default=dict)
    widget_settings = serializers.JSONField(required=False, default=dict)
    pinned_actions = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )


class ToggleFeatureSerializer(serializers.Serializer):
    """Serializer for toggling feature visibility."""

    page_identifier = serializers.CharField(max_length=100)
    feature_id = serializers.CharField(max_length=100)
    visible = serializers.BooleanField()


# ============================================================================
# Saved View Serializers
# ============================================================================

class SavedViewSerializer(serializers.ModelSerializer):
    """Serializer for saved views."""

    owner_username = serializers.CharField(source='owner.username', read_only=True)
    favorite_count = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()

    class Meta:
        model = SavedView
        fields = [
            'id', 'name', 'description', 'owner', 'owner_username',
            'scope', 'table_identifier', 'page_identifier',
            'view_config', 'usage_count', 'last_used',
            'favorite_count', 'is_favorited', 'is_system_view',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'owner', 'owner_username', 'usage_count',
            'last_used', 'favorite_count', 'is_favorited',
            'created_at', 'updated_at'
        ]

    def get_favorite_count(self, obj):
        return obj.favorited_by.count()

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.favorited_by.filter(id=request.user.id).exists()
        return False


class SavedViewCreateSerializer(serializers.Serializer):
    """Serializer for creating saved views."""

    name = serializers.CharField(max_length=100)
    description = serializers.CharField(required=False, allow_blank=True)
    scope = serializers.ChoiceField(
        choices=SavedView.SCOPE_CHOICES,
        default='PRIVATE'
    )
    table_identifier = serializers.CharField(max_length=100, required=False, allow_blank=True)
    page_identifier = serializers.CharField(max_length=100, required=False, allow_blank=True)
    view_config = serializers.JSONField()


class SavedViewUpdateSerializer(serializers.Serializer):
    """Serializer for updating saved views."""

    name = serializers.CharField(max_length=100, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    scope = serializers.ChoiceField(
        choices=SavedView.SCOPE_CHOICES,
        required=False
    )
    view_config = serializers.JSONField(required=False)


class SavedViewShareSerializer(serializers.Serializer):
    """Serializer for sharing saved views."""

    scope = serializers.ChoiceField(choices=SavedView.SCOPE_CHOICES)
    user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=list
    )
    team_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=list
    )
    department_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=list
    )


class SavedViewDuplicateSerializer(serializers.Serializer):
    """Serializer for duplicating views."""

    new_name = serializers.CharField(max_length=100, required=False, allow_blank=True)


# ============================================================================
# Quick Filter Serializers
# ============================================================================

class QuickFilterSerializer(serializers.ModelSerializer):
    """Serializer for quick filters."""

    class Meta:
        model = QuickFilter
        fields = [
            'id', 'user', 'name', 'table_identifier',
            'filter_config', 'icon', 'color', 'is_pinned',
            'usage_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'usage_count', 'created_at', 'updated_at']


class QuickFilterCreateSerializer(serializers.Serializer):
    """Serializer for creating quick filters."""

    name = serializers.CharField(max_length=100)
    table_identifier = serializers.CharField(max_length=100)
    filter_config = serializers.JSONField()
    icon = serializers.CharField(max_length=50, required=False, allow_blank=True)
    color = serializers.CharField(max_length=20, required=False, allow_blank=True)
    is_pinned = serializers.BooleanField(default=False)


# ============================================================================
# User Shortcut Serializers
# ============================================================================

class UserShortcutSerializer(serializers.ModelSerializer):
    """Serializer for user shortcuts."""

    class Meta:
        model = UserShortcut
        fields = [
            'id', 'user', 'name', 'description', 'key_combination',
            'action_type', 'action_config', 'is_active', 'scope',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class UserShortcutCreateSerializer(serializers.Serializer):
    """Serializer for creating shortcuts."""

    name = serializers.CharField(max_length=100)
    description = serializers.CharField(required=False, allow_blank=True)
    key_combination = serializers.CharField(max_length=50)
    action_type = serializers.CharField(max_length=50)
    action_config = serializers.JSONField()
    is_active = serializers.BooleanField(default=True)
    scope = serializers.CharField(max_length=50, default='GLOBAL')


# ============================================================================
# Recent Activity Serializers
# ============================================================================

class RecentActivitySerializer(serializers.ModelSerializer):
    """Serializer for recent activities."""

    activity_type_display = serializers.CharField(source='get_activity_type_display', read_only=True)

    class Meta:
        model = RecentActivity
        fields = [
            'id', 'user', 'activity_type', 'activity_type_display',
            'entity_type', 'entity_id', 'entity_display', 'url',
            'metadata', 'timestamp'
        ]
        read_only_fields = ['id', 'user', 'timestamp']


class RecordActivitySerializer(serializers.Serializer):
    """Serializer for recording activity."""

    activity_type = serializers.ChoiceField(choices=RecentActivity.ACTIVITY_TYPES)
    entity_type = serializers.CharField(max_length=100)
    entity_display = serializers.CharField(max_length=200)
    entity_id = serializers.CharField(max_length=100, required=False, allow_blank=True)
    url = serializers.CharField(max_length=500, required=False, allow_blank=True)
    metadata = serializers.JSONField(required=False, default=dict)


# ============================================================================
# Import/Export Serializers
# ============================================================================

class PreferenceExportSerializer(serializers.Serializer):
    """Serializer for exporting preferences."""

    include_table_views = serializers.BooleanField(default=True)
    include_page_features = serializers.BooleanField(default=True)
    include_quick_filters = serializers.BooleanField(default=True)
    include_shortcuts = serializers.BooleanField(default=True)


class PreferenceImportSerializer(serializers.Serializer):
    """Serializer for importing preferences."""

    data = serializers.JSONField()
    overwrite = serializers.BooleanField(default=False)


class ViewExportSerializer(serializers.Serializer):
    """Serializer for exporting a view."""

    view_id = serializers.IntegerField()


class ViewImportSerializer(serializers.Serializer):
    """Serializer for importing a view."""

    data = serializers.JSONField()
    new_name = serializers.CharField(max_length=100, required=False, allow_blank=True)

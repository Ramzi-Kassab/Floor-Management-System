"""
Preference Service

Service for managing user preferences and settings.
"""

from typing import Dict, Any, Optional, List
from django.contrib.auth import get_user_model
from django.utils import timezone
from floor_app.operations.user_preferences.models import (
    UserPreference,
    TableViewPreference,
    PageFeaturePreference,
    QuickFilter,
    UserShortcut,
    RecentActivity
)

User = get_user_model()


class PreferenceService:
    """Service for managing user preferences."""

    @classmethod
    def get_or_create_user_preferences(cls, user: User) -> UserPreference:
        """
        Get or create user preferences with defaults.

        Args:
            user: User instance

        Returns:
            UserPreference instance
        """
        preferences, created = UserPreference.objects.get_or_create(
            user=user,
            defaults={
                'theme': 'LIGHT',
                'language': 'en',
                'density': 'COMFORTABLE',
                'default_page_size': 25,
                'date_format': 'YYYY-MM-DD',
                'time_format': '24H',
                'timezone': 'UTC',
            }
        )
        return preferences

    @classmethod
    def update_user_preferences(cls, user: User, preferences_data: Dict[str, Any]) -> UserPreference:
        """
        Update user preferences.

        Args:
            user: User instance
            preferences_data: Dictionary of preference fields to update

        Returns:
            Updated UserPreference instance
        """
        preferences = cls.get_or_create_user_preferences(user)

        # Update only provided fields
        for field, value in preferences_data.items():
            if hasattr(preferences, field):
                setattr(preferences, field, value)

        preferences.save()
        return preferences

    @classmethod
    def get_table_view_preference(cls, user: User, table_identifier: str,
                                   view_name: str = '') -> Optional[TableViewPreference]:
        """
        Get table view preference for a specific table.

        Args:
            user: User instance
            table_identifier: Unique table identifier
            view_name: Optional view name (default view if empty)

        Returns:
            TableViewPreference instance or None
        """
        query = TableViewPreference.objects.filter(
            user=user,
            table_identifier=table_identifier
        )

        if view_name:
            query = query.filter(view_name=view_name)
        else:
            # Get default view
            query = query.filter(is_default=True)

        return query.first()

    @classmethod
    def save_table_view_preference(cls, user: User, table_identifier: str,
                                    config: Dict[str, Any],
                                    view_name: str = '',
                                    is_default: bool = False) -> TableViewPreference:
        """
        Save or update table view preference.

        Args:
            user: User instance
            table_identifier: Unique table identifier
            config: View configuration dictionary
            view_name: Optional view name
            is_default: Set as default view

        Returns:
            TableViewPreference instance
        """
        # If setting as default, unset other defaults
        if is_default:
            TableViewPreference.objects.filter(
                user=user,
                table_identifier=table_identifier,
                is_default=True
            ).update(is_default=False)

        # Create or update
        preference, created = TableViewPreference.objects.update_or_create(
            user=user,
            table_identifier=table_identifier,
            view_name=view_name,
            defaults={
                'visible_columns': config.get('visible_columns', []),
                'column_widths': config.get('column_widths', {}),
                'frozen_columns': config.get('frozen_columns', []),
                'sort_by': config.get('sort_by', []),
                'saved_filters': config.get('saved_filters', {}),
                'active_filters': config.get('active_filters', {}),
                'page_size': config.get('page_size'),
                'group_by': config.get('group_by', []),
                'show_totals': config.get('show_totals', False),
                'show_filters_row': config.get('show_filters_row', False),
                'enable_quick_filters': config.get('enable_quick_filters', True),
                'is_default': is_default,
                'is_shared': config.get('is_shared', False),
            }
        )

        return preference

    @classmethod
    def delete_table_view_preference(cls, user: User, table_identifier: str,
                                      view_name: str = '') -> bool:
        """
        Delete a table view preference.

        Args:
            user: User instance
            table_identifier: Unique table identifier
            view_name: View name to delete

        Returns:
            True if deleted, False otherwise
        """
        deleted_count, _ = TableViewPreference.objects.filter(
            user=user,
            table_identifier=table_identifier,
            view_name=view_name
        ).delete()

        return deleted_count > 0

    @classmethod
    def list_table_views(cls, user: User, table_identifier: str) -> List[TableViewPreference]:
        """
        List all saved views for a table.

        Args:
            user: User instance
            table_identifier: Unique table identifier

        Returns:
            List of TableViewPreference instances
        """
        return list(TableViewPreference.objects.filter(
            user=user,
            table_identifier=table_identifier
        ).order_by('-is_default', 'view_name'))

    @classmethod
    def get_page_feature_preference(cls, user: User, page_identifier: str) -> Optional[PageFeaturePreference]:
        """
        Get page feature preferences.

        Args:
            user: User instance
            page_identifier: Unique page identifier

        Returns:
            PageFeaturePreference instance or None
        """
        return PageFeaturePreference.objects.filter(
            user=user,
            page_identifier=page_identifier
        ).first()

    @classmethod
    def save_page_feature_preference(cls, user: User, page_identifier: str,
                                      config: Dict[str, Any]) -> PageFeaturePreference:
        """
        Save or update page feature preferences.

        Args:
            user: User instance
            page_identifier: Unique page identifier
            config: Page configuration dictionary

        Returns:
            PageFeaturePreference instance
        """
        preference, created = PageFeaturePreference.objects.update_or_create(
            user=user,
            page_identifier=page_identifier,
            defaults={
                'visible_features': config.get('visible_features', []),
                'hidden_features': config.get('hidden_features', []),
                'feature_configs': config.get('feature_configs', {}),
                'layout_config': config.get('layout_config', {}),
                'widget_settings': config.get('widget_settings', {}),
                'pinned_actions': config.get('pinned_actions', []),
            }
        )

        return preference

    @classmethod
    def toggle_feature_visibility(cls, user: User, page_identifier: str,
                                   feature_id: str, visible: bool) -> PageFeaturePreference:
        """
        Toggle visibility of a page feature.

        Args:
            user: User instance
            page_identifier: Unique page identifier
            feature_id: Feature identifier
            visible: True to show, False to hide

        Returns:
            Updated PageFeaturePreference instance
        """
        preference = cls.get_page_feature_preference(user, page_identifier)

        if not preference:
            preference = PageFeaturePreference.objects.create(
                user=user,
                page_identifier=page_identifier,
                visible_features=[],
                hidden_features=[]
            )

        if visible:
            # Add to visible, remove from hidden
            if feature_id not in preference.visible_features:
                preference.visible_features.append(feature_id)
            if feature_id in preference.hidden_features:
                preference.hidden_features.remove(feature_id)
        else:
            # Add to hidden, remove from visible
            if feature_id not in preference.hidden_features:
                preference.hidden_features.append(feature_id)
            if feature_id in preference.visible_features:
                preference.visible_features.remove(feature_id)

        preference.save()
        return preference

    @classmethod
    def create_quick_filter(cls, user: User, table_identifier: str,
                            name: str, filter_config: Dict[str, Any],
                            icon: str = '', color: str = '',
                            is_pinned: bool = False) -> QuickFilter:
        """
        Create a quick filter.

        Args:
            user: User instance
            table_identifier: Table identifier
            name: Filter name
            filter_config: Filter configuration
            icon: Optional icon
            color: Optional color
            is_pinned: Pin to quick access

        Returns:
            QuickFilter instance
        """
        quick_filter = QuickFilter.objects.create(
            user=user,
            table_identifier=table_identifier,
            name=name,
            filter_config=filter_config,
            icon=icon,
            color=color,
            is_pinned=is_pinned
        )

        return quick_filter

    @classmethod
    def apply_quick_filter(cls, user: User, filter_id: int) -> QuickFilter:
        """
        Apply a quick filter (increments usage count).

        Args:
            user: User instance
            filter_id: QuickFilter ID

        Returns:
            QuickFilter instance
        """
        quick_filter = QuickFilter.objects.get(id=filter_id, user=user)
        quick_filter.usage_count += 1
        quick_filter.save()

        return quick_filter

    @classmethod
    def list_quick_filters(cls, user: User, table_identifier: str = None,
                           pinned_only: bool = False) -> List[QuickFilter]:
        """
        List quick filters.

        Args:
            user: User instance
            table_identifier: Optional table filter
            pinned_only: Show only pinned filters

        Returns:
            List of QuickFilter instances
        """
        query = QuickFilter.objects.filter(user=user)

        if table_identifier:
            query = query.filter(table_identifier=table_identifier)

        if pinned_only:
            query = query.filter(is_pinned=True)

        return list(query.order_by('-is_pinned', '-usage_count'))

    @classmethod
    def create_shortcut(cls, user: User, name: str, key_combination: str,
                        action_type: str, action_config: Dict[str, Any],
                        description: str = '', scope: str = 'GLOBAL') -> UserShortcut:
        """
        Create a keyboard shortcut.

        Args:
            user: User instance
            name: Shortcut name
            key_combination: Key combination (e.g., 'Ctrl+Shift+N')
            action_type: Type of action
            action_config: Action configuration
            description: Optional description
            scope: Shortcut scope

        Returns:
            UserShortcut instance
        """
        shortcut = UserShortcut.objects.create(
            user=user,
            name=name,
            key_combination=key_combination,
            action_type=action_type,
            action_config=action_config,
            description=description,
            scope=scope
        )

        return shortcut

    @classmethod
    def list_shortcuts(cls, user: User, scope: str = None,
                       active_only: bool = True) -> List[UserShortcut]:
        """
        List user shortcuts.

        Args:
            user: User instance
            scope: Optional scope filter
            active_only: Show only active shortcuts

        Returns:
            List of UserShortcut instances
        """
        query = UserShortcut.objects.filter(user=user)

        if scope:
            query = query.filter(scope=scope)

        if active_only:
            query = query.filter(is_active=True)

        return list(query.order_by('name'))

    @classmethod
    def record_activity(cls, user: User, activity_type: str, entity_type: str,
                        entity_display: str, entity_id: str = '', url: str = '',
                        metadata: Dict[str, Any] = None) -> RecentActivity:
        """
        Record user activity for recent history.

        Args:
            user: User instance
            activity_type: Type of activity
            entity_type: Type of entity
            entity_display: Display name
            entity_id: Optional entity ID
            url: Optional URL
            metadata: Optional metadata

        Returns:
            RecentActivity instance
        """
        activity = RecentActivity.objects.create(
            user=user,
            activity_type=activity_type,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_display=entity_display,
            url=url,
            metadata=metadata or {}
        )

        # Keep only last 100 activities per user
        cls.cleanup_old_activities(user, keep_count=100)

        return activity

    @classmethod
    def cleanup_old_activities(cls, user: User, keep_count: int = 100):
        """
        Clean up old activities, keeping only the most recent.

        Args:
            user: User instance
            keep_count: Number of activities to keep
        """
        activities = RecentActivity.objects.filter(user=user).order_by('-timestamp')

        # Get IDs to keep
        keep_ids = list(activities.values_list('id', flat=True)[:keep_count])

        # Delete older ones
        RecentActivity.objects.filter(user=user).exclude(id__in=keep_ids).delete()

    @classmethod
    def get_recent_activities(cls, user: User, activity_type: str = None,
                              entity_type: str = None, limit: int = 20) -> List[RecentActivity]:
        """
        Get user's recent activities.

        Args:
            user: User instance
            activity_type: Optional activity type filter
            entity_type: Optional entity type filter
            limit: Maximum number of activities

        Returns:
            List of RecentActivity instances
        """
        query = RecentActivity.objects.filter(user=user)

        if activity_type:
            query = query.filter(activity_type=activity_type)

        if entity_type:
            query = query.filter(entity_type=entity_type)

        return list(query.order_by('-timestamp')[:limit])

    @classmethod
    def export_preferences(cls, user: User) -> Dict[str, Any]:
        """
        Export all user preferences for backup/migration.

        Args:
            user: User instance

        Returns:
            Dictionary with all preferences
        """
        preferences = cls.get_or_create_user_preferences(user)

        export_data = {
            'user_preferences': {
                'theme': preferences.theme,
                'language': preferences.language,
                'density': preferences.density,
                'dashboard_layout': preferences.dashboard_layout,
                'default_dashboard': preferences.default_dashboard,
                'enable_email_notifications': preferences.enable_email_notifications,
                'enable_push_notifications': preferences.enable_push_notifications,
                'enable_sound': preferences.enable_sound,
                'notification_position': preferences.notification_position,
                'default_page_size': preferences.default_page_size,
                'enable_row_numbers': preferences.enable_row_numbers,
                'enable_zebra_striping': preferences.enable_zebra_striping,
                'enable_hover_highlight': preferences.enable_hover_highlight,
                'date_format': preferences.date_format,
                'time_format': preferences.time_format,
                'timezone': preferences.timezone,
                'auto_save_forms': preferences.auto_save_forms,
                'confirm_before_delete': preferences.confirm_before_delete,
                'show_tooltips': preferences.show_tooltips,
                'custom_settings': preferences.custom_settings,
            },
            'table_views': [],
            'page_features': [],
            'quick_filters': [],
            'shortcuts': [],
        }

        # Export table views
        for table_view in TableViewPreference.objects.filter(user=user):
            export_data['table_views'].append({
                'table_identifier': table_view.table_identifier,
                'view_name': table_view.view_name,
                'visible_columns': table_view.visible_columns,
                'column_widths': table_view.column_widths,
                'frozen_columns': table_view.frozen_columns,
                'sort_by': table_view.sort_by,
                'saved_filters': table_view.saved_filters,
                'active_filters': table_view.active_filters,
                'page_size': table_view.page_size,
                'group_by': table_view.group_by,
                'show_totals': table_view.show_totals,
                'show_filters_row': table_view.show_filters_row,
                'enable_quick_filters': table_view.enable_quick_filters,
                'is_default': table_view.is_default,
            })

        # Export page features
        for page_pref in PageFeaturePreference.objects.filter(user=user):
            export_data['page_features'].append({
                'page_identifier': page_pref.page_identifier,
                'visible_features': page_pref.visible_features,
                'hidden_features': page_pref.hidden_features,
                'feature_configs': page_pref.feature_configs,
                'layout_config': page_pref.layout_config,
                'widget_settings': page_pref.widget_settings,
                'pinned_actions': page_pref.pinned_actions,
            })

        # Export quick filters
        for qf in QuickFilter.objects.filter(user=user):
            export_data['quick_filters'].append({
                'name': qf.name,
                'table_identifier': qf.table_identifier,
                'filter_config': qf.filter_config,
                'icon': qf.icon,
                'color': qf.color,
                'is_pinned': qf.is_pinned,
            })

        # Export shortcuts
        for shortcut in UserShortcut.objects.filter(user=user):
            export_data['shortcuts'].append({
                'name': shortcut.name,
                'description': shortcut.description,
                'key_combination': shortcut.key_combination,
                'action_type': shortcut.action_type,
                'action_config': shortcut.action_config,
                'scope': shortcut.scope,
                'is_active': shortcut.is_active,
            })

        return export_data

    @classmethod
    def import_preferences(cls, user: User, import_data: Dict[str, Any],
                           overwrite: bool = False):
        """
        Import preferences from exported data.

        Args:
            user: User instance
            import_data: Exported preferences data
            overwrite: If True, overwrite existing preferences
        """
        # Import user preferences
        if 'user_preferences' in import_data:
            cls.update_user_preferences(user, import_data['user_preferences'])

        # Import table views
        if 'table_views' in import_data:
            for view_data in import_data['table_views']:
                table_id = view_data.pop('table_identifier')
                view_name = view_data.pop('view_name', '')

                # Check if exists
                exists = TableViewPreference.objects.filter(
                    user=user,
                    table_identifier=table_id,
                    view_name=view_name
                ).exists()

                if not exists or overwrite:
                    cls.save_table_view_preference(
                        user=user,
                        table_identifier=table_id,
                        view_name=view_name,
                        config=view_data
                    )

        # Import page features
        if 'page_features' in import_data:
            for page_data in import_data['page_features']:
                page_id = page_data.pop('page_identifier')
                cls.save_page_feature_preference(
                    user=user,
                    page_identifier=page_id,
                    config=page_data
                )

        # Import quick filters
        if 'quick_filters' in import_data:
            for filter_data in import_data['quick_filters']:
                # Check if exists
                exists = QuickFilter.objects.filter(
                    user=user,
                    table_identifier=filter_data['table_identifier'],
                    name=filter_data['name']
                ).exists()

                if not exists or overwrite:
                    QuickFilter.objects.update_or_create(
                        user=user,
                        table_identifier=filter_data['table_identifier'],
                        name=filter_data['name'],
                        defaults={
                            'filter_config': filter_data['filter_config'],
                            'icon': filter_data.get('icon', ''),
                            'color': filter_data.get('color', ''),
                            'is_pinned': filter_data.get('is_pinned', False),
                        }
                    )

        # Import shortcuts
        if 'shortcuts' in import_data:
            for shortcut_data in import_data['shortcuts']:
                # Check if exists
                exists = UserShortcut.objects.filter(
                    user=user,
                    key_combination=shortcut_data['key_combination'],
                    scope=shortcut_data.get('scope', 'GLOBAL')
                ).exists()

                if not exists or overwrite:
                    UserShortcut.objects.update_or_create(
                        user=user,
                        key_combination=shortcut_data['key_combination'],
                        scope=shortcut_data.get('scope', 'GLOBAL'),
                        defaults={
                            'name': shortcut_data['name'],
                            'description': shortcut_data.get('description', ''),
                            'action_type': shortcut_data['action_type'],
                            'action_config': shortcut_data['action_config'],
                            'is_active': shortcut_data.get('is_active', True),
                        }
                    )

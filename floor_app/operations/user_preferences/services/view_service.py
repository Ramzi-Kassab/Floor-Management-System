"""
View Service

Service for managing saved views and shared configurations.
"""

from typing import Dict, Any, Optional, List
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Q, F
from floor_app.operations.user_preferences.models import SavedView

User = get_user_model()


class ViewService:
    """Service for managing saved views."""

    @classmethod
    def create_view(cls, owner: User, name: str, view_config: Dict[str, Any],
                    scope: str = 'PRIVATE', description: str = '',
                    table_identifier: str = '', page_identifier: str = '') -> SavedView:
        """
        Create a new saved view.

        Args:
            owner: User who creates the view
            name: View name
            view_config: View configuration dictionary
            scope: Sharing scope
            description: Optional description
            table_identifier: Optional table identifier
            page_identifier: Optional page identifier

        Returns:
            SavedView instance
        """
        view = SavedView.objects.create(
            owner=owner,
            name=name,
            description=description,
            scope=scope,
            table_identifier=table_identifier,
            page_identifier=page_identifier,
            view_config=view_config
        )

        return view

    @classmethod
    def update_view(cls, view_id: int, user: User, **updates) -> SavedView:
        """
        Update a saved view.

        Args:
            view_id: SavedView ID
            user: User performing the update (must be owner or admin)
            **updates: Fields to update

        Returns:
            Updated SavedView instance

        Raises:
            PermissionError: If user is not owner
        """
        view = SavedView.objects.get(id=view_id)

        # Check permission
        if view.owner != user and not user.is_staff:
            raise PermissionError("Only the owner can update this view")

        # Update fields
        for field, value in updates.items():
            if hasattr(view, field):
                setattr(view, field, value)

        view.save()
        return view

    @classmethod
    def delete_view(cls, view_id: int, user: User) -> bool:
        """
        Delete a saved view.

        Args:
            view_id: SavedView ID
            user: User performing the deletion (must be owner or admin)

        Returns:
            True if deleted

        Raises:
            PermissionError: If user is not owner or view is system view
        """
        view = SavedView.objects.get(id=view_id)

        # Check if system view
        if view.is_system_view:
            raise PermissionError("Cannot delete system views")

        # Check permission
        if view.owner != user and not user.is_staff:
            raise PermissionError("Only the owner can delete this view")

        view.delete()
        return True

    @classmethod
    def get_available_views(cls, user: User, table_identifier: str = None,
                            page_identifier: str = None) -> List[SavedView]:
        """
        Get all views available to a user (owned, shared, or public).

        Args:
            user: User instance
            table_identifier: Optional table filter
            page_identifier: Optional page filter

        Returns:
            List of SavedView instances
        """
        # Build query for views accessible to user
        query = Q(owner=user) | Q(scope='PUBLIC')

        # Add shared views
        query |= Q(scope='SHARED', shared_with_users=user)

        # TODO: Add team/department filtering when those models exist
        # query |= Q(scope='TEAM', shared_with_teams__contains=user.team_id)
        # query |= Q(scope='DEPARTMENT', shared_with_departments__contains=user.department_id)

        views_query = SavedView.objects.filter(query).distinct()

        # Apply filters
        if table_identifier:
            views_query = views_query.filter(table_identifier=table_identifier)

        if page_identifier:
            views_query = views_query.filter(page_identifier=page_identifier)

        return list(views_query.order_by('-usage_count', 'name'))

    @classmethod
    def apply_view(cls, view_id: int, user: User) -> SavedView:
        """
        Apply a saved view (increments usage count and updates last_used).

        Args:
            view_id: SavedView ID
            user: User applying the view

        Returns:
            SavedView instance
        """
        view = SavedView.objects.get(id=view_id)

        # Check access
        if not cls._user_can_access_view(user, view):
            raise PermissionError("You don't have access to this view")

        # Update usage statistics
        view.usage_count = F('usage_count') + 1
        view.last_used = timezone.now()
        view.save()

        # Refresh from DB to get actual values
        view.refresh_from_db()

        return view

    @classmethod
    def share_view(cls, view_id: int, owner: User, scope: str,
                   user_ids: List[int] = None, team_ids: List[int] = None,
                   department_ids: List[int] = None) -> SavedView:
        """
        Share a view with users, teams, or departments.

        Args:
            view_id: SavedView ID
            owner: View owner
            scope: New scope (SHARED, TEAM, DEPARTMENT, PUBLIC)
            user_ids: List of user IDs to share with
            team_ids: List of team IDs to share with
            department_ids: List of department IDs to share with

        Returns:
            Updated SavedView instance

        Raises:
            PermissionError: If not owner
        """
        view = SavedView.objects.get(id=view_id)

        # Check permission
        if view.owner != owner and not owner.is_staff:
            raise PermissionError("Only the owner can share this view")

        # Update scope
        view.scope = scope

        # Update sharing lists
        if user_ids is not None:
            view.shared_with_users.set(User.objects.filter(id__in=user_ids))

        if team_ids is not None:
            view.shared_with_teams = team_ids

        if department_ids is not None:
            view.shared_with_departments = department_ids

        view.save()
        return view

    @classmethod
    def toggle_favorite(cls, view_id: int, user: User) -> tuple[SavedView, bool]:
        """
        Toggle a view as favorite for a user.

        Args:
            view_id: SavedView ID
            user: User instance

        Returns:
            Tuple of (SavedView instance, is_favorited)
        """
        view = SavedView.objects.get(id=view_id)

        # Check access
        if not cls._user_can_access_view(user, view):
            raise PermissionError("You don't have access to this view")

        if user in view.favorited_by.all():
            view.favorited_by.remove(user)
            is_favorited = False
        else:
            view.favorited_by.add(user)
            is_favorited = True

        return view, is_favorited

    @classmethod
    def get_favorite_views(cls, user: User) -> List[SavedView]:
        """
        Get user's favorite views.

        Args:
            user: User instance

        Returns:
            List of favorited SavedView instances
        """
        return list(SavedView.objects.filter(
            favorited_by=user
        ).order_by('name'))

    @classmethod
    def duplicate_view(cls, view_id: int, new_owner: User,
                       new_name: str = None) -> SavedView:
        """
        Duplicate a view for a new owner.

        Args:
            view_id: SavedView ID to duplicate
            new_owner: User who will own the copy
            new_name: Optional new name (defaults to "Copy of [original]")

        Returns:
            New SavedView instance
        """
        original = SavedView.objects.get(id=view_id)

        # Check access
        if not cls._user_can_access_view(new_owner, original):
            raise PermissionError("You don't have access to this view")

        # Create copy
        name = new_name or f"Copy of {original.name}"

        duplicate = SavedView.objects.create(
            owner=new_owner,
            name=name,
            description=original.description,
            scope='PRIVATE',  # Always create as private
            table_identifier=original.table_identifier,
            page_identifier=original.page_identifier,
            view_config=original.view_config.copy(),
            is_system_view=False
        )

        return duplicate

    @classmethod
    def get_popular_views(cls, table_identifier: str = None,
                          page_identifier: str = None,
                          limit: int = 10) -> List[SavedView]:
        """
        Get most popular public views.

        Args:
            table_identifier: Optional table filter
            page_identifier: Optional page filter
            limit: Number of views to return

        Returns:
            List of popular SavedView instances
        """
        query = SavedView.objects.filter(scope='PUBLIC')

        if table_identifier:
            query = query.filter(table_identifier=table_identifier)

        if page_identifier:
            query = query.filter(page_identifier=page_identifier)

        return list(query.order_by('-usage_count')[:limit])

    @classmethod
    def search_views(cls, user: User, search_query: str,
                     table_identifier: str = None,
                     page_identifier: str = None) -> List[SavedView]:
        """
        Search for views by name or description.

        Args:
            user: User instance
            search_query: Search string
            table_identifier: Optional table filter
            page_identifier: Optional page filter

        Returns:
            List of matching SavedView instances
        """
        # Get available views
        available_query = Q(owner=user) | Q(scope='PUBLIC')
        available_query |= Q(scope='SHARED', shared_with_users=user)

        query = SavedView.objects.filter(available_query).distinct()

        # Apply search
        query = query.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )

        # Apply filters
        if table_identifier:
            query = query.filter(table_identifier=table_identifier)

        if page_identifier:
            query = query.filter(page_identifier=page_identifier)

        return list(query.order_by('-usage_count', 'name'))

    @classmethod
    def get_view_statistics(cls, view_id: int) -> Dict[str, Any]:
        """
        Get usage statistics for a view.

        Args:
            view_id: SavedView ID

        Returns:
            Dictionary with statistics
        """
        view = SavedView.objects.get(id=view_id)

        stats = {
            'usage_count': view.usage_count,
            'last_used': view.last_used,
            'favorite_count': view.favorited_by.count(),
            'shared_with_count': 0,
            'created_at': view.created_at,
            'owner': view.owner.username,
            'scope': view.scope,
        }

        # Count shared users
        if view.scope == 'SHARED':
            stats['shared_with_count'] = view.shared_with_users.count()
        elif view.scope == 'TEAM':
            stats['shared_with_count'] = len(view.shared_with_teams)
        elif view.scope == 'DEPARTMENT':
            stats['shared_with_count'] = len(view.shared_with_departments)

        return stats

    @classmethod
    def _user_can_access_view(cls, user: User, view: SavedView) -> bool:
        """
        Check if a user can access a view.

        Args:
            user: User instance
            view: SavedView instance

        Returns:
            True if user has access
        """
        # Owner always has access
        if view.owner == user:
            return True

        # Public views are accessible to all
        if view.scope == 'PUBLIC':
            return True

        # Shared with specific users
        if view.scope == 'SHARED' and user in view.shared_with_users.all():
            return True

        # TODO: Check team/department access when those models exist
        # if view.scope == 'TEAM' and user.team_id in view.shared_with_teams:
        #     return True
        # if view.scope == 'DEPARTMENT' and user.department_id in view.shared_with_departments:
        #     return True

        return False

    @classmethod
    def merge_view_config(cls, base_config: Dict[str, Any],
                          override_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge two view configurations (useful for applying saved views).

        Args:
            base_config: Base configuration
            override_config: Configuration to override with

        Returns:
            Merged configuration dictionary
        """
        merged = base_config.copy()

        for key, value in override_config.items():
            if isinstance(value, dict) and key in merged and isinstance(merged[key], dict):
                # Recursively merge dicts
                merged[key] = cls.merge_view_config(merged[key], value)
            else:
                # Override value
                merged[key] = value

        return merged

    @classmethod
    def validate_view_config(cls, view_config: Dict[str, Any],
                             table_identifier: str = None) -> tuple[bool, List[str]]:
        """
        Validate a view configuration.

        Args:
            view_config: Configuration to validate
            table_identifier: Optional table identifier for table-specific validation

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Basic structure validation
        if not isinstance(view_config, dict):
            errors.append("View configuration must be a dictionary")
            return False, errors

        # Validate specific config types
        if 'visible_columns' in view_config:
            if not isinstance(view_config['visible_columns'], list):
                errors.append("visible_columns must be a list")

        if 'column_widths' in view_config:
            if not isinstance(view_config['column_widths'], dict):
                errors.append("column_widths must be a dictionary")

        if 'sort_by' in view_config:
            if not isinstance(view_config['sort_by'], list):
                errors.append("sort_by must be a list")
            else:
                for sort_item in view_config['sort_by']:
                    if not isinstance(sort_item, dict):
                        errors.append("Each sort_by item must be a dictionary")
                    elif 'column' not in sort_item or 'direction' not in sort_item:
                        errors.append("sort_by items must have 'column' and 'direction'")

        if 'page_size' in view_config:
            if not isinstance(view_config['page_size'], (int, type(None))):
                errors.append("page_size must be an integer or null")
            elif view_config['page_size'] is not None:
                if view_config['page_size'] < 5 or view_config['page_size'] > 100:
                    errors.append("page_size must be between 5 and 100")

        # TODO: Add table-specific validation if table_identifier provided

        is_valid = len(errors) == 0
        return is_valid, errors

    @classmethod
    def export_view(cls, view_id: int, user: User) -> Dict[str, Any]:
        """
        Export a view configuration for sharing/backup.

        Args:
            view_id: SavedView ID
            user: User requesting export

        Returns:
            Exportable view data
        """
        view = SavedView.objects.get(id=view_id)

        # Check access
        if not cls._user_can_access_view(user, view):
            raise PermissionError("You don't have access to this view")

        export_data = {
            'name': view.name,
            'description': view.description,
            'table_identifier': view.table_identifier,
            'page_identifier': view.page_identifier,
            'view_config': view.view_config,
            'exported_at': timezone.now().isoformat(),
            'exported_by': user.username,
            'original_owner': view.owner.username,
        }

        return export_data

    @classmethod
    def import_view(cls, user: User, import_data: Dict[str, Any],
                    new_name: str = None) -> SavedView:
        """
        Import a view from exported data.

        Args:
            user: User importing the view
            import_data: Exported view data
            new_name: Optional new name for imported view

        Returns:
            Imported SavedView instance
        """
        # Validate import data
        required_fields = ['name', 'view_config']
        for field in required_fields:
            if field not in import_data:
                raise ValueError(f"Missing required field: {field}")

        # Validate config
        is_valid, errors = cls.validate_view_config(
            import_data['view_config'],
            import_data.get('table_identifier')
        )

        if not is_valid:
            raise ValueError(f"Invalid view configuration: {', '.join(errors)}")

        # Create view
        name = new_name or import_data['name']

        view = SavedView.objects.create(
            owner=user,
            name=name,
            description=import_data.get('description', ''),
            scope='PRIVATE',
            table_identifier=import_data.get('table_identifier', ''),
            page_identifier=import_data.get('page_identifier', ''),
            view_config=import_data['view_config']
        )

        return view

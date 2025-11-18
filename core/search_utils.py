"""
Global search utilities for the Floor Management System.

Provides unified search across all modules with intelligent ranking and filtering.
"""

from django.db.models import Q, Value, CharField
from django.db.models.functions import Concat
from django.apps import apps


class GlobalSearch:
    """
    Global search across multiple models.

    Usage:
        search = GlobalSearch(query="John Doe")
        results = search.execute()
    """

    # Define searchable models and their fields
    SEARCHABLE_MODELS = {
        'hr.HRPeople': {
            'fields': ['first_name_en', 'last_name_en', 'first_name_ar', 'last_name_ar',
                      'national_id', 'iqama_number'],
            'display_fields': ['get_full_name_en', 'national_id'],
            'label': 'People',
            'icon': 'bi-person',
            'url_pattern': 'hr:person_detail',
        },
        'hr.HREmployee': {
            'fields': ['employee_no', 'person__first_name_en', 'person__last_name_en'],
            'display_fields': ['employee_no', 'person'],
            'label': 'Employees',
            'icon': 'bi-people',
            'url_pattern': 'hr:employee_detail',
        },
        'hr.Position': {
            'fields': ['name', 'description'],
            'display_fields': ['name', 'department'],
            'label': 'Positions',
            'icon': 'bi-briefcase',
            'url_pattern': 'hr:position_detail',
        },
        'hr.Department': {
            'fields': ['name', 'code', 'description'],
            'display_fields': ['name', 'code'],
            'label': 'Departments',
            'icon': 'bi-building',
            'url_pattern': 'hr:department_detail',
        },
        'inventory.Item': {
            'fields': ['sku', 'name', 'short_name', 'description'],
            'display_fields': ['sku', 'name'],
            'label': 'Inventory Items',
            'icon': 'bi-box-seam',
            'url_pattern': 'inventory:item_detail',
        },
        'inventory.SerialUnit': {
            'fields': ['serial_number', 'item__sku', 'item__name'],
            'display_fields': ['serial_number', 'item'],
            'label': 'Serial Units',
            'icon': 'bi-upc-scan',
            'url_pattern': 'inventory:serialunit_detail',
        },
        'inventory.BitDesign': {
            'fields': ['design_code', 'name', 'description'],
            'display_fields': ['design_code', 'name'],
            'label': 'Bit Designs',
            'icon': 'bi-gear',
            'url_pattern': 'inventory:bitdesign_detail',
        },
        'inventory.BitDesignRevision': {
            'fields': ['mat_number', 'bit_design__design_code'],
            'display_fields': ['mat_number', 'bit_design'],
            'label': 'MAT Revisions',
            'icon': 'bi-tag',
            'url_pattern': 'inventory:mat_detail',
        },
        'inventory.Location': {
            'fields': ['code', 'name', 'address'],
            'display_fields': ['code', 'name'],
            'label': 'Locations',
            'icon': 'bi-geo-alt',
            'url_pattern': 'inventory:location_detail',
        },
        'core.CostCenter': {
            'fields': ['code', 'name', 'description'],
            'display_fields': ['code', 'name'],
            'label': 'Cost Centers',
            'icon': 'bi-cash-stack',
            'url_pattern': 'core:costcenter_detail',
        },
    }

    def __init__(self, query, modules=None, limit_per_model=10):
        """
        Initialize global search.

        Args:
            query: Search query string
            modules: List of modules to search (None = all)
            limit_per_model: Maximum results per model
        """
        self.query = query.strip()
        self.modules = modules or []
        self.limit_per_model = limit_per_model
        self.results = []

    def execute(self):
        """Execute search across all configured models."""
        if not self.query or len(self.query) < 2:
            return []

        results = []

        for model_path, config in self.SEARCHABLE_MODELS.items():
            # Filter by module if specified
            if self.modules and model_path.split('.')[0] not in self.modules:
                continue

            model_results = self._search_model(model_path, config)
            if model_results:
                results.append({
                    'model_label': config['label'],
                    'model_icon': config['icon'],
                    'model_path': model_path,
                    'count': len(model_results),
                    'results': model_results,
                })

        return results

    def _search_model(self, model_path, config):
        """Search a specific model."""
        try:
            app_label, model_name = model_path.split('.')
            model = apps.get_model(app_label, model_name)
        except (ValueError, LookupError):
            return []

        # Build Q objects for search
        q_objects = Q()
        for field in config['fields']:
            q_objects |= Q(**{f"{field}__icontains": self.query})

        # Execute query
        try:
            queryset = model.objects.filter(q_objects)

            # Apply soft delete filter if model has is_deleted field
            if hasattr(model, 'is_deleted'):
                queryset = queryset.filter(is_deleted=False)

            # Limit results
            queryset = queryset[:self.limit_per_model]

            # Build result items
            results = []
            for obj in queryset:
                item = {
                    'id': obj.pk,
                    'object': obj,
                    'url_pattern': config['url_pattern'],
                    'display': self._get_display_text(obj, config['display_fields']),
                    'model_label': config['label'],
                }
                results.append(item)

            return results
        except Exception as e:
            # Log error but don't break search
            print(f"Error searching {model_path}: {e}")
            return []

    def _get_display_text(self, obj, display_fields):
        """Get display text for an object."""
        parts = []
        for field in display_fields:
            try:
                if hasattr(obj, field):
                    value = getattr(obj, field)
                    if callable(value):
                        value = value()
                    if value:
                        parts.append(str(value))
            except Exception:
                continue

        return ' - '.join(parts) if parts else str(obj)


class AdvancedFilter:
    """
    Advanced filtering with save/load capability.

    Supports:
    - Multiple field filters
    - Date ranges
    - Number ranges
    - Boolean filters
    - Choice filters
    """

    def __init__(self, model, filters=None):
        """
        Initialize advanced filter.

        Args:
            model: Django model class
            filters: Dictionary of filter definitions
        """
        self.model = model
        self.filters = filters or {}
        self.active_filters = {}

    def apply(self, queryset, filter_data):
        """Apply filters to queryset based on filter data."""
        q_objects = Q()

        for field, value in filter_data.items():
            if field not in self.filters or not value:
                continue

            filter_config = self.filters[field]
            filter_type = filter_config.get('type', 'exact')

            if filter_type == 'exact':
                q_objects &= Q(**{field: value})
            elif filter_type == 'icontains':
                q_objects &= Q(**{f"{field}__icontains": value})
            elif filter_type == 'date_range':
                if 'start' in value and value['start']:
                    q_objects &= Q(**{f"{field}__gte": value['start']})
                if 'end' in value and value['end']:
                    q_objects &= Q(**{f"{field}__lte": value['end']})
            elif filter_type == 'number_range':
                if 'min' in value and value['min']:
                    q_objects &= Q(**{f"{field}__gte": value['min']})
                if 'max' in value and value['max']:
                    q_objects &= Q(**{f"{field}__lte": value['max']})
            elif filter_type == 'boolean':
                if value.lower() in ['true', '1', 'yes']:
                    q_objects &= Q(**{field: True})
                elif value.lower() in ['false', '0', 'no']:
                    q_objects &= Q(**{field: False})
            elif filter_type == 'choice':
                q_objects &= Q(**{field: value})

        return queryset.filter(q_objects)

    def get_filter_definitions(self):
        """Get filter definitions for rendering in UI."""
        return self.filters


class SearchHistory:
    """Track and manage user search history."""

    @staticmethod
    def add_search(user, query, module=None):
        """Add search to user's history."""
        from core.models import UserPreference

        pref = UserPreference.get_or_create_for_user(user)

        # Get existing search history
        search_history = pref.preferences_json.get('search_history', [])

        # Add new search (avoid duplicates)
        search_item = {
            'query': query,
            'module': module,
            'timestamp': str(timezone.now())
        }

        # Remove if already exists
        search_history = [s for s in search_history if s['query'] != query]

        # Add to beginning
        search_history.insert(0, search_item)

        # Keep only last 20 searches
        search_history = search_history[:20]

        # Save
        pref.preferences_json['search_history'] = search_history
        pref.save()

    @staticmethod
    def get_recent_searches(user, limit=10):
        """Get user's recent searches."""
        from core.models import UserPreference

        try:
            pref = UserPreference.get_or_create_for_user(user)
            search_history = pref.preferences_json.get('search_history', [])
            return search_history[:limit]
        except Exception:
            return []


class SavedFilter:
    """Save and load filter presets."""

    @staticmethod
    def save_filter(user, name, filters, module=None):
        """Save a filter preset."""
        from core.models import UserPreference

        pref = UserPreference.get_or_create_for_user(user)

        # Get existing saved filters
        saved_filters = pref.preferences_json.get('saved_filters', {})

        # Add new filter
        filter_key = f"{module}_{name}" if module else name
        saved_filters[filter_key] = {
            'name': name,
            'module': module,
            'filters': filters,
            'created_at': str(timezone.now())
        }

        # Save
        pref.preferences_json['saved_filters'] = saved_filters
        pref.save()

    @staticmethod
    def get_saved_filters(user, module=None):
        """Get user's saved filters."""
        from core.models import UserPreference

        try:
            pref = UserPreference.get_or_create_for_user(user)
            saved_filters = pref.preferences_json.get('saved_filters', {})

            if module:
                # Filter by module
                return {k: v for k, v in saved_filters.items() if v.get('module') == module}

            return saved_filters
        except Exception:
            return {}

    @staticmethod
    def delete_filter(user, filter_key):
        """Delete a saved filter."""
        from core.models import UserPreference

        pref = UserPreference.get_or_create_for_user(user)
        saved_filters = pref.preferences_json.get('saved_filters', {})

        if filter_key in saved_filters:
            del saved_filters[filter_key]
            pref.preferences_json['saved_filters'] = saved_filters
            pref.save()


# Timezone import for timestamps
from django.utils import timezone

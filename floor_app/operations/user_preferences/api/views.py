"""
User Preferences API Views

REST API views for user preferences, views, and customizations.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from floor_app.operations.user_preferences.models import (
    UserPreference,
    TableViewPreference,
    PageFeaturePreference,
    SavedView,
    QuickFilter,
    UserShortcut,
    RecentActivity
)
from floor_app.operations.user_preferences.services import (
    PreferenceService,
    ViewService
)
from .serializers import (
    UserPreferenceSerializer,
    UserPreferenceUpdateSerializer,
    TableViewPreferenceSerializer,
    TableViewPreferenceCreateSerializer,
    TableViewPreferenceListSerializer,
    PageFeaturePreferenceSerializer,
    PageFeaturePreferenceSaveSerializer,
    ToggleFeatureSerializer,
    SavedViewSerializer,
    SavedViewCreateSerializer,
    SavedViewUpdateSerializer,
    SavedViewShareSerializer,
    SavedViewDuplicateSerializer,
    QuickFilterSerializer,
    QuickFilterCreateSerializer,
    UserShortcutSerializer,
    UserShortcutCreateSerializer,
    RecentActivitySerializer,
    RecordActivitySerializer,
    PreferenceExportSerializer,
    PreferenceImportSerializer,
    ViewExportSerializer,
    ViewImportSerializer,
)


class UserPreferenceViewSet(viewsets.ViewSet):
    """
    ViewSet for managing user preferences.

    Endpoints:
    - GET /api/preferences/user/ - Get current user's preferences
    - PUT /api/preferences/user/ - Update user preferences
    - POST /api/preferences/user/export/ - Export all preferences
    - POST /api/preferences/user/import/ - Import preferences
    """

    permission_classes = [IsAuthenticated]

    def list(self, request):
        """
        Get current user's preferences.

        GET /api/preferences/user/
        """
        preferences = PreferenceService.get_or_create_user_preferences(request.user)
        serializer = UserPreferenceSerializer(preferences)
        return Response(serializer.data)

    def update(self, request, pk=None):
        """
        Update user preferences.

        PUT /api/preferences/user/
        """
        serializer = UserPreferenceUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        preferences = PreferenceService.update_user_preferences(
            request.user,
            serializer.validated_data
        )

        return Response(UserPreferenceSerializer(preferences).data)

    @action(detail=False, methods=['post'])
    def export(self, request):
        """
        Export all user preferences.

        POST /api/preferences/user/export/
        """
        serializer = PreferenceExportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        export_data = PreferenceService.export_preferences(request.user)

        return Response({
            'export_data': export_data,
            'message': 'Preferences exported successfully'
        })

    @action(detail=False, methods=['post'])
    def import_preferences(self, request):
        """
        Import preferences from exported data.

        POST /api/preferences/user/import/
        Body: {
            "data": {...},
            "overwrite": true/false
        }
        """
        serializer = PreferenceImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        PreferenceService.import_preferences(
            request.user,
            serializer.validated_data['data'],
            serializer.validated_data.get('overwrite', False)
        )

        return Response({
            'message': 'Preferences imported successfully'
        })


class TableViewPreferenceViewSet(viewsets.ViewSet):
    """
    ViewSet for managing table view preferences.

    Endpoints:
    - GET /api/preferences/table-views/?table_identifier=X - Get view for table
    - POST /api/preferences/table-views/ - Save table view
    - GET /api/preferences/table-views/list/?table_identifier=X - List all views for table
    - DELETE /api/preferences/table-views/{id}/ - Delete view
    """

    permission_classes = [IsAuthenticated]

    def list(self, request):
        """
        Get table view preference.

        GET /api/preferences/table-views/?table_identifier=X&view_name=Y
        """
        table_identifier = request.query_params.get('table_identifier')
        view_name = request.query_params.get('view_name', '')

        if not table_identifier:
            return Response(
                {'error': 'table_identifier is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        preference = PreferenceService.get_table_view_preference(
            request.user,
            table_identifier,
            view_name
        )

        if preference:
            serializer = TableViewPreferenceSerializer(preference)
            return Response(serializer.data)
        else:
            return Response(
                {'message': 'No preference found'},
                status=status.HTTP_404_NOT_FOUND
            )

    def create(self, request):
        """
        Save table view preference.

        POST /api/preferences/table-views/
        Body: {
            "table_identifier": "employee_list",
            "view_name": "My View",
            "visible_columns": [...],
            "sort_by": [...],
            ...
        }
        """
        serializer = TableViewPreferenceCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        table_identifier = data.pop('table_identifier')
        view_name = data.pop('view_name', '')
        is_default = data.pop('is_default', False)

        preference = PreferenceService.save_table_view_preference(
            request.user,
            table_identifier,
            data,
            view_name,
            is_default
        )

        return Response(
            TableViewPreferenceSerializer(preference).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=['get'])
    def list_views(self, request):
        """
        List all saved views for a table.

        GET /api/preferences/table-views/list_views/?table_identifier=X
        """
        serializer = TableViewPreferenceListSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        table_identifier = serializer.validated_data['table_identifier']

        views = PreferenceService.list_table_views(request.user, table_identifier)

        return Response(TableViewPreferenceSerializer(views, many=True).data)

    def destroy(self, request, pk=None):
        """
        Delete a table view preference.

        DELETE /api/preferences/table-views/{id}/
        """
        preference = get_object_or_404(TableViewPreference, id=pk, user=request.user)

        deleted = PreferenceService.delete_table_view_preference(
            request.user,
            preference.table_identifier,
            preference.view_name
        )

        if deleted:
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(
                {'error': 'Failed to delete preference'},
                status=status.HTTP_400_BAD_REQUEST
            )


class PageFeaturePreferenceViewSet(viewsets.ViewSet):
    """
    ViewSet for managing page feature preferences.

    Endpoints:
    - GET /api/preferences/page-features/?page_identifier=X - Get page preferences
    - POST /api/preferences/page-features/ - Save page preferences
    - POST /api/preferences/page-features/toggle_feature/ - Toggle feature visibility
    """

    permission_classes = [IsAuthenticated]

    def list(self, request):
        """
        Get page feature preferences.

        GET /api/preferences/page-features/?page_identifier=X
        """
        page_identifier = request.query_params.get('page_identifier')

        if not page_identifier:
            return Response(
                {'error': 'page_identifier is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        preference = PreferenceService.get_page_feature_preference(
            request.user,
            page_identifier
        )

        if preference:
            serializer = PageFeaturePreferenceSerializer(preference)
            return Response(serializer.data)
        else:
            return Response(
                {'message': 'No preference found'},
                status=status.HTTP_404_NOT_FOUND
            )

    def create(self, request):
        """
        Save page feature preferences.

        POST /api/preferences/page-features/
        Body: {
            "page_identifier": "dashboard",
            "visible_features": [...],
            "layout_config": {...},
            ...
        }
        """
        serializer = PageFeaturePreferenceSaveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        page_identifier = data.pop('page_identifier')

        preference = PreferenceService.save_page_feature_preference(
            request.user,
            page_identifier,
            data
        )

        return Response(
            PageFeaturePreferenceSerializer(preference).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=['post'])
    def toggle_feature(self, request):
        """
        Toggle visibility of a page feature.

        POST /api/preferences/page-features/toggle_feature/
        Body: {
            "page_identifier": "dashboard",
            "feature_id": "widget_sales",
            "visible": true/false
        }
        """
        serializer = ToggleFeatureSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        preference = PreferenceService.toggle_feature_visibility(
            request.user,
            serializer.validated_data['page_identifier'],
            serializer.validated_data['feature_id'],
            serializer.validated_data['visible']
        )

        return Response(PageFeaturePreferenceSerializer(preference).data)


class SavedViewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing saved views.

    Endpoints:
    - GET /api/preferences/saved-views/ - List available views
    - POST /api/preferences/saved-views/ - Create new view
    - GET /api/preferences/saved-views/{id}/ - Get view details
    - PUT /api/preferences/saved-views/{id}/ - Update view
    - DELETE /api/preferences/saved-views/{id}/ - Delete view
    - POST /api/preferences/saved-views/{id}/apply/ - Apply view (track usage)
    - POST /api/preferences/saved-views/{id}/share/ - Share view
    - POST /api/preferences/saved-views/{id}/toggle_favorite/ - Toggle favorite
    - POST /api/preferences/saved-views/{id}/duplicate/ - Duplicate view
    - GET /api/preferences/saved-views/favorites/ - Get favorite views
    - GET /api/preferences/saved-views/popular/ - Get popular views
    - GET /api/preferences/saved-views/search/ - Search views
    - POST /api/preferences/saved-views/export_view/ - Export view
    - POST /api/preferences/saved-views/import_view/ - Import view
    """

    permission_classes = [IsAuthenticated]
    serializer_class = SavedViewSerializer

    def get_queryset(self):
        """Get views available to current user."""
        table_id = self.request.query_params.get('table_identifier')
        page_id = self.request.query_params.get('page_identifier')

        return ViewService.get_available_views(
            self.request.user,
            table_id,
            page_id
        )

    def create(self, request):
        """
        Create a new saved view.

        POST /api/preferences/saved-views/
        """
        serializer = SavedViewCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        view = ViewService.create_view(
            owner=request.user,
            **serializer.validated_data
        )

        return Response(
            SavedViewSerializer(view, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

    def update(self, request, pk=None):
        """
        Update a saved view.

        PUT /api/preferences/saved-views/{id}/
        """
        serializer = SavedViewUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            view = ViewService.update_view(
                int(pk),
                request.user,
                **serializer.validated_data
            )
            return Response(SavedViewSerializer(view, context={'request': request}).data)
        except PermissionError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )

    def destroy(self, request, pk=None):
        """
        Delete a saved view.

        DELETE /api/preferences/saved-views/{id}/
        """
        try:
            ViewService.delete_view(int(pk), request.user)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except PermissionError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )

    @action(detail=True, methods=['post'])
    def apply(self, request, pk=None):
        """
        Apply a view (increments usage count).

        POST /api/preferences/saved-views/{id}/apply/
        """
        try:
            view = ViewService.apply_view(int(pk), request.user)
            return Response(SavedViewSerializer(view, context={'request': request}).data)
        except PermissionError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )

    @action(detail=True, methods=['post'])
    def share(self, request, pk=None):
        """
        Share a view with users/teams/departments.

        POST /api/preferences/saved-views/{id}/share/
        Body: {
            "scope": "SHARED",
            "user_ids": [1, 2, 3],
            "team_ids": [1],
            "department_ids": [2]
        }
        """
        serializer = SavedViewShareSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            view = ViewService.share_view(
                int(pk),
                request.user,
                **serializer.validated_data
            )
            return Response(SavedViewSerializer(view, context={'request': request}).data)
        except PermissionError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )

    @action(detail=True, methods=['post'])
    def toggle_favorite(self, request, pk=None):
        """
        Toggle view as favorite.

        POST /api/preferences/saved-views/{id}/toggle_favorite/
        """
        try:
            view, is_favorited = ViewService.toggle_favorite(int(pk), request.user)
            return Response({
                'view': SavedViewSerializer(view, context={'request': request}).data,
                'is_favorited': is_favorited
            })
        except PermissionError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )

    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """
        Duplicate a view.

        POST /api/preferences/saved-views/{id}/duplicate/
        Body: {
            "new_name": "Copy of My View"  # optional
        }
        """
        serializer = SavedViewDuplicateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            view = ViewService.duplicate_view(
                int(pk),
                request.user,
                serializer.validated_data.get('new_name')
            )
            return Response(
                SavedViewSerializer(view, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )
        except PermissionError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )

    @action(detail=False, methods=['get'])
    def favorites(self, request):
        """
        Get user's favorite views.

        GET /api/preferences/saved-views/favorites/
        """
        views = ViewService.get_favorite_views(request.user)
        return Response(SavedViewSerializer(views, many=True, context={'request': request}).data)

    @action(detail=False, methods=['get'])
    def popular(self, request):
        """
        Get popular public views.

        GET /api/preferences/saved-views/popular/?table_identifier=X&limit=10
        """
        table_id = request.query_params.get('table_identifier')
        page_id = request.query_params.get('page_identifier')
        limit = int(request.query_params.get('limit', 10))

        views = ViewService.get_popular_views(table_id, page_id, limit)
        return Response(SavedViewSerializer(views, many=True, context={'request': request}).data)

    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Search for views.

        GET /api/preferences/saved-views/search/?q=query&table_identifier=X
        """
        query = request.query_params.get('q', '')
        table_id = request.query_params.get('table_identifier')
        page_id = request.query_params.get('page_identifier')

        if not query:
            return Response(
                {'error': 'Search query (q) is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        views = ViewService.search_views(request.user, query, table_id, page_id)
        return Response(SavedViewSerializer(views, many=True, context={'request': request}).data)

    @action(detail=False, methods=['post'])
    def export_view(self, request):
        """
        Export a view.

        POST /api/preferences/saved-views/export_view/
        Body: {"view_id": 123}
        """
        serializer = ViewExportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            export_data = ViewService.export_view(
                serializer.validated_data['view_id'],
                request.user
            )
            return Response(export_data)
        except PermissionError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )

    @action(detail=False, methods=['post'])
    def import_view(self, request):
        """
        Import a view.

        POST /api/preferences/saved-views/import_view/
        Body: {
            "data": {...},
            "new_name": "Imported View"  # optional
        }
        """
        serializer = ViewImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            view = ViewService.import_view(
                request.user,
                serializer.validated_data['data'],
                serializer.validated_data.get('new_name')
            )
            return Response(
                SavedViewSerializer(view, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class QuickFilterViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing quick filters.

    Endpoints:
    - GET /api/preferences/quick-filters/ - List filters
    - POST /api/preferences/quick-filters/ - Create filter
    - PUT /api/preferences/quick-filters/{id}/ - Update filter
    - DELETE /api/preferences/quick-filters/{id}/ - Delete filter
    - POST /api/preferences/quick-filters/{id}/apply/ - Apply filter (track usage)
    """

    permission_classes = [IsAuthenticated]
    serializer_class = QuickFilterSerializer

    def get_queryset(self):
        """Get quick filters for current user."""
        table_id = self.request.query_params.get('table_identifier')
        pinned_only = self.request.query_params.get('pinned_only', 'false').lower() == 'true'

        return PreferenceService.list_quick_filters(
            self.request.user,
            table_id,
            pinned_only
        )

    def create(self, request):
        """
        Create a quick filter.

        POST /api/preferences/quick-filters/
        """
        serializer = QuickFilterCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        quick_filter = PreferenceService.create_quick_filter(
            request.user,
            **serializer.validated_data
        )

        return Response(
            QuickFilterSerializer(quick_filter).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'])
    def apply(self, request, pk=None):
        """
        Apply a quick filter (increments usage count).

        POST /api/preferences/quick-filters/{id}/apply/
        """
        quick_filter = PreferenceService.apply_quick_filter(request.user, int(pk))
        return Response(QuickFilterSerializer(quick_filter).data)


class UserShortcutViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user shortcuts.

    Endpoints:
    - GET /api/preferences/shortcuts/ - List shortcuts
    - POST /api/preferences/shortcuts/ - Create shortcut
    - PUT /api/preferences/shortcuts/{id}/ - Update shortcut
    - DELETE /api/preferences/shortcuts/{id}/ - Delete shortcut
    """

    permission_classes = [IsAuthenticated]
    serializer_class = UserShortcutSerializer

    def get_queryset(self):
        """Get shortcuts for current user."""
        scope = self.request.query_params.get('scope')
        active_only = self.request.query_params.get('active_only', 'true').lower() == 'true'

        return PreferenceService.list_shortcuts(
            self.request.user,
            scope,
            active_only
        )

    def create(self, request):
        """
        Create a keyboard shortcut.

        POST /api/preferences/shortcuts/
        """
        serializer = UserShortcutCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        shortcut = PreferenceService.create_shortcut(
            request.user,
            **serializer.validated_data
        )

        return Response(
            UserShortcutSerializer(shortcut).data,
            status=status.HTTP_201_CREATED
        )


class RecentActivityViewSet(viewsets.ViewSet):
    """
    ViewSet for managing recent activities.

    Endpoints:
    - GET /api/preferences/recent-activities/ - Get recent activities
    - POST /api/preferences/recent-activities/record/ - Record new activity
    """

    permission_classes = [IsAuthenticated]

    def list(self, request):
        """
        Get user's recent activities.

        GET /api/preferences/recent-activities/?activity_type=VIEW&entity_type=Employee&limit=20
        """
        activity_type = request.query_params.get('activity_type')
        entity_type = request.query_params.get('entity_type')
        limit = int(request.query_params.get('limit', 20))

        activities = PreferenceService.get_recent_activities(
            request.user,
            activity_type,
            entity_type,
            limit
        )

        return Response(RecentActivitySerializer(activities, many=True).data)

    @action(detail=False, methods=['post'])
    def record(self, request):
        """
        Record a new activity.

        POST /api/preferences/recent-activities/record/
        Body: {
            "activity_type": "VIEW",
            "entity_type": "Employee",
            "entity_display": "John Doe",
            "entity_id": "123",
            "url": "/employees/123/",
            "metadata": {}
        }
        """
        serializer = RecordActivitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        activity = PreferenceService.record_activity(
            request.user,
            **serializer.validated_data
        )

        return Response(
            RecentActivitySerializer(activity).data,
            status=status.HTTP_201_CREATED
        )

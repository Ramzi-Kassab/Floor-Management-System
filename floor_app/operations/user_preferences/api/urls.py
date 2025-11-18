"""
User Preferences API URLs

REST API URL configuration for user preferences.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserPreferenceViewSet,
    TableViewPreferenceViewSet,
    PageFeaturePreferenceViewSet,
    SavedViewViewSet,
    QuickFilterViewSet,
    UserShortcutViewSet,
    RecentActivityViewSet
)

# Create router
router = DefaultRouter()

# Register viewsets
router.register(r'user', UserPreferenceViewSet, basename='user-preference')
router.register(r'table-views', TableViewPreferenceViewSet, basename='table-view-preference')
router.register(r'page-features', PageFeaturePreferenceViewSet, basename='page-feature-preference')
router.register(r'saved-views', SavedViewViewSet, basename='saved-view')
router.register(r'quick-filters', QuickFilterViewSet, basename='quick-filter')
router.register(r'shortcuts', UserShortcutViewSet, basename='user-shortcut')
router.register(r'recent-activities', RecentActivityViewSet, basename='recent-activity')

urlpatterns = [
    path('', include(router.urls)),
]

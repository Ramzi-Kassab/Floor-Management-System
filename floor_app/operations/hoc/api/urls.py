"""HOC API URLs"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import HazardCategoryViewSet, HazardObservationViewSet

router = DefaultRouter()
router.register(r'categories', HazardCategoryViewSet, basename='hoc-category')
router.register(r'observations', HazardObservationViewSet, basename='hoc-observation')

urlpatterns = [
    path('', include(router.urls)),
]

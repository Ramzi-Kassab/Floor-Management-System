"""HR Assets API URLs"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    VehicleViewSet, ParkingZoneViewSet, ParkingSpotViewSet,
    SIMCardViewSet, PhoneViewSet, CameraViewSet, AssetOverviewViewSet
)

router = DefaultRouter()
router.register(r'vehicles', VehicleViewSet, basename='vehicle')
router.register(r'parking-zones', ParkingZoneViewSet, basename='parking-zone')
router.register(r'parking-spots', ParkingSpotViewSet, basename='parking-spot')
router.register(r'sim-cards', SIMCardViewSet, basename='sim-card')
router.register(r'phones', PhoneViewSet, basename='phone')
router.register(r'cameras', CameraViewSet, basename='camera')
router.register(r'overview', AssetOverviewViewSet, basename='asset-overview')

urlpatterns = [
    path('', include(router.urls)),
]

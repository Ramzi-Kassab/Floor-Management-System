"""Journey Management API URLs"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import JourneyPlanViewSet

router = DefaultRouter()
router.register(r'journeys', JourneyPlanViewSet, basename='journey')

urlpatterns = [
    path('', include(router.urls)),
]

"""5S API URLs"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FiveSAuditTemplateViewSet, FiveSAuditViewSet, FiveSLeaderboardViewSet, FiveSAchievementViewSet

router = DefaultRouter()
router.register(r'templates', FiveSAuditTemplateViewSet, basename='fives-template')
router.register(r'audits', FiveSAuditViewSet, basename='fives-audit')
router.register(r'leaderboard', FiveSLeaderboardViewSet, basename='fives-leaderboard')
router.register(r'achievements', FiveSAchievementViewSet, basename='fives-achievement')

urlpatterns = [
    path('', include(router.urls)),
]

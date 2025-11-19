"""5S API Views"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from floor_app.operations.fives.models import FiveSAuditTemplate, FiveSAudit, FiveSLeaderboard, FiveSAchievement
from floor_app.operations.fives.services import FiveSService
from .serializers import *


class FiveSAuditTemplateViewSet(viewsets.ModelViewSet):
    queryset = FiveSAuditTemplate.objects.filter(is_active=True)
    serializer_class = FiveSAuditTemplateSerializer
    permission_classes = [IsAuthenticated]


class FiveSAuditViewSet(viewsets.ModelViewSet):
    serializer_class = FiveSAuditSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FiveSAudit.objects.select_related('template', 'audited_by', 'responsible_person')

    @action(detail=False, methods=['post'], url_path='create-audit/(?P<template_id>[^/.]+)')
    def create_audit(self, request, template_id=None):
        serializer = FiveSAuditCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        audit = FiveSService.create_audit(int(template_id), request.user, serializer.validated_data)
        return Response(FiveSAuditSerializer(audit).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        serializer = FiveSAuditCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        audit = FiveSService.complete_audit(int(pk), **serializer.validated_data)
        return Response(FiveSAuditSerializer(audit).data)

    @action(detail=False, methods=['get'])
    def my_statistics(self, request):
        stats = FiveSService.get_user_statistics(request.user)
        stats['recent_audits'] = FiveSAuditSerializer(stats['recent_audits'], many=True).data
        return Response(stats)


class FiveSLeaderboardViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = FiveSLeaderboardSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        period_type = self.request.query_params.get('period_type', 'MONTHLY')
        limit = int(self.request.query_params.get('limit', 10))
        return FiveSService.get_leaderboard(period_type, limit)


class FiveSAchievementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = FiveSAchievement.objects.filter(is_active=True)
    serializer_class = FiveSAchievementSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def my_achievements(self, request):
        achievements = FiveSUserAchievement.objects.filter(user=request.user).select_related('achievement')
        return Response(FiveSUserAchievementSerializer(achievements, many=True).data)

"""
REST API ViewSets for Core Models

Provides API endpoints for:
- AuditLog (read-only)
- ActivityLog (read-only)
- SystemEvent (read, update resolution)
- ChangeHistory (read-only)
- Notification (read, update, create)
- System Health (read-only)
- Statistics (read-only)
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
# from django_filters.rest_framework import DjangoFilterBackend  # Install django-filter first: pip install django-filter
from django.utils import timezone
from datetime import timedelta

from ..models import AuditLog, ActivityLog, SystemEvent, ChangeHistory
from ..notifications import Notification
from ..utils import get_system_health_summary
from ..permissions import is_staff_or_superuser
from .serializers import (
    AuditLogSerializer, ActivityLogSerializer,
    SystemEventSerializer, ChangeHistorySerializer,
    NotificationSerializer, NotificationCreateSerializer,
    SystemHealthSerializer, ActivityStatsSerializer, AuditStatsSerializer
)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing audit logs

    Provides:
    - list: Get all audit logs (with filtering)
    - retrieve: Get specific audit log
    - stats: Get audit statistics
    """
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]  # Add DjangoFilterBackend after installing django-filter
    filterset_fields = ['action', 'model_name', 'username']
    search_fields = ['username', 'model_name', 'object_repr', 'message']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']

    def get_queryset(self):
        """Filter queryset based on permissions"""
        queryset = super().get_queryset()

        # Only staff can see all logs
        if not is_staff_or_superuser(self.request.user):
            # Regular users can only see their own audit logs
            queryset = queryset.filter(user=self.request.user)

        # Filter by date range if provided
        days = self.request.query_params.get('days')
        if days:
            start_date = timezone.now() - timedelta(days=int(days))
            queryset = queryset.filter(timestamp__gte=start_date)

        return queryset

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get audit log statistics"""
        days = int(request.query_params.get('days', 7))
        start_date = timezone.now() - timedelta(days=days)

        from django.db.models import Count

        queryset = self.get_queryset().filter(timestamp__gte=start_date)

        stats = {
            'total_audits': queryset.count(),
            'by_action': list(queryset.values('action').annotate(
                count=Count('id')
            ).order_by('-count')),
            'by_model': list(queryset.values('model_name').annotate(
                count=Count('id')
            ).order_by('-count')[:10]),
            'by_user': list(queryset.values('username').annotate(
                count=Count('id')
            ).order_by('-count')[:10]),
            'date_range': {
                'start': start_date.isoformat(),
                'end': timezone.now().isoformat(),
            }
        }

        serializer = AuditStatsSerializer(stats)
        return Response(serializer.data)


class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing activity logs

    Provides:
    - list: Get all activity logs (with filtering)
    - retrieve: Get specific activity log
    - stats: Get activity statistics
    """
    queryset = ActivityLog.objects.all()
    serializer_class = ActivityLogSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]  # Add DjangoFilterBackend after installing django-filter
    filterset_fields = ['activity_type', 'user']
    search_fields = ['path', 'description']
    ordering_fields = ['timestamp', 'duration_ms']
    ordering = ['-timestamp']

    def get_queryset(self):
        """Filter queryset based on permissions"""
        queryset = super().get_queryset()

        # Only staff can see all logs
        if not is_staff_or_superuser(self.request.user):
            queryset = queryset.filter(user=self.request.user)

        # Filter by date range
        days = self.request.query_params.get('days')
        if days:
            start_date = timezone.now() - timedelta(days=int(days))
            queryset = queryset.filter(timestamp__gte=start_date)

        return queryset

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get activity statistics"""
        days = int(request.query_params.get('days', 7))
        start_date = timezone.now() - timedelta(days=days)

        from django.db.models import Count, Avg
        from django.db.models.functions import ExtractHour

        queryset = self.get_queryset().filter(timestamp__gte=start_date)

        stats = {
            'total_activities': queryset.count(),
            'unique_users': queryset.values('user').distinct().count(),
            'by_type': list(queryset.values('activity_type').annotate(
                count=Count('id')
            ).order_by('-count')),
            'by_hour': list(queryset.annotate(
                hour=ExtractHour('timestamp')
            ).values('hour').annotate(
                count=Count('id')
            ).order_by('hour')),
            'top_users': list(queryset.values('user__username').annotate(
                count=Count('id')
            ).order_by('-count')[:10]),
            'date_range': {
                'start': start_date.isoformat(),
                'end': timezone.now().isoformat(),
            }
        }

        # Add average duration if available
        avg_duration = queryset.exclude(duration_ms__isnull=True).aggregate(
            avg=Avg('duration_ms')
        )['avg']
        if avg_duration:
            stats['avg_duration_ms'] = avg_duration

        serializer = ActivityStatsSerializer(stats)
        return Response(serializer.data)


class SystemEventViewSet(viewsets.ModelViewSet):
    """
    API endpoint for system events

    Provides:
    - list: Get all system events
    - retrieve: Get specific event
    - update/partial_update: Mark events as resolved
    - unresolved: Get unresolved events only
    """
    queryset = SystemEvent.objects.all()
    serializer_class = SystemEventSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]  # Add DjangoFilterBackend after installing django-filter
    filterset_fields = ['level', 'category', 'is_resolved']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']

    def get_queryset(self):
        """Filter to staff users only"""
        if not is_staff_or_superuser(self.request.user):
            return SystemEvent.objects.none()

        queryset = super().get_queryset()

        # Filter by date range
        days = self.request.query_params.get('days')
        if days:
            start_date = timezone.now() - timedelta(days=int(days))
            queryset = queryset.filter(timestamp__gte=start_date)

        return queryset

    @action(detail=False, methods=['get'])
    def unresolved(self, request):
        """Get only unresolved events"""
        queryset = self.get_queryset().filter(is_resolved=False)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Mark event as resolved"""
        event = self.get_object()
        event.is_resolved = True
        event.resolved_at = timezone.now()
        event.resolved_by = request.user
        event.resolution_notes = request.data.get('resolution_notes', '')
        event.save()

        serializer = self.get_serializer(event)
        return Response(serializer.data)


class ChangeHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for change history

    Provides read-only access to change history
    """
    queryset = ChangeHistory.objects.all()
    serializer_class = ChangeHistorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]  # Add DjangoFilterBackend after installing django-filter
    ordering_fields = ['changed_at']
    ordering = ['-changed_at']

    def get_queryset(self):
        """Filter to staff users only"""
        if not is_staff_or_superuser(self.request.user):
            return ChangeHistory.objects.none()

        queryset = super().get_queryset()

        # Filter by date range
        days = self.request.query_params.get('days')
        if days:
            start_date = timezone.now() - timedelta(days=int(days))
            queryset = queryset.filter(changed_at__gte=start_date)

        return queryset


class NotificationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for notifications

    Provides:
    - list: Get user's notifications
    - retrieve: Get specific notification
    - create: Create notifications (staff only)
    - update: Mark as read
    - mark_read: Mark specific notification as read
    - mark_all_read: Mark all notifications as read
    - unread: Get unread notifications
    - unread_count: Get count of unread notifications
    """
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]  # Add DjangoFilterBackend after installing django-filter
    filterset_fields = ['notification_type', 'is_read']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        """Users can only see their own notifications"""
        return Notification.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        """Use different serializer for creation"""
        if self.action == 'create':
            return NotificationCreateSerializer
        return NotificationSerializer

    def create(self, request, *args, **kwargs):
        """Create notifications (staff only)"""
        if not is_staff_or_superuser(request.user):
            return Response(
                {'error': 'Only staff can create notifications'},
                status=status.HTTP_403_FORBIDDEN
            )

        return super().create(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark notification as read"""
        notification = self.get_object()
        notification.mark_as_read()
        serializer = self.get_serializer(notification)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        count = Notification.mark_all_as_read(request.user)
        return Response({'marked_read': count})

    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Get unread notifications only"""
        queryset = self.get_queryset().filter(is_read=False)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications"""
        count = Notification.get_unread_count(request.user)
        return Response({'unread_count': count})


class SystemHealthViewSet(viewsets.ViewSet):
    """
    API endpoint for system health

    Provides:
    - health: Get system health summary
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def health(self, request):
        """Get system health summary"""
        if not is_staff_or_superuser(request.user):
            return Response(
                {'error': 'Only staff can view system health'},
                status=status.HTTP_403_FORBIDDEN
            )

        health = get_system_health_summary()
        health['timestamp'] = health['timestamp'].isoformat()

        serializer = SystemHealthSerializer(health)
        return Response(serializer.data)

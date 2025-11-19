"""
Notification API Views

REST API viewsets for notification system.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q, Count

from floor_app.operations.notifications.models import (
    NotificationChannel,
    NotificationTemplate,
    Notification,
    NotificationDelivery,
    NotificationPreference,
    Announcement,
    AnnouncementRead
)
from floor_app.operations.notifications.services import NotificationService
from .serializers import (
    NotificationChannelSerializer,
    NotificationTemplateSerializer,
    NotificationSerializer,
    NotificationCreateSerializer,
    NotificationDeliverySerializer,
    NotificationPreferenceSerializer,
    AnnouncementSerializer,
    AnnouncementCreateSerializer,
    AnnouncementReadSerializer
)


class NotificationChannelViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing notification channels.

    list: Get all notification channels
    retrieve: Get a specific notification channel
    create: Create a new notification channel (admin only)
    update: Update a notification channel (admin only)
    destroy: Delete a notification channel (admin only)
    """

    queryset = NotificationChannel.objects.all()
    serializer_class = NotificationChannelSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        """Only admins can create/update/delete channels."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return super().get_permissions()

    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """
        Test a notification channel.

        POST /api/notification-channels/{id}/test/
        Body: {
            "recipient": "+971501234567" or "email@example.com",
            "message": "Test message"
        }
        """
        channel = self.get_object()

        recipient = request.data.get('recipient')
        message = request.data.get('message', 'Test message from Floor Management System')

        if not recipient:
            return Response(
                {'error': 'recipient is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Send test notification
        try:
            if channel.channel_type == 'WHATSAPP':
                from floor_app.operations.notifications.services import WhatsAppService
                success = WhatsAppService.send_message(recipient, message)
            elif channel.channel_type == 'EMAIL':
                from floor_app.operations.notifications.services import EmailService
                success = EmailService.send_email(
                    to_email=recipient,
                    subject='Test Email',
                    body=message
                )
            elif channel.channel_type == 'SMS':
                from floor_app.operations.notifications.services import SMSService
                success = SMSService.send_sms(recipient, message)
            else:
                return Response(
                    {'error': f'Testing not implemented for {channel.channel_type}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if success:
                return Response({'success': True, 'message': 'Test message sent successfully'})
            else:
                return Response(
                    {'success': False, 'error': 'Failed to send test message'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except Exception as e:
            return Response(
                {'success': False, 'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class NotificationTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing notification templates.

    list: Get all notification templates
    retrieve: Get a specific template
    create: Create a new template
    update: Update a template
    destroy: Delete a template
    """

    queryset = NotificationTemplate.objects.all()
    serializer_class = NotificationTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['template_category', 'is_active']
    search_fields = ['name', 'description']

    @action(detail=True, methods=['post'])
    def preview(self, request, pk=None):
        """
        Preview a template with variables.

        POST /api/notification-templates/{id}/preview/
        Body: {
            "variables": {"name": "Ahmed", "amount": "1500"}
        }
        """
        template = self.get_object()
        variables = request.data.get('variables', {})

        try:
            from django.template import Template, Context

            # Render subject
            subject_template = Template(template.subject_template)
            subject = subject_template.render(Context(variables))

            # Render body
            body_template = Template(template.body_template)
            body = body_template.render(Context(variables))

            return Response({
                'subject': subject,
                'body': body
            })

        except Exception as e:
            return Response(
                {'error': f'Template rendering error: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing notifications.

    list: Get notifications for current user
    retrieve: Get a specific notification
    create: Send a new notification
    """

    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['priority', 'status', 'category']
    search_fields = ['title', 'message']
    ordering_fields = ['created_at', 'priority']
    ordering = ['-created_at']

    def get_queryset(self):
        """Get notifications for current user."""
        user = self.request.user

        # Admin can see all notifications
        if user.is_staff:
            return Notification.objects.all()

        # Regular users see their own notifications
        try:
            employee = user.hremployee
            return Notification.objects.filter(
                Q(recipient_user=user) | Q(recipient_employee=employee)
            ).select_related('recipient_user', 'recipient_employee')
        except Exception:
            return Notification.objects.filter(recipient_user=user)

    def get_serializer_class(self):
        """Use different serializer for create action."""
        if self.action == 'create':
            return NotificationCreateSerializer
        return NotificationSerializer

    def create(self, request, *args, **kwargs):
        """
        Send a new notification.

        POST /api/notifications/
        Body: {
            "recipient_user_id": 1,
            "title": "Approval Required",
            "message": "Please approve request #123",
            "priority": "HIGH",
            "channels": ["EMAIL", "PUSH"],
            "action_url": "/approvals/123/"
        }
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        # Get recipients
        from django.contrib.auth import get_user_model
        User = get_user_model()

        recipient_user = None
        recipient_employee = None

        if data.get('recipient_user_id'):
            recipient_user = User.objects.get(id=data['recipient_user_id'])

        if data.get('recipient_employee_id'):
            from floor_app.hr.models import HREmployee
            recipient_employee = HREmployee.objects.get(id=data['recipient_employee_id'])

        # Send notification
        notification = NotificationService.send(
            recipient_user=recipient_user,
            recipient_employee=recipient_employee,
            title=data['title'],
            message=data['message'],
            priority=data.get('priority', 'NORMAL'),
            channels=data.get('channels'),
            category=data.get('category', ''),
            action_url=data.get('action_url', ''),
            action_label=data.get('action_label', ''),
            template_name=data.get('template_name'),
            template_variables=data.get('template_variables')
        )

        output_serializer = NotificationSerializer(notification)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """
        Mark notification as read.

        POST /api/notifications/{id}/mark_read/
        """
        notification = self.get_object()

        if not notification.read_at:
            notification.read_at = timezone.now()
            notification.save(update_fields=['read_at'])

        serializer = self.get_serializer(notification)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """
        Mark all notifications as read for current user.

        POST /api/notifications/mark_all_read/
        """
        queryset = self.get_queryset().filter(read_at__isnull=True)
        count = queryset.update(read_at=timezone.now())

        return Response({
            'success': True,
            'count': count,
            'message': f'{count} notifications marked as read'
        })

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """
        Get count of unread notifications.

        GET /api/notifications/unread_count/
        """
        count = self.get_queryset().filter(read_at__isnull=True).count()

        return Response({
            'count': count
        })

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get notification summary for current user.

        GET /api/notifications/summary/
        """
        queryset = self.get_queryset()

        total = queryset.count()
        unread = queryset.filter(read_at__isnull=True).count()
        by_priority = queryset.values('priority').annotate(count=Count('id'))

        return Response({
            'total': total,
            'unread': unread,
            'read': total - unread,
            'by_priority': list(by_priority)
        })


class NotificationPreferenceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user notification preferences.

    list: Get notification preferences
    retrieve: Get specific user's preferences
    update: Update notification preferences
    """

    queryset = NotificationPreference.objects.all()
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Users can only see their own preferences."""
        user = self.request.user

        if user.is_staff:
            return NotificationPreference.objects.all()

        return NotificationPreference.objects.filter(user=user)

    @action(detail=False, methods=['get', 'put', 'patch'])
    def me(self, request):
        """
        Get or update current user's notification preferences.

        GET /api/notification-preferences/me/
        PUT/PATCH /api/notification-preferences/me/
        """
        # Get or create preferences for current user
        preference, created = NotificationPreference.objects.get_or_create(
            user=request.user
        )

        if request.method == 'GET':
            serializer = self.get_serializer(preference)
            return Response(serializer.data)

        # Update preferences
        serializer = self.get_serializer(
            preference,
            data=request.data,
            partial=(request.method == 'PATCH')
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)


class AnnouncementViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing announcements.

    list: Get all published announcements
    retrieve: Get a specific announcement
    create: Create a new announcement
    update: Update an announcement
    destroy: Delete an announcement
    """

    serializer_class = AnnouncementSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['priority', 'is_published', 'target_type']
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'publish_at', 'priority']
    ordering = ['-created_at']

    def get_queryset(self):
        """Get announcements visible to current user."""
        user = self.request.user

        # Admin can see all announcements
        if user.is_staff:
            return Announcement.objects.all()

        # Regular users see published announcements targeted to them
        now = timezone.now()

        queryset = Announcement.objects.filter(
            is_published=True,
            publish_at__lte=now
        ).filter(
            Q(expire_at__isnull=True) | Q(expire_at__gt=now)
        )

        # Filter by target
        queryset = queryset.filter(
            Q(target_type='ALL') |
            Q(target_users=user)
        )

        return queryset.distinct()

    def get_serializer_class(self):
        """Use different serializer for create action."""
        if self.action == 'create':
            return AnnouncementCreateSerializer
        return AnnouncementSerializer

    def perform_create(self, serializer):
        """Set author to current user."""
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """
        Mark announcement as read by current user.

        POST /api/announcements/{id}/mark_read/
        """
        announcement = self.get_object()
        user = request.user

        # Get or create read record
        read_record, created = AnnouncementRead.objects.get_or_create(
            announcement=announcement,
            user=user
        )

        serializer = AnnouncementReadSerializer(read_record)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def readers(self, request, pk=None):
        """
        Get list of users who read this announcement.

        GET /api/announcements/{id}/readers/
        """
        announcement = self.get_object()
        readers = announcement.read_by.all()

        serializer = AnnouncementReadSerializer(readers, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def unread(self, request):
        """
        Get announcements not yet read by current user.

        GET /api/announcements/unread/
        """
        user = request.user
        queryset = self.get_queryset().exclude(read_by__user=user)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

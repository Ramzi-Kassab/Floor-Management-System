"""
Notification & Announcement System Views

Template-rendering views for notification center, announcements,
and administrative interfaces.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Count, Prefetch
from django.utils import timezone
from django.http import Http404

from .models import (
    Notification,
    NotificationChannel,
    NotificationTemplate,
    NotificationPreference,
    NotificationDelivery,
    Announcement,
    AnnouncementRead,
)


def is_staff_user(user):
    """Check if user is staff member."""
    return user.is_staff or user.is_superuser


@login_required
def notification_center(request):
    """
    Display user's notification center with all notifications.

    Shows:
    - Unread notifications
    - Read notifications
    - Notification statistics
    """
    user = request.user

    # Get user's notifications
    notifications = Notification.objects.filter(
        Q(recipient_user=user) | Q(recipient_employee__user=user)
    ).select_related(
        'template',
        'content_type'
    ).prefetch_related('deliveries')

    # Separate unread and read
    unread_notifications = notifications.filter(read_at__isnull=True)
    read_notifications = notifications.filter(read_at__isnull=False)[:50]  # Limit to 50 most recent

    # Statistics
    stats = {
        'total': notifications.count(),
        'unread': unread_notifications.count(),
        'urgent': notifications.filter(priority='URGENT', read_at__isnull=True).count(),
        'high': notifications.filter(priority='HIGH', read_at__isnull=True).count(),
    }

    # Handle mark all as read
    if request.method == 'POST' and 'mark_all_read' in request.POST:
        unread_count = unread_notifications.update(
            read_at=timezone.now(),
            status='READ'
        )
        messages.success(request, f'{unread_count} notifications marked as read.')
        return redirect('notifications:notification_center')

    context = {
        'unread_notifications': unread_notifications,
        'read_notifications': read_notifications,
        'stats': stats,
        'page_title': 'Notification Center',
    }

    return render(request, 'notifications/notification_center.html', context)


@login_required
def notification_detail(request, pk):
    """
    Display detailed view of a single notification.

    Marks notification as read when viewed.
    Shows delivery status across all channels.
    """
    user = request.user

    try:
        notification = Notification.objects.select_related(
            'template',
            'recipient_user',
            'recipient_employee',
            'content_type'
        ).prefetch_related(
            'deliveries__channel'
        ).get(
            Q(recipient_user=user) | Q(recipient_employee__user=user),
            pk=pk
        )
    except Notification.DoesNotExist:
        messages.error(request, 'Notification not found or you do not have permission to view it.')
        raise Http404('Notification not found')

    # Mark as read
    if not notification.is_read:
        notification.mark_as_read()

    # Get delivery details
    deliveries = notification.deliveries.select_related('channel').all()

    context = {
        'notification': notification,
        'deliveries': deliveries,
        'page_title': notification.title,
    }

    return render(request, 'notifications/notification_detail.html', context)


@login_required
def user_preferences(request):
    """
    Manage user notification preferences.

    Allows users to:
    - Enable/disable channels
    - Set contact information
    - Configure quiet hours
    - Set up daily digest
    """
    user = request.user

    # Get or create preferences
    try:
        preferences = NotificationPreference.objects.select_related(
            'employee'
        ).get(user=user)
    except NotificationPreference.DoesNotExist:
        # Create default preferences
        preferences = NotificationPreference.objects.create(user=user)

    if request.method == 'POST':
        try:
            # Update channel preferences
            preferences.enable_whatsapp = request.POST.get('enable_whatsapp') == 'on'
            preferences.enable_email = request.POST.get('enable_email') == 'on'
            preferences.enable_sms = request.POST.get('enable_sms') == 'on'
            preferences.enable_push = request.POST.get('enable_push') == 'on'
            preferences.enable_in_app = request.POST.get('enable_in_app') == 'on'
            preferences.enable_telegram = request.POST.get('enable_telegram') == 'on'

            # Update contact information
            preferences.whatsapp_number = request.POST.get('whatsapp_number', '').strip()
            preferences.telegram_chat_id = request.POST.get('telegram_chat_id', '').strip()

            # Update quiet hours
            preferences.quiet_hours_enabled = request.POST.get('quiet_hours_enabled') == 'on'
            quiet_start = request.POST.get('quiet_hours_start')
            quiet_end = request.POST.get('quiet_hours_end')

            if quiet_start:
                preferences.quiet_hours_start = quiet_start
            if quiet_end:
                preferences.quiet_hours_end = quiet_end

            # Update digest preferences
            preferences.enable_daily_digest = request.POST.get('enable_daily_digest') == 'on'
            digest_time = request.POST.get('digest_time')
            if digest_time:
                preferences.digest_time = digest_time

            preferences.save()
            messages.success(request, 'Notification preferences updated successfully.')
            return redirect('notifications:user_preferences')

        except Exception as e:
            messages.error(request, f'Error updating preferences: {str(e)}')

    # Get available channels
    available_channels = NotificationChannel.objects.filter(
        is_enabled=True
    ).order_by('priority')

    context = {
        'preferences': preferences,
        'available_channels': available_channels,
        'page_title': 'Notification Preferences',
    }

    return render(request, 'notifications/user_preferences.html', context)


@login_required
def announcement_list(request):
    """
    Display list of announcements visible to the user.

    Shows:
    - Pinned announcements at top
    - Published announcements targeted to user
    - Read/unread status
    """
    user = request.user

    # Get announcements visible to user
    announcements = Announcement.objects.filter(
        status='PUBLISHED',
        is_deleted=False,
    ).select_related(
        'author'
    ).prefetch_related(
        'target_departments',
        'target_locations',
        'target_users',
        Prefetch(
            'reads',
            queryset=AnnouncementRead.objects.filter(user=user),
            to_attr='user_reads'
        )
    )

    # Filter by targeting
    # This is simplified - ideally done at DB level
    visible_announcements = []
    for announcement in announcements:
        if (announcement.target_type == 'ALL' or
            (announcement.target_type == 'CUSTOM' and user in announcement.target_users.all()) or
            (announcement.target_type == 'DEPARTMENT' and hasattr(user, 'hremployee') and
             user.hremployee.current_department in announcement.target_departments.all()) or
            (announcement.target_type == 'LOCATION' and hasattr(user, 'hremployee') and
             user.hremployee.work_location in announcement.target_locations.all())):

            # Check if published and not expired
            if announcement.is_published:
                visible_announcements.append(announcement)

    # Mark announcement as read if clicked
    if request.method == 'POST' and 'mark_read' in request.POST:
        announcement_id = request.POST.get('announcement_id')
        if announcement_id:
            try:
                announcement = Announcement.objects.get(pk=announcement_id)
                AnnouncementRead.objects.get_or_create(
                    announcement=announcement,
                    user=user
                )
                messages.success(request, 'Announcement marked as read.')
            except Announcement.DoesNotExist:
                messages.error(request, 'Announcement not found.')
        return redirect('notifications:announcement_list')

    context = {
        'announcements': visible_announcements,
        'page_title': 'Announcements',
    }

    return render(request, 'notifications/announcement_list.html', context)


@login_required
def announcement_detail(request, pk):
    """
    Display detailed view of an announcement.

    Automatically marks as read when viewed.
    Shows full content, attachments, and action buttons.
    """
    user = request.user

    try:
        announcement = Announcement.objects.select_related(
            'author'
        ).prefetch_related(
            'target_departments',
            'target_locations',
            'target_users',
        ).get(
            pk=pk,
            status='PUBLISHED',
            is_deleted=False
        )
    except Announcement.DoesNotExist:
        messages.error(request, 'Announcement not found or not published.')
        raise Http404('Announcement not found')

    # Check if user should see this announcement
    has_access = False
    if announcement.target_type == 'ALL':
        has_access = True
    elif announcement.target_type == 'CUSTOM' and user in announcement.target_users.all():
        has_access = True
    elif announcement.target_type == 'DEPARTMENT' and hasattr(user, 'hremployee'):
        if user.hremployee.current_department in announcement.target_departments.all():
            has_access = True
    elif announcement.target_type == 'LOCATION' and hasattr(user, 'hremployee'):
        if user.hremployee.work_location in announcement.target_locations.all():
            has_access = True

    if not has_access:
        messages.error(request, 'You do not have permission to view this announcement.')
        raise Http404('Announcement not found')

    # Mark as read
    read_record, created = AnnouncementRead.objects.get_or_create(
        announcement=announcement,
        user=user
    )

    # Get read statistics (for display)
    total_reads = announcement.reads.count()

    context = {
        'announcement': announcement,
        'total_reads': total_reads,
        'is_read': not created,
        'page_title': announcement.title,
    }

    return render(request, 'notifications/announcement_detail.html', context)


@login_required
@user_passes_test(is_staff_user)
def channel_config(request):
    """
    Configure notification channels (staff only).

    Allows staff to:
    - Enable/disable channels
    - Configure API credentials
    - Set rate limits
    - Test channel connectivity
    """
    channels = NotificationChannel.objects.all().order_by('priority')

    if request.method == 'POST':
        try:
            channel_id = request.POST.get('channel_id')
            if channel_id:
                channel = get_object_or_404(NotificationChannel, pk=channel_id)

                # Update channel settings
                channel.is_enabled = request.POST.get('is_enabled') == 'on'
                channel.priority = int(request.POST.get('priority', channel.priority))

                # Rate limiting
                max_per_hour = request.POST.get('max_per_hour')
                max_per_day = request.POST.get('max_per_day')

                channel.max_per_hour = int(max_per_hour) if max_per_hour else None
                channel.max_per_day = int(max_per_day) if max_per_day else None

                channel.save()
                messages.success(request, f'{channel.get_channel_type_display()} channel updated successfully.')

            return redirect('notifications:channel_config')

        except Exception as e:
            messages.error(request, f'Error updating channel: {str(e)}')

    context = {
        'channels': channels,
        'page_title': 'Channel Configuration',
    }

    return render(request, 'notifications/channel_config.html', context)


@login_required
@user_passes_test(is_staff_user)
def template_editor(request):
    """
    Edit notification templates (staff only).

    Allows staff to:
    - Create new templates
    - Edit existing templates
    - Preview templates
    - Manage template variables
    """
    templates = NotificationTemplate.objects.filter(
        is_active=True
    ).order_by('template_type', 'name')

    # Get template types for filter
    template_types = NotificationTemplate.TEMPLATE_TYPES

    # Filter by type if requested
    filter_type = request.GET.get('type')
    if filter_type:
        templates = templates.filter(template_type=filter_type)

    if request.method == 'POST':
        try:
            template_id = request.POST.get('template_id')

            if template_id:
                # Edit existing template
                template = get_object_or_404(NotificationTemplate, pk=template_id)
                action = 'updated'
            else:
                # Create new template
                template = NotificationTemplate()
                action = 'created'

            # Update template fields
            template.template_type = request.POST.get('template_type')
            template.name = request.POST.get('name')
            template.whatsapp_template = request.POST.get('whatsapp_template', '')
            template.email_subject = request.POST.get('email_subject', '')
            template.email_template = request.POST.get('email_template', '')
            template.sms_template = request.POST.get('sms_template', '')
            template.push_title = request.POST.get('push_title', '')
            template.push_body = request.POST.get('push_body', '')
            template.in_app_title = request.POST.get('in_app_title', '')
            template.in_app_message = request.POST.get('in_app_message', '')
            template.is_active = request.POST.get('is_active') == 'on'

            template.save()
            messages.success(request, f'Template "{template.name}" {action} successfully.')
            return redirect('notifications:template_editor')

        except Exception as e:
            messages.error(request, f'Error saving template: {str(e)}')

    context = {
        'templates': templates,
        'template_types': template_types,
        'filter_type': filter_type,
        'page_title': 'Template Editor',
    }

    return render(request, 'notifications/template_editor.html', context)


@login_required
@user_passes_test(is_staff_user)
def delivery_status(request):
    """
    View notification delivery status and statistics (staff only).

    Shows:
    - Recent deliveries
    - Success/failure rates
    - Channel performance
    - Failed deliveries requiring attention
    """
    # Get recent deliveries
    deliveries = NotificationDelivery.objects.select_related(
        'notification',
        'channel',
        'notification__recipient_user'
    ).order_by('-sent_at')[:100]

    # Filter by status if requested
    filter_status = request.GET.get('status')
    if filter_status:
        deliveries = deliveries.filter(status=filter_status)

    # Filter by channel if requested
    filter_channel = request.GET.get('channel')
    if filter_channel:
        deliveries = deliveries.filter(channel__channel_type=filter_channel)

    # Get statistics
    total_deliveries = NotificationDelivery.objects.count()
    failed_deliveries = NotificationDelivery.objects.filter(status='FAILED').count()
    pending_deliveries = NotificationDelivery.objects.filter(status='PENDING').count()

    # Channel statistics
    channel_stats = NotificationDelivery.objects.values(
        'channel__channel_type'
    ).annotate(
        total=Count('id'),
        failed=Count('id', filter=Q(status='FAILED')),
        delivered=Count('id', filter=Q(status='DELIVERED'))
    )

    # Recent notifications
    recent_notifications = Notification.objects.select_related(
        'recipient_user'
    ).order_by('-created_at')[:50]

    context = {
        'deliveries': deliveries,
        'recent_notifications': recent_notifications,
        'total_deliveries': total_deliveries,
        'failed_deliveries': failed_deliveries,
        'pending_deliveries': pending_deliveries,
        'channel_stats': channel_stats,
        'filter_status': filter_status,
        'filter_channel': filter_channel,
        'page_title': 'Delivery Status',
    }

    return render(request, 'notifications/delivery_status.html', context)

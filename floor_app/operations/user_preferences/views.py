"""
User Preferences System Views

Template-rendering views for user preferences and settings.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from .models import (
    UserPreference,
    SavedView,
)


@login_required
def preferences_dashboard(request):
    """
    Main preferences dashboard.

    Shows:
    - User preferences overview
    - Quick settings
    - Personalization options
    """
    try:
        user = request.user

        # Get or create user preferences
        preferences, created = UserPreference.objects.get_or_create(user=user)

        if request.method == 'POST':
            try:
                # Update general preferences
                preferences.theme = request.POST.get('theme', 'LIGHT')
                preferences.language = request.POST.get('language', 'en')
                preferences.timezone = request.POST.get('timezone', 'UTC')
                preferences.date_format = request.POST.get('date_format', 'YYYY-MM-DD')
                preferences.time_format = request.POST.get('time_format', '24')

                # Dashboard settings
                preferences.default_dashboard = request.POST.get('default_dashboard', 'MAIN')
                preferences.show_recent_activities = request.POST.get('show_recent_activities') == 'on'
                preferences.show_quick_actions = request.POST.get('show_quick_actions') == 'on'

                # Save preferences
                preferences.save()

                messages.success(request, 'Preferences updated successfully.')
                return redirect('user_preferences:preferences_dashboard')

            except Exception as e:
                messages.error(request, f'Error updating preferences: {str(e)}')

        # Get dashboard widgets
        widgets = SavedView.objects.filter(
            user=user,
            is_enabled=True
        ).order_by('position')

        # Available themes
        themes = UserPreference.THEME_CHOICES

        # Available languages
        languages = UserPreference.LANGUAGE_CHOICES

        context = {
            'preferences': preferences,
            'widgets': widgets,
            'themes': themes,
            'languages': languages,
            'page_title': 'Preferences',
        }

    except Exception as e:
        messages.error(request, f'Error loading preferences: {str(e)}')
        context = {
            'preferences': None,
            'widgets': [],
            'themes': [],
            'languages': [],
            'page_title': 'Preferences',
        }

    return render(request, 'user_preferences/preferences_dashboard.html', context)


@login_required
def notification_settings(request):
    """
    Notification preferences.

    Allows users to configure:
    - Email notifications
    - Push notifications
    - In-app notifications
    - Notification frequency
    """
    try:
        user = request.user

        # Get or create user preferences
        preferences, created = UserPreference.objects.get_or_create(user=user)

        if request.method == 'POST':
            try:
                # Email notifications
                preferences.email_notifications = request.POST.get('email_notifications') == 'on'
                preferences.email_frequency = request.POST.get('email_frequency', 'INSTANT')

                # Push notifications
                preferences.push_notifications = request.POST.get('push_notifications') == 'on'

                # In-app notifications
                preferences.in_app_notifications = request.POST.get('in_app_notifications') == 'on'

                # Specific notification types
                preferences.notify_on_approval = request.POST.get('notify_on_approval') == 'on'
                preferences.notify_on_message = request.POST.get('notify_on_message') == 'on'
                preferences.notify_on_task = request.POST.get('notify_on_task') == 'on'
                preferences.notify_on_announcement = request.POST.get('notify_on_announcement') == 'on'

                # Quiet hours
                preferences.quiet_hours_enabled = request.POST.get('quiet_hours_enabled') == 'on'
                quiet_start = request.POST.get('quiet_hours_start')
                quiet_end = request.POST.get('quiet_hours_end')

                if quiet_start:
                    preferences.quiet_hours_start = quiet_start
                if quiet_end:
                    preferences.quiet_hours_end = quiet_end

                # Save preferences
                preferences.save()

                messages.success(request, 'Notification settings updated successfully.')
                return redirect('user_preferences:notification_settings')

            except Exception as e:
                messages.error(request, f'Error updating notification settings: {str(e)}')

        # Email frequency options
        frequency_choices = [
            ('INSTANT', 'Instant'),
            ('DAILY', 'Daily Digest'),
            ('WEEKLY', 'Weekly Digest'),
            ('NEVER', 'Never'),
        ]

        context = {
            'preferences': preferences,
            'frequency_choices': frequency_choices,
            'page_title': 'Notification Settings',
        }

    except Exception as e:
        messages.error(request, f'Error loading notification settings: {str(e)}')
        context = {
            'preferences': None,
            'frequency_choices': [],
            'page_title': 'Notification Settings',
        }

    return render(request, 'user_preferences/notification_settings.html', context)

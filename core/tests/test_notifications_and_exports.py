"""
Tests for Notifications and Export Functionality

Tests:
- Notification model methods
- Notification API endpoints
- Export functionality
- Activity logging
"""

import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone

from core.models import Notification, ActivityLog, UserPreference
from core.notification_utils import (
    create_notification,
    notify_users,
    notify_admins,
    get_unread_notifications,
    get_unread_count,
    mark_all_read,
    log_activity,
    log_create,
    log_update,
    log_delete,
)

User = get_user_model()


class TestNotificationModel(TestCase):
    """Test Notification model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_create_notification(self):
        """Test creating a notification."""
        notif = Notification.objects.create(
            user=self.user,
            title='Test Notification',
            message='This is a test message',
            notification_type='INFO',
            priority='NORMAL'
        )

        self.assertEqual(str(notif), 'Test Notification - testuser')
        self.assertFalse(notif.is_read)
        self.assertIsNone(notif.read_at)

    def test_mark_as_read(self):
        """Test marking notification as read."""
        notif = Notification.objects.create(
            user=self.user,
            title='Test Notification',
            message='Test message'
        )

        notif.mark_as_read()

        self.assertTrue(notif.is_read)
        self.assertIsNotNone(notif.read_at)

    def test_mark_as_unread(self):
        """Test marking notification as unread."""
        notif = Notification.objects.create(
            user=self.user,
            title='Test Notification',
            message='Test message'
        )

        notif.mark_as_read()
        notif.mark_as_unread()

        self.assertFalse(notif.is_read)
        self.assertIsNone(notif.read_at)

    def test_get_icon(self):
        """Test get_icon method."""
        notif_info = Notification.objects.create(
            user=self.user,
            title='Info',
            message='Test',
            notification_type='INFO'
        )
        self.assertEqual(notif_info.get_icon(), 'bi-info-circle-fill')

        notif_success = Notification.objects.create(
            user=self.user,
            title='Success',
            message='Test',
            notification_type='SUCCESS'
        )
        self.assertEqual(notif_success.get_icon(), 'bi-check-circle-fill')

        notif_error = Notification.objects.create(
            user=self.user,
            title='Error',
            message='Test',
            notification_type='ERROR'
        )
        self.assertEqual(notif_error.get_icon(), 'bi-x-circle-fill')


class TestNotificationUtils(TestCase):
    """Test notification utility functions."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='testpass123',
            is_staff=True
        )

    def test_create_notification_single_user(self):
        """Test creating notification for single user."""
        notifications = create_notification(
            user=self.user,
            title='Test Title',
            message='Test Message',
            notification_type='INFO'
        )

        self.assertEqual(len(notifications), 1)
        self.assertEqual(notifications[0].user, self.user)
        self.assertEqual(notifications[0].title, 'Test Title')

    def test_create_notification_multiple_users(self):
        """Test creating notification for multiple users."""
        user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )

        notifications = create_notification(
            user=[self.user, user2],
            title='Test Title',
            message='Test Message'
        )

        self.assertEqual(len(notifications), 2)

    def test_notify_users(self):
        """Test notify_users function."""
        users = User.objects.all()
        notifications = notify_users(
            users=users,
            title='Bulk Notification',
            message='Message for all users'
        )

        self.assertGreaterEqual(len(notifications), 2)

    def test_notify_admins(self):
        """Test notify_admins function."""
        notifications = notify_admins(
            title='Admin Notification',
            message='Important message for admins'
        )

        self.assertGreaterEqual(len(notifications), 1)
        # Verify all recipients are staff
        for notif in notifications:
            self.assertTrue(notif.user.is_staff)

    def test_get_unread_notifications(self):
        """Test getting unread notifications."""
        # Create some notifications
        create_notification(self.user, 'Unread 1', 'Message 1')
        create_notification(self.user, 'Unread 2', 'Message 2')
        read_notif = create_notification(self.user, 'Read', 'Message 3')[0]
        read_notif.mark_as_read()

        unread = get_unread_notifications(self.user)

        self.assertEqual(unread.count(), 2)

    def test_get_unread_count(self):
        """Test getting unread notification count."""
        create_notification(self.user, 'Unread 1', 'Message 1')
        create_notification(self.user, 'Unread 2', 'Message 2')

        count = get_unread_count(self.user)

        self.assertEqual(count, 2)

    def test_mark_all_read(self):
        """Test marking all notifications as read."""
        create_notification(self.user, 'Unread 1', 'Message 1')
        create_notification(self.user, 'Unread 2', 'Message 2')

        count = mark_all_read(self.user)

        self.assertEqual(count, 2)
        self.assertEqual(get_unread_count(self.user), 0)


class TestNotificationAPI(TestCase):
    """Test notification API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

    def test_get_notifications(self):
        """Test getting notifications via API."""
        # Create some notifications
        create_notification(self.user, 'Notif 1', 'Message 1')
        create_notification(self.user, 'Notif 2', 'Message 2')

        response = self.client.get(reverse('core:api_notifications_list'))

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('notifications', data)
        self.assertGreaterEqual(len(data['notifications']), 2)

    def test_get_unread_count_api(self):
        """Test getting unread count via API."""
        create_notification(self.user, 'Unread', 'Message')

        response = self.client.get(reverse('core:api_notifications_unread_count'))

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('count', data)
        self.assertGreaterEqual(data['count'], 1)

    def test_mark_notification_read_api(self):
        """Test marking notification as read via API."""
        notif = create_notification(self.user, 'Test', 'Message')[0]

        response = self.client.post(
            reverse('core:api_notification_read', kwargs={'notification_id': notif.id})
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])

        # Verify notification is read
        notif.refresh_from_db()
        self.assertTrue(notif.is_read)

    def test_mark_all_notifications_read_api(self):
        """Test marking all notifications as read via API."""
        create_notification(self.user, 'Notif 1', 'Message 1')
        create_notification(self.user, 'Notif 2', 'Message 2')

        response = self.client.post(reverse('core:api_notifications_mark_all_read'))

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['count'], 2)

    def test_delete_notification_api(self):
        """Test deleting notification via API."""
        notif = create_notification(self.user, 'Test', 'Message')[0]

        response = self.client.post(
            reverse('core:api_notification_delete', kwargs={'notification_id': notif.id})
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])

        # Verify notification is deleted
        self.assertFalse(Notification.objects.filter(id=notif.id).exists())

    def test_api_requires_authentication(self):
        """Test that API endpoints require authentication."""
        self.client.logout()

        response = self.client.get(reverse('core:api_notifications_list'))
        self.assertIn(response.status_code, [302, 401, 403])


class TestActivityLog(TestCase):
    """Test activity logging functionality."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_log_activity(self):
        """Test basic activity logging."""
        activity = log_activity(
            user=self.user,
            action='CREATE',
            description='Created test object'
        )

        self.assertEqual(activity.user, self.user)
        self.assertEqual(activity.action, 'CREATE')
        self.assertEqual(activity.description, 'Created test object')

    def test_log_create(self):
        """Test log_create helper."""
        # Create a test object (using User as example)
        test_user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='testpass123'
        )

        activity = log_create(self.user, test_user)

        self.assertEqual(activity.action, 'CREATE')
        self.assertIn('newuser', activity.description)

    def test_log_update(self):
        """Test log_update helper."""
        test_user = User.objects.create_user(
            username='updateuser',
            email='update@example.com',
            password='testpass123'
        )

        changes = {'email': 'newemail@example.com'}
        activity = log_update(self.user, test_user, changes=changes)

        self.assertEqual(activity.action, 'UPDATE')
        self.assertIn('email', activity.extra_data['changes'])

    def test_log_delete(self):
        """Test log_delete helper."""
        test_user = User.objects.create_user(
            username='deleteuser',
            email='delete@example.com',
            password='testpass123'
        )

        activity = log_delete(self.user, test_user)

        self.assertEqual(activity.action, 'DELETE')
        self.assertIn('object_str', activity.extra_data)


class TestExportFunctionality(TestCase):
    """Test export functionality."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

    def test_export_data_validation(self):
        """Test export endpoint validation."""
        # Test missing model parameter
        response = self.client.get(reverse('core:api_export_data'), {
            'format': 'csv',
            'fields': 'id,username'
        })
        self.assertEqual(response.status_code, 400)

        # Test missing fields parameter
        response = self.client.get(reverse('core:api_export_data'), {
            'model': 'auth.User',
            'format': 'csv'
        })
        self.assertEqual(response.status_code, 400)

    def test_export_data_invalid_model(self):
        """Test export with invalid model."""
        response = self.client.get(reverse('core:api_export_data'), {
            'model': 'invalid.Model',
            'format': 'csv',
            'fields': 'id'
        })
        self.assertEqual(response.status_code, 400)

    def test_export_data_csv(self):
        """Test CSV export."""
        response = self.client.get(reverse('core:api_export_data'), {
            'model': 'auth.User',
            'format': 'csv',
            'fields': 'id,username,email'
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment', response['Content-Disposition'])

    def test_export_data_with_headers(self):
        """Test export with custom headers."""
        response = self.client.get(reverse('core:api_export_data'), {
            'model': 'auth.User',
            'format': 'csv',
            'fields': 'id,username,email',
            'headers': 'ID,Username,Email Address'
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')

    def test_export_data_requires_authentication(self):
        """Test that export requires authentication."""
        self.client.logout()

        response = self.client.get(reverse('core:api_export_data'), {
            'model': 'auth.User',
            'format': 'csv',
            'fields': 'id,username'
        })

        self.assertIn(response.status_code, [302, 401, 403])


class TestIntegration(TestCase):
    """Integration tests for notifications and exports."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

    def test_notification_workflow(self):
        """Test complete notification workflow."""
        # 1. Create notification
        notif = create_notification(
            user=self.user,
            title='Workflow Test',
            message='Testing complete workflow',
            notification_type='INFO',
            priority='NORMAL'
        )[0]

        # 2. Verify it appears in API
        response = self.client.get(reverse('core:api_notifications_list'))
        data = response.json()
        self.assertGreater(len(data['notifications']), 0)

        # 3. Mark as read
        response = self.client.post(
            reverse('core:api_notification_read', kwargs={'notification_id': notif.id})
        )
        self.assertTrue(response.json()['success'])

        # 4. Verify unread count decreased
        response = self.client.get(reverse('core:api_notifications_unread_count'))
        count = response.json()['count']
        self.assertEqual(count, 0)

        # 5. Delete notification
        response = self.client.post(
            reverse('core:api_notification_delete', kwargs={'notification_id': notif.id})
        )
        self.assertTrue(response.json()['success'])

    def test_export_logs_activity(self):
        """Test that export creates activity log."""
        # Perform export
        response = self.client.get(reverse('core:api_export_data'), {
            'model': 'auth.User',
            'format': 'csv',
            'fields': 'id,username'
        })

        self.assertEqual(response.status_code, 200)

        # Verify activity was logged
        activity_exists = ActivityLog.objects.filter(
            user=self.user,
            action='EXPORT'
        ).exists()

        self.assertTrue(activity_exists)

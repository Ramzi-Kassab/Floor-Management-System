"""
Unit tests for Core models

Tests:
- AuditLog
- ActivityLog
- SystemEvent
- ChangeHistory
- Notification
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from ..models import AuditLog, ActivityLog, SystemEvent, ChangeHistory
from ..notifications import Notification


class AuditLogTestCase(TestCase):
    """Test AuditLog model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_create_audit_log(self):
        """Test creating an audit log"""
        log = AuditLog.log_action(
            user=self.user,
            action='CREATE',
            message='Test audit log',
            ip_address='127.0.0.1'
        )

        self.assertIsNotNone(log)
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.action, 'CREATE')
        self.assertEqual(log.message, 'Test audit log')
        self.assertEqual(log.ip_address, '127.0.0.1')

    def test_audit_log_string_representation(self):
        """Test __str__ method"""
        log = AuditLog.log_action(
            user=self.user,
            action='UPDATE',
            message='Test'
        )

        self.assertIn(self.user.username, str(log))
        self.assertIn('UPDATE', str(log))


class ActivityLogTestCase(TestCase):
    """Test ActivityLog model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_create_activity_log(self):
        """Test creating an activity log"""
        log = ActivityLog.objects.create(
            user=self.user,
            activity_type='PAGE_VIEW',
            path='/dashboard/',
            duration_ms=150
        )

        self.assertEqual(log.user, self.user)
        self.assertEqual(log.activity_type, 'PAGE_VIEW')
        self.assertEqual(log.path, '/dashboard/')
        self.assertEqual(log.duration_ms, 150)

    def test_activity_log_ordering(self):
        """Test that logs are ordered by timestamp DESC"""
        log1 = ActivityLog.objects.create(
            user=self.user,
            activity_type='PAGE_VIEW',
            path='/page1/'
        )
        log2 = ActivityLog.objects.create(
            user=self.user,
            activity_type='PAGE_VIEW',
            path='/page2/'
        )

        logs = ActivityLog.objects.all()
        self.assertEqual(logs[0], log2)  # Most recent first
        self.assertEqual(logs[1], log1)


class SystemEventTestCase(TestCase):
    """Test SystemEvent model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_create_system_event(self):
        """Test creating a system event"""
        event = SystemEvent.log_event(
            level='ERROR',
            category='SYSTEM',
            event_name='Test Error',
            message='This is a test error',
            user=self.user
        )

        self.assertEqual(event.level, 'ERROR')
        self.assertEqual(event.category, 'SYSTEM')
        self.assertEqual(event.event_name, 'Test Error')
        self.assertFalse(event.is_resolved)

    def test_log_event_with_exception(self):
        """Test logging an event with exception"""
        try:
            raise ValueError("Test exception")
        except ValueError as e:
            event = SystemEvent.log_event(
                level='ERROR',
                category='SYSTEM',
                event_name='Exception Test',
                message='Test exception logging',
                exception=e
            )

            self.assertEqual(event.exception_type, 'ValueError')
            self.assertIn('Test exception', event.exception_message)
            self.assertIsNotNone(event.stack_trace)


class NotificationTestCase(TestCase):
    """Test Notification model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_create_notification(self):
        """Test creating a notification"""
        notification = Notification.create_notification(
            user=self.user,
            title='Test Notification',
            message='This is a test',
            notification_type='INFO'
        )

        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.title, 'Test Notification')
        self.assertFalse(notification.is_read)
        self.assertFalse(notification.email_sent)

    def test_mark_as_read(self):
        """Test marking notification as read"""
        notification = Notification.create_notification(
            user=self.user,
            title='Test',
            message='Test'
        )

        self.assertFalse(notification.is_read)
        self.assertIsNone(notification.read_at)

        notification.mark_as_read()

        self.assertTrue(notification.is_read)
        self.assertIsNotNone(notification.read_at)

    def test_bulk_create_notifications(self):
        """Test creating notifications for multiple users"""
        user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com'
        )

        notifications = Notification.bulk_create_notifications(
            users=[self.user, user2],
            title='Bulk Test',
            message='Bulk notification test'
        )

        self.assertEqual(len(notifications), 2)
        self.assertEqual(Notification.objects.count(), 2)

    def test_unread_count(self):
        """Test getting unread count"""
        Notification.create_notification(
            user=self.user,
            title='Test 1',
            message='Test'
        )
        Notification.create_notification(
            user=self.user,
            title='Test 2',
            message='Test'
        )

        count = Notification.get_unread_count(self.user)
        self.assertEqual(count, 2)

        # Mark one as read
        notification = Notification.objects.first()
        notification.mark_as_read()

        count = Notification.get_unread_count(self.user)
        self.assertEqual(count, 1)

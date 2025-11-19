"""
Tests for Health Check Endpoints

Test health, readiness, and liveness check endpoints.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.db import connection
import json


class HealthCheckTests(TestCase):
    """Test health check endpoints."""

    def setUp(self):
        """Set up test client."""
        self.client = Client()

    def test_health_check_endpoint_exists(self):
        """Test that health check endpoint is accessible."""
        response = self.client.get(reverse('core:health_check'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_health_check_response_structure(self):
        """Test health check response has correct structure."""
        response = self.client.get(reverse('core:health_check'))
        data = json.loads(response.content)

        # Check required fields
        self.assertIn('status', data)
        self.assertIn('timestamp', data)
        self.assertIn('version', data)
        self.assertIn('components', data)

    def test_health_check_database_component(self):
        """Test that health check includes database status."""
        response = self.client.get(reverse('core:health_check'))
        data = json.loads(response.content)

        self.assertIn('database', data['components'])
        self.assertIn('status', data['components']['database'])

    def test_health_check_with_healthy_database(self):
        """Test health check when database is healthy."""
        response = self.client.get(reverse('core:health_check'))
        data = json.loads(response.content)

        # Database should be healthy in tests
        self.assertEqual(data['components']['database']['status'], 'healthy')
        self.assertEqual(data['status'], 'healthy')

    def test_readiness_check_endpoint(self):
        """Test readiness check endpoint."""
        response = self.client.get(reverse('core:readiness_check'))

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertIn('status', data)
        self.assertIn('message', data)

    def test_readiness_check_with_no_pending_migrations(self):
        """Test readiness check when migrations are up to date."""
        response = self.client.get(reverse('core:readiness_check'))
        data = json.loads(response.content)

        # In tests, migrations should be applied
        self.assertEqual(data['status'], 'ready')

    def test_liveness_check_endpoint(self):
        """Test liveness check endpoint."""
        response = self.client.get(reverse('core:liveness_check'))

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertEqual(data['status'], 'alive')
        self.assertIn('timestamp', data)

    def test_health_check_url_pattern(self):
        """Test health check can be accessed via standard path."""
        response = self.client.get('/api/health/')

        self.assertEqual(response.status_code, 200)

    def test_health_check_returns_json(self):
        """Test health check returns valid JSON."""
        response = self.client.get(reverse('core:health_check'))

        try:
            data = json.loads(response.content)
            self.assertIsInstance(data, dict)
        except json.JSONDecodeError:
            self.fail("Health check did not return valid JSON")


class HealthCheckSecurityTests(TestCase):
    """Test health check security."""

    def setUp(self):
        """Set up test client."""
        self.client = Client()

    def test_health_check_does_not_expose_sensitive_info(self):
        """Test that health check doesn't expose sensitive information."""
        response = self.client.get(reverse('core:health_check'))
        data = json.loads(response.content)
        content_str = json.dumps(data).lower()

        # Should not contain sensitive info
        sensitive_terms = ['password', 'secret', 'key', 'token', 'credential']

        for term in sensitive_terms:
            self.assertNotIn(term, content_str,
                           f"Health check exposed sensitive term: {term}")

    def test_health_check_accessible_without_authentication(self):
        """Test health check is accessible without authentication."""
        # Don't log in
        response = self.client.get(reverse('core:health_check'))

        # Should still be accessible
        self.assertEqual(response.status_code, 200)


class HealthCheckPerformanceTests(TestCase):
    """Test health check performance."""

    def test_health_check_response_time(self):
        """Test that health check responds quickly."""
        import time

        start_time = time.time()
        response = self.client.get(reverse('core:health_check'))
        end_time = time.time()

        response_time = end_time - start_time

        # Health check should respond in less than 1 second
        self.assertLess(response_time, 1.0,
                       f"Health check took too long: {response_time:.2f}s")

    def test_multiple_health_checks_dont_slow_down(self):
        """Test that multiple health checks maintain performance."""
        import time

        times = []

        for _ in range(10):
            start_time = time.time()
            self.client.get(reverse('core:health_check'))
            end_time = time.time()
            times.append(end_time - start_time)

        avg_time = sum(times) / len(times)

        # Average should still be under 1 second
        self.assertLess(avg_time, 1.0,
                       f"Average health check time: {avg_time:.2f}s")

"""
Tests for URL Resolution and Namespace Consistency

Tests that all key URLs across the application:
- Resolve correctly with their namespaces
- Return appropriate HTTP status codes
- Use correct view classes/functions
- Maintain namespace consistency
"""

from django.test import TestCase, Client
from django.urls import reverse, resolve, NoReverseMatch
from django.contrib.auth import get_user_model

User = get_user_model()


class TestCoreURLResolution(TestCase):
    """Test Core module URL resolution."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()

    def test_core_home_url_resolves(self):
        """Test that core:home URL resolves correctly."""
        url = reverse('core:home')
        self.assertEqual(url, '/')

    def test_core_main_dashboard_url_resolves(self):
        """Test that core:main_dashboard URL resolves correctly."""
        url = reverse('core:main_dashboard')
        self.assertEqual(url, '/dashboard/')

    def test_core_user_preferences_url_resolves(self):
        """Test that core:user_preferences URL resolves correctly."""
        url = reverse('core:user_preferences')
        self.assertEqual(url, '/preferences/')

    def test_core_finance_dashboard_url_resolves(self):
        """Test that core:finance_dashboard URL resolves correctly."""
        url = reverse('core:finance_dashboard')
        self.assertEqual(url, '/finance/')

    def test_core_search_urls_resolve(self):
        """Test that core global search URLs resolve correctly."""
        url = reverse('core:global_search')
        self.assertEqual(url, '/search/')

        api_url = reverse('core:global_search_api')
        self.assertEqual(api_url, '/search/api/')


class TestHRURLResolution(TestCase):
    """Test HR module URL resolution."""

    def test_hr_dashboard_url_resolves(self):
        """Test that hr:hr_dashboard URL resolves correctly."""
        url = reverse('hr:hr_dashboard')
        self.assertEqual(url, '/hr/')

    def test_hr_employee_urls_resolve(self):
        """Test that HR employee URLs resolve correctly."""
        list_url = reverse('hr:employee_list')
        self.assertEqual(list_url, '/hr/employees/')

        create_url = reverse('hr:employee_create')
        self.assertEqual(create_url, '/hr/employees/create/')

        # Detail/update/delete require pk
        detail_url = reverse('hr:employee_detail', kwargs={'pk': 1})
        self.assertIn('/hr/employees/1/', detail_url)

    def test_hr_position_urls_resolve(self):
        """Test that HR position URLs resolve correctly."""
        list_url = reverse('hr:position_list')
        self.assertEqual(list_url, '/hr/positions/')

        create_url = reverse('hr:position_create')
        self.assertEqual(create_url, '/hr/positions/create/')

        detail_url = reverse('hr:position_detail', kwargs={'pk': 1})
        self.assertIn('/hr/positions/1/', detail_url)

    def test_hr_department_urls_resolve(self):
        """Test that HR department URLs resolve correctly."""
        list_url = reverse('hr:department_list')
        self.assertEqual(list_url, '/hr/departments/')

        create_url = reverse('hr:department_create')
        self.assertEqual(create_url, '/hr/departments/create/')


class TestProductionURLResolution(TestCase):
    """Test Production module URL resolution."""

    def test_production_dashboard_url_resolves(self):
        """Test that production:dashboard URL resolves correctly."""
        url = reverse('production:dashboard')
        self.assertEqual(url, '/production/')

    def test_production_jobcard_urls_resolve(self):
        """Test that production job card URLs resolve correctly."""
        list_url = reverse('production:jobcard_list')
        self.assertEqual(list_url, '/production/jobcards/')

        create_url = reverse('production:jobcard_create')
        self.assertEqual(create_url, '/production/jobcards/create/')

        detail_url = reverse('production:jobcard_detail', kwargs={'pk': 1})
        self.assertIn('/production/jobcards/1/', detail_url)

    def test_production_batch_urls_resolve(self):
        """Test that production batch URLs resolve correctly."""
        list_url = reverse('production:batch_list')
        self.assertEqual(list_url, '/production/batches/')

        create_url = reverse('production:batch_create')
        self.assertEqual(create_url, '/production/batches/create/')

    def test_production_global_lists_resolve(self):
        """Test that production global list views resolve correctly (NEW)."""
        # These are the new global list views added in the routing fix
        eval_url = reverse('production:evaluation_list_all')
        self.assertEqual(eval_url, '/production/evaluations/')

        ndt_url = reverse('production:ndt_list_all')
        self.assertEqual(ndt_url, '/production/ndt/')

        thread_url = reverse('production:thread_inspection_list_all')
        self.assertEqual(thread_url, '/production/thread-inspections/')

        checklist_url = reverse('production:checklist_list_all')
        self.assertEqual(checklist_url, '/production/checklists/')


class TestInventoryURLResolution(TestCase):
    """Test Inventory module URL resolution."""

    def test_inventory_dashboard_url_resolves(self):
        """Test that inventory:dashboard URL resolves correctly."""
        url = reverse('inventory:dashboard')
        self.assertEqual(url, '/inventory/')

    def test_inventory_item_urls_resolve(self):
        """Test that inventory item URLs resolve correctly."""
        list_url = reverse('inventory:item_list')
        self.assertEqual(list_url, '/inventory/items/')

        create_url = reverse('inventory:item_create')
        self.assertEqual(create_url, '/inventory/items/create/')

        detail_url = reverse('inventory:item_detail', kwargs={'pk': 1})
        self.assertIn('/inventory/items/1/', detail_url)

    def test_inventory_location_urls_resolve(self):
        """Test that inventory location URLs resolve correctly."""
        list_url = reverse('inventory:location_list')
        self.assertEqual(list_url, '/inventory/locations/')

        create_url = reverse('inventory:location_create')
        self.assertEqual(create_url, '/inventory/locations/create/')

    def test_inventory_bitdesign_urls_resolve(self):
        """Test that inventory bit design URLs resolve correctly."""
        list_url = reverse('inventory:bitdesign_list')
        self.assertEqual(list_url, '/inventory/bitdesigns/')

        create_url = reverse('inventory:bitdesign_create')
        self.assertEqual(create_url, '/inventory/bitdesigns/create/')


class TestQualityURLResolution(TestCase):
    """Test Quality module URL resolution."""

    def test_quality_dashboard_url_resolves(self):
        """Test that quality:dashboard URL resolves correctly."""
        url = reverse('quality:dashboard')
        self.assertEqual(url, '/quality/')

    def test_quality_ncr_urls_resolve(self):
        """Test that quality NCR URLs resolve correctly."""
        list_url = reverse('quality:ncr_list')
        self.assertEqual(list_url, '/quality/ncrs/')

        create_url = reverse('quality:ncr_create')
        self.assertEqual(create_url, '/quality/ncrs/create/')

        detail_url = reverse('quality:ncr_detail', kwargs={'pk': 1})
        self.assertIn('/quality/ncrs/1/', detail_url)


class TestEvaluationURLResolution(TestCase):
    """Test Evaluation module URL resolution."""

    def test_evaluation_dashboard_url_resolves(self):
        """Test that evaluation:dashboard URL resolves correctly."""
        url = reverse('evaluation:dashboard')
        self.assertEqual(url, '/evaluation/')

    def test_evaluation_session_urls_resolve(self):
        """Test that evaluation session URLs resolve correctly."""
        list_url = reverse('evaluation:session_list')
        self.assertEqual(list_url, '/evaluation/sessions/')

        create_url = reverse('evaluation:session_create')
        self.assertEqual(create_url, '/evaluation/sessions/create/')

        detail_url = reverse('evaluation:session_detail', kwargs={'pk': 1})
        self.assertIn('/evaluation/sessions/1/', detail_url)


class TestURLNamespaceConsistency(TestCase):
    """Test URL namespace consistency across all modules."""

    def test_all_core_urls_use_namespace(self):
        """Test that all core URLs use the 'core' namespace."""
        core_urls = [
            'core:home',
            'core:main_dashboard',
            'core:user_preferences',
            'core:finance_dashboard',
            'core:global_search',
            'core:global_search_api',
        ]

        for url_name in core_urls:
            with self.subTest(url=url_name):
                try:
                    url = reverse(url_name)
                    self.assertIsNotNone(url)
                except NoReverseMatch:
                    self.fail(f"URL {url_name} does not resolve")

    def test_all_hr_urls_use_namespace(self):
        """Test that all HR URLs use the 'hr' namespace."""
        hr_urls = [
            'hr:hr_dashboard',
            'hr:employee_list',
            'hr:employee_create',
            'hr:position_list',
            'hr:position_create',
            'hr:department_list',
            'hr:department_create',
        ]

        for url_name in hr_urls:
            with self.subTest(url=url_name):
                try:
                    url = reverse(url_name)
                    self.assertIsNotNone(url)
                except NoReverseMatch:
                    self.fail(f"URL {url_name} does not resolve")

    def test_all_production_urls_use_namespace(self):
        """Test that all production URLs use the 'production' namespace."""
        production_urls = [
            'production:dashboard',
            'production:jobcard_list',
            'production:batch_list',
            'production:evaluation_list_all',
            'production:ndt_list_all',
            'production:thread_inspection_list_all',
            'production:checklist_list_all',
        ]

        for url_name in production_urls:
            with self.subTest(url=url_name):
                try:
                    url = reverse(url_name)
                    self.assertIsNotNone(url)
                except NoReverseMatch:
                    self.fail(f"URL {url_name} does not resolve")

    def test_non_namespaced_urls_fail(self):
        """Test that non-namespaced URLs (except auth) raise NoReverseMatch."""
        # These should NOT resolve without namespace
        non_namespaced = [
            'home',  # Should be 'core:home'
            'employee_list',  # Should be 'hr:employee_list'
            'dashboard',  # Should have a namespace prefix
        ]

        for url_name in non_namespaced:
            with self.subTest(url=url_name):
                # These should fail because they're not properly namespaced
                # (except if they happen to be defined as auth URLs)
                if url_name not in ['login', 'logout', 'signup']:
                    with self.assertRaises(NoReverseMatch):
                        reverse(url_name)


class TestAuthenticationURLs(TestCase):
    """Test authentication URL resolution."""

    def test_auth_urls_resolve(self):
        """Test that authentication URLs resolve correctly."""
        # These are intentionally non-namespaced per Django convention
        login_url = reverse('login')
        self.assertEqual(login_url, '/login/')

        logout_url = reverse('logout')
        self.assertEqual(logout_url, '/logout/')

        signup_url = reverse('signup')
        self.assertEqual(signup_url, '/signup/')


class TestDashboardCardRouting(TestCase):
    """Test that dashboard cards route to correct pages."""

    def test_production_dashboard_cards_route_correctly(self):
        """Test that production dashboard cards link to correct global lists."""
        # These URLs were specifically fixed in the routing cleanup
        urls_to_test = [
            ('production:evaluation_list_all', '/production/evaluations/'),
            ('production:ndt_list_all', '/production/ndt/'),
            ('production:thread_inspection_list_all', '/production/thread-inspections/'),
            ('production:checklist_list_all', '/production/checklists/'),
        ]

        for url_name, expected_path in urls_to_test:
            with self.subTest(url=url_name):
                url = reverse(url_name)
                self.assertEqual(url, expected_path)

    def test_hr_dashboard_cards_route_correctly(self):
        """Test that HR dashboard cards link correctly."""
        urls_to_test = [
            ('hr:employee_list', '/hr/employees/'),
            ('hr:position_list', '/hr/positions/'),
            ('hr:department_list', '/hr/departments/'),
        ]

        for url_name, expected_path in urls_to_test:
            with self.subTest(url=url_name):
                url = reverse(url_name)
                self.assertEqual(url, expected_path)


class TestURLViewMapping(TestCase):
    """Test that URLs map to correct view functions/classes."""

    def test_core_urls_map_to_correct_views(self):
        """Test that core URLs resolve to correct view functions."""
        from core.views import main_dashboard, global_search

        # Test main_dashboard
        resolver = resolve('/dashboard/')
        self.assertEqual(resolver.func, main_dashboard)

        # Test global_search
        resolver = resolve('/search/')
        self.assertEqual(resolver.func, global_search)

    def test_production_urls_map_to_correct_views(self):
        """Test that production URLs resolve to correct view classes."""
        from floor_app.operations.production.views import (
            ProductionDashboard,
            EvaluationSessionListAll,
            NDTRecordListAll,
            ThreadInspectionListAll,
            ChecklistListAll,
        )

        # Test dashboard
        resolver = resolve('/production/')
        self.assertEqual(resolver.func.view_class, ProductionDashboard)

        # Test new global list views
        resolver = resolve('/production/evaluations/')
        self.assertEqual(resolver.func.view_class, EvaluationSessionListAll)

        resolver = resolve('/production/ndt/')
        self.assertEqual(resolver.func.view_class, NDTRecordListAll)

        resolver = resolve('/production/thread-inspections/')
        self.assertEqual(resolver.func.view_class, ThreadInspectionListAll)

        resolver = resolve('/production/checklists/')
        self.assertEqual(resolver.func.view_class, ChecklistListAll)

"""
Tests for Global Search Functionality

Tests the comprehensive global search system including:
- GlobalSearch utility class
- Search across multiple models
- Module filtering
- Search history tracking
- Saved filters
- Search views and API endpoints
"""

import json
from datetime import datetime
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from core.models import UserPreference, CostCenter
from core.search_utils import GlobalSearch, SearchHistory, SavedFilter, AdvancedFilter
from floor_app.operations.hr.models import HRPeople, HREmployee, Department, Position
from floor_app.operations.inventory.models import Item, Location, BitDesign, BitDesignRevision

User = get_user_model()


class TestGlobalSearchUtility(TestCase):
    """Test the GlobalSearch utility class."""

    def setUp(self):
        """Set up test data."""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # Create test HR data
        self.person = HRPeople.objects.create(
            first_name_en='John',
            middle_name_en='Michael',
            last_name_en='Smith',
            first_name_ar='جون',
            last_name_ar='سميث',
            gender='MALE',
            date_of_birth='1990-05-15',
            primary_nationality_iso2='US',
            national_id='123456789'
        )

        self.department = Department.objects.create(
            name='Engineering Department',
            department_type='PRODUCTION'
        )

        self.position = Position.objects.create(
            name='Senior Engineer',
            department=self.department,
            position_level='SENIOR',
            salary_grade='GRADE_B',
            is_active=True
        )

        self.employee = HREmployee.objects.create(
            person=self.person,
            employee_no='EMP001',
            status='ACTIVE',
            department=self.department,
            position=self.position,
            hire_date='2024-01-01'
        )

        # Create test Inventory data
        self.location = Location.objects.create(
            code='WH-01',
            name='Main Warehouse',
            location_type='WAREHOUSE',
            is_active=True
        )

        self.item = Item.objects.create(
            item_no='ITEM-001',
            name='Test Item',
            item_type='RAW_MATERIAL',
            uom='PIECE'
        )

        # Create test Core data
        self.cost_center = CostCenter.objects.create(
            code='CC-001',
            name='Production Cost Center',
            status='ACTIVE',
            created_by=self.user
        )

    def test_global_search_finds_people(self):
        """Test that global search finds people records."""
        search = GlobalSearch(query='John', limit_per_model=10)
        results = search.execute()

        # Should find at least one result group
        self.assertGreater(len(results), 0)

        # Find the People results
        people_results = None
        for group in results:
            if group['model_label'] == 'People':
                people_results = group
                break

        self.assertIsNotNone(people_results, "Should find People results")
        self.assertGreater(people_results['count'], 0)
        self.assertEqual(people_results['results'][0]['display'], 'John Smith')

    def test_global_search_finds_items(self):
        """Test that global search finds inventory items."""
        search = GlobalSearch(query='ITEM-001', limit_per_model=10)
        results = search.execute()

        # Find the Item results
        item_results = None
        for group in results:
            if group['model_label'] == 'Items':
                item_results = group
                break

        self.assertIsNotNone(item_results, "Should find Item results")
        self.assertGreater(item_results['count'], 0)

    def test_global_search_finds_locations(self):
        """Test that global search finds locations."""
        search = GlobalSearch(query='Warehouse', limit_per_model=10)
        results = search.execute()

        # Find the Location results
        location_results = None
        for group in results:
            if group['model_label'] == 'Locations':
                location_results = group
                break

        self.assertIsNotNone(location_results, "Should find Location results")
        self.assertGreater(location_results['count'], 0)

    def test_global_search_module_filter(self):
        """Test that module filtering works correctly."""
        # Search only in HR module
        search = GlobalSearch(query='John', modules=['hr'], limit_per_model=10)
        results = search.execute()

        # Should only have HR results
        for group in results:
            model_path = group['model_path']
            self.assertTrue(
                model_path.startswith('hr.'),
                f"Should only return HR models, got {model_path}"
            )

    def test_global_search_minimum_query_length(self):
        """Test that searches require minimum 2 characters."""
        # Single character should return empty
        search = GlobalSearch(query='J', limit_per_model=10)
        results = search.execute()
        self.assertEqual(len(results), 0)

        # Empty query should return empty
        search = GlobalSearch(query='', limit_per_model=10)
        results = search.execute()
        self.assertEqual(len(results), 0)

    def test_global_search_case_insensitive(self):
        """Test that search is case-insensitive."""
        search1 = GlobalSearch(query='john', limit_per_model=10)
        results1 = search1.execute()

        search2 = GlobalSearch(query='JOHN', limit_per_model=10)
        results2 = search2.execute()

        # Both should return same number of groups
        self.assertEqual(len(results1), len(results2))

    def test_global_search_partial_match(self):
        """Test that partial matches work."""
        search = GlobalSearch(query='Eng', limit_per_model=10)
        results = search.execute()

        # Should find Engineering Department and Senior Engineer
        self.assertGreater(len(results), 0)

    def test_global_search_limit_per_model(self):
        """Test that limit_per_model works correctly."""
        # Create 15 people
        for i in range(15):
            HRPeople.objects.create(
                first_name_en=f'Test{i}',
                last_name_en='User',
                gender='MALE',
                date_of_birth='1990-01-01',
                primary_nationality_iso2='US',
                national_id=f'ID{i:09d}'
            )

        search = GlobalSearch(query='Test', limit_per_model=5)
        results = search.execute()

        # Find People results
        people_results = None
        for group in results:
            if group['model_label'] == 'People':
                people_results = group
                break

        # Should be limited to 5 results
        self.assertIsNotNone(people_results)
        self.assertLessEqual(len(people_results['results']), 5)

    def test_global_search_excludes_deleted(self):
        """Test that soft-deleted records are excluded."""
        # Mark person as deleted
        self.person.is_deleted = True
        self.person.save()

        search = GlobalSearch(query='John', limit_per_model=10)
        results = search.execute()

        # Should not find the deleted person
        people_results = None
        for group in results:
            if group['model_label'] == 'People':
                people_results = group
                break

        if people_results:
            # No results or results don't include our deleted person
            for result in people_results['results']:
                self.assertNotEqual(result['id'], self.person.id)


class TestSearchHistory(TestCase):
    """Test the SearchHistory functionality."""

    def setUp(self):
        """Set up test user."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_add_search_creates_history(self):
        """Test that adding search creates history."""
        SearchHistory.add_search(self.user, 'test query')

        recent = SearchHistory.get_recent_searches(self.user)
        self.assertEqual(len(recent), 1)
        self.assertEqual(recent[0]['query'], 'test query')

    def test_search_history_limited_to_20(self):
        """Test that search history is limited to 20 items."""
        # Add 25 searches
        for i in range(25):
            SearchHistory.add_search(self.user, f'query {i}')

        recent = SearchHistory.get_recent_searches(self.user)
        self.assertEqual(len(recent), 20)

        # Should have the most recent 20
        self.assertEqual(recent[0]['query'], 'query 24')
        self.assertEqual(recent[19]['query'], 'query 5')

    def test_search_history_with_module(self):
        """Test that module is stored in search history."""
        SearchHistory.add_search(self.user, 'test', module='hr')

        recent = SearchHistory.get_recent_searches(self.user)
        self.assertEqual(recent[0]['module'], 'hr')

    def test_get_recent_searches_limit(self):
        """Test that get_recent_searches respects limit."""
        for i in range(10):
            SearchHistory.add_search(self.user, f'query {i}')

        recent = SearchHistory.get_recent_searches(self.user, limit=5)
        self.assertEqual(len(recent), 5)

    def test_clear_search_history(self):
        """Test clearing search history."""
        SearchHistory.add_search(self.user, 'test 1')
        SearchHistory.add_search(self.user, 'test 2')

        SearchHistory.clear_history(self.user)

        recent = SearchHistory.get_recent_searches(self.user)
        self.assertEqual(len(recent), 0)


class TestSavedFilters(TestCase):
    """Test the SavedFilter functionality."""

    def setUp(self):
        """Set up test user."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_save_filter(self):
        """Test saving a filter."""
        filters = {
            'status': 'ACTIVE',
            'department': 'Engineering'
        }

        SavedFilter.save_filter(self.user, 'My Filter', filters, module='hr')

        saved = SavedFilter.get_saved_filters(self.user)
        self.assertEqual(len(saved), 1)
        self.assertEqual(saved[0]['name'], 'My Filter')
        self.assertEqual(saved[0]['filters']['status'], 'ACTIVE')

    def test_multiple_saved_filters(self):
        """Test saving multiple filters."""
        SavedFilter.save_filter(self.user, 'Filter 1', {'test': '1'})
        SavedFilter.save_filter(self.user, 'Filter 2', {'test': '2'})

        saved = SavedFilter.get_saved_filters(self.user)
        self.assertEqual(len(saved), 2)

    def test_get_filter_by_name(self):
        """Test getting a specific filter by name."""
        SavedFilter.save_filter(self.user, 'Test Filter', {'status': 'ACTIVE'})

        filter_data = SavedFilter.get_filter(self.user, 'Test Filter')
        self.assertIsNotNone(filter_data)
        self.assertEqual(filter_data['status'], 'ACTIVE')

    def test_delete_saved_filter(self):
        """Test deleting a saved filter."""
        SavedFilter.save_filter(self.user, 'To Delete', {'test': '1'})
        SavedFilter.delete_filter(self.user, 'To Delete')

        saved = SavedFilter.get_saved_filters(self.user)
        self.assertEqual(len(saved), 0)

    def test_get_filters_by_module(self):
        """Test filtering saved filters by module."""
        SavedFilter.save_filter(self.user, 'HR Filter', {'test': '1'}, module='hr')
        SavedFilter.save_filter(self.user, 'Inv Filter', {'test': '2'}, module='inventory')

        hr_filters = SavedFilter.get_saved_filters(self.user, module='hr')
        self.assertEqual(len(hr_filters), 1)
        self.assertEqual(hr_filters[0]['name'], 'HR Filter')


class TestAdvancedFilter(TestCase):
    """Test the AdvancedFilter functionality."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        # Create test people with various attributes
        self.person1 = HRPeople.objects.create(
            first_name_en='Alice',
            last_name_en='Johnson',
            gender='FEMALE',
            date_of_birth='1985-03-15',
            primary_nationality_iso2='US',
            national_id='111111111'
        )

        self.person2 = HRPeople.objects.create(
            first_name_en='Bob',
            last_name_en='Smith',
            gender='MALE',
            date_of_birth='1990-07-20',
            primary_nationality_iso2='UK',
            national_id='222222222'
        )

    def test_exact_filter(self):
        """Test exact match filtering."""
        filter_data = {
            'gender': {'type': 'exact', 'value': 'FEMALE'}
        }

        queryset = HRPeople.objects.all()
        advanced_filter = AdvancedFilter(filter_data)
        filtered = advanced_filter.apply(queryset, filter_data)

        self.assertEqual(filtered.count(), 1)
        self.assertEqual(filtered.first(), self.person1)

    def test_icontains_filter(self):
        """Test case-insensitive contains filtering."""
        filter_data = {
            'first_name_en': {'type': 'icontains', 'value': 'ali'}
        }

        queryset = HRPeople.objects.all()
        advanced_filter = AdvancedFilter(filter_data)
        filtered = advanced_filter.apply(queryset, filter_data)

        self.assertEqual(filtered.count(), 1)
        self.assertEqual(filtered.first(), self.person1)

    def test_date_range_filter(self):
        """Test date range filtering."""
        filter_data = {
            'date_of_birth': {
                'type': 'date_range',
                'start': '1988-01-01',
                'end': '1995-12-31'
            }
        }

        queryset = HRPeople.objects.all()
        advanced_filter = AdvancedFilter(filter_data)
        filtered = advanced_filter.apply(queryset, filter_data)

        # Should find person2 (1990-07-20)
        self.assertEqual(filtered.count(), 1)
        self.assertEqual(filtered.first(), self.person2)

    def test_boolean_filter(self):
        """Test boolean filtering."""
        # Add is_deleted field filtering
        self.person1.is_deleted = True
        self.person1.save()

        filter_data = {
            'is_deleted': {'type': 'boolean', 'value': True}
        }

        queryset = HRPeople.objects.all()
        advanced_filter = AdvancedFilter(filter_data)
        filtered = advanced_filter.apply(queryset, filter_data)

        self.assertEqual(filtered.count(), 1)
        self.assertEqual(filtered.first(), self.person1)

    def test_choice_filter(self):
        """Test choice filtering (multiple values)."""
        filter_data = {
            'primary_nationality_iso2': {
                'type': 'choice',
                'values': ['US', 'UK']
            }
        }

        queryset = HRPeople.objects.all()
        advanced_filter = AdvancedFilter(filter_data)
        filtered = advanced_filter.apply(queryset, filter_data)

        # Should find both people
        self.assertEqual(filtered.count(), 2)


class TestGlobalSearchViews(TestCase):
    """Test the global search views and API endpoints."""

    def setUp(self):
        """Set up test data and client."""
        self.client = Client()

        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        self.client.login(username='testuser', password='testpass123')

        # Create test data
        self.person = HRPeople.objects.create(
            first_name_en='Search',
            last_name_en='Test',
            gender='MALE',
            date_of_birth='1990-01-01',
            primary_nationality_iso2='US',
            national_id='999999999'
        )

    def test_global_search_view_requires_login(self):
        """Test that search view requires authentication."""
        self.client.logout()
        response = self.client.get(reverse('core:global_search'))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_global_search_view_loads(self):
        """Test that search view loads correctly."""
        response = self.client.get(reverse('core:global_search'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/search_results.html')

    def test_global_search_view_with_query(self):
        """Test search view with query parameter."""
        response = self.client.get(
            reverse('core:global_search'),
            {'q': 'Search'}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Search')
        self.assertIn('results', response.context)
        self.assertGreater(response.context['total_count'], 0)

    def test_global_search_view_with_module_filter(self):
        """Test search view with module filtering."""
        response = self.client.get(
            reverse('core:global_search'),
            {'q': 'Search', 'modules': ['hr']}
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('selected_modules', response.context)
        self.assertIn('hr', response.context['selected_modules'])

    def test_global_search_view_saves_history(self):
        """Test that search view saves search history."""
        response = self.client.get(
            reverse('core:global_search'),
            {'q': 'test search'}
        )

        self.assertEqual(response.status_code, 200)

        # Check that search was saved to history
        recent = SearchHistory.get_recent_searches(self.user)
        self.assertGreater(len(recent), 0)
        self.assertEqual(recent[0]['query'], 'test search')

    def test_global_search_api_requires_login(self):
        """Test that API endpoint requires authentication."""
        self.client.logout()
        response = self.client.get(reverse('core:global_search_api'))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_global_search_api_returns_json(self):
        """Test that API endpoint returns JSON."""
        response = self.client.get(
            reverse('core:global_search_api'),
            {'q': 'Search'}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

        data = json.loads(response.content)
        self.assertIn('results', data)
        self.assertIsInstance(data['results'], list)

    def test_global_search_api_minimum_query_length(self):
        """Test that API respects minimum query length."""
        response = self.client.get(
            reverse('core:global_search_api'),
            {'q': 'S'}  # Single character
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['results']), 0)

    def test_global_search_api_result_format(self):
        """Test that API returns results in correct format."""
        response = self.client.get(
            reverse('core:global_search_api'),
            {'q': 'Search'}
        )

        data = json.loads(response.content)
        self.assertGreater(len(data['results']), 0)

        # Check result structure
        result = data['results'][0]
        self.assertIn('id', result)
        self.assertIn('text', result)
        self.assertIn('icon', result)
        self.assertIn('label', result)
        self.assertIn('url', result)

    def test_global_search_api_limits_results(self):
        """Test that API limits results to 20."""
        # Create many test people
        for i in range(30):
            HRPeople.objects.create(
                first_name_en=f'SearchTest{i}',
                last_name_en='User',
                gender='MALE',
                date_of_birth='1990-01-01',
                primary_nationality_iso2='US',
                national_id=f'TEST{i:06d}'
            )

        response = self.client.get(
            reverse('core:global_search_api'),
            {'q': 'SearchTest'}
        )

        data = json.loads(response.content)
        # Should be limited to 20
        self.assertLessEqual(len(data['results']), 20)

    def test_search_results_show_recent_searches(self):
        """Test that search results page shows recent searches."""
        # Perform a few searches
        self.client.get(reverse('core:global_search'), {'q': 'search1'})
        self.client.get(reverse('core:global_search'), {'q': 'search2'})
        self.client.get(reverse('core:global_search'), {'q': 'search3'})

        response = self.client.get(reverse('core:global_search'))

        self.assertIn('recent_searches', response.context)
        recent = response.context['recent_searches']
        self.assertEqual(len(recent), 3)


class TestSearchIntegration(TestCase):
    """Integration tests for search functionality."""

    def setUp(self):
        """Set up comprehensive test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='integrationuser',
            password='testpass123',
            is_staff=True
        )
        self.client.login(username='integrationuser', password='testpass123')

        # Create diverse test data across multiple models
        self.department = Department.objects.create(
            name='Integration Test Dept',
            department_type='PRODUCTION'
        )

        self.person = HRPeople.objects.create(
            first_name_en='Integration',
            last_name_en='User',
            gender='MALE',
            date_of_birth='1985-01-01',
            primary_nationality_iso2='US',
            national_id='INT123456'
        )

        self.location = Location.objects.create(
            code='INT-WH',
            name='Integration Warehouse',
            location_type='WAREHOUSE',
            is_active=True
        )

        self.cost_center = CostCenter.objects.create(
            code='INT-CC',
            name='Integration Cost Center',
            status='ACTIVE',
            created_by=self.user
        )

    def test_search_finds_all_model_types(self):
        """Test that search can find records from all searchable models."""
        response = self.client.get(
            reverse('core:global_search'),
            {'q': 'Integration'}
        )

        self.assertEqual(response.status_code, 200)
        results = response.context['results']

        # Should find results from multiple models
        model_labels = [r['model_label'] for r in results]
        self.assertGreater(len(model_labels), 1, "Should find multiple model types")

    def test_end_to_end_search_workflow(self):
        """Test complete search workflow from search to navigation."""
        # 1. Perform search via main view
        response = self.client.get(
            reverse('core:global_search'),
            {'q': 'Integration User'}
        )
        self.assertEqual(response.status_code, 200)

        # 2. Verify search saved to history
        recent = SearchHistory.get_recent_searches(self.user)
        self.assertEqual(recent[0]['query'], 'Integration User')

        # 3. Use API to get autocomplete results
        api_response = self.client.get(
            reverse('core:global_search_api'),
            {'q': 'Integration'}
        )
        api_data = json.loads(api_response.content)
        self.assertGreater(len(api_data['results']), 0)

        # 4. Save a filter
        SavedFilter.save_filter(
            self.user,
            'Active Integration Records',
            {'status': 'ACTIVE'},
            module='core'
        )

        # 5. Retrieve saved filter
        saved = SavedFilter.get_filter(self.user, 'Active Integration Records')
        self.assertIsNotNone(saved)

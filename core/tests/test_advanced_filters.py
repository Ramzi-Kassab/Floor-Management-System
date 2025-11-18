"""
Tests for Advanced Filter and Saved Filter Functionality

Tests:
- Saved filter CRUD operations
- Filter API endpoints
- Search history management
- Clear history functionality
"""

import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from core.models import UserPreference
from core.search_utils import SavedFilter, SearchHistory

User = get_user_model()


class TestSavedFilters(TestCase):
    """Test saved filter functionality."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

    def test_save_filter(self):
        """Test saving a filter preset."""
        filters = {
            'query': 'test search',
            'modules': ['hr', 'inventory']
        }

        SavedFilter.save_filter(
            user=self.user,
            name='My Test Filter',
            filters=filters,
            module='hr'
        )

        # Verify filter was saved
        saved_filters = SavedFilter.get_saved_filters(self.user)
        self.assertGreater(len(saved_filters), 0)

        # Find our filter
        filter_found = False
        for key, saved_filter in saved_filters.items():
            if saved_filter['name'] == 'My Test Filter':
                filter_found = True
                self.assertEqual(saved_filter['module'], 'hr')
                self.assertEqual(saved_filter['filters'], filters)
                break

        self.assertTrue(filter_found, "Saved filter not found")

    def test_get_saved_filters(self):
        """Test retrieving saved filters."""
        # Save multiple filters
        SavedFilter.save_filter(self.user, 'Filter 1', {'query': 'test1'}, module='hr')
        SavedFilter.save_filter(self.user, 'Filter 2', {'query': 'test2'}, module='inventory')
        SavedFilter.save_filter(self.user, 'Filter 3', {'query': 'test3'}, module='hr')

        # Get all filters
        all_filters = SavedFilter.get_saved_filters(self.user)
        self.assertEqual(len(all_filters), 3)

        # Get HR filters only
        hr_filters = SavedFilter.get_saved_filters(self.user, module='hr')
        self.assertEqual(len(hr_filters), 2)

    def test_delete_filter(self):
        """Test deleting a saved filter."""
        # Save a filter
        SavedFilter.save_filter(self.user, 'Filter to Delete', {'query': 'test'})

        # Get the filter key
        filters = SavedFilter.get_saved_filters(self.user)
        filter_key = list(filters.keys())[0]

        # Delete it
        SavedFilter.delete_filter(self.user, filter_key)

        # Verify it's gone
        filters_after = SavedFilter.get_saved_filters(self.user)
        self.assertNotIn(filter_key, filters_after)


class TestSavedFiltersAPI(TestCase):
    """Test saved filter API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

    def test_list_filters_api(self):
        """Test listing saved filters via API."""
        # Save some filters
        SavedFilter.save_filter(self.user, 'Test Filter 1', {'query': 'test1'})
        SavedFilter.save_filter(self.user, 'Test Filter 2', {'query': 'test2'})

        # Call API
        response = self.client.get(reverse('core:api_filters_list'))
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('filters', data)
        self.assertGreaterEqual(len(data['filters']), 2)

    def test_save_filter_api(self):
        """Test saving filter via API."""
        filter_data = {
            'name': 'API Test Filter',
            'filters': {
                'query': 'test search',
                'modules': ['hr', 'inventory']
            },
            'module': 'hr'
        }

        response = self.client.post(
            reverse('core:api_filter_save'),
            data=json.dumps(filter_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('Filter "API Test Filter" saved successfully', data['message'])

    def test_save_filter_api_validation(self):
        """Test filter save validation."""
        # Missing name
        response = self.client.post(
            reverse('core:api_filter_save'),
            data=json.dumps({'filters': {'query': 'test'}}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

        # Missing filters
        response = self.client.post(
            reverse('core:api_filter_save'),
            data=json.dumps({'name': 'Test'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_delete_filter_api(self):
        """Test deleting filter via API."""
        # Save a filter
        SavedFilter.save_filter(self.user, 'Filter to Delete', {'query': 'test'})

        # Get the filter key
        filters = SavedFilter.get_saved_filters(self.user)
        filter_key = list(filters.keys())[0]

        # Delete via API
        response = self.client.post(
            reverse('core:api_filter_delete', kwargs={'filter_key': filter_key})
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])

        # Verify it's deleted
        filters_after = SavedFilter.get_saved_filters(self.user)
        self.assertNotIn(filter_key, filters_after)

    def test_api_requires_authentication(self):
        """Test that API endpoints require authentication."""
        # Logout
        self.client.logout()

        # Try to access APIs
        response = self.client.get(reverse('core:api_filters_list'))
        self.assertIn(response.status_code, [302, 401, 403])  # Redirect or unauthorized


class TestSearchHistory(TestCase):
    """Test search history functionality."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_add_search_to_history(self):
        """Test adding search to history."""
        SearchHistory.add_search(self.user, 'test query', module='hr')

        # Verify it was added
        history = SearchHistory.get_recent_searches(self.user)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['query'], 'test query')
        self.assertEqual(history[0]['module'], 'hr')

    def test_search_history_limit(self):
        """Test that search history is limited to 20 items."""
        # Add 25 searches
        for i in range(25):
            SearchHistory.add_search(self.user, f'query {i}')

        # Should only have 20
        history = SearchHistory.get_recent_searches(self.user)
        self.assertEqual(len(history), 20)

        # Most recent should be query 24
        self.assertEqual(history[0]['query'], 'query 24')

    def test_duplicate_searches_removed(self):
        """Test that duplicate searches are moved to top."""
        SearchHistory.add_search(self.user, 'query 1')
        SearchHistory.add_search(self.user, 'query 2')
        SearchHistory.add_search(self.user, 'query 3')

        # Add query 1 again
        SearchHistory.add_search(self.user, 'query 1')

        history = SearchHistory.get_recent_searches(self.user)

        # Should still have 3 items
        self.assertEqual(len(history), 3)

        # Query 1 should be at top
        self.assertEqual(history[0]['query'], 'query 1')

    def test_get_recent_searches_with_limit(self):
        """Test getting recent searches with custom limit."""
        # Add 10 searches
        for i in range(10):
            SearchHistory.add_search(self.user, f'query {i}')

        # Get only 5
        history = SearchHistory.get_recent_searches(self.user, limit=5)
        self.assertEqual(len(history), 5)

        # Should be most recent 5
        self.assertEqual(history[0]['query'], 'query 9')
        self.assertEqual(history[4]['query'], 'query 5')


class TestClearSearchHistory(TestCase):
    """Test clear search history functionality."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

        # Add some search history
        for i in range(5):
            SearchHistory.add_search(self.user, f'query {i}')

    def test_clear_search_history_api(self):
        """Test clearing search history via API."""
        # Verify we have history
        history_before = SearchHistory.get_recent_searches(self.user)
        self.assertEqual(len(history_before), 5)

        # Clear via API
        response = self.client.post(reverse('core:api_clear_search_history'))

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])

        # Verify history is cleared
        history_after = SearchHistory.get_recent_searches(self.user)
        self.assertEqual(len(history_after), 0)

    def test_clear_requires_post(self):
        """Test that clear history requires POST."""
        response = self.client.get(reverse('core:api_clear_search_history'))
        self.assertEqual(response.status_code, 400)


class TestIntegration(TestCase):
    """Integration tests for search and filter functionality."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

    def test_search_saves_history(self):
        """Test that performing a search saves to history."""
        # Perform search
        response = self.client.get(reverse('core:global_search'), {'q': 'test search'})
        self.assertEqual(response.status_code, 200)

        # Verify history was saved
        history = SearchHistory.get_recent_searches(self.user)
        self.assertGreater(len(history), 0)
        self.assertEqual(history[0]['query'], 'test search')

    def test_filter_workflow(self):
        """Test complete filter workflow: save, list, apply, delete."""
        # 1. Save a filter
        filter_data = {
            'name': 'My Search',
            'filters': {'query': 'important search'},
            'module': None
        }
        response = self.client.post(
            reverse('core:api_filter_save'),
            data=json.dumps(filter_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

        # 2. List filters
        response = self.client.get(reverse('core:api_filters_list'))
        data = response.json()
        self.assertGreater(len(data['filters']), 0)

        # 3. Get filter key
        filter_key = list(data['filters'].keys())[0]

        # 4. Delete filter
        response = self.client.post(
            reverse('core:api_filter_delete', kwargs={'filter_key': filter_key})
        )
        self.assertEqual(response.status_code, 200)

        # 5. Verify deletion
        response = self.client.get(reverse('core:api_filters_list'))
        data = response.json()
        self.assertNotIn(filter_key, data['filters'])

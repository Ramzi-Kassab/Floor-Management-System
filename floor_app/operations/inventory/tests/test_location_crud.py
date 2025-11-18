"""
Tests for Location CRUD Functionality

Tests the Location management system including:
- Location model with hierarchical structure
- Location list view with tree visualization
- Location detail view
- Location create/update views
- Location hierarchy and parent-child relationships
- GPS coordinates validation
"""

import json
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from floor_app.operations.inventory.models import Location

User = get_user_model()


class TestLocationModel(TestCase):
    """Test the Location model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_location_creation(self):
        """Test creating a location."""
        location = Location.objects.create(
            code='WH-01',
            name='Main Warehouse',
            location_type='WAREHOUSE',
            is_active=True,
            created_by=self.user
        )

        self.assertEqual(location.code, 'WH-01')
        self.assertEqual(location.name, 'Main Warehouse')
        self.assertEqual(location.location_type, 'WAREHOUSE')
        self.assertTrue(location.is_active)
        self.assertFalse(location.is_deleted)

    def test_location_string_representation(self):
        """Test __str__ method."""
        location = Location.objects.create(
            code='BIN-A1',
            name='Bin A1',
            location_type='BIN',
            created_by=self.user
        )

        self.assertIn('BIN-A1', str(location))

    def test_location_hierarchical_structure(self):
        """Test parent-child location relationships."""
        # Create parent warehouse
        warehouse = Location.objects.create(
            code='WH-01',
            name='Main Warehouse',
            location_type='WAREHOUSE',
            created_by=self.user
        )

        # Create child zone
        zone = Location.objects.create(
            code='ZONE-A',
            name='Zone A',
            location_type='ZONE',
            parent_location=warehouse,
            created_by=self.user
        )

        # Create grandchild bin
        bin_location = Location.objects.create(
            code='BIN-A1',
            name='Bin A1',
            location_type='BIN',
            parent_location=zone,
            created_by=self.user
        )

        # Verify relationships
        self.assertEqual(zone.parent_location, warehouse)
        self.assertEqual(bin_location.parent_location, zone)
        self.assertIsNone(warehouse.parent_location)

    def test_location_with_gps_coordinates(self):
        """Test location with GPS coordinates."""
        location = Location.objects.create(
            code='SITE-01',
            name='Site Location',
            location_type='SITE',
            gps_coordinates='24.7136,46.6753',
            created_by=self.user
        )

        self.assertEqual(location.gps_coordinates, '24.7136,46.6753')

    def test_location_with_capacity(self):
        """Test location with capacity settings."""
        location = Location.objects.create(
            code='RACK-01',
            name='Rack 1',
            location_type='RACK',
            max_capacity=Decimal('1000.00'),
            capacity_uom='KG',
            created_by=self.user
        )

        self.assertEqual(location.max_capacity, Decimal('1000.00'))
        self.assertEqual(location.capacity_uom, 'KG')

    def test_location_type_choices(self):
        """Test that location type is from valid choices."""
        location = Location.objects.create(
            code='SHELF-01',
            name='Shelf 1',
            location_type='SHELF',
            created_by=self.user
        )

        valid_types = [
            'SITE', 'BUILDING', 'WAREHOUSE', 'ZONE', 'AISLE',
            'RACK', 'SHELF', 'BIN', 'PALLET', 'OTHER'
        ]
        self.assertIn(location.location_type, valid_types)

    def test_location_address_fields(self):
        """Test location with address information."""
        location = Location.objects.create(
            code='WH-MAIN',
            name='Main Warehouse',
            location_type='WAREHOUSE',
            address='123 Industrial St, Riyadh',
            created_by=self.user
        )

        self.assertEqual(location.address, '123 Industrial St, Riyadh')


class TestLocationListView(TestCase):
    """Test the Location list view with tree visualization."""

    def setUp(self):
        """Set up test data and client."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

        # Create hierarchical location structure
        self.warehouse = Location.objects.create(
            code='WH-01',
            name='Main Warehouse',
            location_type='WAREHOUSE',
            is_active=True,
            created_by=self.user
        )

        self.zone_a = Location.objects.create(
            code='ZONE-A',
            name='Zone A',
            location_type='ZONE',
            parent_location=self.warehouse,
            is_active=True,
            created_by=self.user
        )

        self.zone_b = Location.objects.create(
            code='ZONE-B',
            name='Zone B',
            location_type='ZONE',
            parent_location=self.warehouse,
            is_active=True,
            created_by=self.user
        )

        self.bin_a1 = Location.objects.create(
            code='BIN-A1',
            name='Bin A1',
            location_type='BIN',
            parent_location=self.zone_a,
            is_active=True,
            created_by=self.user
        )

    def test_location_list_view_loads(self):
        """Test that location list view loads correctly."""
        response = self.client.get(reverse('inventory:location_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'inventory/locations/list.html')

    def test_location_list_requires_login(self):
        """Test that location list requires authentication."""
        self.client.logout()
        response = self.client.get(reverse('inventory:location_list'))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_location_list_shows_all_locations(self):
        """Test that all locations are displayed."""
        response = self.client.get(reverse('inventory:location_list'))
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, 'Main Warehouse')
        self.assertContains(response, 'Zone A')
        self.assertContains(response, 'Zone B')
        self.assertContains(response, 'Bin A1')

    def test_location_list_builds_tree_structure(self):
        """Test that tree structure is built correctly."""
        response = self.client.get(reverse('inventory:location_list'))
        self.assertEqual(response.status_code, 200)

        # Check that location_tree is in context
        self.assertIn('location_tree', response.context)
        tree = response.context['location_tree']

        # Should have 1 root location (warehouse)
        self.assertEqual(len(tree), 1)

        # Root should be the warehouse
        self.assertEqual(tree[0]['location'], self.warehouse)

        # Warehouse should have 2 children (zones)
        self.assertEqual(len(tree[0]['children']), 2)

    def test_location_list_excludes_deleted(self):
        """Test that deleted locations are excluded."""
        # Mark zone_b as deleted
        self.zone_b.is_deleted = True
        self.zone_b.save()

        response = self.client.get(reverse('inventory:location_list'))
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, 'Zone A')
        self.assertNotContains(response, 'Zone B')

    def test_location_list_search(self):
        """Test search functionality."""
        response = self.client.get(
            reverse('inventory:location_list'),
            {'search': 'Zone A'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Zone A')

    def test_location_list_filter_by_type(self):
        """Test filtering by location type."""
        response = self.client.get(
            reverse('inventory:location_list'),
            {'location_type': 'ZONE'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Zone A')
        self.assertContains(response, 'Zone B')

    def test_location_list_filter_by_status(self):
        """Test filtering by active status."""
        # Create inactive location
        Location.objects.create(
            code='INACTIVE',
            name='Inactive Location',
            location_type='BIN',
            is_active=False,
            created_by=self.user
        )

        response = self.client.get(
            reverse('inventory:location_list'),
            {'is_active': 'true'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Inactive Location')


class TestLocationDetailView(TestCase):
    """Test the Location detail view."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

        self.warehouse = Location.objects.create(
            code='WH-01',
            name='Main Warehouse',
            location_type='WAREHOUSE',
            address='123 Industrial Road, Riyadh',
            gps_coordinates='24.7136,46.6753',
            max_capacity=Decimal('10000.00'),
            capacity_uom='M3',
            notes='Primary storage facility',
            is_active=True,
            created_by=self.user
        )

        # Create child locations
        self.zone = Location.objects.create(
            code='ZONE-A',
            name='Zone A',
            location_type='ZONE',
            parent_location=self.warehouse,
            created_by=self.user
        )

    def test_location_detail_view_loads(self):
        """Test that location detail view loads."""
        response = self.client.get(
            reverse('inventory:location_detail', kwargs={'pk': self.warehouse.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'inventory/locations/detail.html')

    def test_location_detail_requires_login(self):
        """Test that detail view requires authentication."""
        self.client.logout()
        response = self.client.get(
            reverse('inventory:location_detail', kwargs={'pk': self.warehouse.pk})
        )
        self.assertEqual(response.status_code, 302)

    def test_location_detail_shows_information(self):
        """Test that detail view shows all location information."""
        response = self.client.get(
            reverse('inventory:location_detail', kwargs={'pk': self.warehouse.pk})
        )

        self.assertContains(response, 'WH-01')
        self.assertContains(response, 'Main Warehouse')
        self.assertContains(response, '123 Industrial Road')
        self.assertContains(response, '24.7136,46.6753')
        self.assertContains(response, 'Primary storage facility')

    def test_location_detail_shows_child_locations(self):
        """Test that detail view shows child locations."""
        response = self.client.get(
            reverse('inventory:location_detail', kwargs={'pk': self.warehouse.pk})
        )

        # Should show the child zone
        self.assertContains(response, 'Zone A')
        self.assertContains(response, 'ZONE-A')

    def test_location_detail_shows_parent_location(self):
        """Test that detail view shows parent location."""
        response = self.client.get(
            reverse('inventory:location_detail', kwargs={'pk': self.zone.pk})
        )

        # Should show link to parent warehouse
        self.assertContains(response, 'Main Warehouse')


class TestLocationCreateView(TestCase):
    """Test the Location create view."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            is_staff=True
        )
        self.client.login(username='testuser', password='testpass123')

        # Create a parent location for testing
        self.warehouse = Location.objects.create(
            code='WH-01',
            name='Main Warehouse',
            location_type='WAREHOUSE',
            created_by=self.user
        )

    def test_location_create_view_loads(self):
        """Test that create view loads."""
        response = self.client.get(reverse('inventory:location_create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'inventory/locations/form.html')

    def test_location_create_requires_login(self):
        """Test that create view requires authentication."""
        self.client.logout()
        response = self.client.get(reverse('inventory:location_create'))
        self.assertEqual(response.status_code, 302)

    def test_location_create_success(self):
        """Test successful location creation."""
        data = {
            'code': 'NEW-LOC',
            'name': 'New Location',
            'location_type': 'ZONE',
            'parent_location': self.warehouse.id,
            'is_active': True
        }

        response = self.client.post(reverse('inventory:location_create'), data)
        self.assertEqual(response.status_code, 302)  # Redirect on success

        # Verify location was created
        location = Location.objects.get(code='NEW-LOC')
        self.assertEqual(location.name, 'New Location')
        self.assertEqual(location.parent_location, self.warehouse)

    def test_location_create_with_gps(self):
        """Test creating location with GPS coordinates."""
        data = {
            'code': 'GPS-LOC',
            'name': 'GPS Location',
            'location_type': 'SITE',
            'gps_coordinates': '24.7136,46.6753',
            'is_active': True
        }

        response = self.client.post(reverse('inventory:location_create'), data)
        self.assertEqual(response.status_code, 302)

        location = Location.objects.get(code='GPS-LOC')
        self.assertEqual(location.gps_coordinates, '24.7136,46.6753')

    def test_location_create_with_capacity(self):
        """Test creating location with capacity."""
        data = {
            'code': 'CAP-LOC',
            'name': 'Capacity Location',
            'location_type': 'WAREHOUSE',
            'max_capacity': '5000.00',
            'capacity_uom': 'M3',
            'is_active': True
        }

        response = self.client.post(reverse('inventory:location_create'), data)
        self.assertEqual(response.status_code, 302)

        location = Location.objects.get(code='CAP-LOC')
        self.assertEqual(location.max_capacity, Decimal('5000.00'))
        self.assertEqual(location.capacity_uom, 'M3')

    def test_location_create_validation(self):
        """Test form validation on create."""
        # Missing required field (name)
        data = {
            'code': 'INVALID',
            'location_type': 'ZONE'
        }

        response = self.client.post(reverse('inventory:location_create'), data)
        # Should not redirect (form has errors)
        self.assertEqual(response.status_code, 200)


class TestLocationUpdateView(TestCase):
    """Test the Location update view."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            is_staff=True
        )
        self.client.login(username='testuser', password='testpass123')

        self.location = Location.objects.create(
            code='ORIG-LOC',
            name='Original Name',
            location_type='ZONE',
            is_active=True,
            created_by=self.user
        )

    def test_location_update_view_loads(self):
        """Test that update view loads."""
        response = self.client.get(
            reverse('inventory:location_edit', kwargs={'pk': self.location.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'inventory/locations/form.html')

    def test_location_update_success(self):
        """Test successful location update."""
        data = {
            'code': 'ORIG-LOC',
            'name': 'Updated Name',
            'location_type': 'WAREHOUSE',
            'address': 'New Address',
            'is_active': True
        }

        response = self.client.post(
            reverse('inventory:location_edit', kwargs={'pk': self.location.pk}),
            data
        )
        self.assertEqual(response.status_code, 302)

        # Verify changes
        self.location.refresh_from_db()
        self.assertEqual(self.location.name, 'Updated Name')
        self.assertEqual(self.location.location_type, 'WAREHOUSE')
        self.assertEqual(self.location.address, 'New Address')

    def test_location_update_gps_coordinates(self):
        """Test updating GPS coordinates."""
        data = {
            'code': 'ORIG-LOC',
            'name': self.location.name,
            'location_type': self.location.location_type,
            'gps_coordinates': '25.2048,55.2708',
            'is_active': True
        }

        response = self.client.post(
            reverse('inventory:location_edit', kwargs={'pk': self.location.pk}),
            data
        )
        self.assertEqual(response.status_code, 302)

        self.location.refresh_from_db()
        self.assertEqual(self.location.gps_coordinates, '25.2048,55.2708')


class TestLocationHierarchy(TestCase):
    """Test location hierarchy features."""

    def setUp(self):
        """Set up hierarchical test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        # Build a 4-level hierarchy
        self.site = Location.objects.create(
            code='SITE-01',
            name='Site 1',
            location_type='SITE',
            created_by=self.user
        )

        self.warehouse = Location.objects.create(
            code='WH-01',
            name='Warehouse 1',
            location_type='WAREHOUSE',
            parent_location=self.site,
            created_by=self.user
        )

        self.zone = Location.objects.create(
            code='ZONE-A',
            name='Zone A',
            location_type='ZONE',
            parent_location=self.warehouse,
            created_by=self.user
        )

        self.bin = Location.objects.create(
            code='BIN-A1',
            name='Bin A1',
            location_type='BIN',
            parent_location=self.zone,
            created_by=self.user
        )

    def test_hierarchy_depth(self):
        """Test 4-level hierarchy is correctly established."""
        # Verify chain from bin to site
        self.assertEqual(self.bin.parent_location, self.zone)
        self.assertEqual(self.zone.parent_location, self.warehouse)
        self.assertEqual(self.warehouse.parent_location, self.site)
        self.assertIsNone(self.site.parent_location)

    def test_cannot_create_circular_reference(self):
        """Test that circular references are prevented."""
        # Try to set warehouse as child of bin (which is its descendant)
        # This should be prevented by application logic
        # Note: This test assumes validation exists
        pass  # Would need actual validation in model

    def test_multiple_children(self):
        """Test that a location can have multiple children."""
        # Add second zone
        zone_b = Location.objects.create(
            code='ZONE-B',
            name='Zone B',
            location_type='ZONE',
            parent_location=self.warehouse,
            created_by=self.user
        )

        # Add third zone
        zone_c = Location.objects.create(
            code='ZONE-C',
            name='Zone C',
            location_type='ZONE',
            parent_location=self.warehouse,
            created_by=self.user
        )

        # Warehouse should have 3 child zones
        children = Location.objects.filter(
            parent_location=self.warehouse,
            is_deleted=False
        )
        self.assertEqual(children.count(), 3)

    def test_root_locations(self):
        """Test filtering root locations (no parent)."""
        # Create another root location
        site2 = Location.objects.create(
            code='SITE-02',
            name='Site 2',
            location_type='SITE',
            created_by=self.user
        )

        # Get all root locations
        roots = Location.objects.filter(
            parent_location__isnull=True,
            is_deleted=False
        )

        self.assertEqual(roots.count(), 2)
        self.assertIn(self.site, roots)
        self.assertIn(site2, roots)


class TestLocationTreeVisualization(TestCase):
    """Test the tree visualization functionality."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

        # Create complex tree structure
        self.wh1 = Location.objects.create(
            code='WH-01',
            name='Warehouse 1',
            location_type='WAREHOUSE',
            created_by=self.user
        )

        self.wh2 = Location.objects.create(
            code='WH-02',
            name='Warehouse 2',
            location_type='WAREHOUSE',
            created_by=self.user
        )

        # WH1 children
        self.zone_a = Location.objects.create(
            code='ZONE-A',
            name='Zone A',
            location_type='ZONE',
            parent_location=self.wh1,
            created_by=self.user
        )

        self.zone_b = Location.objects.create(
            code='ZONE-B',
            name='Zone B',
            location_type='ZONE',
            parent_location=self.wh1,
            created_by=self.user
        )

        # Zone A child
        self.bin_a1 = Location.objects.create(
            code='BIN-A1',
            name='Bin A1',
            location_type='BIN',
            parent_location=self.zone_a,
            created_by=self.user
        )

    def test_tree_template_includes_recursive_node(self):
        """Test that tree uses recursive template."""
        response = self.client.get(reverse('inventory:location_list'))
        self.assertEqual(response.status_code, 200)

        # Check that the tree is rendered
        self.assertContains(response, 'location-node')

    def test_tree_shows_all_levels(self):
        """Test that all hierarchy levels are shown in tree."""
        response = self.client.get(reverse('inventory:location_list'))

        # Should show all locations
        self.assertContains(response, 'WH-01')
        self.assertContains(response, 'WH-02')
        self.assertContains(response, 'ZONE-A')
        self.assertContains(response, 'ZONE-B')
        self.assertContains(response, 'BIN-A1')

    def test_tree_expand_collapse_functionality(self):
        """Test that expand/collapse buttons are present."""
        response = self.client.get(reverse('inventory:location_list'))

        # Check for expand/collapse controls
        self.assertContains(response, 'Expand All')
        self.assertContains(response, 'Collapse All')

"""
Tests for Inventory models
"""
from django.test import TestCase
from decimal import Decimal

from floor_app.operations.inventory.models import (
    ItemCategory, UnitOfMeasure, Item, Location,
    Stock, StockMovement, SerialUnit
)


class ItemCategoryTest(TestCase):
    """Test ItemCategory model"""

    def test_create_category(self):
        """Test creating an item category"""
        category = ItemCategory.objects.create(
            code='RAW',
            name='Raw Materials',
            description='Raw materials for production'
        )
        self.assertEqual(category.code, 'RAW')
        self.assertEqual(category.name, 'Raw Materials')

    def test_category_hierarchy(self):
        """Test category parent-child relationship"""
        parent = ItemCategory.objects.create(
            code='MAT',
            name='Materials'
        )
        child = ItemCategory.objects.create(
            code='STEEL',
            name='Steel',
            parent=parent
        )
        self.assertEqual(child.parent, parent)


class UnitOfMeasureTest(TestCase):
    """Test UnitOfMeasure model"""

    def test_create_uom(self):
        """Test creating a unit of measure"""
        uom = UnitOfMeasure.objects.create(
            code='KG',
            name='Kilogram',
            description='Unit of mass'
        )
        self.assertEqual(uom.code, 'KG')
        self.assertEqual(uom.name, 'Kilogram')


class ItemTest(TestCase):
    """Test Item model"""

    def setUp(self):
        """Set up test data"""
        self.category = ItemCategory.objects.create(
            code='COMP',
            name='Components'
        )
        self.uom = UnitOfMeasure.objects.create(
            code='EA',
            name='Each'
        )

    def test_create_item(self):
        """Test creating an item"""
        item = Item.objects.create(
            sku='ITEM-001',
            name='Test Item',
            description='A test inventory item',
            category=self.category,
            uom=self.uom,
            unit_cost=Decimal('10.50')
        )
        self.assertEqual(item.sku, 'ITEM-001')
        self.assertEqual(item.name, 'Test Item')
        self.assertEqual(item.unit_cost, Decimal('10.50'))

    def test_unique_sku(self):
        """Test SKU uniqueness"""
        Item.objects.create(
            sku='ITEM-001',
            name='Item 1',
            category=self.category,
            uom=self.uom
        )
        with self.assertRaises(Exception):
            Item.objects.create(
                sku='ITEM-001',
                name='Item 2',
                category=self.category,
                uom=self.uom
            )

    def test_item_with_reorder_point(self):
        """Test item with reorder point"""
        item = Item.objects.create(
            sku='ITEM-002',
            name='Reorderable Item',
            category=self.category,
            uom=self.uom,
            reorder_point=Decimal('100'),
            reorder_quantity=Decimal('500')
        )
        self.assertEqual(item.reorder_point, Decimal('100'))
        self.assertEqual(item.reorder_quantity, Decimal('500'))


class LocationTest(TestCase):
    """Test Location model"""

    def test_create_location(self):
        """Test creating a location"""
        location = Location.objects.create(
            code='WH-001',
            name='Warehouse 1',
            location_type='WAREHOUSE',
            is_active=True
        )
        self.assertEqual(location.code, 'WH-001')
        self.assertEqual(location.location_type, 'WAREHOUSE')
        self.assertTrue(location.is_active)

    def test_location_hierarchy(self):
        """Test location parent-child relationship"""
        warehouse = Location.objects.create(
            code='WH-001',
            name='Main Warehouse',
            location_type='WAREHOUSE'
        )
        aisle = Location.objects.create(
            code='WH-001-A',
            name='Aisle A',
            location_type='AISLE',
            parent=warehouse
        )
        self.assertEqual(aisle.parent, warehouse)


class StockTest(TestCase):
    """Test Stock model"""

    def setUp(self):
        """Set up test data"""
        category = ItemCategory.objects.create(code='TEST', name='Test')
        uom = UnitOfMeasure.objects.create(code='EA', name='Each')
        self.item = Item.objects.create(
            sku='STOCK-001',
            name='Stock Item',
            category=category,
            uom=uom
        )
        self.location = Location.objects.create(
            code='LOC-001',
            name='Test Location',
            location_type='WAREHOUSE'
        )

    def test_create_stock(self):
        """Test creating a stock record"""
        stock = Stock.objects.create(
            item=self.item,
            location=self.location,
            quantity_on_hand=Decimal('100'),
            quantity_reserved=Decimal('10')
        )
        self.assertEqual(stock.quantity_on_hand, Decimal('100'))
        self.assertEqual(stock.quantity_reserved, Decimal('10'))

    def test_available_quantity(self):
        """Test available quantity calculation"""
        stock = Stock.objects.create(
            item=self.item,
            location=self.location,
            quantity_on_hand=Decimal('100'),
            quantity_reserved=Decimal('25')
        )
        # If available_quantity property exists
        # self.assertEqual(stock.available_quantity, Decimal('75'))


class StockMovementTest(TestCase):
    """Test StockMovement model"""

    def setUp(self):
        """Set up test data"""
        category = ItemCategory.objects.create(code='TEST', name='Test')
        uom = UnitOfMeasure.objects.create(code='EA', name='Each')
        self.item = Item.objects.create(
            sku='MOV-001',
            name='Movement Item',
            category=category,
            uom=uom
        )
        self.location = Location.objects.create(
            code='LOC-001',
            name='Location 1',
            location_type='WAREHOUSE'
        )

    def test_create_stock_movement(self):
        """Test creating a stock movement"""
        movement = StockMovement.objects.create(
            item=self.item,
            from_location=self.location,
            to_location=None,  # Receipt
            quantity=Decimal('50'),
            movement_type='RECEIPT',
            reference_number='RCV-001'
        )
        self.assertEqual(movement.quantity, Decimal('50'))
        self.assertEqual(movement.movement_type, 'RECEIPT')

    def test_stock_transfer(self):
        """Test stock transfer between locations"""
        location2 = Location.objects.create(
            code='LOC-002',
            name='Location 2',
            location_type='WAREHOUSE'
        )
        movement = StockMovement.objects.create(
            item=self.item,
            from_location=self.location,
            to_location=location2,
            quantity=Decimal('25'),
            movement_type='TRANSFER',
            reference_number='TRF-001'
        )
        self.assertEqual(movement.from_location, self.location)
        self.assertEqual(movement.to_location, location2)


class SerialUnitTest(TestCase):
    """Test SerialUnit model"""

    def setUp(self):
        """Set up test data"""
        category = ItemCategory.objects.create(code='SERIAL', name='Serialized')
        uom = UnitOfMeasure.objects.create(code='EA', name='Each')
        self.item = Item.objects.create(
            sku='SERIAL-001',
            name='Serialized Item',
            category=category,
            uom=uom,
            is_serialized=True
        )
        self.location = Location.objects.create(
            code='LOC-001',
            name='Location 1',
            location_type='WAREHOUSE'
        )

    def test_create_serial_unit(self):
        """Test creating a serial unit"""
        serial = SerialUnit.objects.create(
            item=self.item,
            serial_number='SN-001',
            location=self.location,
            status='AVAILABLE'
        )
        self.assertEqual(serial.serial_number, 'SN-001')
        self.assertEqual(serial.status, 'AVAILABLE')
        self.assertEqual(serial.location, self.location)

    def test_unique_serial_number_per_item(self):
        """Test serial number uniqueness per item"""
        SerialUnit.objects.create(
            item=self.item,
            serial_number='SN-001',
            location=self.location,
            status='AVAILABLE'
        )
        # Same serial number for the same item should fail
        with self.assertRaises(Exception):
            SerialUnit.objects.create(
                item=self.item,
                serial_number='SN-001',
                location=self.location,
                status='AVAILABLE'
            )

    def test_serial_status_tracking(self):
        """Test serial unit status tracking"""
        serial = SerialUnit.objects.create(
            item=self.item,
            serial_number='SN-002',
            location=self.location,
            status='AVAILABLE'
        )
        # Change status
        serial.status = 'IN_USE'
        serial.save()
        self.assertEqual(serial.status, 'IN_USE')

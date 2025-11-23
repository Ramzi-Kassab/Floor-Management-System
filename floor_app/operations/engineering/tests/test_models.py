"""
Tests for Engineering models
"""
from django.test import TestCase
from datetime import date

from floor_app.operations.engineering.models import (
    BitDesignLevel, BitDesignType, BitDesign, BitDesignRevision,
    BOM, BOMLine, RollerConeDesign, RollerConeComponent
)
from floor_app.operations.inventory.models import Item, UnitOfMeasure


class BitDesignLevelTest(TestCase):
    """Test BitDesignLevel model"""

    def test_create_design_level(self):
        """Test creating a design level"""
        level = BitDesignLevel.objects.create(
            code='L1',
            name='Level 1',
            description='Basic design level'
        )
        self.assertEqual(level.code, 'L1')
        self.assertEqual(level.name, 'Level 1')


class BitDesignTypeTest(TestCase):
    """Test BitDesignType model"""

    def test_create_design_type(self):
        """Test creating a design type"""
        design_type = BitDesignType.objects.create(
            code='PDC',
            name='PDC Bit',
            description='Polycrystalline Diamond Compact bit'
        )
        self.assertEqual(design_type.code, 'PDC')
        self.assertEqual(design_type.name, 'PDC Bit')


class BitDesignTest(TestCase):
    """Test BitDesign model"""

    def setUp(self):
        """Set up test data"""
        self.design_level = BitDesignLevel.objects.create(
            code='L1',
            name='Level 1'
        )
        self.design_type = BitDesignType.objects.create(
            code='PDC',
            name='PDC Bit'
        )

    def test_create_bit_design(self):
        """Test creating a bit design"""
        design = BitDesign.objects.create(
            design_code='PDC-8.5-001',
            design_level=self.design_level,
            design_type=self.design_type,
            size='8.5',
            description='8.5 inch PDC bit'
        )
        self.assertEqual(design.design_code, 'PDC-8.5-001')
        self.assertEqual(design.size, '8.5')
        self.assertEqual(design.design_level, self.design_level)

    def test_unique_design_code(self):
        """Test design code uniqueness"""
        BitDesign.objects.create(
            design_code='PDC-8.5-001',
            design_level=self.design_level,
            design_type=self.design_type
        )
        with self.assertRaises(Exception):
            BitDesign.objects.create(
                design_code='PDC-8.5-001',
                design_level=self.design_level,
                design_type=self.design_type
            )


class BitDesignRevisionTest(TestCase):
    """Test BitDesignRevision model"""

    def setUp(self):
        """Set up test data"""
        design_level = BitDesignLevel.objects.create(code='L1', name='Level 1')
        design_type = BitDesignType.objects.create(code='PDC', name='PDC')
        self.bit_design = BitDesign.objects.create(
            design_code='PDC-8.5-001',
            design_level=design_level,
            design_type=design_type
        )

    def test_create_revision(self):
        """Test creating a design revision"""
        revision = BitDesignRevision.objects.create(
            bit_design=self.bit_design,
            revision_number='R1',
            mat_number='MAT-001',
            effective_date=date.today(),
            description='Initial revision'
        )
        self.assertEqual(revision.revision_number, 'R1')
        self.assertEqual(revision.mat_number, 'MAT-001')
        self.assertEqual(revision.bit_design, self.bit_design)


class BOMTest(TestCase):
    """Test BOM model"""

    def setUp(self):
        """Set up test data"""
        design_level = BitDesignLevel.objects.create(code='L1', name='Level 1')
        design_type = BitDesignType.objects.create(code='PDC', name='PDC')
        bit_design = BitDesign.objects.create(
            design_code='PDC-8.5-001',
            design_level=design_level,
            design_type=design_type
        )
        self.revision = BitDesignRevision.objects.create(
            bit_design=bit_design,
            revision_number='R1',
            mat_number='MAT-001',
            effective_date=date.today()
        )

    def test_create_bom(self):
        """Test creating a BOM"""
        bom = BOM.objects.create(
            revision=self.revision,
            bom_number='BOM-001',
            version='1.0',
            status='ACTIVE'
        )
        self.assertEqual(bom.bom_number, 'BOM-001')
        self.assertEqual(bom.version, '1.0')
        self.assertEqual(bom.status, 'ACTIVE')


class BOMLineTest(TestCase):
    """Test BOMLine model"""

    def setUp(self):
        """Set up test data"""
        design_level = BitDesignLevel.objects.create(code='L1', name='Level 1')
        design_type = BitDesignType.objects.create(code='PDC', name='PDC')
        bit_design = BitDesign.objects.create(
            design_code='PDC-8.5-001',
            design_level=design_level,
            design_type=design_type
        )
        revision = BitDesignRevision.objects.create(
            bit_design=bit_design,
            revision_number='R1',
            mat_number='MAT-001',
            effective_date=date.today()
        )
        self.bom = BOM.objects.create(
            revision=revision,
            bom_number='BOM-001',
            version='1.0'
        )

        # Create inventory item
        uom = UnitOfMeasure.objects.create(code='EA', name='Each')
        self.item = Item.objects.create(
            sku='ITEM-001',
            name='Test Component',
            uom=uom
        )

    def test_create_bom_line(self):
        """Test creating a BOM line"""
        bom_line = BOMLine.objects.create(
            bom=self.bom,
            line_number=10,
            item=self.item,
            quantity=2.0,
            notes='Test component'
        )
        self.assertEqual(bom_line.line_number, 10)
        self.assertEqual(bom_line.quantity, 2.0)
        self.assertEqual(bom_line.item, self.item)


class RollerConeDesignTest(TestCase):
    """Test RollerConeDesign model"""

    def test_create_roller_cone_design(self):
        """Test creating a roller cone design"""
        design = RollerConeDesign.objects.create(
            design_code='RC-7875',
            bit_type='TRICONE',
            bearing='SEALED',
            seal='METAL',
            description='7 7/8 inch tricone bit'
        )
        self.assertEqual(design.design_code, 'RC-7875')
        self.assertEqual(design.bit_type, 'TRICONE')
        self.assertEqual(design.bearing, 'SEALED')


class RollerConeComponentTest(TestCase):
    """Test RollerConeComponent model"""

    def setUp(self):
        """Set up test data"""
        self.design = RollerConeDesign.objects.create(
            design_code='RC-7875',
            bit_type='TRICONE'
        )

        uom = UnitOfMeasure.objects.create(code='EA', name='Each')
        self.item = Item.objects.create(
            sku='CONE-001',
            name='Roller Cone',
            uom=uom
        )

    def test_create_roller_cone_component(self):
        """Test creating a roller cone component"""
        component = RollerConeComponent.objects.create(
            roller_cone_design=self.design,
            sequence=1,
            component_name='Main Cone',
            item=self.item,
            quantity=3,
            notes='Three cones required'
        )
        self.assertEqual(component.sequence, 1)
        self.assertEqual(component.quantity, 3)
        self.assertEqual(component.roller_cone_design, self.design)

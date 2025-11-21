"""
Tests for Bit Design and MAT Revision CRUD Functionality

Tests the Bit Design and MAT (Material) Revision management including:
- BitDesign model and CRUD operations
- BitDesignRevision (MAT) model and CRUD operations
- Relationship between designs and revisions
- Form validation
"""

from decimal import Decimal
from datetime import date
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from floor_app.operations.engineering.models import BitDesign, BitDesignRevision

User = get_user_model()


class TestBitDesignModel(TestCase):
    """Test the BitDesign model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_bitdesign_creation(self):
        """Test creating a bit design."""
        design = BitDesign.objects.create(
            design_number='DES-001',
            design_name='PDC Drill Bit Design',
            bit_type='PDC',
            nominal_diameter=Decimal('8.50'),
            diameter_unit='INCH',
            is_active=True,
            created_by=self.user
        )

        self.assertEqual(design.design_number, 'DES-001')
        self.assertEqual(design.design_name, 'PDC Drill Bit Design')
        self.assertEqual(design.bit_type, 'PDC')
        self.assertEqual(design.nominal_diameter, Decimal('8.50'))
        self.assertTrue(design.is_active)

    def test_bitdesign_string_representation(self):
        """Test __str__ method."""
        design = BitDesign.objects.create(
            design_number='DES-002',
            design_name='Roller Cone Bit',
            bit_type='ROLLER_CONE',
            created_by=self.user
        )

        str_repr = str(design)
        self.assertIn('DES-002', str_repr)

    def test_bitdesign_with_specifications(self):
        """Test bit design with detailed specifications."""
        design = BitDesign.objects.create(
            design_number='DES-003',
            design_name='Advanced PDC',
            bit_type='PDC',
            nominal_diameter=Decimal('12.25'),
            diameter_unit='INCH',
            number_of_blades=6,
            hydraulic_design='Optimized Flow',
            gauge_type='Cylindrical',
            iadc_code='M323',
            design_notes='High performance design for hard rock',
            is_active=True,
            created_by=self.user
        )

        self.assertEqual(design.number_of_blades, 6)
        self.assertEqual(design.hydraulic_design, 'Optimized Flow')
        self.assertEqual(design.iadc_code, 'M323')

    def test_bitdesign_bit_type_choices(self):
        """Test that bit type is from valid choices."""
        design = BitDesign.objects.create(
            design_number='DES-004',
            design_name='Hybrid Bit',
            bit_type='HYBRID',
            created_by=self.user
        )

        valid_types = ['PDC', 'ROLLER_CONE', 'HYBRID', 'NATURAL_DIAMOND', 'TSP', 'IMPREGNATED', 'OTHER']
        self.assertIn(design.bit_type, valid_types)


class TestBitDesignRevisionModel(TestCase):
    """Test the BitDesignRevision (MAT) model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        self.design = BitDesign.objects.create(
            design_number='DES-001',
            design_name='Base Design',
            bit_type='PDC',
            created_by=self.user
        )

    def test_revision_creation(self):
        """Test creating a revision."""
        revision = BitDesignRevision.objects.create(
            bit_design=self.design,
            mat_number='MAT-001-R01',
            revision_number='R01',
            revision_date=date(2024, 1, 15),
            description='Initial production revision',
            is_current=True,
            created_by=self.user
        )

        self.assertEqual(revision.bit_design, self.design)
        self.assertEqual(revision.mat_number, 'MAT-001-R01')
        self.assertEqual(revision.revision_number, 'R01')
        self.assertTrue(revision.is_current)

    def test_revision_string_representation(self):
        """Test __str__ method."""
        revision = BitDesignRevision.objects.create(
            bit_design=self.design,
            mat_number='MAT-001-R02',
            revision_number='R02',
            created_by=self.user
        )

        str_repr = str(revision)
        self.assertIn('MAT-001-R02', str_repr)

    def test_multiple_revisions_for_design(self):
        """Test that a design can have multiple revisions."""
        rev1 = BitDesignRevision.objects.create(
            bit_design=self.design,
            mat_number='MAT-001-R01',
            revision_number='R01',
            is_current=False,
            created_by=self.user
        )

        rev2 = BitDesignRevision.objects.create(
            bit_design=self.design,
            mat_number='MAT-001-R02',
            revision_number='R02',
            is_current=False,
            created_by=self.user
        )

        rev3 = BitDesignRevision.objects.create(
            bit_design=self.design,
            mat_number='MAT-001-R03',
            revision_number='R03',
            is_current=True,
            created_by=self.user
        )

        # Verify all revisions are linked to the design
        revisions = self.design.revisions.all()
        self.assertEqual(revisions.count(), 3)
        self.assertIn(rev1, revisions)
        self.assertIn(rev2, revisions)
        self.assertIn(rev3, revisions)

    def test_revision_with_changes(self):
        """Test revision with documented changes."""
        revision = BitDesignRevision.objects.create(
            bit_design=self.design,
            mat_number='MAT-001-R04',
            revision_number='R04',
            revision_date=date(2024, 2, 1),
            description='Updated cutter layout',
            changes_made='Increased number of backup cutters from 3 to 5',
            reason_for_change='Improve durability in abrasive formations',
            approved_by=self.user,
            is_current=True,
            created_by=self.user
        )

        self.assertEqual(revision.changes_made, 'Increased number of backup cutters from 3 to 5')
        self.assertEqual(revision.reason_for_change, 'Improve durability in abrasive formations')
        self.assertEqual(revision.approved_by, self.user)


class TestBitDesignCreateView(TestCase):
    """Test the BitDesign create view."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            is_staff=True
        )
        self.client.login(username='testuser', password='testpass123')

    def test_bitdesign_create_view_loads(self):
        """Test that create view loads."""
        response = self.client.get(reverse('inventory:bitdesign_create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'inventory/bit_designs/form.html')

    def test_bitdesign_create_requires_login(self):
        """Test that create view requires authentication."""
        self.client.logout()
        response = self.client.get(reverse('inventory:bitdesign_create'))
        self.assertEqual(response.status_code, 302)

    def test_bitdesign_create_success(self):
        """Test successful bit design creation."""
        data = {
            'design_number': 'NEW-DES-001',
            'design_name': 'New PDC Design',
            'bit_type': 'PDC',
            'nominal_diameter': '8.50',
            'diameter_unit': 'INCH',
            'is_active': True
        }

        response = self.client.post(reverse('inventory:bitdesign_create'), data)
        self.assertEqual(response.status_code, 302)  # Redirect on success

        # Verify design was created
        design = BitDesign.objects.get(design_number='NEW-DES-001')
        self.assertEqual(design.design_name, 'New PDC Design')
        self.assertEqual(design.bit_type, 'PDC')

    def test_bitdesign_create_with_full_specs(self):
        """Test creating design with full specifications."""
        data = {
            'design_number': 'FULL-SPEC-001',
            'design_name': 'Fully Specified Design',
            'bit_type': 'PDC',
            'nominal_diameter': '12.25',
            'diameter_unit': 'INCH',
            'number_of_blades': 7,
            'hydraulic_design': 'Multi-stage nozzle',
            'gauge_type': 'Tapered',
            'iadc_code': 'M333',
            'design_notes': 'Optimized for deep drilling',
            'is_active': True
        }

        response = self.client.post(reverse('inventory:bitdesign_create'), data)
        self.assertEqual(response.status_code, 302)

        design = BitDesign.objects.get(design_number='FULL-SPEC-001')
        self.assertEqual(design.number_of_blades, 7)
        self.assertEqual(design.iadc_code, 'M333')


class TestBitDesignUpdateView(TestCase):
    """Test the BitDesign update view."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            is_staff=True
        )
        self.client.login(username='testuser', password='testpass123')

        self.design = BitDesign.objects.create(
            design_number='ORIG-DES',
            design_name='Original Name',
            bit_type='PDC',
            created_by=self.user
        )

    def test_bitdesign_update_view_loads(self):
        """Test that update view loads."""
        response = self.client.get(
            reverse('inventory:bitdesign_edit', kwargs={'pk': self.design.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'inventory/bit_designs/form.html')

    def test_bitdesign_update_success(self):
        """Test successful design update."""
        data = {
            'design_number': 'ORIG-DES',
            'design_name': 'Updated Name',
            'bit_type': 'HYBRID',
            'nominal_diameter': '9.875',
            'diameter_unit': 'INCH',
            'is_active': True
        }

        response = self.client.post(
            reverse('inventory:bitdesign_edit', kwargs={'pk': self.design.pk}),
            data
        )
        self.assertEqual(response.status_code, 302)

        # Verify changes
        self.design.refresh_from_db()
        self.assertEqual(self.design.design_name, 'Updated Name')
        self.assertEqual(self.design.bit_type, 'HYBRID')
        self.assertEqual(self.design.nominal_diameter, Decimal('9.875'))


class TestBitDesignRevisionCreateView(TestCase):
    """Test the BitDesignRevision (MAT) create view."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            is_staff=True
        )
        self.client.login(username='testuser', password='testpass123')

        self.design = BitDesign.objects.create(
            design_number='DES-001',
            design_name='Base Design',
            bit_type='PDC',
            created_by=self.user
        )

    def test_revision_create_view_loads(self):
        """Test that MAT create view loads."""
        response = self.client.get(reverse('inventory:mat_create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'inventory/bit_designs/mat_form.html')

    def test_revision_create_requires_login(self):
        """Test that create view requires authentication."""
        self.client.logout()
        response = self.client.get(reverse('inventory:mat_create'))
        self.assertEqual(response.status_code, 302)

    def test_revision_create_success(self):
        """Test successful revision creation."""
        data = {
            'bit_design': self.design.id,
            'mat_number': 'MAT-NEW-001',
            'revision_number': 'R01',
            'revision_date': '2024-03-01',
            'description': 'New revision',
            'is_current': True
        }

        response = self.client.post(reverse('inventory:mat_create'), data)
        self.assertEqual(response.status_code, 302)

        # Verify revision was created
        revision = BitDesignRevision.objects.get(mat_number='MAT-NEW-001')
        self.assertEqual(revision.bit_design, self.design)
        self.assertEqual(revision.revision_number, 'R01')
        self.assertTrue(revision.is_current)

    def test_revision_create_with_changes(self):
        """Test creating revision with change documentation."""
        data = {
            'bit_design': self.design.id,
            'mat_number': 'MAT-CHANGE-001',
            'revision_number': 'R02',
            'revision_date': '2024-03-15',
            'description': 'Performance improvement',
            'changes_made': 'Modified cutter layout',
            'reason_for_change': 'Better ROP in hard formations',
            'is_current': True
        }

        response = self.client.post(reverse('inventory:mat_create'), data)
        self.assertEqual(response.status_code, 302)

        revision = BitDesignRevision.objects.get(mat_number='MAT-CHANGE-001')
        self.assertEqual(revision.changes_made, 'Modified cutter layout')
        self.assertEqual(revision.reason_for_change, 'Better ROP in hard formations')


class TestBitDesignRevisionUpdateView(TestCase):
    """Test the BitDesignRevision (MAT) update view."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            is_staff=True
        )
        self.client.login(username='testuser', password='testpass123')

        self.design = BitDesign.objects.create(
            design_number='DES-001',
            design_name='Base Design',
            bit_type='PDC',
            created_by=self.user
        )

        self.revision = BitDesignRevision.objects.create(
            bit_design=self.design,
            mat_number='MAT-ORIG',
            revision_number='R01',
            is_current=True,
            created_by=self.user
        )

    def test_revision_update_view_loads(self):
        """Test that MAT update view loads."""
        response = self.client.get(
            reverse('inventory:mat_edit', kwargs={'pk': self.revision.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'inventory/bit_designs/mat_form.html')

    def test_revision_update_success(self):
        """Test successful revision update."""
        data = {
            'bit_design': self.design.id,
            'mat_number': 'MAT-ORIG',
            'revision_number': 'R01-A',
            'revision_date': '2024-04-01',
            'description': 'Updated description',
            'is_current': True
        }

        response = self.client.post(
            reverse('inventory:mat_edit', kwargs={'pk': self.revision.pk}),
            data
        )
        self.assertEqual(response.status_code, 302)

        # Verify changes
        self.revision.refresh_from_db()
        self.assertEqual(self.revision.revision_number, 'R01-A')
        self.assertEqual(self.revision.description, 'Updated description')


class TestBitDesignRevisionRelationship(TestCase):
    """Test the relationship between BitDesign and BitDesignRevision."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        self.design = BitDesign.objects.create(
            design_number='DES-REL-001',
            design_name='Relationship Test Design',
            bit_type='PDC',
            created_by=self.user
        )

    def test_design_can_have_multiple_revisions(self):
        """Test that one design can have many revisions."""
        # Create 5 revisions
        for i in range(1, 6):
            BitDesignRevision.objects.create(
                bit_design=self.design,
                mat_number=f'MAT-{i:03d}',
                revision_number=f'R{i:02d}',
                created_by=self.user
            )

        revisions = self.design.revisions.all()
        self.assertEqual(revisions.count(), 5)

    def test_revision_belongs_to_one_design(self):
        """Test that a revision belongs to exactly one design."""
        revision = BitDesignRevision.objects.create(
            bit_design=self.design,
            mat_number='MAT-SINGLE',
            revision_number='R01',
            created_by=self.user
        )

        self.assertEqual(revision.bit_design, self.design)
        self.assertEqual(revision.bit_design.design_number, 'DES-REL-001')

    def test_current_revision_tracking(self):
        """Test tracking of current revision."""
        old_rev = BitDesignRevision.objects.create(
            bit_design=self.design,
            mat_number='MAT-OLD',
            revision_number='R01',
            is_current=False,
            created_by=self.user
        )

        current_rev = BitDesignRevision.objects.create(
            bit_design=self.design,
            mat_number='MAT-CURRENT',
            revision_number='R02',
            is_current=True,
            created_by=self.user
        )

        # Get current revision
        current = self.design.revisions.filter(is_current=True).first()
        self.assertEqual(current, current_rev)
        self.assertEqual(current.mat_number, 'MAT-CURRENT')

    def test_revision_deletion_preserves_design(self):
        """Test that deleting a revision doesn't delete the design."""
        revision = BitDesignRevision.objects.create(
            bit_design=self.design,
            mat_number='MAT-DELETE',
            revision_number='R01',
            created_by=self.user
        )

        revision_id = revision.id
        revision.delete()

        # Design should still exist
        self.assertTrue(BitDesign.objects.filter(id=self.design.id).exists())

        # Revision should be gone
        self.assertFalse(BitDesignRevision.objects.filter(id=revision_id).exists())


class TestBitDesignFormValidation(TestCase):
    """Test form validation for BitDesign."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            is_staff=True
        )
        self.client.login(username='testuser', password='testpass123')

    def test_unique_design_number(self):
        """Test that design numbers must be unique."""
        # Create first design
        BitDesign.objects.create(
            design_number='UNIQUE-001',
            design_name='First Design',
            bit_type='PDC',
            created_by=self.user
        )

        # Try to create second with same number
        data = {
            'design_number': 'UNIQUE-001',
            'design_name': 'Second Design',
            'bit_type': 'ROLLER_CONE',
            'is_active': True
        }

        response = self.client.post(reverse('inventory:bitdesign_create'), data)

        # Should not redirect (form has errors)
        # Note: This assumes unique constraint exists
        self.assertEqual(response.status_code, 200)

    def test_required_fields(self):
        """Test that required fields are enforced."""
        # Missing design_number
        data = {
            'design_name': 'Missing Number',
            'bit_type': 'PDC'
        }

        response = self.client.post(reverse('inventory:bitdesign_create'), data)
        self.assertEqual(response.status_code, 200)  # Form error, no redirect


class TestBitDesignRevisionFormValidation(TestCase):
    """Test form validation for BitDesignRevision."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            is_staff=True
        )
        self.client.login(username='testuser', password='testpass123')

        self.design = BitDesign.objects.create(
            design_number='VAL-001',
            design_name='Validation Test',
            bit_type='PDC',
            created_by=self.user
        )

    def test_revision_requires_design(self):
        """Test that revision must be linked to a design."""
        data = {
            'mat_number': 'MAT-NO-DESIGN',
            'revision_number': 'R01',
            'is_current': True
            # Missing bit_design
        }

        response = self.client.post(reverse('inventory:mat_create'), data)
        self.assertEqual(response.status_code, 200)  # Form error

    def test_unique_mat_number(self):
        """Test that MAT numbers should be unique."""
        # Create first revision
        BitDesignRevision.objects.create(
            bit_design=self.design,
            mat_number='UNIQUE-MAT-001',
            revision_number='R01',
            created_by=self.user
        )

        # Try to create second with same MAT number
        data = {
            'bit_design': self.design.id,
            'mat_number': 'UNIQUE-MAT-001',
            'revision_number': 'R02',
            'is_current': True
        }

        response = self.client.post(reverse('inventory:mat_create'), data)

        # Should have form error (assuming unique constraint)
        self.assertEqual(response.status_code, 200)

# Generated migration to create the generic Address model in operations app

from django.db import migrations, models
import django.db.models.deletion
from django.db.models import Q
from django.db.models.functions import Lower
from uuid import uuid4


class Migration(migrations.Migration):

    dependencies = [
        ('floor_app', '0019_add_position_and_enhance_employee'),
    ]

    operations = [
        # Create the generic Address model
        migrations.CreateModel(
            name='Address',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('public_id', models.UUIDField(db_index=True, default=uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True, db_index=True)),
                ('is_deleted', models.BooleanField(db_index=True, default=False, editable=False)),
                ('deleted_at', models.DateTimeField(blank=True, editable=False, null=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(app_label)s_%(class)s_created', to='auth.user')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(app_label)s_%(class)s_updated', to='auth.user')),
                ('remarks', models.CharField(blank=True, default='', max_length=255)),
                ('address_line1', models.CharField(help_text='Primary address line (street, building, etc.)', max_length=200)),
                ('address_line2', models.CharField(blank=True, default='', help_text='Secondary address line (apartment, suite, etc.)', max_length=200)),
                ('city', models.CharField(blank=True, default='', help_text='City/Town name', max_length=120)),
                ('state_region', models.CharField(blank=True, default='', help_text='State, Province, or Region', max_length=120)),
                ('postal_code', models.CharField(blank=True, default='', help_text='Postal code or ZIP code', max_length=20)),
                ('country_iso2', models.CharField(help_text='Country code (ISO 3166-1 alpha-2)', max_length=2)),
                ('latitude', models.DecimalField(blank=True, decimal_places=6, help_text='Latitude coordinate', max_digits=9, null=True)),
                ('longitude', models.DecimalField(blank=True, decimal_places=6, help_text='Longitude coordinate', max_digits=9, null=True)),
                ('address_kind', models.CharField(choices=[('STREET', 'Street Address'), ('PO_BOX', 'PO Box')], default='STREET', help_text='Type of address (street address or PO box)', max_length=8)),
                ('street_name', models.CharField(blank=True, default='', help_text='Street name (for KSA National Address)', max_length=200)),
                ('building_number', models.CharField(blank=True, default='', help_text='Building number (for KSA National Address)', max_length=16)),
                ('unit_number', models.CharField(blank=True, default='', help_text='Unit/Apartment/Office number', max_length=16)),
                ('neighborhood', models.CharField(blank=True, default='', help_text='Neighborhood name (for KSA National Address)', max_length=120)),
                ('additional_number', models.CharField(blank=True, default='', help_text='Additional number - 4 digits (for KSA National Address)', max_length=8)),
                ('po_box', models.CharField(blank=True, default='', help_text='PO Box number (when address_kind=PO_BOX)', max_length=20)),
                ('components', models.JSONField(blank=True, help_text='Additional address components (JSON format)', null=True)),
                ('label', models.CharField(blank=True, default='', help_text="Label for this address (e.g., 'Home', 'Well #5', 'Rig Alpha')", max_length=64)),
                ('verification_status', models.CharField(choices=[('UNVERIFIED', 'Unverified'), ('VERIFIED', 'Verified'), ('INVALID', 'Invalid')], default='UNVERIFIED', help_text='Address verification status', max_length=16)),
                ('accessibility_notes', models.TextField(blank=True, default='', help_text='Notes about accessibility (wheelchair, elevator, parking, etc.)')),
            ],
            options={
                'db_table': 'operations_address',
                'ordering': ['country_iso2', 'city', 'address_line1'],
            },
        ),

        # Add indexes
        migrations.AddIndex(
            model_name='address',
            index=models.Index(fields=['country_iso2', 'city', 'postal_code'], name='operations_country_city_postal'),
        ),
        migrations.AddIndex(
            model_name='address',
            index=models.Index(fields=['verification_status', 'is_deleted'], name='operations_verify_deleted'),
        ),

        # Add constraints
        migrations.AddConstraint(
            model_name='address',
            constraint=models.UniqueConstraint(
                condition=Q(('address_kind', 'STREET'), ('is_deleted', False)),
                fields=['country_iso2', 'city', 'neighborhood', 'street_name', 'building_number', 'unit_number'],
                name='uq_operations_address_street_tuple_ci',
            ),
        ),
        migrations.AddConstraint(
            model_name='address',
            constraint=models.UniqueConstraint(
                condition=Q(('address_kind', 'PO_BOX'), ('is_deleted', False)),
                fields=['country_iso2', 'city', 'po_box'],
                name='uq_operations_address_pobox_tuple_ci',
            ),
        ),
    ]

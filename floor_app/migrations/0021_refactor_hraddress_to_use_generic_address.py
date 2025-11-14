# Generated migration to add address FK to HRAddress

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('floor_app', '0020_create_generic_address_model'),
    ]

    operations = [
        # Add the new address foreign key field to HRAddress
        migrations.AddField(
            model_name='hraddress',
            name='address',
            field=models.ForeignKey(
                null=True,
                blank=True,
                help_text='The actual address data',
                on_delete=django.db.models.deletion.PROTECT,
                related_name='hr_people',
                to='floor_app.address'
            ),
        ),

        # Add new indexes for HR-specific lookups (if not already present)
        # Only add if they don't already exist
        migrations.AddIndex(
            model_name='hraddress',
            index=models.Index(fields=['person', 'kind'], name='hr_address_person_kind'),
        ),
        migrations.AddIndex(
            model_name='hraddress',
            index=models.Index(fields=['person', 'is_primary_hint'], name='hr_address_person_primary'),
        ),

        # Update Meta options
        migrations.AlterModelOptions(
            name='hraddress',
            options={
                'ordering': ['-is_primary_hint', '-updated_at'],
                'verbose_name': 'HR Address',
                'verbose_name_plural': 'HR Addresses',
            },
        ),

    ]

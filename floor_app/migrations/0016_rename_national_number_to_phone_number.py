# Generated migration for renaming national_number to phone_number in HRPhone model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('floor_app', '0015_hraddress_person_hremail_person_hrphone_person_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='hrphone',
            old_name='national_number',
            new_name='phone_number',
        ),
        migrations.AlterField(
            model_name='hrphone',
            name='phone_number',
            field=models.CharField(blank=True, default='', help_text='Phone number digits without country calling code', max_length=20, validators=[]),
        ),
    ]

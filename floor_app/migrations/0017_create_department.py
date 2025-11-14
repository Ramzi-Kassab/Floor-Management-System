# Generated migration to create Department model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('floor_app', '0016_replace_is_operator_with_employee_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='Department',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Department name', max_length=200, unique=True)),
                ('description', models.TextField(blank=True, help_text='Department description and responsibilities', null=True)),
                ('department_type', models.CharField(
                    choices=[
                        ('PRODUCTION', 'Production'),
                        ('SUPPORT', 'Support'),
                        ('MANAGEMENT', 'Management'),
                        ('OTHER', 'Other'),
                    ],
                    default='OTHER',
                    help_text='Category of department',
                    max_length=20,
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Department',
                'verbose_name_plural': 'Departments',
                'db_table': 'hr_department',
                'ordering': ['name'],
            },
        ),
        migrations.AddIndex(
            model_name='department',
            index=models.Index(fields=['name'], name='hr_departm_name_idx'),
        ),
        migrations.AddIndex(
            model_name='department',
            index=models.Index(fields=['department_type'], name='hr_departm_dept_type_idx'),
        ),
    ]

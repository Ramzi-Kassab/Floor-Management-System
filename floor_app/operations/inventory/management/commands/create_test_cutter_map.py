"""
Management command to create test cutter maps from BOM.

Usage:
    python manage.py create_test_cutter_map --job-card JC-001
    python manage.py create_test_cutter_map --job-card JC-001 --map-type AS_BUILT
    python manage.py create_test_cutter_map --job-card JC-001 --fill-random
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
import random

from floor_app.operations.inventory.models import (
    CutterBOMGridHeader,
    CutterMapHeader,
    CutterMapCell,
    CutterDetail,
)
from floor_app.operations.production.models import JobCard


class Command(BaseCommand):
    help = 'Create test cutter map from BOM grid'

    def add_arguments(self, parser):
        parser.add_argument(
            '--job-card',
            type=str,
            required=True,
            help='Job card number'
        )
        parser.add_argument(
            '--bom',
            type=str,
            default='BOM-TEST-GRID-001',
            help='BOM number to use (default: BOM-TEST-GRID-001)'
        )
        parser.add_argument(
            '--map-type',
            type=str,
            default='AS_BUILT',
            choices=[
                'DESIGN',
                'AS_RECEIVED',
                'AS_BUILT',
                'POST_EVAL',
                'POST_NDT',
                'POST_REWORK',
                'FINAL'
            ],
            help='Map type (default: AS_BUILT)'
        )
        parser.add_argument(
            '--sequence',
            type=int,
            default=1,
            help='Sequence number (default: 1)'
        )
        parser.add_argument(
            '--fill-random',
            action='store_true',
            help='Randomly fill some cells with actual cutters'
        )
        parser.add_argument(
            '--fill-percentage',
            type=int,
            default=70,
            help='Percentage of cells to fill when using --fill-random (default: 70)'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        job_card_number = options['job_card']
        bom_number = options['bom']
        map_type = options['map_type']
        sequence = options['sequence']
        fill_random = options['fill_random']
        fill_percentage = options['fill_percentage']

        self.stdout.write(
            self.style.SUCCESS(
                f'\nCreating test cutter map: {map_type} for {job_card_number}'
            )
        )

        # Get or create job card
        try:
            job_card = JobCard.objects.get(job_card_number=job_card_number)
            self.stdout.write(f'  Using job card: {job_card_number}')
        except JobCard.DoesNotExist:
            raise CommandError(
                f'Job card "{job_card_number}" not found. '
                f'Please create it first or use an existing job card number.'
            )

        # Get BOM grid
        try:
            grid_header = CutterBOMGridHeader.objects.select_related('bom_header').get(
                bom_header__bom_number=bom_number
            )
            self.stdout.write(f'  Using BOM: {bom_number}')
        except CutterBOMGridHeader.DoesNotExist:
            raise CommandError(
                f'BOM grid "{bom_number}" not found. '
                f'Run create_test_cutter_bom first.'
            )

        # Create or get map header
        map_header, created = CutterMapHeader.objects.get_or_create(
            job_card=job_card,
            map_type=map_type,
            sequence_number=sequence,
            defaults={
                'source_bom_grid': grid_header,
                'validation_status': 'PENDING',
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created map header'))
        else:
            self.stdout.write(f'  Using existing map')

        # Create cells from BOM
        self.stdout.write('  Creating map cells from BOM...')
        cells = map_header.create_from_bom()
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(cells)} map cells'))

        # Fill random cells if requested
        if fill_random:
            self.stdout.write(
                f'  Randomly filling {fill_percentage}% of cells...'
            )

            cells_to_fill = random.sample(
                list(map_header.cells.all()),
                k=int(len(cells) * fill_percentage / 100)
            )

            filled_count = 0
            substitution_count = 0

            for cell in cells_to_fill:
                # 80% chance to use correct type, 20% chance to substitute
                if random.random() < 0.8 and cell.required_cutter_type:
                    # Use correct type
                    actual_type = cell.required_cutter_type
                    cell.status = 'CORRECT'
                else:
                    # Use random substitute
                    all_cutters = list(CutterDetail.objects.all()[:10])
                    if all_cutters:
                        actual_type = random.choice(all_cutters)
                        cell.status = 'SUBSTITUTED'
                        substitution_count += 1
                    else:
                        continue

                cell.actual_cutter_type = actual_type

                # Add random notes based on map type
                if map_type == 'AS_RECEIVED':
                    cell.receiving_notes = f'Received OK - Inspector #{random.randint(1, 5)}'
                elif map_type == 'AS_BUILT':
                    cell.production_notes = f'Installed by brazer #{random.randint(1, 10)}'
                elif map_type == 'POST_EVAL':
                    cell.qc_notes = f'QC check - Grade {random.choice(["A", "B", "C"])}'
                elif map_type == 'POST_NDT':
                    cell.ndt_notes = 'NDT inspection passed'
                elif map_type == 'POST_REWORK':
                    cell.rework_notes = 'Reworked - depth adjusted'
                elif map_type == 'FINAL':
                    cell.final_inspection_notes = 'Final inspection OK'

                cell.save()
                filled_count += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Filled {filled_count} cells '
                    f'({substitution_count} substitutions)'
                )
            )

        # Validate map
        self.stdout.write('  Validating map against BOM...')
        validation = map_header.validate_against_bom()

        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Validation complete: {map_header.validation_status}'
            )
        )

        # Display results
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('Test Cutter Map Created Successfully!'))
        self.stdout.write('='*60)
        self.stdout.write(f'Job Card: {job_card_number}')
        self.stdout.write(f'Map Type: {map_type}')
        self.stdout.write(f'Sequence: {sequence}')
        self.stdout.write(f'Source BOM: {bom_number}')
        self.stdout.write(f'Total Cells: {map_header.cells.count()}')
        self.stdout.write(f'Validation Status: {map_header.validation_status}')
        self.stdout.write('')

        # Display validation summary
        if validation['summary']:
            self.stdout.write('Cutter Type Status:')
            for cutter_type, info in validation['summary'].items():
                status_icon = {
                    'OK': '✓',
                    'UNDER': '⚠',
                    'OVER': '✗',
                }.get(info['status'], '?')

                self.stdout.write(
                    f'  {status_icon} {cutter_type}: '
                    f'{info["actual"]}/{info["required"]} '
                    f'(remaining: {info["remaining"]})'
                )

        if validation['errors']:
            self.stdout.write('\nErrors:')
            for error in validation['errors']:
                self.stdout.write(self.style.ERROR(f'  ✗ {error}'))

        if validation['warnings']:
            self.stdout.write('\nWarnings:')
            for warning in validation['warnings']:
                self.stdout.write(self.style.WARNING(f'  ⚠ {warning}'))

        self.stdout.write('\n✅ Done! You can now test the map in Django admin.')

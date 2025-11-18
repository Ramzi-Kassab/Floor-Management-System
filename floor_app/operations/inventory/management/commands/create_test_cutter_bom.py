"""
Management command to create test cutter BOM grids.

Usage:
    python manage.py create_test_cutter_bom
    python manage.py create_test_cutter_bom --blades 6 --pockets 12
    python manage.py create_test_cutter_bom --ordering FORMATION
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from floor_app.operations.inventory.models import (
    BOMHeader,
    CutterBOMGridHeader,
    CutterBOMGridCell,
    CutterDetail,
)
from floor_app.operations.evaluation.models import BitSection


class Command(BaseCommand):
    help = 'Create test cutter BOM grid with sample data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--blades',
            type=int,
            default=5,
            help='Number of blades (default: 5)'
        )
        parser.add_argument(
            '--pockets',
            type=int,
            default=10,
            help='Maximum pockets per blade (default: 10)'
        )
        parser.add_argument(
            '--ordering',
            type=str,
            default='CONTINUOUS',
            choices=['CONTINUOUS', 'RESET_PER_TYPE', 'FORMATION'],
            help='Ordering scheme (default: CONTINUOUS)'
        )
        parser.add_argument(
            '--no-reclaimed',
            action='store_true',
            help='Do not show reclaimed cutters (for new bit production)'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        blade_count = options['blades']
        max_pockets = options['pockets']
        ordering = options['ordering']
        show_reclaimed = not options['no_reclaimed']

        self.stdout.write(
            self.style.SUCCESS(
                f'\nCreating test BOM grid: {blade_count} blades × {max_pockets} pockets'
            )
        )

        # Create or get a test BOM header
        bom_header, created = BOMHeader.objects.get_or_create(
            bom_number='BOM-TEST-GRID-001',
            defaults={
                'name': 'Test Cutter Grid BOM',
                'bom_type': 'PRODUCTION',
                'status': 'ACTIVE',
                'description': 'Test BOM for cutter grid system',
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created BOM header: {bom_header.bom_number}'))
        else:
            self.stdout.write(f'  Using existing BOM: {bom_header.bom_number}')

        # Create or get grid header
        grid_header, created = CutterBOMGridHeader.objects.get_or_create(
            bom_header=bom_header,
            defaults={
                'blade_count': blade_count,
                'max_pockets_per_blade': max_pockets,
                'cutter_ordering_scheme': ordering,
                'show_reclaimed_cutters': show_reclaimed,
            }
        )

        if not created:
            # Update existing
            grid_header.blade_count = blade_count
            grid_header.max_pockets_per_blade = max_pockets
            grid_header.cutter_ordering_scheme = ordering
            grid_header.show_reclaimed_cutters = show_reclaimed
            grid_header.save()
            # Clear existing cells
            grid_header.cells.all().delete()
            self.stdout.write('  Cleared existing grid cells')

        self.stdout.write(self.style.SUCCESS(f'✓ Grid header ready'))

        # Get some test cutter types
        cutter_types = list(CutterDetail.objects.all()[:5])

        if not cutter_types:
            self.stdout.write(
                self.style.WARNING(
                    '\n⚠ No cutter types found. Please create some CutterDetail records first.'
                )
            )
            return

        self.stdout.write(f'  Using {len(cutter_types)} cutter types')

        # Get bit sections
        sections = {
            'cone': BitSection.objects.filter(section_name__icontains='cone').first(),
            'nose': BitSection.objects.filter(section_name__icontains='nose').first(),
            'taper': BitSection.objects.filter(section_name__icontains='taper').first(),
            'shoulder': BitSection.objects.filter(section_name__icontains='shoulder').first(),
            'gauge': BitSection.objects.filter(section_name__icontains='gauge').first(),
        }

        # Define section distribution
        section_ranges = [
            ('cone', 0.0, 0.15),    # First 15%
            ('nose', 0.15, 0.35),   # Next 20%
            ('taper', 0.35, 0.6),   # Next 25%
            ('shoulder', 0.6, 0.85),  # Next 25%
            ('gauge', 0.85, 1.0),   # Last 15%
        ]

        # Create grid cells
        cells_created = 0
        primary_count = 0
        secondary_count = 0

        for blade_num in range(1, blade_count + 1):
            # Determine pockets for this blade (some variation)
            pockets_in_blade = max_pockets - (blade_num % 2)  # Slight variation

            for pocket_num in range(1, pockets_in_blade + 1):
                # Calculate position ratio
                position_ratio = (pocket_num - 1) / max(pockets_in_blade - 1, 1)

                # Determine section
                section = None
                section_name = ''
                for sect_name, start, end in section_ranges:
                    if start <= position_ratio < end:
                        section = sections.get(sect_name)
                        section_name = sect_name.capitalize()
                        break

                # Determine if primary or secondary
                # Let's put secondaries in first few pockets
                is_primary = pocket_num > 3

                # Select cutter type (vary by position)
                cutter_idx = (blade_num + pocket_num) % len(cutter_types)
                cutter_type = cutter_types[cutter_idx]

                # Create location name
                pocket_in_section = pocket_num if is_primary else pocket_num
                location_name = f"{section_name} {pocket_in_section}"

                # Create cell
                cell = CutterBOMGridCell.objects.create(
                    grid_header=grid_header,
                    blade_number=blade_num,
                    pocket_number=pocket_num,
                    is_primary=is_primary,
                    location_name=location_name,
                    section=section,
                    cutter_type=cutter_type,
                    notes=f'Test cell for B{blade_num}P{pocket_num}'
                )

                cells_created += 1
                if is_primary:
                    primary_count += 1
                else:
                    secondary_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Created {cells_created} cells '
                f'({primary_count} primary, {secondary_count} secondary)'
            )
        )

        # Assign sequence numbers
        self.stdout.write('  Assigning sequence numbers...')
        grid_header.assign_all_sequence_numbers()
        self.stdout.write(self.style.SUCCESS(f'✓ Sequence numbers assigned using {ordering} scheme'))

        # Recalculate totals
        self.stdout.write('  Recalculating totals...')
        grid_header.recalculate_totals()
        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Totals: {grid_header.total_primary_cutters} primary, '
                f'{grid_header.total_secondary_cutters} secondary'
            )
        )

        # Refresh summaries
        self.stdout.write('  Refreshing BOM summaries...')
        grid_header.refresh_summaries()
        summary_count = grid_header.summaries.count()
        self.stdout.write(self.style.SUCCESS(f'✓ Created {summary_count} BOM summaries'))

        # Display summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('Test BOM Grid Created Successfully!'))
        self.stdout.write('='*60)
        self.stdout.write(f'BOM Number: {bom_header.bom_number}')
        self.stdout.write(f'Grid: {blade_count} blades × {max_pockets} pockets')
        self.stdout.write(f'Ordering: {ordering}')
        self.stdout.write(f'Show Reclaimed: {"Yes" if show_reclaimed else "No"}')
        self.stdout.write(f'Total Cells: {cells_created}')
        self.stdout.write(f'Primary Cutters: {primary_count}')
        self.stdout.write(f'Secondary Cutters: {secondary_count}')
        self.stdout.write('')

        # Display summaries
        self.stdout.write('Cutter Type Summary:')
        for summary in grid_header.summaries.all():
            self.stdout.write(
                f'  • {summary.cutter_type}: {summary.required_quantity} '
                f'({summary.primary_count}P + {summary.secondary_count}S)'
            )

        self.stdout.write('\n✅ Done! You can now test the grid in Django admin.')

"""
Management command to auto-approve eligible retrieval requests.

This should be run periodically (e.g., every 5 minutes via cron or Celery).

Usage:
    python manage.py auto_approve_retrievals
"""

from django.core.management.base import BaseCommand
from floor_app.operations.retrieval.services import RetrievalService


class Command(BaseCommand):
    help = 'Auto-approve eligible retrieval requests'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be approved without actually approving'
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        self.stdout.write('Checking for eligible retrieval requests...')

        if dry_run:
            # In dry run, just show what would be approved
            from floor_app.operations.retrieval.models import RetrievalRequest

            pending_requests = RetrievalRequest.objects.filter(status='PENDING')
            eligible_count = 0

            for request in pending_requests:
                can_auto, reason = request.can_auto_approve()
                if can_auto:
                    eligible_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Would auto-approve: Request #{request.id} - "
                            f"{request.employee.username} - {request.get_object_display()}"
                        )
                    )

            self.stdout.write(
                self.style.SUCCESS(
                    f"\nDry run complete. {eligible_count} request(s) would be auto-approved."
                )
            )
        else:
            # Actually auto-approve
            approved_count = RetrievalService.auto_approve_eligible_requests()

            if approved_count > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ Successfully auto-approved {approved_count} retrieval request(s)"
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING('No eligible requests found for auto-approval')
                )

"""
Django management command to check deployment readiness
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connection
import sys


class Command(BaseCommand):
    help = 'Check deployment readiness and configuration'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('Floor Management System - Deployment Check'))
        self.stdout.write(self.style.SUCCESS('=' * 70))

        checks = [
            self.check_debug_mode,
            self.check_secret_key,
            self.check_database,
            self.check_static_files,
            self.check_media_files,
            self.check_allowed_hosts,
            self.check_email_config,
            self.check_migrations,
        ]

        passed = 0
        failed = 0

        for check in checks:
            result = check()
            if result:
                passed += 1
            else:
                failed += 1

        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(f'Results: {passed} passed, {failed} failed')
        self.stdout.write('=' * 70 + '\n')

        if failed > 0:
            self.stdout.write(self.style.ERROR('Deployment check failed!'))
            sys.exit(1)
        else:
            self.stdout.write(self.style.SUCCESS('All checks passed! System is ready for deployment.'))
            sys.exit(0)

    def check_debug_mode(self):
        """Check if DEBUG mode is disabled"""
        self.stdout.write('\nChecking DEBUG mode...', ending='')
        if settings.DEBUG:
            self.stdout.write(self.style.ERROR(' FAIL'))
            self.stdout.write(self.style.WARNING('  DEBUG mode is enabled. Must be False in production.'))
            return False
        else:
            self.stdout.write(self.style.SUCCESS(' PASS'))
            return True

    def check_secret_key(self):
        """Check if SECRET_KEY is set and secure"""
        self.stdout.write('\nChecking SECRET_KEY...', ending='')
        if not settings.SECRET_KEY:
            self.stdout.write(self.style.ERROR(' FAIL'))
            self.stdout.write(self.style.WARNING('  SECRET_KEY is not set.'))
            return False
        elif settings.SECRET_KEY == 'insecure-change-me' or len(settings.SECRET_KEY) < 50:
            self.stdout.write(self.style.ERROR(' FAIL'))
            self.stdout.write(self.style.WARNING('  SECRET_KEY appears to be default or too short.'))
            return False
        else:
            self.stdout.write(self.style.SUCCESS(' PASS'))
            return True

    def check_database(self):
        """Check database connection"""
        self.stdout.write('\nChecking database connection...', ending='')
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
                row = cursor.fetchone()
                if row[0] == 1:
                    self.stdout.write(self.style.SUCCESS(' PASS'))
                    db_engine = settings.DATABASES['default']['ENGINE']
                    self.stdout.write(f'  Database engine: {db_engine}')
                    return True
        except Exception as e:
            self.stdout.write(self.style.ERROR(' FAIL'))
            self.stdout.write(self.style.WARNING(f'  Database connection error: {e}'))
            return False

    def check_static_files(self):
        """Check static files configuration"""
        self.stdout.write('\nChecking static files...', ending='')
        if not settings.STATIC_ROOT:
            self.stdout.write(self.style.ERROR(' FAIL'))
            self.stdout.write(self.style.WARNING('  STATIC_ROOT is not set.'))
            return False
        else:
            self.stdout.write(self.style.SUCCESS(' PASS'))
            self.stdout.write(f'  STATIC_ROOT: {settings.STATIC_ROOT}')
            return True

    def check_media_files(self):
        """Check media files configuration"""
        self.stdout.write('\nChecking media files...', ending='')
        if not settings.MEDIA_ROOT:
            self.stdout.write(self.style.ERROR(' FAIL'))
            self.stdout.write(self.style.WARNING('  MEDIA_ROOT is not set.'))
            return False
        else:
            self.stdout.write(self.style.SUCCESS(' PASS'))
            self.stdout.write(f'  MEDIA_ROOT: {settings.MEDIA_ROOT}')
            return True

    def check_allowed_hosts(self):
        """Check ALLOWED_HOSTS configuration"""
        self.stdout.write('\nChecking ALLOWED_HOSTS...', ending='')
        if not settings.ALLOWED_HOSTS:
            self.stdout.write(self.style.ERROR(' FAIL'))
            self.stdout.write(self.style.WARNING('  ALLOWED_HOSTS is empty.'))
            return False
        elif settings.ALLOWED_HOSTS == ['*']:
            self.stdout.write(self.style.WARNING(' WARNING'))
            self.stdout.write(self.style.WARNING('  ALLOWED_HOSTS allows all hosts. Should be specific in production.'))
            return True
        else:
            self.stdout.write(self.style.SUCCESS(' PASS'))
            self.stdout.write(f'  ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}')
            return True

    def check_email_config(self):
        """Check email configuration"""
        self.stdout.write('\nChecking email configuration...', ending='')
        if not settings.EMAIL_HOST:
            self.stdout.write(self.style.WARNING(' WARNING'))
            self.stdout.write(self.style.WARNING('  EMAIL_HOST is not configured.'))
            return True  # Not critical, just warning
        else:
            self.stdout.write(self.style.SUCCESS(' PASS'))
            self.stdout.write(f'  EMAIL_HOST: {settings.EMAIL_HOST}')
            return True

    def check_migrations(self):
        """Check if there are unapplied migrations"""
        self.stdout.write('\nChecking migrations...', ending='')
        from django.core.management import call_command
        from io import StringIO

        try:
            output = StringIO()
            call_command('showmigrations', '--plan', stdout=output, no_color=True)
            output_str = output.getvalue()

            if '[ ]' in output_str:
                self.stdout.write(self.style.ERROR(' FAIL'))
                self.stdout.write(self.style.WARNING('  There are unapplied migrations.'))
                self.stdout.write(self.style.WARNING('  Run: python manage.py migrate'))
                return False
            else:
                self.stdout.write(self.style.SUCCESS(' PASS'))
                self.stdout.write('  All migrations applied.')
                return True
        except Exception as e:
            self.stdout.write(self.style.ERROR(' FAIL'))
            self.stdout.write(self.style.WARNING(f'  Error checking migrations: {e}'))
            return False

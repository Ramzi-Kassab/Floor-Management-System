"""
Health Check Views

Provides health check endpoints for monitoring system status.
"""
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
import sys


def health_check(request):
    """
    Comprehensive health check endpoint.

    Returns JSON with status of all system components.
    Used by Docker healthcheck, load balancers, and monitoring tools.
    """
    health_status = {
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'version': '1.0.0',
        'components': {}
    }

    overall_healthy = True

    # Check Database
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        health_status['components']['database'] = {
            'status': 'healthy',
            'message': 'Connected'
        }
    except Exception as e:
        overall_healthy = False
        health_status['components']['database'] = {
            'status': 'unhealthy',
            'message': str(e)
        }

    # Check Cache (if configured)
    try:
        cache_key = 'health_check_test'
        cache.set(cache_key, 'test', 10)
        cache_value = cache.get(cache_key)
        if cache_value == 'test':
            health_status['components']['cache'] = {
                'status': 'healthy',
                'message': 'Connected'
            }
        else:
            health_status['components']['cache'] = {
                'status': 'degraded',
                'message': 'Cache read/write mismatch'
            }
    except Exception as e:
        # Cache is optional, so don't fail overall health
        health_status['components']['cache'] = {
            'status': 'unavailable',
            'message': str(e)
        }

    # Check Python version
    health_status['components']['python'] = {
        'status': 'healthy',
        'version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    }

    # Check Django DEBUG mode
    health_status['components']['django'] = {
        'debug_mode': settings.DEBUG,
        'status': 'healthy'
    }

    # Set overall status
    health_status['status'] = 'healthy' if overall_healthy else 'unhealthy'

    # Return appropriate HTTP status code
    status_code = 200 if overall_healthy else 503

    return JsonResponse(health_status, status=status_code)


def readiness_check(request):
    """
    Readiness check - is the application ready to receive traffic?

    Used by Kubernetes and other orchestration platforms.
    """
    try:
        # Check if database migrations are applied
        from django.db.migrations.executor import MigrationExecutor
        executor = MigrationExecutor(connection)
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())

        if plan:
            return JsonResponse({
                'status': 'not_ready',
                'message': 'Pending migrations',
                'pending_migrations': len(plan)
            }, status=503)

        return JsonResponse({
            'status': 'ready',
            'message': 'Application is ready to receive traffic'
        })

    except Exception as e:
        return JsonResponse({
            'status': 'not_ready',
            'message': str(e)
        }, status=503)


def liveness_check(request):
    """
    Liveness check - is the application alive?

    Used by Kubernetes and other orchestration platforms.
    Simple check that the process is running.
    """
    return JsonResponse({
        'status': 'alive',
        'timestamp': timezone.now().isoformat()
    })

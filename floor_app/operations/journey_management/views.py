"""
Journey Management System Views

Template-rendering views for journey planning, tracking, and management.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone

from .models import (
    Journey,
    JourneyWaypoint,
    JourneyCheckpoint,
)


@login_required
def journey_list(request):
    """List all journeys."""
    try:
        journeys = Journey.objects.select_related(
            'employee',
            'vehicle'
        ).order_by('-departure_time')

        # Filter by status
        status_filter = request.GET.get('status')
        if status_filter:
            journeys = journeys.filter(status=status_filter)

        # Filter by employee
        employee_id = request.GET.get('employee')
        if employee_id:
            journeys = journeys.filter(employee_id=employee_id)

        # Search
        search = request.GET.get('q')
        if search:
            journeys = journeys.filter(
                Q(origin__icontains=search) |
                Q(destination__icontains=search) |
                Q(purpose__icontains=search)
            )

        # Statistics
        stats = {
            'total': Journey.objects.count(),
            'planned': Journey.objects.filter(status='PLANNED').count(),
            'in_progress': Journey.objects.filter(status='IN_PROGRESS').count(),
            'completed': Journey.objects.filter(status='COMPLETED').count(),
        }

        context = {
            'journeys': journeys,
            'stats': stats,
            'status_choices': Journey.STATUS_CHOICES,
            'page_title': 'Journey List',
        }

    except Exception as e:
        messages.error(request, f'Error loading journeys: {str(e)}')
        context = {'journeys': [], 'stats': {}, 'page_title': 'Journey List'}

    return render(request, 'journey_management/journey_list.html', context)


@login_required
def journey_planner(request):
    """Plan a new journey."""
    try:
        if request.method == 'POST':
            try:
                origin = request.POST.get('origin')
                destination = request.POST.get('destination')
                departure_time = request.POST.get('departure_time')
                estimated_arrival = request.POST.get('estimated_arrival')
                purpose = request.POST.get('purpose')
                vehicle_id = request.POST.get('vehicle')

                if not all([origin, destination, departure_time, purpose]):
                    messages.error(request, 'Please fill in all required fields.')
                else:
                    from floor_app.operations.hr.models import HREmployee
                    employee = HREmployee.objects.filter(user=request.user).first()

                    journey = Journey.objects.create(
                        employee=employee,
                        origin=origin,
                        destination=destination,
                        departure_time=departure_time,
                        estimated_arrival=estimated_arrival,
                        purpose=purpose,
                        status='PLANNED'
                    )

                    if vehicle_id:
                        journey.vehicle_id = vehicle_id
                        journey.save()

                    messages.success(request, 'Journey planned successfully.')
                    return redirect('journey_management:journey_tracking', pk=journey.pk)

            except Exception as e:
                messages.error(request, f'Error planning journey: {str(e)}')

        # Get available vehicles
        from floor_app.operations.hr_assets.models import CompanyVehicle
        vehicles = CompanyVehicle.objects.filter(is_available=True)

        context = {
            'vehicles': vehicles,
            'page_title': 'Plan Journey',
        }

    except Exception as e:
        messages.error(request, f'Error loading planner: {str(e)}')
        context = {'vehicles': [], 'page_title': 'Plan Journey'}

    return render(request, 'journey_management/journey_planner.html', context)


@login_required
def journey_tracking(request, pk):
    """Track journey progress."""
    try:
        journey = get_object_or_404(
            Journey.objects.select_related('employee', 'vehicle'),
            pk=pk
        )

        if request.method == 'POST':
            action = request.POST.get('action')

            try:
                if action == 'start':
                    journey.status = 'IN_PROGRESS'
                    journey.actual_departure_time = timezone.now()
                    journey.save()
                    messages.success(request, 'Journey started.')

                elif action == 'complete':
                    journey.status = 'COMPLETED'
                    journey.actual_arrival_time = timezone.now()
                    journey.save()
                    messages.success(request, 'Journey completed.')

                elif action == 'checkpoint':
                    checkpoint_name = request.POST.get('checkpoint_name')
                    latitude = request.POST.get('latitude')
                    longitude = request.POST.get('longitude')

                    if checkpoint_name:
                        JourneyCheckpoint.objects.create(
                            journey=journey,
                            checkpoint_name=checkpoint_name,
                            checkpoint_time=timezone.now(),
                            latitude=latitude,
                            longitude=longitude
                        )
                        messages.success(request, 'Checkpoint added.')

                return redirect('journey_management:journey_tracking', pk=pk)

            except Exception as e:
                messages.error(request, f'Error: {str(e)}')

        # Get waypoints and checkpoints
        waypoints = journey.waypoints.order_by('waypoint_order')
        checkpoints = journey.checkpoints.order_by('-checkpoint_time')

        context = {
            'journey': journey,
            'waypoints': waypoints,
            'checkpoints': checkpoints,
            'page_title': f'Journey Tracking - {journey.origin} to {journey.destination}',
        }

    except Exception as e:
        messages.error(request, f'Error loading journey: {str(e)}')
        return redirect('journey_management:journey_list')

    return render(request, 'journey_management/journey_tracking.html', context)

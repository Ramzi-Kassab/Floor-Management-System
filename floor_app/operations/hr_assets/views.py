"""
HR Assets Management Views

Template-rendering views for vehicles, parking, SIM cards, phones, and cameras.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone

from .models import (
    Vehicle,
    VehicleAssignment,
    ParkingZone,
    ParkingSpot,
    ParkingAssignment,
    SIMCard,
    SIMAssignment,
    Phone,
    PhoneAssignment,
    Camera,
    CameraAssignment,
)


@login_required
def vehicle_list(request):
    """List all company vehicles with filters."""
    try:
        vehicles = Vehicle.objects.annotate(
            assignment_count=Count('assignments')
        ).order_by('-is_available', 'registration_number')

        # Filters
        status_filter = request.GET.get('status')
        if status_filter == 'available':
            vehicles = vehicles.filter(is_available=True)
        elif status_filter == 'assigned':
            vehicles = vehicles.filter(is_available=False)

        search = request.GET.get('q')
        if search:
            vehicles = vehicles.filter(
                Q(registration_number__icontains=search) |
                Q(make__icontains=search) |
                Q(model__icontains=search)
            )

        stats = {
            'total': Vehicle.objects.count(),
            'available': Vehicle.objects.filter(is_available=True).count(),
            'assigned': Vehicle.objects.filter(is_available=False).count(),
        }

        context = {
            'vehicles': vehicles,
            'stats': stats,
            'page_title': 'Company Vehicles',
        }

    except Exception as e:
        messages.error(request, f'Error loading vehicles: {str(e)}')
        context = {'vehicles': [], 'stats': {}, 'page_title': 'Company Vehicles'}

    return render(request, 'hr_assets/vehicle_list.html', context)


@login_required
def parking_dashboard(request):
    """Parking management dashboard."""
    try:
        parking_spaces = ParkingSpot.objects.annotate(
            allocation_count=Count('allocations')
        ).order_by('zone', 'space_number')

        allocations = ParkingAssignment.objects.select_related(
            'parking_space',
            'employee',
            'allocated_by'
        ).filter(is_active=True).order_by('-allocated_at')

        stats = {
            'total_spaces': ParkingSpot.objects.count(),
            'available': ParkingSpot.objects.filter(is_occupied=False).count(),
            'occupied': ParkingSpot.objects.filter(is_occupied=True).count(),
            'reserved': ParkingSpot.objects.filter(is_reserved=True).count(),
        }

        context = {
            'parking_spaces': parking_spaces,
            'allocations': allocations,
            'stats': stats,
            'page_title': 'Parking Management',
        }

    except Exception as e:
        messages.error(request, f'Error loading parking data: {str(e)}')
        context = {'parking_spaces': [], 'allocations': [], 'stats': {}, 'page_title': 'Parking Management'}

    return render(request, 'hr_assets/parking_dashboard.html', context)


@login_required
def sim_list(request):
    """List all SIM cards."""
    try:
        sim_cards = SIMCard.objects.select_related(
            'assigned_to',
            'company_phone'
        ).order_by('-is_active', 'phone_number')

        status_filter = request.GET.get('status')
        if status_filter == 'active':
            sim_cards = sim_cards.filter(is_active=True)
        elif status_filter == 'inactive':
            sim_cards = sim_cards.filter(is_active=False)

        search = request.GET.get('q')
        if search:
            sim_cards = sim_cards.filter(
                Q(phone_number__icontains=search) |
                Q(sim_number__icontains=search) |
                Q(carrier__icontains=search)
            )

        stats = {
            'total': SIMCard.objects.count(),
            'active': SIMCard.objects.filter(is_active=True).count(),
            'assigned': SIMCard.objects.filter(assigned_to__isnull=False).count(),
        }

        context = {
            'sim_cards': sim_cards,
            'stats': stats,
            'page_title': 'SIM Cards',
        }

    except Exception as e:
        messages.error(request, f'Error loading SIM cards: {str(e)}')
        context = {'sim_cards': [], 'stats': {}, 'page_title': 'SIM Cards'}

    return render(request, 'hr_assets/sim_list.html', context)


@login_required
def phone_list(request):
    """List all company phones."""
    try:
        phones = Phone.objects.select_related(
            'assigned_to',
            'sim_card'
        ).order_by('-is_active', 'make', 'model')

        status_filter = request.GET.get('status')
        if status_filter == 'active':
            phones = phones.filter(is_active=True)
        elif status_filter == 'inactive':
            phones = phones.filter(is_active=False)

        search = request.GET.get('q')
        if search:
            phones = phones.filter(
                Q(make__icontains=search) |
                Q(model__icontains=search) |
                Q(imei__icontains=search)
            )

        stats = {
            'total': Phone.objects.count(),
            'active': Phone.objects.filter(is_active=True).count(),
            'assigned': Phone.objects.filter(assigned_to__isnull=False).count(),
        }

        context = {
            'phones': phones,
            'stats': stats,
            'page_title': 'Company Phones',
        }

    except Exception as e:
        messages.error(request, f'Error loading phones: {str(e)}')
        context = {'phones': [], 'stats': {}, 'page_title': 'Company Phones'}

    return render(request, 'hr_assets/phone_list.html', context)


@login_required
def camera_list(request):
    """List all security cameras."""
    try:
        cameras = Camera.objects.order_by('location', 'camera_name')

        status_filter = request.GET.get('status')
        if status_filter == 'active':
            cameras = cameras.filter(is_active=True)
        elif status_filter == 'inactive':
            cameras = cameras.filter(is_active=False)

        search = request.GET.get('q')
        if search:
            cameras = cameras.filter(
                Q(camera_name__icontains=search) |
                Q(location__icontains=search) |
                Q(ip_address__icontains=search)
            )

        stats = {
            'total': Camera.objects.count(),
            'active': Camera.objects.filter(is_active=True).count(),
            'recording': Camera.objects.filter(is_recording=True).count(),
        }

        context = {
            'cameras': cameras,
            'stats': stats,
            'page_title': 'Security Cameras',
        }

    except Exception as e:
        messages.error(request, f'Error loading cameras: {str(e)}')
        context = {'cameras': [], 'stats': {}, 'page_title': 'Security Cameras'}

    return render(request, 'hr_assets/camera_list.html', context)


@login_required
def asset_dashboard(request):
    """Overall asset management dashboard."""
    try:
        stats = {
            'vehicles': {
                'total': Vehicle.objects.count(),
                'available': Vehicle.objects.filter(is_available=True).count(),
            },
            'parking': {
                'total': ParkingSpot.objects.count(),
                'available': ParkingSpot.objects.filter(is_occupied=False).count(),
            },
            'sim_cards': {
                'total': SIMCard.objects.count(),
                'active': SIMCard.objects.filter(is_active=True).count(),
            },
            'phones': {
                'total': Phone.objects.count(),
                'active': Phone.objects.filter(is_active=True).count(),
            },
            'cameras': {
                'total': Camera.objects.count(),
                'active': Camera.objects.filter(is_active=True).count(),
            },
        }

        recent_assignments = VehicleAssignment.objects.select_related(
            'vehicle',
            'employee',
            'assigned_by'
        ).filter(is_active=True).order_by('-assigned_at')[:10]

        context = {
            'stats': stats,
            'recent_assignments': recent_assignments,
            'page_title': 'Asset Dashboard',
        }

    except Exception as e:
        messages.error(request, f'Error loading dashboard: {str(e)}')
        context = {'stats': {}, 'recent_assignments': [], 'page_title': 'Asset Dashboard'}

    return render(request, 'hr_assets/asset_dashboard.html', context)

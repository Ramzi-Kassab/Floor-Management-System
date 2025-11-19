"""
Views for GPS Location Verification System.
"""
import json
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Q

from .models import LocationVerification, GeofenceDefinition, GPSTrackingLog


@login_required
def verification_dashboard(request):
    """
    GPS Verification Dashboard.

    Shows overview of location verifications and active geofence zones.
    """
    # Verification statistics
    total_verifications = LocationVerification.objects.count()
    verified_count = LocationVerification.objects.filter(status='VERIFIED').count()
    failed_count = LocationVerification.objects.filter(status='FAILED').count()
    pending_count = LocationVerification.objects.filter(status='PENDING').count()

    # Recent verifications
    recent_verifications = LocationVerification.objects.select_related(
        'verified_by_user',
        'verified_by_employee'
    ).order_by('-created_at')[:10]

    # Active geofence zones
    zones = GeofenceDefinition.objects.filter(is_active=True).order_by('name')

    # Verification types breakdown
    verifications_by_type = LocationVerification.objects.values('verification_type').annotate(
        count=Count('id')
    ).order_by('-count')

    # Today's statistics
    today = timezone.now().date()
    today_verified = LocationVerification.objects.filter(
        verified_at__date=today,
        status='VERIFIED'
    ).count()
    today_failed = LocationVerification.objects.filter(
        verified_at__date=today,
        status='FAILED'
    ).count()

    context = {
        'total_verifications': total_verifications,
        'verified_count': verified_count,
        'failed_count': failed_count,
        'pending_count': pending_count,
        'recent_verifications': recent_verifications,
        'zones': zones,
        'verifications_by_type': verifications_by_type,
        'today_verified': today_verified,
        'today_failed': today_failed,
    }

    return render(request, 'gps_system/verification_dashboard.html', context)


@login_required
def zone_list(request):
    """
    List all geofence zones.

    Supports filtering by type and active status.
    """
    zones = GeofenceDefinition.objects.all()

    # Filter by type
    zone_type = request.GET.get('type')
    if zone_type:
        zones = zones.filter(geofence_type=zone_type)

    # Filter by active status
    active = request.GET.get('active')
    if active == 'true':
        zones = zones.filter(is_active=True)
    elif active == 'false':
        zones = zones.filter(is_active=False)

    # Search
    search = request.GET.get('search')
    if search:
        zones = zones.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search) |
            Q(address__icontains=search)
        )

    zones = zones.order_by('name')

    context = {
        'zones': zones,
        'geofence_types': GeofenceDefinition.GEOFENCE_TYPES,
        'current_type': zone_type or '',
        'current_active': active or '',
        'search': search or '',
    }

    return render(request, 'gps_system/zone_list.html', context)


@login_required
def zone_form(request, pk=None):
    """
    Create or edit geofence zone.

    Args:
        pk: GeofenceDefinition primary key (None for create, int for edit)
    """
    zone = None
    if pk:
        zone = get_object_or_404(GeofenceDefinition, pk=pk)

    if request.method == 'POST':
        # Extract form data
        name = request.POST.get('name')
        geofence_type = request.POST.get('geofence_type')
        description = request.POST.get('description', '')
        shape = request.POST.get('shape', 'CIRCLE')
        address = request.POST.get('address', '')
        is_active = request.POST.get('is_active') == 'on'

        # Circle parameters
        center_latitude = request.POST.get('center_latitude')
        center_longitude = request.POST.get('center_longitude')
        radius_meters = request.POST.get('radius_meters', 100)

        # Polygon parameters
        polygon_points_json = request.POST.get('polygon_points', '[]')

        try:
            polygon_points = json.loads(polygon_points_json)
        except (json.JSONDecodeError, TypeError):
            polygon_points = []

        # Location FK (optional)
        location_id = request.POST.get('location_id')
        if location_id and not location_id.isdigit():
            location_id = None

        if zone:
            # Update existing zone
            zone.name = name
            zone.geofence_type = geofence_type
            zone.description = description
            zone.shape = shape
            zone.address = address
            zone.is_active = is_active

            if shape == 'CIRCLE':
                zone.center_latitude = Decimal(center_latitude) if center_latitude else None
                zone.center_longitude = Decimal(center_longitude) if center_longitude else None
                zone.radius_meters = int(radius_meters) if radius_meters else 100
            elif shape == 'POLYGON':
                zone.polygon_points = polygon_points

            zone.location_id = location_id
            zone.save()

            messages.success(request, f"Geofence zone '{name}' updated successfully")
        else:
            # Create new zone
            zone = GeofenceDefinition(
                name=name,
                geofence_type=geofence_type,
                description=description,
                shape=shape,
                address=address,
                is_active=is_active,
                radius_meters=int(radius_meters) if radius_meters else 100,
            )

            if shape == 'CIRCLE':
                zone.center_latitude = Decimal(center_latitude) if center_latitude else None
                zone.center_longitude = Decimal(center_longitude) if center_longitude else None
            elif shape == 'POLYGON':
                zone.polygon_points = polygon_points

            zone.location_id = location_id
            zone.save()

            messages.success(request, f"Geofence zone '{name}' created successfully")

        return redirect('gps_system:zone_list')

    # Prepare map data for Leaflet.js
    map_data = {
        'center_lat': None,
        'center_lon': None,
        'radius_meters': 100,
        'polygon_points': [],
        'shape': 'CIRCLE',
    }

    if zone:
        map_data['shape'] = zone.shape
        if zone.shape == 'CIRCLE':
            map_data['center_lat'] = float(zone.center_latitude) if zone.center_latitude else None
            map_data['center_lon'] = float(zone.center_longitude) if zone.center_longitude else None
            map_data['radius_meters'] = zone.radius_meters
        elif zone.shape == 'POLYGON':
            map_data['polygon_points'] = zone.polygon_points

    context = {
        'zone': zone,
        'geofence_types': GeofenceDefinition.GEOFENCE_TYPES,
        'geofence_shapes': GeofenceDefinition.GEOFENCE_SHAPES,
        'map_data': json.dumps(map_data),
        'is_edit': pk is not None,
    }

    return render(request, 'gps_system/zone_form.html', context)


@login_required
def verification_request(request):
    """
    Create and verify GPS location request.

    GET: Show verification form
    POST: Process verification with actual GPS coordinates
    """
    if request.method == 'POST':
        # Extract verification data
        verification_type = request.POST.get('verification_type')
        expected_latitude = request.POST.get('expected_latitude')
        expected_longitude = request.POST.get('expected_longitude')
        expected_address = request.POST.get('expected_address', '')
        geofence_radius_meters = request.POST.get('geofence_radius_meters', 100)

        # Actual GPS location (from device)
        actual_latitude = request.POST.get('actual_latitude')
        actual_longitude = request.POST.get('actual_longitude')
        gps_accuracy_meters = request.POST.get('gps_accuracy_meters')

        notes = request.POST.get('notes', '')

        # Device info
        device_info = {
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'ip_address': request.META.get('REMOTE_ADDR', ''),
        }

        # Get employee info
        employee_id = None
        try:
            from floor_app.operations.hr.models import HREmployee
            employee = HREmployee.objects.filter(user=request.user).first()
            if employee:
                employee_id = employee.pk
        except Exception:
            pass

        # Create verification record
        verification = LocationVerification.objects.create(
            verification_type=verification_type,
            expected_latitude=Decimal(expected_latitude),
            expected_longitude=Decimal(expected_longitude),
            expected_address=expected_address,
            geofence_radius_meters=int(geofence_radius_meters),
            notes=notes,
            created_by=request.user,
        )

        # Perform verification if actual location provided
        if actual_latitude and actual_longitude:
            verification.verify_location(
                actual_lat=Decimal(actual_latitude),
                actual_lon=Decimal(actual_longitude),
                accuracy=float(gps_accuracy_meters) if gps_accuracy_meters else None,
                user=request.user,
                employee_id=employee_id,
                device_info=device_info
            )

            if verification.status == 'VERIFIED':
                messages.success(
                    request,
                    f"Location verified! Within {verification.distance_meters:.1f}m of expected location."
                )
            elif verification.status == 'WARNING':
                messages.warning(
                    request,
                    f"Location verification warning: {verification.distance_meters:.1f}m away "
                    f"(geofence radius: {verification.geofence_radius_meters}m)"
                )
            elif verification.status == 'FAILED':
                messages.error(
                    request,
                    f"Location verification failed: {verification.distance_meters:.1f}m away "
                    f"(geofence radius: {verification.geofence_radius_meters}m)"
                )
        else:
            messages.info(request, "Verification created. Awaiting GPS location.")

        return redirect('gps_system:map_view', verification_id=verification.pk)

    # GET: Show verification form
    # Get available zones for quick selection
    zones = GeofenceDefinition.objects.filter(is_active=True).order_by('name')

    context = {
        'verification_types': LocationVerification.VERIFICATION_TYPES,
        'zones': zones,
    }

    return render(request, 'gps_system/verification_request.html', context)


@login_required
def verification_history(request):
    """
    View verification history.

    Shows all location verifications with filtering options.
    """
    verifications = LocationVerification.objects.select_related(
        'verified_by_user',
        'verified_by_employee'
    ).order_by('-created_at')

    # Filter by verification type
    verification_type = request.GET.get('type')
    if verification_type:
        verifications = verifications.filter(verification_type=verification_type)

    # Filter by status
    status = request.GET.get('status')
    if status:
        verifications = verifications.filter(status=status)

    # Filter by date range
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date:
        verifications = verifications.filter(verified_at__date__gte=start_date)
    if end_date:
        verifications = verifications.filter(verified_at__date__lte=end_date)

    # Filter by user
    user_id = request.GET.get('user_id')
    if user_id:
        verifications = verifications.filter(verified_by_user_id=user_id)

    # Search
    search = request.GET.get('search')
    if search:
        verifications = verifications.filter(
            Q(expected_address__icontains=search) |
            Q(actual_address__icontains=search) |
            Q(notes__icontains=search)
        )

    # Pagination (limit to 100 results)
    verifications = verifications[:100]

    context = {
        'verifications': verifications,
        'verification_types': LocationVerification.VERIFICATION_TYPES,
        'status_choices': LocationVerification.STATUS_CHOICES,
        'current_type': verification_type or '',
        'current_status': status or '',
        'search': search or '',
    }

    return render(request, 'gps_system/verification_history.html', context)


@login_required
def map_view(request, verification_id):
    """
    Show verification result on interactive map using Leaflet.js.

    Displays expected vs actual location with geofence circle/polygon.

    Args:
        verification_id: LocationVerification primary key
    """
    verification = get_object_or_404(
        LocationVerification.objects.select_related('verified_by_user', 'verified_by_employee'),
        pk=verification_id
    )

    # Prepare Leaflet.js map data
    map_data = {
        'expected': {
            'lat': float(verification.expected_latitude),
            'lon': float(verification.expected_longitude),
            'address': verification.expected_address,
        },
        'actual': None,
        'geofence_radius_meters': verification.geofence_radius_meters,
        'status': verification.status,
        'distance_meters': verification.distance_meters,
    }

    if verification.actual_latitude and verification.actual_longitude:
        map_data['actual'] = {
            'lat': float(verification.actual_latitude),
            'lon': float(verification.actual_longitude),
            'address': verification.actual_address,
            'accuracy_meters': verification.gps_accuracy_meters,
        }

    # Calculate map center and zoom level
    if map_data['actual']:
        # Center between expected and actual
        map_data['center_lat'] = (map_data['expected']['lat'] + map_data['actual']['lat']) / 2
        map_data['center_lon'] = (map_data['expected']['lon'] + map_data['actual']['lon']) / 2

        # Auto-zoom to fit both points plus geofence
        if verification.distance_meters:
            # Zoom based on distance
            if verification.distance_meters < 100:
                map_data['zoom'] = 17
            elif verification.distance_meters < 500:
                map_data['zoom'] = 15
            elif verification.distance_meters < 2000:
                map_data['zoom'] = 13
            else:
                map_data['zoom'] = 11
        else:
            map_data['zoom'] = 15
    else:
        # Only expected location
        map_data['center_lat'] = map_data['expected']['lat']
        map_data['center_lon'] = map_data['expected']['lon']
        map_data['zoom'] = 15

    # Status color for map markers
    status_colors = {
        'VERIFIED': '#28a745',  # Green
        'WARNING': '#ffc107',   # Yellow
        'FAILED': '#dc3545',    # Red
        'PENDING': '#6c757d',   # Gray
        'OVERRIDDEN': '#007bff', # Blue
    }
    map_data['status_color'] = status_colors.get(verification.status, '#6c757d')

    context = {
        'verification': verification,
        'map_data': json.dumps(map_data),
    }

    return render(request, 'gps_system/map_view.html', context)

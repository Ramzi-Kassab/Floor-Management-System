"""
Device Tracking Views

Template-rendering views for the Employee Device Tracking System.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count, Max
from decimal import Decimal, InvalidOperation

from floor_app.operations.device_tracking.models import (
    EmployeeDevice,
    EmployeeActivity,
    EmployeePresence,
    DeviceSession
)


@login_required
def dashboard(request):
    """
    Render dashboard with map data showing all devices and their locations.

    Displays:
    - Map with device locations
    - Active devices count
    - Recent activities
    - Current presence status
    """
    # Get all active devices with their latest location
    devices = EmployeeDevice.objects.filter(is_active=True).select_related(
        'employee', 'user'
    ).prefetch_related('activities')

    # Get latest activity with GPS coordinates for each device
    devices_with_location = []
    for device in devices:
        latest_activity = device.activities.filter(
            latitude__isnull=False,
            longitude__isnull=False
        ).first()

        if latest_activity:
            devices_with_location.append({
                'device': device,
                'latitude': float(latest_activity.latitude),
                'longitude': float(latest_activity.longitude),
                'last_seen': latest_activity.activity_at,
                'accuracy': latest_activity.gps_accuracy_meters,
            })

    # Get recent activities
    recent_activities = EmployeeActivity.objects.select_related(
        'employee', 'device'
    ).order_by('-activity_at')[:20]

    # Get today's presence records
    today = timezone.now().date()
    today_presence = EmployeePresence.objects.filter(
        date=today
    ).select_related('employee', 'clock_in_device', 'clock_out_device')

    # Statistics
    stats = {
        'total_devices': devices.count(),
        'online_devices': sum(1 for d in devices if d.is_online),
        'clocked_in': today_presence.filter(clock_in_time__isnull=False, clock_out_time__isnull=True).count(),
        'total_activities_today': EmployeeActivity.objects.filter(
            activity_at__date=today
        ).count(),
    }

    context = {
        'devices_with_location': devices_with_location,
        'recent_activities': recent_activities,
        'today_presence': today_presence,
        'stats': stats,
    }

    return render(request, 'device_tracking/dashboard.html', context)


@login_required
def device_list(request):
    """
    Render list of all devices.

    Displays all registered devices with filtering options.
    """
    devices = EmployeeDevice.objects.select_related(
        'employee', 'user', 'deactivated_by'
    ).prefetch_related('activities', 'sessions')

    # Filter by active status
    status_filter = request.GET.get('status')
    if status_filter == 'active':
        devices = devices.filter(is_active=True)
    elif status_filter == 'inactive':
        devices = devices.filter(is_active=False)

    # Filter by device type
    device_type = request.GET.get('device_type')
    if device_type:
        devices = devices.filter(device_type=device_type)

    # Filter by employee
    employee_id = request.GET.get('employee')
    if employee_id:
        devices = devices.filter(employee_id=employee_id)

    # Search by device name or ID
    search_query = request.GET.get('q')
    if search_query:
        devices = devices.filter(
            Q(device_name__icontains=search_query) |
            Q(device_id__icontains=search_query) |
            Q(employee__full_name__icontains=search_query)
        )

    # Annotate with activity counts
    devices = devices.annotate(
        activity_count=Count('activities'),
        last_activity=Max('activities__activity_at')
    ).order_by('-is_primary_device', '-last_seen_at')

    context = {
        'devices': devices,
        'device_types': EmployeeDevice.DEVICE_TYPES,
        'status_filter': status_filter,
        'device_type_filter': device_type,
        'search_query': search_query,
    }

    return render(request, 'device_tracking/device_list.html', context)


@login_required
def device_detail(request, pk):
    """
    Render detailed view of a specific device.

    Shows:
    - Device information
    - Activity history
    - Session history
    - Location history map
    """
    device = get_object_or_404(
        EmployeeDevice.objects.select_related(
            'employee', 'user', 'deactivated_by'
        ),
        pk=pk
    )

    # Get recent activities
    activities = device.activities.select_related('employee').order_by('-activity_at')[:50]

    # Get activities with GPS coordinates for map
    location_activities = device.activities.filter(
        latitude__isnull=False,
        longitude__isnull=False
    ).order_by('-activity_at')[:100]

    # Convert to list for map display
    locations = [
        {
            'latitude': float(activity.latitude),
            'longitude': float(activity.longitude),
            'timestamp': activity.activity_at.isoformat(),
            'activity_type': activity.get_activity_type_display(),
            'accuracy': activity.gps_accuracy_meters,
        }
        for activity in location_activities
    ]

    # Get sessions
    sessions = device.sessions.order_by('-started_at')[:20]

    # Get presence records
    presence_records = EmployeePresence.objects.filter(
        Q(clock_in_device=device) | Q(clock_out_device=device)
    ).select_related('employee', 'verified_by').order_by('-date')[:10]

    context = {
        'device': device,
        'activities': activities,
        'locations': locations,
        'sessions': sessions,
        'presence_records': presence_records,
    }

    return render(request, 'device_tracking/device_detail.html', context)


@login_required
def device_register(request):
    """
    Register a new device (GET/POST).

    Handles device registration with GPS coordinates.
    """
    if request.method == 'POST':
        # Extract form data
        device_id = request.POST.get('device_id', '').strip()
        device_name = request.POST.get('device_name', '').strip()
        device_type = request.POST.get('device_type')
        device_model = request.POST.get('device_model', '').strip()
        os_version = request.POST.get('os_version', '').strip()
        app_version = request.POST.get('app_version', '').strip()
        employee_id = request.POST.get('employee_id')

        # GPS coordinates
        latitude = request.POST.get('latitude', '').strip()
        longitude = request.POST.get('longitude', '').strip()

        # Validation
        errors = []

        if not device_id:
            errors.append('Device ID is required.')

        if not device_type or device_type not in dict(EmployeeDevice.DEVICE_TYPES):
            errors.append('Valid device type is required.')

        if not employee_id:
            errors.append('Employee is required.')

        # Check if device_id already exists
        if device_id and EmployeeDevice.objects.filter(device_id=device_id).exists():
            errors.append(f'Device with ID "{device_id}" is already registered.')

        # Validate GPS coordinates if provided
        lat_decimal = None
        lon_decimal = None
        if latitude and longitude:
            try:
                lat_decimal = Decimal(latitude)
                lon_decimal = Decimal(longitude)

                # Validate ranges
                if not (-90 <= lat_decimal <= 90):
                    errors.append('Latitude must be between -90 and 90.')
                if not (-180 <= lon_decimal <= 180):
                    errors.append('Longitude must be between -180 and 180.')
            except (InvalidOperation, ValueError):
                errors.append('Invalid GPS coordinates format.')

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            # Create device
            try:
                # Import here to avoid circular imports
                from floor_app.hr.models import HREmployee

                employee = get_object_or_404(HREmployee, pk=employee_id)

                device = EmployeeDevice.objects.create(
                    employee=employee,
                    user=employee.user if hasattr(employee, 'user') else None,
                    device_id=device_id,
                    device_name=device_name,
                    device_type=device_type,
                    device_model=device_model,
                    os_version=os_version,
                    app_version=app_version,
                    is_active=True,
                )

                # Log registration activity with GPS
                EmployeeActivity.objects.create(
                    employee=employee,
                    device=device,
                    activity_type='LOGIN',
                    activity_description=f'Device registered: {device_name or device_id}',
                    latitude=lat_decimal,
                    longitude=lon_decimal,
                )

                messages.success(request, f'Device "{device_name or device_id}" registered successfully!')
                return redirect('device_tracking:device_detail', pk=device.pk)

            except Exception as e:
                messages.error(request, f'Error registering device: {str(e)}')

    # GET request or form errors - show form
    # Get employees for dropdown
    from floor_app.hr.models import HREmployee
    employees = HREmployee.objects.filter(is_active=True).order_by('full_name')

    context = {
        'device_types': EmployeeDevice.DEVICE_TYPES,
        'employees': employees,
    }

    return render(request, 'device_tracking/device_register.html', context)


@login_required
def check_in(request):
    """
    Employee check-in/clock-in with GPS (GET/POST).

    Records employee presence with GPS coordinates.
    """
    if request.method == 'POST':
        device_id = request.POST.get('device_id', '').strip()
        action = request.POST.get('action')  # 'clock_in' or 'clock_out'
        latitude = request.POST.get('latitude', '').strip()
        longitude = request.POST.get('longitude', '').strip()

        errors = []

        if not device_id:
            errors.append('Device ID is required.')

        if action not in ['clock_in', 'clock_out']:
            errors.append('Invalid action.')

        # Validate GPS coordinates
        lat_decimal = None
        lon_decimal = None
        if latitude and longitude:
            try:
                lat_decimal = Decimal(latitude)
                lon_decimal = Decimal(longitude)

                if not (-90 <= lat_decimal <= 90):
                    errors.append('Latitude must be between -90 and 90.')
                if not (-180 <= lon_decimal <= 180):
                    errors.append('Longitude must be between -180 and 180.')
            except (InvalidOperation, ValueError):
                errors.append('Invalid GPS coordinates format.')
        else:
            errors.append('GPS coordinates are required for check-in.')

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            try:
                # Get device
                device = get_object_or_404(EmployeeDevice, device_id=device_id, is_active=True)
                employee = device.employee

                # Get or create today's presence record
                today = timezone.now().date()
                presence, created = EmployeePresence.objects.get_or_create(
                    employee=employee,
                    date=today
                )

                if action == 'clock_in':
                    if presence.is_clocked_in:
                        messages.warning(request, 'Already clocked in today.')
                    else:
                        presence.clock_in(
                            device=device,
                            latitude=lat_decimal,
                            longitude=lon_decimal
                        )

                        # Log activity
                        EmployeeActivity.objects.create(
                            employee=employee,
                            device=device,
                            activity_type='CLOCK_IN',
                            activity_description='Clocked in',
                            latitude=lat_decimal,
                            longitude=lon_decimal,
                        )

                        messages.success(request, f'Clocked in successfully at {presence.clock_in_time.strftime("%H:%M")}!')

                elif action == 'clock_out':
                    if not presence.clock_in_time:
                        messages.warning(request, 'Must clock in before clocking out.')
                    elif presence.clock_out_time:
                        messages.warning(request, 'Already clocked out today.')
                    else:
                        presence.clock_out(
                            device=device,
                            latitude=lat_decimal,
                            longitude=lon_decimal
                        )

                        # Log activity
                        EmployeeActivity.objects.create(
                            employee=employee,
                            device=device,
                            activity_type='CLOCK_OUT',
                            activity_description='Clocked out',
                            latitude=lat_decimal,
                            longitude=lon_decimal,
                        )

                        hours_worked = float(presence.total_hours) if presence.total_hours else 0
                        messages.success(request, f'Clocked out successfully! Total hours: {hours_worked:.2f}')

                # Update device last seen
                device.update_last_seen()

                return redirect('device_tracking:check_in')

            except Exception as e:
                messages.error(request, f'Error during check-in: {str(e)}')

    # GET request - show form and current status
    # Get user's devices if available
    user_devices = []
    if hasattr(request.user, 'devices'):
        user_devices = request.user.devices.filter(is_active=True)

    # Get today's presence for user's employee record if available
    today_presence = None
    if hasattr(request.user, 'hr_employee'):
        today = timezone.now().date()
        try:
            today_presence = EmployeePresence.objects.get(
                employee=request.user.hr_employee,
                date=today
            )
        except EmployeePresence.DoesNotExist:
            pass

    context = {
        'user_devices': user_devices,
        'today_presence': today_presence,
    }

    return render(request, 'device_tracking/check_in.html', context)


@login_required
def location_history(request, device_id):
    """
    Render location history for a specific device.

    Shows all GPS-tagged activities on a map with timeline.
    """
    device = get_object_or_404(
        EmployeeDevice.objects.select_related('employee', 'user'),
        pk=device_id
    )

    # Get activities with GPS coordinates
    activities = device.activities.filter(
        latitude__isnull=False,
        longitude__isnull=False
    ).order_by('-activity_at')

    # Filter by date range if provided
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if start_date:
        try:
            activities = activities.filter(activity_at__date__gte=start_date)
        except ValueError:
            messages.warning(request, 'Invalid start date format.')

    if end_date:
        try:
            activities = activities.filter(activity_at__date__lte=end_date)
        except ValueError:
            messages.warning(request, 'Invalid end date format.')

    # Filter by activity type
    activity_type = request.GET.get('activity_type')
    if activity_type:
        activities = activities.filter(activity_type=activity_type)

    # Limit to recent records (configurable)
    limit = request.GET.get('limit', '100')
    try:
        limit = int(limit)
        if limit > 1000:
            limit = 1000  # Max limit
    except ValueError:
        limit = 100

    activities = activities[:limit]

    # Convert to list for map display
    locations = [
        {
            'id': activity.id,
            'latitude': float(activity.latitude),
            'longitude': float(activity.longitude),
            'timestamp': activity.activity_at.isoformat(),
            'activity_type': activity.activity_type,
            'activity_type_display': activity.get_activity_type_display(),
            'description': activity.activity_description,
            'accuracy': activity.gps_accuracy_meters,
        }
        for activity in activities
    ]

    context = {
        'device': device,
        'activities': activities,
        'locations': locations,
        'activity_types': EmployeeActivity.ACTIVITY_TYPES,
        'start_date': start_date,
        'end_date': end_date,
        'activity_type_filter': activity_type,
        'limit': limit,
    }

    return render(request, 'device_tracking/location_history.html', context)

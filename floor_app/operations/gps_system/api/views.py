"""
GPS Verification System API Views

REST API viewsets for GPS verification system.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q

from floor_app.operations.gps_system.models import (
    LocationVerification,
    Geofence,
    GPSLog
)
from floor_app.operations.gps_system.services import GPSVerificationService
from .serializers import (
    LocationVerificationSerializer,
    LocationVerificationCreateSerializer,
    LocationVerifySerializer,
    GeofenceSerializer,
    GeofenceCreateSerializer,
    GeofenceCheckSerializer,
    GPSLogSerializer,
    GPSLogCreateSerializer,
    DistanceCalculationSerializer,
    ReverseGeocodeSerializer
)


class LocationVerificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing location verifications.

    list: Get all location verifications
    retrieve: Get a specific verification
    create: Create a new location verification
    update: Update a verification
    """

    queryset = LocationVerification.objects.all().select_related('verified_by')
    serializer_class = LocationVerificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['verification_type', 'is_within_geofence']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Use different serializer for create action."""
        if self.action == 'create':
            return LocationVerificationCreateSerializer
        return LocationVerificationSerializer

    def create(self, request, *args, **kwargs):
        """
        Create a new location verification.

        POST /api/gps/location-verifications/
        Body: {
            "verification_type": "DELIVERY",
            "expected_latitude": 24.1234,
            "expected_longitude": 55.5678,
            "expected_address": "Dubai Industrial Park",
            "geofence_radius_meters": 100,
            "actual_latitude": 24.1240,
            "actual_longitude": 55.5680
        }
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        # Create verification
        verification = LocationVerification.objects.create(
            verification_type=data['verification_type'],
            expected_latitude=data['expected_latitude'],
            expected_longitude=data['expected_longitude'],
            expected_address=data.get('expected_address', ''),
            geofence_radius_meters=data.get('geofence_radius_meters', 100),
            metadata=data.get('metadata', {})
        )

        # If actual location provided, verify it
        if data.get('actual_latitude') and data.get('actual_longitude'):
            verification.verify_location(
                actual_lat=data['actual_latitude'],
                actual_lon=data['actual_longitude'],
                user=request.user,
                override_reason=data.get('override_reason')
            )

        output_serializer = LocationVerificationSerializer(verification)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """
        Verify a location against expected coordinates.

        POST /api/gps/location-verifications/{id}/verify/
        Body: {
            "latitude": 24.1240,
            "longitude": 55.5680
        }
        """
        verification = self.get_object()
        serializer = LocationVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        # Verify location
        verification.verify_location(
            actual_lat=data['latitude'],
            actual_lon=data['longitude'],
            user=request.user
        )

        output_serializer = self.get_serializer(verification)
        return Response(output_serializer.data)

    @action(detail=True, methods=['post'])
    def override(self, request, pk=None):
        """
        Override a failed verification.

        POST /api/gps/location-verifications/{id}/override/
        Body: {
            "reason": "Site entrance relocated to north gate"
        }
        """
        verification = self.get_object()

        if not request.user.is_staff:
            return Response(
                {'error': 'Only staff can override verifications'},
                status=status.HTTP_403_FORBIDDEN
            )

        reason = request.data.get('reason', '')
        if not reason:
            return Response(
                {'error': 'Override reason is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        verification.override_reason = reason
        verification.is_within_geofence = True
        verification.save(update_fields=['override_reason', 'is_within_geofence'])

        output_serializer = self.get_serializer(verification)
        return Response(output_serializer.data)

    @action(detail=False, methods=['get'])
    def failed(self, request):
        """
        Get failed verifications (outside geofence).

        GET /api/gps/location-verifications/failed/
        """
        queryset = self.get_queryset().filter(
            is_within_geofence=False,
            override_reason=''
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class GeofenceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing geofences.

    list: Get all geofences
    retrieve: Get a specific geofence
    create: Create a new geofence
    update: Update a geofence
    destroy: Deactivate a geofence
    """

    queryset = Geofence.objects.filter(is_active=True).select_related('created_by')
    serializer_class = GeofenceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['geofence_type', 'is_active']
    search_fields = ['name', 'description']
    ordering = ['name']

    def get_serializer_class(self):
        """Use different serializer for create action."""
        if self.action == 'create':
            return GeofenceCreateSerializer
        return GeofenceSerializer

    def create(self, request, *args, **kwargs):
        """
        Create a new geofence.

        Circular geofence:
        POST /api/gps/geofences/
        Body: {
            "name": "Main Warehouse",
            "geofence_type": "WAREHOUSE",
            "center_latitude": 24.1234,
            "center_longitude": 55.5678,
            "radius_meters": 500
        }

        Polygon geofence:
        POST /api/gps/geofences/
        Body: {
            "name": "Industrial Zone",
            "geofence_type": "FACTORY",
            "polygon_points": [
                {"lat": 24.1234, "lon": 55.5678},
                {"lat": 24.1240, "lon": 55.5680},
                {"lat": 24.1238, "lon": 55.5690},
                {"lat": 24.1232, "lon": 55.5688}
            ]
        }
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        # Create geofence
        geofence = Geofence.objects.create(
            name=data['name'],
            description=data.get('description', ''),
            geofence_type=data['geofence_type'],
            center_latitude=data.get('center_latitude'),
            center_longitude=data.get('center_longitude'),
            radius_meters=data.get('radius_meters'),
            polygon_points=data.get('polygon_points'),
            is_active=data.get('is_active', True),
            created_by=request.user,
            metadata=data.get('metadata', {})
        )

        output_serializer = GeofenceSerializer(geofence)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def check(self, request, pk=None):
        """
        Check if a point is within this geofence.

        POST /api/gps/geofences/{id}/check/
        Body: {
            "latitude": 24.1236,
            "longitude": 55.5682
        }
        """
        geofence = self.get_object()
        serializer = GeofenceCheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        # Check if point is within geofence
        is_within = geofence.is_point_within(
            latitude=float(data['latitude']),
            longitude=float(data['longitude'])
        )

        # Calculate distance to center for circular geofences
        distance = None
        if geofence.center_latitude and geofence.center_longitude:
            distance = GPSVerificationService.calculate_distance(
                float(geofence.center_latitude),
                float(geofence.center_longitude),
                float(data['latitude']),
                float(data['longitude'])
            )

        return Response({
            'is_within': is_within,
            'distance_from_center_meters': round(distance, 2) if distance else None,
            'geofence_name': geofence.name,
            'geofence_type': geofence.geofence_type
        })

    @action(detail=False, methods=['post'])
    def find_containing(self, request):
        """
        Find all geofences that contain a given point.

        POST /api/gps/geofences/find_containing/
        Body: {
            "latitude": 24.1236,
            "longitude": 55.5682
        }
        """
        serializer = GeofenceCheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        lat = float(data['latitude'])
        lon = float(data['longitude'])

        # Find all geofences containing this point
        containing_geofences = []

        for geofence in self.get_queryset():
            if geofence.is_point_within(lat, lon):
                containing_geofences.append(geofence)

        serializer = self.get_serializer(containing_geofences, many=True)
        return Response({
            'count': len(containing_geofences),
            'geofences': serializer.data
        })


class GPSLogViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing GPS logs.

    list: Get all GPS logs
    retrieve: Get a specific log
    create: Create a new GPS log
    """

    queryset = GPSLog.objects.all().select_related('employee')
    serializer_class = GPSLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['log_type', 'employee']
    ordering = ['-timestamp']

    def get_queryset(self):
        """Users see their own logs, admins see all."""
        user = self.request.user

        if user.is_staff:
            return GPSLog.objects.all()

        try:
            employee = user.hremployee
            return GPSLog.objects.filter(employee=employee).select_related('employee')
        except Exception:
            return GPSLog.objects.none()

    def get_serializer_class(self):
        """Use different serializer for create action."""
        if self.action == 'create':
            return GPSLogCreateSerializer
        return GPSLogSerializer

    def create(self, request, *args, **kwargs):
        """
        Create a new GPS log.

        POST /api/gps/logs/
        Body: {
            "log_type": "TRACKING",
            "latitude": 24.1236,
            "longitude": 55.5682,
            "accuracy_meters": 5.2,
            "altitude_meters": 10.5,
            "speed_mps": 0.0,
            "bearing_degrees": 180.0
        }
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        # Get employee
        try:
            employee = request.user.hremployee
        except Exception:
            return Response(
                {'error': 'User does not have an associated employee record'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create GPS log
        gps_log = GPSLog.objects.create(
            employee=employee,
            log_type=data['log_type'],
            latitude=data['latitude'],
            longitude=data['longitude'],
            accuracy_meters=data.get('accuracy_meters'),
            altitude_meters=data.get('altitude_meters'),
            speed_mps=data.get('speed_mps'),
            bearing_degrees=data.get('bearing_degrees'),
            metadata=data.get('metadata', {})
        )

        # Reverse geocode (async in production)
        try:
            address = GPSVerificationService.reverse_geocode(
                float(data['latitude']),
                float(data['longitude'])
            )
            gps_log.address = address
            gps_log.save(update_fields=['address'])
        except Exception:
            pass

        output_serializer = GPSLogSerializer(gps_log)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def track(self, request):
        """
        Get tracking logs for a time period.

        GET /api/gps/logs/track/?hours=24
        """
        from datetime import timedelta

        hours = int(request.query_params.get('hours', 24))
        since = timezone.now() - timedelta(hours=hours)

        queryset = self.get_queryset().filter(
            log_type='TRACKING',
            timestamp__gte=since
        )

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'count': queryset.count(),
            'hours': hours,
            'logs': serializer.data
        })


class GPSUtilsViewSet(viewsets.ViewSet):
    """
    ViewSet for GPS utility functions (calculations, geocoding).
    """

    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['post'])
    def calculate_distance(self, request):
        """
        Calculate distance between two GPS coordinates.

        POST /api/gps/utils/calculate_distance/
        Body: {
            "lat1": 24.1234,
            "lon1": 55.5678,
            "lat2": 24.1240,
            "lon2": 55.5680
        }
        """
        serializer = DistanceCalculationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        distance = GPSVerificationService.calculate_distance(
            float(data['lat1']),
            float(data['lon1']),
            float(data['lat2']),
            float(data['lon2'])
        )

        bearing = GPSVerificationService.calculate_bearing(
            float(data['lat1']),
            float(data['lon1']),
            float(data['lat2']),
            float(data['lon2'])
        )

        direction = GPSVerificationService.get_direction_name(bearing)

        return Response({
            'distance_meters': round(distance, 2),
            'distance_kilometers': round(distance / 1000, 2),
            'bearing_degrees': round(bearing, 2),
            'direction': direction
        })

    @action(detail=False, methods=['post'])
    def reverse_geocode(self, request):
        """
        Convert GPS coordinates to address.

        POST /api/gps/utils/reverse_geocode/
        Body: {
            "latitude": 24.1234,
            "longitude": 55.5678
        }
        """
        serializer = ReverseGeocodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        try:
            address = GPSVerificationService.reverse_geocode(
                float(data['latitude']),
                float(data['longitude'])
            )

            return Response({
                'latitude': float(data['latitude']),
                'longitude': float(data['longitude']),
                'address': address
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def forward_geocode(self, request):
        """
        Convert address to GPS coordinates.

        POST /api/gps/utils/forward_geocode/
        Body: {
            "address": "Sheikh Zayed Road, Dubai, UAE"
        }
        """
        address = request.data.get('address', '')
        if not address:
            return Response(
                {'error': 'Address is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            coords = GPSVerificationService.forward_geocode(address)

            if coords:
                return Response({
                    'address': address,
                    'latitude': coords[0],
                    'longitude': coords[1]
                })
            else:
                return Response(
                    {'error': 'Address not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

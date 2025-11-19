"""HR Assets API Views"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model

from floor_app.operations.hr_assets.models import (
    Vehicle, ParkingZone, ParkingSpot, SIMCard, Phone, Camera
)
from floor_app.operations.hr_assets.services import AssetService
from .serializers import *

User = get_user_model()


class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        serializer = VehicleAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        assigned_to = User.objects.get(id=serializer.validated_data['assigned_to_id'])
        assignment = AssetService.assign_vehicle(
            int(pk), assigned_to, request.user, **{k: v for k, v in serializer.validated_data.items() if k != 'assigned_to_id'}
        )
        return Response(VehicleAssignmentSerializer(assignment).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def return_vehicle(self, request, pk=None):
        serializer = VehicleReturnSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vehicle = AssetService.return_vehicle(int(pk), **serializer.validated_data)
        return Response(VehicleSerializer(vehicle).data)

    @action(detail=False, methods=['get'])
    def available(self, request):
        vehicles = AssetService.get_available_vehicles()
        return Response(VehicleSerializer(vehicles, many=True).data)


class ParkingZoneViewSet(viewsets.ModelViewSet):
    queryset = ParkingZone.objects.filter(is_active=True)
    serializer_class = ParkingZoneSerializer
    permission_classes = [IsAuthenticated]


class ParkingSpotViewSet(viewsets.ModelViewSet):
    queryset = ParkingSpot.objects.select_related('zone')
    serializer_class = ParkingSpotSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        serializer = ParkingAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        assigned_to = User.objects.get(id=serializer.validated_data['assigned_to_id'])
        vehicle = Vehicle.objects.get(id=serializer.validated_data['vehicle_id']) if serializer.validated_data.get('vehicle_id') else None
        assignment = AssetService.assign_parking(
            int(pk), assigned_to, request.user,
            serializer.validated_data['start_date'],
            serializer.validated_data.get('end_date'),
            vehicle
        )
        return Response(ParkingAssignmentSerializer(assignment).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def release(self, request, pk=None):
        spot = AssetService.release_parking(int(pk))
        return Response(ParkingSpotSerializer(spot).data)

    @action(detail=False, methods=['get'])
    def available(self, request):
        zone_id = request.query_params.get('zone_id')
        spot_type = request.query_params.get('spot_type')
        spots = AssetService.get_available_parking(int(zone_id) if zone_id else None, spot_type)
        return Response(ParkingSpotSerializer(spots, many=True).data)


class SIMCardViewSet(viewsets.ModelViewSet):
    queryset = SIMCard.objects.all()
    serializer_class = SIMCardSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        serializer = SIMAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        assigned_to = User.objects.get(id=serializer.validated_data['assigned_to_id'])
        assignment = AssetService.assign_sim(
            int(pk), assigned_to, request.user, **{k: v for k, v in serializer.validated_data.items() if k != 'assigned_to_id'}
        )
        return Response(SIMAssignmentSerializer(assignment).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def return_sim(self, request, pk=None):
        sim = AssetService.return_sim(int(pk))
        return Response(SIMCardSerializer(sim).data)


class PhoneViewSet(viewsets.ModelViewSet):
    queryset = Phone.objects.all()
    serializer_class = PhoneSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        serializer = PhoneAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        assigned_to = User.objects.get(id=serializer.validated_data['assigned_to_id'])
        assignment = AssetService.assign_phone(
            int(pk), assigned_to, request.user, **{k: v for k, v in serializer.validated_data.items() if k != 'assigned_to_id'}
        )
        return Response(PhoneAssignmentSerializer(assignment).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def return_phone(self, request, pk=None):
        serializer = PhoneReturnSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = AssetService.return_phone(int(pk), **serializer.validated_data)
        return Response(PhoneSerializer(phone).data)


class CameraViewSet(viewsets.ModelViewSet):
    queryset = Camera.objects.all()
    serializer_class = CameraSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        serializer = CameraAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        assigned_to = User.objects.get(id=serializer.validated_data['assigned_to_id'])
        assignment = AssetService.assign_camera(
            int(pk), assigned_to, request.user, **{k: v for k, v in serializer.validated_data.items() if k != 'assigned_to_id'}
        )
        return Response(CameraAssignmentSerializer(assignment).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def return_camera(self, request, pk=None):
        serializer = CameraReturnSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        camera = AssetService.return_camera(int(pk), **serializer.validated_data)
        return Response(CameraSerializer(camera).data)


class AssetOverviewViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def my_assets(self, request):
        assets = AssetService.get_user_assets(request.user)
        return Response({
            'vehicles': VehicleSerializer(assets['vehicles'], many=True).data,
            'parking_spots': ParkingSpotSerializer(assets['parking_spots'], many=True).data,
            'sim_cards': SIMCardSerializer(assets['sim_cards'], many=True).data,
            'phones': PhoneSerializer(assets['phones'], many=True).data,
            'cameras': CameraSerializer(assets['cameras'], many=True).data,
        })

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        stats = AssetService.get_asset_statistics()
        return Response(stats)

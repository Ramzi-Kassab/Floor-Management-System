"""HR Assets API Serializers"""

from rest_framework import serializers
from floor_app.operations.hr_assets.models import (
    Vehicle, VehicleAssignment, ParkingZone, ParkingSpot, ParkingAssignment,
    SIMCard, SIMAssignment, Phone, PhoneAssignment, Camera, CameraAssignment
)


# Vehicle Serializers
class VehicleSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    class Meta:
        model = Vehicle
        fields = '__all__'

class VehicleAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleAssignment
        fields = '__all__'

class VehicleAssignSerializer(serializers.Serializer):
    assigned_to_id = serializers.IntegerField()
    start_date = serializers.DateField()
    end_date = serializers.DateField(required=False, allow_null=True)
    purpose = serializers.CharField(required=False, allow_blank=True)
    start_odometer = serializers.IntegerField(required=False, allow_null=True)

class VehicleReturnSerializer(serializers.Serializer):
    end_odometer = serializers.IntegerField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True)


# Parking Serializers
class ParkingZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParkingZone
        fields = '__all__'

class ParkingSpotSerializer(serializers.ModelSerializer):
    zone_name = serializers.CharField(source='zone.name', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    class Meta:
        model = ParkingSpot
        fields = '__all__'

class ParkingAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParkingAssignment
        fields = '__all__'

class ParkingAssignSerializer(serializers.Serializer):
    assigned_to_id = serializers.IntegerField()
    start_date = serializers.DateField()
    end_date = serializers.DateField(required=False, allow_null=True)
    vehicle_id = serializers.IntegerField(required=False, allow_null=True)


# SIM Card Serializers
class SIMCardSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    class Meta:
        model = SIMCard
        fields = '__all__'

class SIMAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SIMAssignment
        fields = '__all__'

class SIMAssignSerializer(serializers.Serializer):
    assigned_to_id = serializers.IntegerField()
    start_date = serializers.DateField()
    end_date = serializers.DateField(required=False, allow_null=True)
    purpose = serializers.CharField(required=False, allow_blank=True)


# Phone Serializers
class PhoneSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    class Meta:
        model = Phone
        fields = '__all__'

class PhoneAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhoneAssignment
        fields = '__all__'

class PhoneAssignSerializer(serializers.Serializer):
    assigned_to_id = serializers.IntegerField()
    start_date = serializers.DateField()
    end_date = serializers.DateField(required=False, allow_null=True)
    purpose = serializers.CharField(required=False, allow_blank=True)
    condition = serializers.CharField(default='GOOD')

class PhoneReturnSerializer(serializers.Serializer):
    condition = serializers.CharField(default='GOOD')
    notes = serializers.CharField(required=False, allow_blank=True)


# Camera Serializers
class CameraSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    class Meta:
        model = Camera
        fields = '__all__'

class CameraAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CameraAssignment
        fields = '__all__'

class CameraAssignSerializer(serializers.Serializer):
    assigned_to_id = serializers.IntegerField()
    start_date = serializers.DateField()
    end_date = serializers.DateField(required=False, allow_null=True)
    purpose = serializers.CharField(required=False, allow_blank=True)
    project = serializers.CharField(required=False, allow_blank=True)
    condition = serializers.CharField(default='GOOD')
    accessories = serializers.ListField(child=serializers.CharField(), required=False, default=list)

class CameraReturnSerializer(serializers.Serializer):
    condition = serializers.CharField(default='GOOD')
    accessories_returned = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    notes = serializers.CharField(required=False, allow_blank=True)

"""Journey Management API Serializers"""

from rest_framework import serializers
from floor_app.operations.journey_management.models import (
    JourneyPlan, JourneyWaypoint, JourneyCheckIn, JourneyDocument, JourneyStatusHistory
)


class JourneyWaypointSerializer(serializers.ModelSerializer):
    class Meta:
        model = JourneyWaypoint
        fields = ['id', 'journey', 'sequence', 'location_name', 'address', 'gps_coordinates',
                  'planned_arrival_time', 'planned_departure_time', 'actual_arrival_time',
                  'actual_departure_time', 'purpose', 'contact_person', 'contact_phone',
                  'notes', 'completed']
        read_only_fields = ['journey']


class JourneyCheckInSerializer(serializers.ModelSerializer):
    class Meta:
        model = JourneyCheckIn
        fields = ['id', 'journey', 'waypoint', 'check_type', 'check_time', 'location_name',
                  'gps_coordinates', 'notes', 'vehicle_odometer', 'fuel_level', 'all_safe',
                  'issues_reported', 'photo']
        read_only_fields = ['journey', 'check_time']


class JourneyDocumentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)

    class Meta:
        model = JourneyDocument
        fields = ['id', 'journey', 'document_type', 'title', 'file', 'uploaded_by',
                  'uploaded_by_name', 'uploaded_date', 'notes']
        read_only_fields = ['journey', 'uploaded_by', 'uploaded_date']


class JourneyPlanSerializer(serializers.ModelSerializer):
    traveler_name = serializers.CharField(source='traveler.get_full_name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    waypoints = JourneyWaypointSerializer(many=True, read_only=True)
    check_ins = JourneyCheckInSerializer(many=True, read_only=True)

    class Meta:
        model = JourneyPlan
        fields = ['id', 'journey_number', 'title', 'description', 'traveler', 'traveler_name',
                  'companions', 'departure_location', 'destination', 'planned_departure_time',
                  'planned_return_time', 'actual_departure_time', 'actual_return_time',
                  'route_description', 'estimated_distance_km', 'vehicle_type', 'vehicle_number',
                  'vehicle_details', 'risk_level', 'risk_assessment', 'hazards_identified',
                  'mitigation_measures', 'emergency_contact_name', 'emergency_contact_phone',
                  'emergency_contact_relationship', 'medical_conditions', 'status',
                  'submitted_date', 'approved_by', 'approved_by_name', 'approval_date',
                  'approval_comments', 'completion_notes', 'incidents_reported',
                  'incident_details', 'purpose_category', 'estimated_cost', 'actual_cost',
                  'tags', 'custom_fields', 'is_overdue', 'waypoints', 'check_ins']
        read_only_fields = ['journey_number', 'traveler', 'is_overdue']


class JourneyCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, allow_blank=True)
    departure_location = serializers.CharField(max_length=200)
    destination = serializers.CharField(max_length=200)
    planned_departure_time = serializers.DateTimeField()
    planned_return_time = serializers.DateTimeField()
    route_description = serializers.CharField(required=False, allow_blank=True)
    estimated_distance_km = serializers.DecimalField(max_digits=8, decimal_places=2, required=False, allow_null=True)
    vehicle_type = serializers.CharField(max_length=50)
    vehicle_number = serializers.CharField(max_length=50, required=False, allow_blank=True)
    vehicle_details = serializers.JSONField(required=False, default=dict)
    risk_level = serializers.ChoiceField(choices=JourneyPlan.RISK_LEVEL_CHOICES, default='LOW')
    risk_assessment = serializers.CharField(required=False, allow_blank=True)
    hazards_identified = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    mitigation_measures = serializers.CharField(required=False, allow_blank=True)
    emergency_contact_name = serializers.CharField(max_length=100)
    emergency_contact_phone = serializers.CharField(max_length=20)
    emergency_contact_relationship = serializers.CharField(max_length=50, required=False, allow_blank=True)
    medical_conditions = serializers.CharField(required=False, allow_blank=True)
    purpose_category = serializers.CharField(max_length=50, default='OTHER')
    estimated_cost = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    companion_ids = serializers.ListField(child=serializers.IntegerField(), required=False, default=list)
    tags = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    custom_fields = serializers.JSONField(required=False, default=dict)


class JourneyApproveSerializer(serializers.Serializer):
    comments = serializers.CharField(required=False, allow_blank=True)


class JourneyRejectSerializer(serializers.Serializer):
    reason = serializers.CharField()


class JourneyCompleteSerializer(serializers.Serializer):
    completion_notes = serializers.CharField(required=False, allow_blank=True)
    incidents_reported = serializers.BooleanField(default=False)
    incident_details = serializers.CharField(required=False, allow_blank=True)
    actual_cost = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)


class JourneyCancelSerializer(serializers.Serializer):
    reason = serializers.CharField()


class WaypointCreateSerializer(serializers.Serializer):
    location_name = serializers.CharField(max_length=200)
    address = serializers.CharField(required=False, allow_blank=True)
    gps_coordinates = serializers.CharField(max_length=100, required=False, allow_blank=True)
    planned_arrival_time = serializers.DateTimeField(required=False, allow_null=True)
    planned_departure_time = serializers.DateTimeField(required=False, allow_null=True)
    purpose = serializers.CharField(required=False, allow_blank=True)
    contact_person = serializers.CharField(max_length=100, required=False, allow_blank=True)
    contact_phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)


class CheckInCreateSerializer(serializers.Serializer):
    check_type = serializers.ChoiceField(choices=JourneyCheckIn.CHECK_TYPE_CHOICES)
    location_name = serializers.CharField(max_length=200)
    waypoint_id = serializers.IntegerField(required=False, allow_null=True)
    gps_coordinates = serializers.CharField(max_length=100, required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    vehicle_odometer = serializers.IntegerField(required=False, allow_null=True)
    fuel_level = serializers.CharField(max_length=20, required=False, allow_blank=True)
    all_safe = serializers.BooleanField(default=True)
    issues_reported = serializers.CharField(required=False, allow_blank=True)
    photo = serializers.ImageField(required=False, allow_null=True)

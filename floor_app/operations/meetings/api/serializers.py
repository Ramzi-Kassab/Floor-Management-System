"""Meeting API Serializers"""

from rest_framework import serializers
from floor_app.operations.meetings.models import (
    MeetingRoom, RoomBooking, MorningMeetingGroup, MorningMeeting,
    MorningMeetingAttendance, MeetingActionItem
)

# Room Booking Serializers
class MeetingRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeetingRoom
        fields = '__all__'

class RoomBookingSerializer(serializers.ModelSerializer):
    room_name = serializers.CharField(source='room.name', read_only=True)
    booked_by_name = serializers.CharField(source='booked_by.get_full_name', read_only=True)
    is_conflicting = serializers.BooleanField(read_only=True)
    class Meta:
        model = RoomBooking
        fields = '__all__'

class RoomBookingCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, allow_blank=True)
    meeting_type = serializers.CharField(max_length=50, default='INTERNAL')
    start_time = serializers.DateTimeField()
    end_time = serializers.DateTimeField()
    expected_attendees = serializers.IntegerField(min_value=1)
    organizer_id = serializers.IntegerField(required=False)
    participant_ids = serializers.ListField(child=serializers.IntegerField(), required=False, default=list)
    external_participants = serializers.CharField(required=False, allow_blank=True)
    setup_requirements = serializers.CharField(required=False, allow_blank=True)
    catering_required = serializers.BooleanField(default=False)
    catering_details = serializers.CharField(required=False, allow_blank=True)
    it_support_required = serializers.BooleanField(default=False)
    it_support_details = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)

class RoomAvailabilitySerializer(serializers.Serializer):
    start_time = serializers.DateTimeField()
    end_time = serializers.DateTimeField()
    capacity = serializers.IntegerField(required=False, allow_null=True)

# Morning Meeting Serializers
class MorningMeetingGroupSerializer(serializers.ModelSerializer):
    coordinator_name = serializers.CharField(source='coordinator.get_full_name', read_only=True)
    member_count = serializers.SerializerMethodField()
    class Meta:
        model = MorningMeetingGroup
        fields = '__all__'
    def get_member_count(self, obj):
        return obj.members.count()

class MorningMeetingAttendanceSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    class Meta:
        model = MorningMeetingAttendance
        fields = '__all__'

class MorningMeetingSerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(source='group.name', read_only=True)
    led_by_name = serializers.CharField(source='led_by.get_full_name', read_only=True)
    attendance = MorningMeetingAttendanceSerializer(many=True, read_only=True)
    class Meta:
        model = MorningMeeting
        fields = '__all__'

class MorningMeetingCreateSerializer(serializers.Serializer):
    meeting_date = serializers.DateField()
    led_by_id = serializers.IntegerField(required=False, allow_null=True)
    agenda_items = serializers.ListField(child=serializers.CharField(), required=False, default=list)

class MorningMeetingCompleteSerializer(serializers.Serializer):
    meeting_notes = serializers.CharField(required=False, allow_blank=True)
    key_points = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    action_items = serializers.ListField(required=False, default=list)
    safety_moments = serializers.CharField(required=False, allow_blank=True)

class AttendanceRecordSerializer(serializers.Serializer):
    employee_id = serializers.IntegerField()
    status = serializers.ChoiceField(choices=MorningMeetingAttendance.STATUS_CHOICES)
    check_in_time = serializers.TimeField(required=False, allow_null=True)
    minutes_late = serializers.IntegerField(required=False, allow_null=True)
    absence_reason = serializers.CharField(required=False, allow_blank=True)

# Action Items
class MeetingActionItemSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    class Meta:
        model = MeetingActionItem
        fields = '__all__'

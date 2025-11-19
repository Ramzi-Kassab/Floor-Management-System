"""Meeting API Views"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model

from floor_app.operations.meetings.models import MeetingRoom, RoomBooking, MorningMeetingGroup, MorningMeeting
from floor_app.operations.meetings.services import MeetingService
from .serializers import *

User = get_user_model()


class MeetingRoomViewSet(viewsets.ModelViewSet):
    queryset = MeetingRoom.objects.filter(is_active=True)
    serializer_class = MeetingRoomSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def check_availability(self, request):
        serializer = RoomAvailabilitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        rooms = MeetingService.get_available_rooms(**serializer.validated_data)
        return Response(MeetingRoomSerializer(rooms, many=True).data)


class RoomBookingViewSet(viewsets.ModelViewSet):
    serializer_class = RoomBookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = RoomBooking.objects.select_related('room', 'booked_by')
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if self.request.query_params.get('mine') == 'true':
            queryset = queryset.filter(booked_by=self.request.user)
        return queryset

    @action(detail=False, methods=['post'], url_path='create-booking/(?P<room_id>[^/.]+)')
    def create_booking(self, request, room_id=None):
        serializer = RoomBookingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        booking = MeetingService.create_booking(int(room_id), request.user, serializer.validated_data)
        return Response(RoomBookingSerializer(booking).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        booking = MeetingService.approve_booking(int(pk), request.user)
        return Response(RoomBookingSerializer(booking).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        reason = request.data.get('reason', '')
        booking = MeetingService.reject_booking(int(pk), request.user, reason)
        return Response(RoomBookingSerializer(booking).data)

    @action(detail=True, methods=['post'])
    def check_in(self, request, pk=None):
        booking = MeetingService.check_in_booking(int(pk))
        return Response(RoomBookingSerializer(booking).data)

    @action(detail=True, methods=['post'])
    def check_out(self, request, pk=None):
        booking = MeetingService.check_out_booking(
            int(pk),
            request.data.get('actual_attendees'),
            request.data.get('feedback', ''),
            request.data.get('rating')
        )
        return Response(RoomBookingSerializer(booking).data)

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        days = int(request.query_params.get('days', 7))
        bookings = MeetingService.get_upcoming_bookings(request.user, days)
        return Response(RoomBookingSerializer(bookings, many=True).data)


class MorningMeetingGroupViewSet(viewsets.ModelViewSet):
    queryset = MorningMeetingGroup.objects.filter(is_active=True)
    serializer_class = MorningMeetingGroupSerializer
    permission_classes = [IsAuthenticated]


class MorningMeetingViewSet(viewsets.ModelViewSet):
    serializer_class = MorningMeetingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return MorningMeeting.objects.select_related('group', 'led_by').prefetch_related('attendance')

    @action(detail=False, methods=['post'], url_path='create-meeting/(?P<group_id>[^/.]+)')
    def create_meeting(self, request, group_id=None):
        serializer = MorningMeetingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        led_by = User.objects.get(id=serializer.validated_data['led_by_id']) if serializer.validated_data.get('led_by_id') else None
        meeting = MeetingService.create_morning_meeting(
            int(group_id),
            serializer.validated_data['meeting_date'],
            led_by,
            serializer.validated_data.get('agenda_items')
        )
        return Response(MorningMeetingSerializer(meeting).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        meeting = MeetingService.start_morning_meeting(int(pk))
        return Response(MorningMeetingSerializer(meeting).data)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        serializer = MorningMeetingCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        meeting = MeetingService.complete_morning_meeting(int(pk), **serializer.validated_data)
        return Response(MorningMeetingSerializer(meeting).data)

    @action(detail=True, methods=['post'])
    def record_attendance(self, request, pk=None):
        serializer = AttendanceRecordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        attendance = MeetingService.record_attendance(int(pk), **serializer.validated_data)
        return Response(MorningMeetingAttendanceSerializer(attendance).data)

    @action(detail=False, methods=['get'])
    def today(self, request):
        meetings = MeetingService.get_todays_morning_meetings(request.user)
        return Response(MorningMeetingSerializer(meetings, many=True).data)

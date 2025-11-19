"""Meeting Service - Business logic for meeting management"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, date, time
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Q, Count
from django.db import transaction
from floor_app.operations.meetings.models import (
    MeetingRoom, RoomBooking, MorningMeetingGroup, MorningMeeting,
    MorningMeetingAttendance, MeetingActionItem
)

User = get_user_model()


class MeetingService:
    """Service for managing meetings."""

    # ============================================================================
    # Room Booking
    # ============================================================================

    @classmethod
    def generate_booking_number(cls) -> str:
        """Generate unique booking number. Format: BK-YYYY-NNNN"""
        year = timezone.now().year
        prefix = f"BK-{year}-"

        last_booking = RoomBooking.objects.filter(
            booking_number__startswith=prefix
        ).order_by('-booking_number').first()

        if last_booking:
            last_number = int(last_booking.booking_number.split('-')[-1])
            new_number = last_number + 1
        else:
            new_number = 1

        return f"{prefix}{new_number:04d}"

    @classmethod
    @transaction.atomic
    def create_booking(cls, room_id: int, booked_by: User, data: Dict[str, Any]) -> RoomBooking:
        """Create a room booking."""
        room = MeetingRoom.objects.get(id=room_id)

        # Check availability
        if cls.check_room_availability(room_id, data['start_time'], data['end_time']):
            raise ValueError("Room is not available for the selected time")

        # Calculate duration
        duration = (data['end_time'] - data['start_time']).total_seconds() / 60

        booking_number = cls.generate_booking_number()

        booking = RoomBooking.objects.create(
            booking_number=booking_number,
            room=room,
            booked_by=booked_by,
            title=data['title'],
            description=data.get('description', ''),
            meeting_type=data.get('meeting_type', 'INTERNAL'),
            start_time=data['start_time'],
            end_time=data['end_time'],
            duration_minutes=duration,
            organizer_id=data.get('organizer_id', booked_by.id),
            expected_attendees=data['expected_attendees'],
            external_participants=data.get('external_participants', ''),
            status='PENDING' if room.requires_approval else 'APPROVED',
            setup_requirements=data.get('setup_requirements', ''),
            catering_required=data.get('catering_required', False),
            catering_details=data.get('catering_details', ''),
            it_support_required=data.get('it_support_required', False),
            it_support_details=data.get('it_support_details', ''),
            notes=data.get('notes', '')
        )

        # Add participants
        if 'participant_ids' in data:
            booking.participants.set(User.objects.filter(id__in=data['participant_ids']))

        return booking

    @classmethod
    def check_room_availability(cls, room_id: int, start_time: datetime, end_time: datetime) -> bool:
        """Check if room is available for the time slot."""
        return RoomBooking.objects.filter(
            room_id=room_id,
            status__in=['APPROVED', 'CONFIRMED', 'IN_PROGRESS'],
            start_time__lt=end_time,
            end_time__gt=start_time
        ).exists()

    @classmethod
    @transaction.atomic
    def approve_booking(cls, booking_id: int, approved_by: User) -> RoomBooking:
        """Approve a room booking."""
        booking = RoomBooking.objects.get(id=booking_id)

        if booking.status != 'PENDING':
            raise ValueError("Only pending bookings can be approved")

        booking.status = 'APPROVED'
        booking.approved_by = approved_by
        booking.approval_date = timezone.now()
        booking.save()

        return booking

    @classmethod
    @transaction.atomic
    def reject_booking(cls, booking_id: int, rejected_by: User, reason: str) -> RoomBooking:
        """Reject a room booking."""
        booking = RoomBooking.objects.get(id=booking_id)

        if booking.status != 'PENDING':
            raise ValueError("Only pending bookings can be rejected")

        booking.status = 'REJECTED'
        booking.approved_by = rejected_by
        booking.approval_date = timezone.now()
        booking.rejection_reason = reason
        booking.save()

        return booking

    @classmethod
    @transaction.atomic
    def check_in_booking(cls, booking_id: int) -> RoomBooking:
        """Check in to a booking."""
        booking = RoomBooking.objects.get(id=booking_id)

        booking.checked_in = True
        booking.check_in_time = timezone.now()
        booking.status = 'IN_PROGRESS'
        booking.save()

        return booking

    @classmethod
    @transaction.atomic
    def check_out_booking(cls, booking_id: int, actual_attendees: int = None, feedback: str = '', rating: int = None) -> RoomBooking:
        """Check out from a booking."""
        booking = RoomBooking.objects.get(id=booking_id)

        booking.checked_out = True
        booking.check_out_time = timezone.now()
        booking.status = 'COMPLETED'
        booking.actual_attendees = actual_attendees
        booking.feedback = feedback
        booking.rating = rating
        booking.save()

        return booking

    @classmethod
    def get_available_rooms(cls, start_time: datetime, end_time: datetime,
                            capacity: int = None) -> List[MeetingRoom]:
        """Get available rooms for a time slot."""
        # Get all active rooms
        rooms = MeetingRoom.objects.filter(is_active=True, is_bookable=True)

        if capacity:
            rooms = rooms.filter(capacity__gte=capacity)

        # Filter out booked rooms
        booked_room_ids = RoomBooking.objects.filter(
            status__in=['APPROVED', 'CONFIRMED', 'IN_PROGRESS'],
            start_time__lt=end_time,
            end_time__gt=start_time
        ).values_list('room_id', flat=True)

        return list(rooms.exclude(id__in=booked_room_ids))

    # ============================================================================
    # Morning Meetings
    # ============================================================================

    @classmethod
    def generate_morning_meeting_number(cls) -> str:
        """Generate unique morning meeting number. Format: MM-YYYY-NNNN"""
        year = timezone.now().year
        prefix = f"MM-{year}-"

        last_meeting = MorningMeeting.objects.filter(
            meeting_number__startswith=prefix
        ).order_by('-meeting_number').first()

        if last_meeting:
            last_number = int(last_meeting.meeting_number.split('-')[-1])
            new_number = last_number + 1
        else:
            new_number = 1

        return f"{prefix}{new_number:04d}"

    @classmethod
    @transaction.atomic
    def create_morning_meeting(cls, group_id: int, meeting_date: date,
                                led_by: User = None, agenda_items: List[str] = None) -> MorningMeeting:
        """Create a morning meeting."""
        group = MorningMeetingGroup.objects.get(id=group_id)

        meeting_number = cls.generate_morning_meeting_number()

        meeting = MorningMeeting.objects.create(
            meeting_number=meeting_number,
            group=group,
            meeting_date=meeting_date,
            start_time=group.meeting_time,
            led_by=led_by or group.coordinator,
            agenda_items=agenda_items or group.agenda_template,
            total_expected=group.members.count(),
            status='SCHEDULED'
        )

        # Create attendance records
        for member in group.members.all():
            MorningMeetingAttendance.objects.create(
                meeting=meeting,
                employee=member,
                status='PRESENT'  # Default, will be updated
            )

        return meeting

    @classmethod
    @transaction.atomic
    def start_morning_meeting(cls, meeting_id: int) -> MorningMeeting:
        """Start a morning meeting."""
        meeting = MorningMeeting.objects.get(id=meeting_id)

        meeting.status = 'IN_PROGRESS'
        meeting.started_at = timezone.now()
        meeting.save()

        return meeting

    @classmethod
    @transaction.atomic
    def complete_morning_meeting(cls, meeting_id: int, meeting_notes: str = '',
                                  key_points: List[str] = None, action_items: List[Dict] = None,
                                  safety_moments: str = '') -> MorningMeeting:
        """Complete a morning meeting."""
        meeting = MorningMeeting.objects.get(id=meeting_id)

        # Calculate metrics
        attendance = meeting.attendance.all()
        total_present = attendance.filter(status='PRESENT').count()
        total_late = attendance.filter(status='LATE').count()
        total_absent = attendance.filter(status='ABSENT').count()

        # Calculate duration
        if meeting.started_at:
            duration = (timezone.now() - meeting.started_at).total_seconds() / 60
        else:
            duration = None

        meeting.status = 'COMPLETED'
        meeting.completed_at = timezone.now()
        meeting.end_time = timezone.now().time()
        meeting.actual_duration = duration
        meeting.meeting_notes = meeting_notes
        meeting.key_points = key_points or []
        meeting.action_items = action_items or []
        meeting.safety_moments = safety_moments
        meeting.total_present = total_present
        meeting.total_late = total_late
        meeting.total_absent = total_absent
        meeting.save()

        # Create action items
        if action_items:
            for item in action_items:
                MeetingActionItem.objects.create(
                    morning_meeting=meeting,
                    title=item['title'],
                    description=item.get('description', ''),
                    assigned_to_id=item['assigned_to_id'],
                    assigned_by_id=item.get('assigned_by_id', meeting.led_by.id),
                    due_date=item['due_date'],
                    priority=item.get('priority', 'MEDIUM')
                )

        return meeting

    @classmethod
    @transaction.atomic
    def record_attendance(cls, meeting_id: int, employee_id: int,
                          status: str, check_in_time: time = None,
                          minutes_late: int = None, absence_reason: str = '') -> MorningMeetingAttendance:
        """Record attendance for a morning meeting."""
        attendance = MorningMeetingAttendance.objects.get(
            meeting_id=meeting_id,
            employee_id=employee_id
        )

        attendance.status = status
        attendance.check_in_time = check_in_time
        attendance.minutes_late = minutes_late
        attendance.absence_reason = absence_reason
        attendance.save()

        return attendance

    @classmethod
    def auto_create_daily_meetings(cls, target_date: date = None):
        """Auto-create morning meetings for groups with auto-create enabled."""
        if not target_date:
            target_date = timezone.now().date()

        # Get weekday (0=Monday, 6=Sunday)
        weekday = target_date.weekday()

        # Get groups that meet on this day
        groups = MorningMeetingGroup.objects.filter(
            is_active=True,
            auto_create_meetings=True,
            meeting_days__contains=[weekday]
        )

        for group in groups:
            # Check if meeting already exists
            if not MorningMeeting.objects.filter(group=group, meeting_date=target_date).exists():
                cls.create_morning_meeting(group.id, target_date)

    @classmethod
    def get_upcoming_bookings(cls, user: User, days_ahead: int = 7) -> List[RoomBooking]:
        """Get upcoming room bookings for a user."""
        start = timezone.now()
        end = start + timedelta(days=days_ahead)

        return list(RoomBooking.objects.filter(
            Q(booked_by=user) | Q(organizer=user) | Q(participants=user),
            start_time__gte=start,
            start_time__lte=end,
            status__in=['APPROVED', 'CONFIRMED']
        ).distinct().select_related('room', 'booked_by'))

    @classmethod
    def get_todays_morning_meetings(cls, user: User) -> List[MorningMeeting]:
        """Get today's morning meetings for a user."""
        today = timezone.now().date()

        return list(MorningMeeting.objects.filter(
            group__members=user,
            meeting_date=today
        ).select_related('group', 'led_by'))

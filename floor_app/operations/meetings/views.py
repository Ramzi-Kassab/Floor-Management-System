"""
MorningMeeting Management System Views

Template-rendering views for meeting scheduling, room booking, and management.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone

from .models import (
    MorningMeeting,
    MeetingRoom,
    MorningMeetingAttendance,
)


@login_required
def meeting_scheduler(request):
    """Schedule new meeting or view calendar."""
    try:
        if request.method == 'POST':
            try:
                title = request.POST.get('title')
                meeting_date = request.POST.get('meeting_date')
                start_time = request.POST.get('start_time')
                end_time = request.POST.get('end_time')
                agenda = request.POST.get('agenda', '')
                room_id = request.POST.get('room')

                if not all([title, meeting_date, start_time, end_time]):
                    messages.error(request, 'Please fill in all required fields.')
                else:
                    meeting = MorningMeeting.objects.create(
                        title=title,
                        meeting_date=meeting_date,
                        start_time=start_time,
                        end_time=end_time,
                        agenda=agenda,
                        organizer=request.user,
                        status='SCHEDULED'
                    )

                    if room_id:
                        meeting.room_id = room_id
                        meeting.save()

                    # Add organizer as attendee
                    MorningMeetingAttendance.objects.create(
                        meeting=meeting,
                        user=request.user,
                        is_organizer=True,
                        response='ACCEPTED'
                    )

                    messages.success(request, 'MorningMeeting scheduled successfully.')
                    return redirect('meetings:meeting_list')

            except Exception as e:
                messages.error(request, f'Error scheduling meeting: {str(e)}')

        # Get available rooms
        rooms = MeetingRoom.objects.filter(is_active=True)

        # Get upcoming meetings
        upcoming_meetings = MorningMeeting.objects.filter(
            meeting_date__gte=timezone.now().date(),
            status='SCHEDULED'
        ).select_related('organizer', 'room').order_by('meeting_date', 'start_time')[:10]

        context = {
            'rooms': rooms,
            'upcoming_meetings': upcoming_meetings,
            'page_title': 'Schedule MorningMeeting',
        }

    except Exception as e:
        messages.error(request, f'Error loading scheduler: {str(e)}')
        context = {'rooms': [], 'upcoming_meetings': [], 'page_title': 'Schedule MorningMeeting'}

    return render(request, 'meetings/meeting_scheduler.html', context)


@login_required
def meeting_list(request):
    """List all meetings."""
    try:
        meetings = MorningMeeting.objects.select_related(
            'organizer',
            'room'
        ).annotate(
            attendee_count=Count('attendees')
        ).order_by('-meeting_date', '-start_time')

        # Filter by status
        status_filter = request.GET.get('status')
        if status_filter:
            meetings = meetings.filter(status=status_filter)

        # Filter by time (upcoming/past)
        time_filter = request.GET.get('time')
        if time_filter == 'upcoming':
            meetings = meetings.filter(meeting_date__gte=timezone.now().date())
        elif time_filter == 'past':
            meetings = meetings.filter(meeting_date__lt=timezone.now().date())

        # Filter user's meetings
        my_meetings_filter = request.GET.get('my_meetings')
        if my_meetings_filter == 'true':
            meetings = meetings.filter(
                Q(organizer=request.user) | Q(attendees__user=request.user)
            ).distinct()

        # Search
        search = request.GET.get('q')
        if search:
            meetings = meetings.filter(
                Q(title__icontains=search) |
                Q(agenda__icontains=search)
            )

        # Statistics
        stats = {
            'total': MorningMeeting.objects.count(),
            'scheduled': MorningMeeting.objects.filter(status='SCHEDULED').count(),
            'completed': MorningMeeting.objects.filter(status='COMPLETED').count(),
            'my_upcoming': MorningMeeting.objects.filter(
                Q(organizer=request.user) | Q(attendees__user=request.user),
                meeting_date__gte=timezone.now().date(),
                status='SCHEDULED'
            ).distinct().count(),
        }

        context = {
            'meetings': meetings,
            'stats': stats,
            'status_choices': MorningMeeting.STATUS_CHOICES,
            'page_title': 'Meetings',
        }

    except Exception as e:
        messages.error(request, f'Error loading meetings: {str(e)}')
        context = {'meetings': [], 'stats': {}, 'page_title': 'Meetings'}

    return render(request, 'meetings/meeting_list.html', context)


@login_required
def room_booking(request):
    """View and manage room bookings."""
    try:
        rooms = MeetingRoom.objects.filter(is_active=True).annotate(
            booking_count=Count('meetings')
        )

        # Get today's bookings
        today = timezone.now().date()
        todays_bookings = MorningMeeting.objects.filter(
            meeting_date=today,
            status='SCHEDULED'
        ).select_related('organizer', 'room').order_by('start_time')

        # Room availability for today
        room_availability = {}
        for room in rooms:
            room_bookings = todays_bookings.filter(room=room)
            room_availability[room.id] = {
                'room': room,
                'bookings': room_bookings,
                'is_available': room_bookings.count() == 0
            }

        context = {
            'rooms': rooms,
            'todays_bookings': todays_bookings,
            'room_availability': room_availability,
            'page_title': 'Room Booking',
        }

    except Exception as e:
        messages.error(request, f'Error loading room bookings: {str(e)}')
        context = {'rooms': [], 'todays_bookings': [], 'room_availability': {}, 'page_title': 'Room Booking'}

    return render(request, 'meetings/room_booking.html', context)

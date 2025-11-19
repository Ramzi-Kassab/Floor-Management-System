"""
Meeting Systems Forms

Forms for meeting room bookings and morning meetings.
"""

from django import forms
from django.contrib.auth import get_user_model
from .models import MeetingRoom, RoomBooking, MorningMeeting, MorningMeetingGroup

User = get_user_model()


class MeetingForm(forms.ModelForm):
    """Form for creating/editing meetings (room bookings)."""

    class Meta:
        model = RoomBooking
        fields = ['room', 'title', 'description', 'meeting_type', 'start_time', 'end_time',
                  'organizer', 'participants', 'expected_attendees', 'external_participants',
                  'setup_requirements', 'catering_required', 'catering_details',
                  'it_support_required', 'it_support_details']
        widgets = {
            'room': forms.Select(attrs={
                'class': 'form-control',
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Weekly Production Review',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Meeting agenda or description...',
            }),
            'meeting_type': forms.Select(attrs={
                'class': 'form-control',
            }),
            'start_time': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local',
            }),
            'end_time': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local',
            }),
            'organizer': forms.Select(attrs={
                'class': 'form-control',
            }),
            'participants': forms.SelectMultiple(attrs={
                'class': 'form-control',
            }),
            'expected_attendees': forms.NumberInput(attrs={
                'class': 'form-control',
                'value': '1',
            }),
            'external_participants': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'External participants (names, emails)',
            }),
            'setup_requirements': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Special setup requirements...',
            }),
            'catering_required': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'catering_details': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Catering requirements...',
            }),
            'it_support_required': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'it_support_details': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'IT support requirements...',
            }),
        }
        help_texts = {
            'room': 'Select meeting room',
            'title': 'Meeting title/subject',
            'meeting_type': 'Type of meeting',
            'start_time': 'Meeting start date and time',
            'end_time': 'Meeting end date and time',
            'organizer': 'Meeting organizer',
            'participants': 'Internal participants',
            'expected_attendees': 'Total expected number of attendees',
            'external_participants': 'External participants (if any)',
            'catering_required': 'Need catering?',
            'it_support_required': 'Need IT support?',
        }

    def __init__(self, *args, **kwargs):
        self.booked_by = kwargs.pop('booked_by', None)
        super().__init__(*args, **kwargs)

        # Only show active, bookable rooms
        self.fields['room'].queryset = MeetingRoom.objects.filter(
            is_active=True,
            is_bookable=True
        )

        # Filter active users
        self.fields['organizer'].queryset = User.objects.filter(is_active=True)
        self.fields['participants'].queryset = User.objects.filter(is_active=True)

        # Set booked_by user as default organizer
        if self.booked_by:
            self.fields['organizer'].initial = self.booked_by

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        room = cleaned_data.get('room')
        expected_attendees = cleaned_data.get('expected_attendees')

        # Validate times
        if start_time and end_time:
            from django.utils import timezone

            # Check if start time is in the future
            if start_time < timezone.now():
                raise forms.ValidationError({
                    'start_time': 'Meeting must be scheduled in the future'
                })

            # Check if end time is after start time
            if end_time <= start_time:
                raise forms.ValidationError({
                    'end_time': 'End time must be after start time'
                })

            # Calculate duration
            duration = (end_time - start_time).total_seconds() / 60

            # Check room booking constraints
            if room:
                if duration < room.min_booking_duration:
                    raise forms.ValidationError({
                        'end_time': f'Minimum booking duration is {room.min_booking_duration} minutes'
                    })
                if duration > room.max_booking_duration:
                    raise forms.ValidationError({
                        'end_time': f'Maximum booking duration is {room.max_booking_duration} minutes'
                    })

            # Store duration for save
            cleaned_data['duration_minutes'] = int(duration)

        # Check room capacity
        if room and expected_attendees:
            if expected_attendees > room.capacity:
                raise forms.ValidationError({
                    'expected_attendees': f'Room capacity is {room.capacity}. Please select a larger room.'
                })

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.booked_by:
            instance.booked_by = self.booked_by

        # Set duration
        if 'duration_minutes' in self.cleaned_data:
            instance.duration_minutes = self.cleaned_data['duration_minutes']

        # Set initial status based on room approval requirement
        if instance.room and instance.room.requires_approval:
            instance.status = 'PENDING'
        else:
            instance.status = 'CONFIRMED'

        if commit:
            instance.save()
            # Save many-to-many relationships
            self.save_m2m()
        return instance


class RoomBookingForm(forms.ModelForm):
    """Simplified form for quick room booking."""

    class Meta:
        model = RoomBooking
        fields = ['room', 'title', 'start_time', 'end_time', 'expected_attendees']
        widgets = {
            'room': forms.Select(attrs={
                'class': 'form-control',
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Meeting title',
            }),
            'start_time': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local',
            }),
            'end_time': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local',
            }),
            'expected_attendees': forms.NumberInput(attrs={
                'class': 'form-control',
                'value': '1',
            }),
        }
        help_texts = {
            'room': 'Select meeting room',
            'title': 'Meeting title',
            'start_time': 'Start date and time',
            'end_time': 'End date and time',
            'expected_attendees': 'Number of attendees',
        }

    def __init__(self, *args, **kwargs):
        self.booked_by = kwargs.pop('booked_by', None)
        super().__init__(*args, **kwargs)

        # Only show active, bookable rooms
        self.fields['room'].queryset = MeetingRoom.objects.filter(
            is_active=True,
            is_bookable=True
        )

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        room = cleaned_data.get('room')

        if start_time and end_time:
            from django.utils import timezone

            if start_time < timezone.now():
                raise forms.ValidationError({
                    'start_time': 'Meeting must be scheduled in the future'
                })

            if end_time <= start_time:
                raise forms.ValidationError({
                    'end_time': 'End time must be after start time'
                })

            # Calculate duration
            duration = (end_time - start_time).total_seconds() / 60
            cleaned_data['duration_minutes'] = int(duration)

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.booked_by:
            instance.booked_by = self.booked_by
            instance.organizer = self.booked_by

        if 'duration_minutes' in self.cleaned_data:
            instance.duration_minutes = self.cleaned_data['duration_minutes']

        # Set default meeting type
        instance.meeting_type = 'INTERNAL'

        # Set initial status
        if instance.room and instance.room.requires_approval:
            instance.status = 'PENDING'
        else:
            instance.status = 'CONFIRMED'

        if commit:
            instance.save()
        return instance


class MorningMeetingForm(forms.ModelForm):
    """Form for creating/editing morning meetings."""

    class Meta:
        model = MorningMeeting
        fields = ['group', 'meeting_date', 'start_time', 'led_by', 'agenda_items',
                  'meeting_notes', 'safety_moments']
        widgets = {
            'group': forms.Select(attrs={
                'class': 'form-control',
            }),
            'meeting_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'start_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',
            }),
            'led_by': forms.Select(attrs={
                'class': 'form-control',
            }),
            'agenda_items': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Agenda items (one per line or JSON format)...',
            }),
            'meeting_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Meeting notes and discussion points...',
            }),
            'safety_moments': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Safety moment shared in this meeting...',
            }),
        }
        help_texts = {
            'group': 'Morning meeting group',
            'meeting_date': 'Meeting date',
            'start_time': 'Meeting start time',
            'led_by': 'Who is leading this meeting?',
            'agenda_items': 'Agenda items for discussion',
            'meeting_notes': 'Notes from the meeting',
            'safety_moments': 'Safety moment/topic discussed',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Only show active groups
        self.fields['group'].queryset = MorningMeetingGroup.objects.filter(is_active=True)

        # Filter active users
        self.fields['led_by'].queryset = User.objects.filter(is_active=True)

    def clean_meeting_date(self):
        meeting_date = self.cleaned_data.get('meeting_date')
        if meeting_date:
            from django.utils import timezone
            # Allow past dates for recording historical meetings
            pass
        return meeting_date


class MeetingCheckInForm(forms.Form):
    """Form for checking into a meeting."""

    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Any notes (optional)',
        }),
        help_text='Optional check-in notes'
    )


class MeetingFeedbackForm(forms.ModelForm):
    """Form for meeting feedback."""

    class Meta:
        model = RoomBooking
        fields = ['feedback', 'rating', 'actual_attendees']
        widgets = {
            'feedback': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'How was the meeting? Any feedback on the room or facilities?',
            }),
            'rating': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '5',
            }),
            'actual_attendees': forms.NumberInput(attrs={
                'class': 'form-control',
            }),
        }
        help_texts = {
            'feedback': 'Feedback about the meeting or room',
            'rating': 'Rate the room/facilities (1-5)',
            'actual_attendees': 'How many people actually attended?',
        }

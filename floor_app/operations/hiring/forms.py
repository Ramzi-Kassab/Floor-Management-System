"""
Hiring/Recruitment Portal Forms

Forms for job postings, candidates, and interviews.
"""

from django import forms
from django.contrib.auth import get_user_model
from .models import JobPosting, Candidate, JobApplication, Interview

User = get_user_model()


class JobPostingForm(forms.ModelForm):
    """Form for creating/editing job postings."""

    class Meta:
        model = JobPosting
        fields = ['title', 'department', 'location', 'job_type', 'experience_level',
                  'description', 'responsibilities', 'requirements', 'preferred_qualifications',
                  'salary_min', 'salary_max', 'currency', 'benefits',
                  'positions_count', 'closing_date', 'hiring_manager']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Senior Production Engineer',
            }),
            'department': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Production, Engineering',
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Dubai, UAE',
            }),
            'job_type': forms.Select(attrs={
                'class': 'form-control',
            }),
            'experience_level': forms.Select(attrs={
                'class': 'form-control',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Job description and overview...',
            }),
            'responsibilities': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Key responsibilities and duties...',
            }),
            'requirements': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Required qualifications, skills, and experience...',
            }),
            'preferred_qualifications': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Nice to have qualifications...',
            }),
            'salary_min': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Minimum salary',
            }),
            'salary_max': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Maximum salary',
            }),
            'currency': forms.TextInput(attrs={
                'class': 'form-control',
                'value': 'USD',
            }),
            'benefits': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Benefits and perks...',
            }),
            'positions_count': forms.NumberInput(attrs={
                'class': 'form-control',
                'value': '1',
            }),
            'closing_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'hiring_manager': forms.Select(attrs={
                'class': 'form-control',
            }),
        }
        help_texts = {
            'title': 'Job title',
            'job_type': 'Employment type',
            'experience_level': 'Required experience level',
            'salary_min': 'Minimum salary (optional)',
            'salary_max': 'Maximum salary (optional)',
            'positions_count': 'Number of positions available',
            'closing_date': 'Application deadline',
            'hiring_manager': 'Hiring manager for this position',
        }

    def __init__(self, *args, **kwargs):
        self.posted_by = kwargs.pop('posted_by', None)
        super().__init__(*args, **kwargs)

        # Filter active users for hiring manager
        self.fields['hiring_manager'].queryset = User.objects.filter(is_active=True)

    def clean(self):
        cleaned_data = super().clean()
        salary_min = cleaned_data.get('salary_min')
        salary_max = cleaned_data.get('salary_max')
        closing_date = cleaned_data.get('closing_date')

        if salary_min and salary_max:
            if salary_max < salary_min:
                raise forms.ValidationError({
                    'salary_max': 'Maximum salary must be greater than minimum salary'
                })

        if closing_date:
            from django.utils import timezone
            if closing_date < timezone.now().date():
                raise forms.ValidationError({
                    'closing_date': 'Closing date cannot be in the past'
                })

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.posted_by:
            instance.posted_by = self.posted_by
        if commit:
            instance.save()
        return instance


class CandidateForm(forms.ModelForm):
    """Form for candidate registration/application."""

    class Meta:
        model = Candidate
        fields = ['first_name', 'last_name', 'email', 'phone', 'current_location',
                  'linkedin_profile', 'portfolio_url', 'current_company', 'current_position',
                  'total_experience_years', 'highest_education', 'university',
                  'resume', 'cover_letter']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'First name',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Last name',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'your.email@example.com',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+971 50 123 4567',
            }),
            'current_location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Dubai, UAE',
            }),
            'linkedin_profile': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://linkedin.com/in/yourprofile',
            }),
            'portfolio_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://yourportfolio.com',
            }),
            'current_company': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Current employer',
            }),
            'current_position': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Current job title',
            }),
            'total_experience_years': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Years of experience',
            }),
            'highest_education': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Bachelor of Engineering',
            }),
            'university': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'University/Institution name',
            }),
            'resume': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx',
            }),
            'cover_letter': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx',
            }),
        }
        help_texts = {
            'resume': 'Upload your resume (PDF or Word format)',
            'cover_letter': 'Upload cover letter (optional)',
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Check if email already exists (only for new candidates)
        if not self.instance.pk:
            if Candidate.objects.filter(email=email).exists():
                raise forms.ValidationError(
                    'A candidate with this email already exists'
                )
        return email

    def clean_total_experience_years(self):
        years = self.cleaned_data.get('total_experience_years')
        if years is not None and years < 0:
            raise forms.ValidationError('Cannot be negative')
        return years


class InterviewForm(forms.ModelForm):
    """Form for scheduling interviews."""

    class Meta:
        model = Interview
        fields = ['interview_type', 'round_number', 'scheduled_date', 'scheduled_time',
                  'duration_minutes', 'location', 'meeting_link', 'interviewers', 'notes']
        widgets = {
            'interview_type': forms.Select(attrs={
                'class': 'form-control',
            }),
            'round_number': forms.NumberInput(attrs={
                'class': 'form-control',
                'value': '1',
            }),
            'scheduled_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'scheduled_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',
            }),
            'duration_minutes': forms.NumberInput(attrs={
                'class': 'form-control',
                'value': '60',
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Conference Room A, Building 1',
            }),
            'meeting_link': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://zoom.us/j/...',
            }),
            'interviewers': forms.SelectMultiple(attrs={
                'class': 'form-control',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Interview instructions or notes...',
            }),
        }
        help_texts = {
            'interview_type': 'Type of interview',
            'round_number': 'Interview round (1, 2, 3, etc.)',
            'scheduled_date': 'Interview date',
            'scheduled_time': 'Interview time',
            'duration_minutes': 'Expected duration in minutes',
            'location': 'Physical location (for in-person interviews)',
            'meeting_link': 'Video conference link (for virtual interviews)',
            'interviewers': 'Select interviewers',
        }

    def __init__(self, *args, **kwargs):
        self.application = kwargs.pop('application', None)
        super().__init__(*args, **kwargs)

        # Filter active users for interviewers
        self.fields['interviewers'].queryset = User.objects.filter(is_active=True)

    def clean(self):
        cleaned_data = super().clean()
        scheduled_date = cleaned_data.get('scheduled_date')
        scheduled_time = cleaned_data.get('scheduled_time')
        interview_type = cleaned_data.get('interview_type')
        location = cleaned_data.get('location')
        meeting_link = cleaned_data.get('meeting_link')

        # Validate date is in future
        if scheduled_date and scheduled_time:
            from django.utils import timezone
            from datetime import datetime
            scheduled_datetime = timezone.make_aware(
                datetime.combine(scheduled_date, scheduled_time)
            )
            if scheduled_datetime < timezone.now():
                raise forms.ValidationError({
                    'scheduled_date': 'Interview must be scheduled in the future'
                })

        # For in-person interviews, location is required
        if interview_type == 'IN_PERSON' and not location:
            raise forms.ValidationError({
                'location': 'Location is required for in-person interviews'
            })

        # For video interviews, meeting link is required
        if interview_type == 'VIDEO' and not meeting_link:
            raise forms.ValidationError({
                'meeting_link': 'Meeting link is required for video interviews'
            })

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.application:
            instance.application = self.application
        if commit:
            instance.save()
            # Save many-to-many relationships
            self.save_m2m()
        return instance


class InterviewFeedbackForm(forms.ModelForm):
    """Form for interview feedback."""

    class Meta:
        model = Interview
        fields = ['feedback', 'technical_rating', 'communication_rating',
                  'cultural_fit_rating', 'overall_recommendation']
        widgets = {
            'feedback': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Detailed interview feedback...',
            }),
            'technical_rating': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '5',
            }),
            'communication_rating': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '5',
            }),
            'cultural_fit_rating': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '5',
            }),
            'overall_recommendation': forms.Select(attrs={
                'class': 'form-control',
            }),
        }
        help_texts = {
            'feedback': 'Detailed feedback from the interview',
            'technical_rating': 'Rate technical skills (1-5)',
            'communication_rating': 'Rate communication skills (1-5)',
            'cultural_fit_rating': 'Rate cultural fit (1-5)',
            'overall_recommendation': 'Overall recommendation',
        }

    def clean_feedback(self):
        feedback = self.cleaned_data.get('feedback')
        if not feedback or len(feedback.strip()) < 20:
            raise forms.ValidationError(
                'Please provide detailed feedback (at least 20 characters)'
            )
        return feedback

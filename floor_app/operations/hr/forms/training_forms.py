"""
Training Management Forms
Forms for training programs, sessions, and employee enrollment
"""

from django import forms
from django.utils import timezone
from floor_app.operations.hr.models import (
    TrainingProgram, TrainingSession, EmployeeTraining,
    HREmployee, TrainingType, TrainingStatus
)


class TrainingProgramForm(forms.ModelForm):
    """Form for creating/editing training programs"""

    class Meta:
        model = TrainingProgram
        fields = [
            'code', 'name', 'training_type', 'description',
            'duration_hours', 'duration_days', 'provider', 'is_internal',
            'prerequisites', 'target_audience', 'max_participants',
            'has_assessment', 'passing_score', 'grants_certificate',
            'certificate_validity_months', 'cost_per_person', 'currency',
            'is_mandatory', 'is_active'
        ]
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., TRN-001'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Training program name'}),
            'training_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'duration_hours': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.5'}),
            'duration_days': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'provider': forms.TextInput(attrs={'class': 'form-control'}),
            'is_internal': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'prerequisites': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'target_audience': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'max_participants': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'has_assessment': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'passing_score': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '100'}),
            'grants_certificate': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'certificate_validity_months': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'cost_per_person': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'currency': forms.TextInput(attrs={'class': 'form-control'}),
            'is_mandatory': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class TrainingSessionForm(forms.ModelForm):
    """Form for creating/editing training sessions"""

    class Meta:
        model = TrainingSession
        fields = [
            'program', 'session_code', 'status',
            'start_date', 'end_date', 'start_time', 'end_time',
            'location', 'is_virtual', 'virtual_link',
            'instructor_name', 'instructor_contact', 'notes'
        ]
        widgets = {
            'program': forms.Select(attrs={'class': 'form-select'}),
            'session_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Auto-generated if empty'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'is_virtual': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'virtual_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://...'}),
            'instructor_name': forms.TextInput(attrs={'class': 'form-control'}),
            'instructor_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date:
            if end_date < start_date:
                raise forms.ValidationError('End date cannot be before start date')

        is_virtual = cleaned_data.get('is_virtual')
        virtual_link = cleaned_data.get('virtual_link')

        if is_virtual and not virtual_link:
            self.add_error('virtual_link', 'Virtual link is required for virtual sessions')

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Auto-generate session code if not provided
        if not instance.session_code and instance.program:
            instance.session_code = TrainingSession.generate_session_code(instance.program)

        if commit:
            instance.save()

        return instance


class EnrollmentForm(forms.ModelForm):
    """Form for enrolling employees in training sessions"""

    employees = forms.ModelMultipleChoiceField(
        queryset=HREmployee.objects.filter(is_deleted=False),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=True,
        help_text='Select employees to enroll'
    )

    class Meta:
        model = EmployeeTraining
        fields = ['notes']
        widgets = {
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional enrollment notes'}),
        }

    def __init__(self, *args, session=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = session

        if session:
            # Exclude already enrolled employees
            enrolled_ids = session.participants.values_list('employee_id', flat=True)
            self.fields['employees'].queryset = HREmployee.objects.filter(
                is_deleted=False
            ).exclude(id__in=enrolled_ids).order_by('employee_no')


class TrainingCompletionForm(forms.ModelForm):
    """Form for marking training as completed"""

    class Meta:
        model = EmployeeTraining
        fields = ['attended', 'attendance_percentage', 'assessment_score', 'passed', 'notes']
        widgets = {
            'attended': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'attendance_percentage': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '100', 'step': '0.1'}),
            'assessment_score': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '100', 'step': '0.1'}),
            'passed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        attended = cleaned_data.get('attended')
        assessment_score = cleaned_data.get('assessment_score')
        passed = cleaned_data.get('passed')

        if passed and assessment_score:
            # Check if score meets passing criteria
            training = self.instance
            if training.training_session and training.training_session.program:
                passing_score = training.training_session.program.passing_score
                if assessment_score < passing_score:
                    self.add_error('passed', f'Score must be at least {passing_score}% to pass')

        return cleaned_data


class TrainingFeedbackForm(forms.ModelForm):
    """Form for employee feedback on training"""

    class Meta:
        model = EmployeeTraining
        fields = ['feedback_rating', 'feedback_comments']
        widgets = {
            'feedback_rating': forms.RadioSelect(
                choices=[(1, '1 - Poor'), (2, '2 - Fair'), (3, '3 - Good'), (4, '4 - Very Good'), (5, '5 - Excellent')],
                attrs={'class': 'form-check-input'}
            ),
            'feedback_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Share your experience...'}),
        }


class TrainingSearchForm(forms.Form):
    """Form for searching training records"""

    program = forms.ModelChoiceField(
        queryset=TrainingProgram.objects.filter(is_deleted=False),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
        empty_label='All Programs'
    )

    training_type = forms.ChoiceField(
        choices=[('', 'All Types')] + TrainingType.CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )

    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + TrainingStatus.CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )

    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control form-control-sm', 'type': 'date'})
    )

    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control form-control-sm', 'type': 'date'})
    )

    employee = forms.ModelChoiceField(
        queryset=HREmployee.objects.filter(is_deleted=False),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
        empty_label='All Employees'
    )

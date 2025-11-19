"""
Hazard Observation Card (HOC) Forms

Forms for submitting and managing hazard observations.
"""

from django import forms
from django.contrib.auth import get_user_model
from .models import HazardObservation, HOCComment, HazardCategory

User = get_user_model()


class HazardObservationForm(forms.ModelForm):
    """Form for submitting hazard observations."""

    class Meta:
        model = HazardObservation
        fields = ['category', 'severity', 'title', 'description', 'location',
                  'department', 'building', 'floor_level', 'potential_consequence',
                  'people_at_risk', 'immediate_action_taken', 'area_isolated', 'work_stopped']
        widgets = {
            'category': forms.Select(attrs={
                'class': 'form-control',
            }),
            'severity': forms.Select(attrs={
                'class': 'form-control',
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Brief description of the hazard',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Detailed description of the hazard observed...',
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Production Floor A, Near Machine #5',
            }),
            'department': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Production, Warehouse',
            }),
            'building': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Building 1',
            }),
            'floor_level': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Ground Floor, Level 2',
            }),
            'potential_consequence': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'What could happen if this hazard is not addressed?',
            }),
            'people_at_risk': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Number of people',
            }),
            'immediate_action_taken': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Did you take any immediate action? Describe here...',
            }),
            'area_isolated': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'work_stopped': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }
        help_texts = {
            'category': 'Category of hazard',
            'severity': 'How severe is this hazard?',
            'title': 'Short description of the hazard',
            'description': 'Detailed description of what you observed',
            'location': 'Specific location where hazard was observed',
            'potential_consequence': 'What could happen if not addressed?',
            'people_at_risk': 'How many people could be affected?',
            'immediate_action_taken': 'Any immediate action you took',
            'area_isolated': 'Has the area been cordoned off?',
            'work_stopped': 'Has work been stopped in this area?',
        }

    def __init__(self, *args, **kwargs):
        self.submitted_by = kwargs.pop('submitted_by', None)
        super().__init__(*args, **kwargs)

        # Only show active categories
        self.fields['category'].queryset = HazardCategory.objects.filter(is_active=True)

        # Make key fields required
        self.fields['title'].required = True
        self.fields['description'].required = True
        self.fields['location'].required = True

    def clean_description(self):
        description = self.cleaned_data.get('description')
        if description and len(description.strip()) < 20:
            raise forms.ValidationError(
                'Please provide a detailed description (at least 20 characters)'
            )
        return description

    def clean_people_at_risk(self):
        people = self.cleaned_data.get('people_at_risk')
        if people is not None and people < 0:
            raise forms.ValidationError('Cannot be negative')
        return people

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.submitted_by:
            instance.submitted_by = self.submitted_by
        if commit:
            instance.save()
        return instance


class HOCCommentForm(forms.ModelForm):
    """Form for adding comments to hazard observations."""

    class Meta:
        model = HOCComment
        fields = ['comment', 'is_internal']
        widgets = {
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Add your comment or update...',
            }),
            'is_internal': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }
        help_texts = {
            'comment': 'Your comment or update',
            'is_internal': 'Check this if comment should not be visible to the submitter',
        }

    def __init__(self, *args, **kwargs):
        self.observation = kwargs.pop('observation', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_comment(self):
        comment = self.cleaned_data.get('comment')
        if not comment or len(comment.strip()) < 5:
            raise forms.ValidationError(
                'Comment must be at least 5 characters long'
            )
        return comment

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.observation:
            instance.observation = self.observation
        if self.user:
            instance.commented_by = self.user
        if commit:
            instance.save()
        return instance


class HOCReviewForm(forms.ModelForm):
    """Form for reviewing hazard observations."""

    class Meta:
        model = HazardObservation
        fields = ['status', 'review_comments', 'assigned_to', 'due_date',
                  'corrective_action_plan']
        widgets = {
            'status': forms.Select(attrs={
                'class': 'form-control',
            }),
            'review_comments': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Review comments and assessment...',
            }),
            'assigned_to': forms.Select(attrs={
                'class': 'form-control',
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'corrective_action_plan': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Plan for corrective actions...',
            }),
        }
        help_texts = {
            'status': 'Update the status',
            'review_comments': 'Your review and assessment',
            'assigned_to': 'Assign to responsible person',
            'due_date': 'Target completion date',
            'corrective_action_plan': 'Plan for addressing this hazard',
        }

    def __init__(self, *args, **kwargs):
        self.reviewer = kwargs.pop('reviewer', None)
        super().__init__(*args, **kwargs)

        # Filter active users for assignment
        self.fields['assigned_to'].queryset = User.objects.filter(is_active=True)

        # Limit status choices to review-related statuses
        status_choices = [
            ('UNDER_REVIEW', 'Under Review'),
            ('APPROVED', 'Approved'),
            ('REJECTED', 'Rejected'),
            ('ACTION_ASSIGNED', 'Action Assigned'),
        ]
        self.fields['status'].choices = status_choices

    def clean_due_date(self):
        due_date = self.cleaned_data.get('due_date')
        if due_date:
            from django.utils import timezone
            if due_date < timezone.now().date():
                raise forms.ValidationError(
                    'Due date cannot be in the past'
                )
        return due_date

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.reviewer:
            instance.reviewed_by = self.reviewer
            from django.utils import timezone
            instance.reviewed_date = timezone.now()
        if commit:
            instance.save()
        return instance


class HOCActionForm(forms.ModelForm):
    """Form for updating corrective actions taken."""

    class Meta:
        model = HazardObservation
        fields = ['corrective_action_taken', 'status']
        widgets = {
            'corrective_action_taken': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe the corrective actions that were taken...',
            }),
            'status': forms.Select(attrs={
                'class': 'form-control',
            }),
        }
        help_texts = {
            'corrective_action_taken': 'Describe what actions were taken',
            'status': 'Update status',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Limit status choices
        status_choices = [
            ('IN_PROGRESS', 'In Progress'),
            ('COMPLETED', 'Completed'),
        ]
        self.fields['status'].choices = status_choices

    def clean_corrective_action_taken(self):
        action = self.cleaned_data.get('corrective_action_taken')
        if not action or len(action.strip()) < 20:
            raise forms.ValidationError(
                'Please provide detailed description of actions taken (at least 20 characters)'
            )
        return action


class HOCVerificationForm(forms.ModelForm):
    """Form for verifying completed corrective actions."""

    class Meta:
        model = HazardObservation
        fields = ['verification_comments', 'status']
        widgets = {
            'verification_comments': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Verify that corrective actions are satisfactory...',
            }),
            'status': forms.Select(attrs={
                'class': 'form-control',
            }),
        }
        help_texts = {
            'verification_comments': 'Verification comments',
            'status': 'Verify or request rework',
        }

    def __init__(self, *args, **kwargs):
        self.verifier = kwargs.pop('verifier', None)
        super().__init__(*args, **kwargs)

        # Limit status choices
        status_choices = [
            ('VERIFIED', 'Verified'),
            ('IN_PROGRESS', 'Needs Rework'),
        ]
        self.fields['status'].choices = status_choices

    def clean_verification_comments(self):
        comments = self.cleaned_data.get('verification_comments')
        if not comments or len(comments.strip()) < 10:
            raise forms.ValidationError(
                'Please provide verification comments (at least 10 characters)'
            )
        return comments

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.verifier:
            instance.verified_by = self.verifier
            from django.utils import timezone
            instance.verified_date = timezone.now()
        if commit:
            instance.save()
        return instance

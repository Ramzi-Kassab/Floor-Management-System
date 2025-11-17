# floor_app/operations/knowledge/forms/__init__.py
"""
Forms for Knowledge & Instructions module.
"""
from django import forms
from django.contrib.contenttypes.models import ContentType
from ..models import (
    Article, Document, InstructionRule, RuleCondition, RuleAction,
    TrainingCourse, Category, Tag
)


class ArticleForm(forms.ModelForm):
    """Form for creating/editing knowledge articles."""

    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = Article
        fields = [
            'code', 'title', 'summary', 'body', 'article_type',
            'priority', 'category', 'tags', 'owner_department',
            'effective_from', 'effective_until', 'review_due_date',
            'is_featured', 'is_pinned', 'requires_acknowledgment'
        ]
        widgets = {
            'summary': forms.Textarea(attrs={'rows': 3}),
            'body': forms.Textarea(attrs={'rows': 20, 'class': 'rich-editor'}),
            'effective_from': forms.DateInput(attrs={'type': 'date'}),
            'effective_until': forms.DateInput(attrs={'type': 'date'}),
            'review_due_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name not in ['is_featured', 'is_pinned', 'requires_acknowledgment', 'tags']:
                field.widget.attrs['class'] = field.widget.attrs.get('class', '') + ' form-control'


class DocumentForm(forms.ModelForm):
    """Form for uploading documents."""

    class Meta:
        model = Document
        fields = ['title', 'file', 'file_type', 'description', 'version', 'is_public', 'expires_at']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'expires_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name != 'is_public':
                field.widget.attrs['class'] = field.widget.attrs.get('class', '') + ' form-control'


class InstructionRuleForm(forms.ModelForm):
    """Form for creating/editing instruction rules."""

    class Meta:
        model = InstructionRule
        fields = [
            'code', 'title', 'short_description', 'description',
            'instruction_type', 'priority', 'is_default', 'is_temporary',
            'valid_from', 'valid_until', 'owner_department', 'source_article',
            'execution_order'
        ]
        widgets = {
            'short_description': forms.Textarea(attrs={'rows': 2}),
            'description': forms.Textarea(attrs={'rows': 10, 'class': 'rich-editor'}),
            'valid_from': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'valid_until': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name not in ['is_default', 'is_temporary']:
                field.widget.attrs['class'] = field.widget.attrs.get('class', '') + ' form-control'


class RuleConditionForm(forms.ModelForm):
    """Form for adding conditions to instruction rules."""

    class Meta:
        model = RuleCondition
        fields = [
            'target_model', 'field_path', 'operator', 'value',
            'value_max', 'logical_operator', 'condition_group', 'order', 'case_sensitive'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit target models to relevant ones
        self.fields['target_model'].queryset = ContentType.objects.filter(
            app_label__in=['hr', 'knowledge']
        )


class RuleActionForm(forms.ModelForm):
    """Form for adding actions to instruction rules."""

    class Meta:
        model = RuleAction
        fields = [
            'action_type', 'message_template', 'target_field',
            'value_expression', 'severity', 'order', 'stop_propagation'
        ]
        widgets = {
            'message_template': forms.Textarea(attrs={'rows': 3}),
            'value_expression': forms.Textarea(attrs={'rows': 2}),
            'parameters': forms.Textarea(attrs={'rows': 5}),
        }


class TrainingCourseForm(forms.ModelForm):
    """Form for creating/editing training courses."""

    class Meta:
        model = TrainingCourse
        fields = [
            'code', 'title', 'description', 'objectives', 'prerequisites',
            'course_type', 'difficulty_level', 'estimated_duration_minutes',
            'validity_months', 'owner_department', 'is_mandatory',
            'requires_assessment', 'passing_score', 'max_attempts',
            'allow_self_enrollment', 'grants_qualification'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'objectives': forms.Textarea(attrs={'rows': 4}),
            'prerequisites': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name not in ['is_mandatory', 'requires_assessment', 'allow_self_enrollment']:
                field.widget.attrs['class'] = field.widget.attrs.get('class', '') + ' form-control'


class CategoryForm(forms.ModelForm):
    """Form for categories."""

    class Meta:
        model = Category
        fields = ['name', 'slug', 'description', 'parent', 'icon', 'color', 'order', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'color': forms.TextInput(attrs={'type': 'color'}),
        }


class ArticleSearchForm(forms.Form):
    """Search form for articles."""
    q = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search articles...'
        })
    )
    article_type = forms.ChoiceField(
        choices=[('', 'All Types')] + list(Article.ArticleType.choices),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(is_active=True, is_deleted=False),
        required=False,
        empty_label='All Categories',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    tag = forms.ModelChoiceField(
        queryset=Tag.objects.all(),
        required=False,
        empty_label='All Tags',
        widget=forms.Select(attrs={'class': 'form-select'})
    )


__all__ = [
    'ArticleForm',
    'DocumentForm',
    'InstructionRuleForm',
    'RuleConditionForm',
    'RuleActionForm',
    'TrainingCourseForm',
    'CategoryForm',
    'ArticleSearchForm',
]

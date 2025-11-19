"""HOC API Serializers"""

from rest_framework import serializers
from floor_app.operations.hoc.models import (
    HazardCategory, HazardObservation, HOCPhoto, HOCComment, HOCStatusHistory
)


class HazardCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = HazardCategory
        fields = ['id', 'name', 'description', 'color', 'icon', 'is_active', 'sort_order']


class HOCPhotoSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)

    class Meta:
        model = HOCPhoto
        fields = ['id', 'observation', 'photo_type', 'photo', 'thumbnail', 'caption',
                  'uploaded_by', 'uploaded_by_name', 'uploaded_date', 'sort_order']
        read_only_fields = ['uploaded_by', 'uploaded_date']


class HOCCommentSerializer(serializers.ModelSerializer):
    commented_by_name = serializers.CharField(source='commented_by.get_full_name', read_only=True)

    class Meta:
        model = HOCComment
        fields = ['id', 'observation', 'comment', 'commented_by', 'commented_by_name',
                  'comment_date', 'is_internal']
        read_only_fields = ['commented_by', 'comment_date']


class HOCStatusHistorySerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(source='changed_by.get_full_name', read_only=True)

    class Meta:
        model = HOCStatusHistory
        fields = ['id', 'from_status', 'to_status', 'changed_by', 'changed_by_name',
                  'changed_date', 'reason']
        read_only_fields = ['changed_by', 'changed_date']


class HazardObservationSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    submitted_by_name = serializers.CharField(source='submitted_by.get_full_name', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    days_open = serializers.IntegerField(read_only=True)
    photos = HOCPhotoSerializer(many=True, read_only=True)
    comments = HOCCommentSerializer(many=True, read_only=True)

    class Meta:
        model = HazardObservation
        fields = [
            'id', 'card_number', 'submitted_by', 'submitted_by_name', 'submission_date',
            'category', 'category_name', 'severity', 'title', 'description',
            'location', 'department', 'building', 'floor_level', 'gps_coordinates',
            'potential_consequence', 'people_at_risk', 'immediate_action_taken',
            'area_isolated', 'work_stopped', 'status', 'reviewed_by', 'reviewed_date',
            'review_comments', 'assigned_to', 'assigned_to_name', 'assigned_date',
            'due_date', 'corrective_action_plan', 'corrective_action_taken',
            'action_completed_date', 'verified_by', 'verified_date', 'verification_comments',
            'closed_by', 'closed_date', 'closure_comments', 'is_repeat_observation',
            'related_incident', 'cost_estimate', 'actual_cost', 'tags', 'custom_fields',
            'is_overdue', 'days_open', 'photos', 'comments'
        ]
        read_only_fields = ['card_number', 'submitted_by', 'submission_date', 'is_overdue', 'days_open']


class HazardObservationCreateSerializer(serializers.Serializer):
    category_id = serializers.IntegerField()
    severity = serializers.ChoiceField(choices=HazardObservation.SEVERITY_CHOICES)
    title = serializers.CharField(max_length=200)
    description = serializers.CharField()
    location = serializers.CharField(max_length=200)
    department = serializers.CharField(max_length=100, required=False, allow_blank=True)
    building = serializers.CharField(max_length=100, required=False, allow_blank=True)
    floor_level = serializers.CharField(max_length=50, required=False, allow_blank=True)
    gps_coordinates = serializers.CharField(max_length=100, required=False, allow_blank=True)
    potential_consequence = serializers.CharField(required=False, allow_blank=True)
    people_at_risk = serializers.IntegerField(required=False, allow_null=True)
    immediate_action_taken = serializers.CharField(required=False, allow_blank=True)
    area_isolated = serializers.BooleanField(default=False)
    work_stopped = serializers.BooleanField(default=False)
    is_repeat_observation = serializers.BooleanField(default=False)
    related_incident = serializers.CharField(max_length=100, required=False, allow_blank=True)
    tags = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    custom_fields = serializers.JSONField(required=False, default=dict)


class HOCAssignSerializer(serializers.Serializer):
    assigned_to_id = serializers.IntegerField()
    due_date = serializers.DateField(required=False, allow_null=True)
    corrective_action_plan = serializers.CharField(required=False, allow_blank=True)


class HOCStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=HazardObservation.STATUS_CHOICES)
    reason = serializers.CharField(required=False, allow_blank=True)


class HOCCorrectiveActionSerializer(serializers.Serializer):
    corrective_action_taken = serializers.CharField()


class HOCVerifySerializer(serializers.Serializer):
    is_verified = serializers.BooleanField()
    verification_comments = serializers.CharField(required=False, allow_blank=True)


class HOCCloseSerializer(serializers.Serializer):
    closure_comments = serializers.CharField(required=False, allow_blank=True)
    actual_cost = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)


class HOCPhotoUploadSerializer(serializers.Serializer):
    photo = serializers.ImageField()
    photo_type = serializers.ChoiceField(choices=HOCPhoto.PHOTO_TYPES, default='BEFORE')
    caption = serializers.CharField(max_length=200, required=False, allow_blank=True)


class HOCCommentCreateSerializer(serializers.Serializer):
    comment = serializers.CharField()
    is_internal = serializers.BooleanField(default=False)

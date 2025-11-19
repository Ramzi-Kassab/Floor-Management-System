"""5S API Serializers"""

from rest_framework import serializers
from floor_app.operations.fives.models import (
    FiveSAuditTemplate, FiveSAudit, FiveSPhoto, FiveSLeaderboard,
    FiveSAchievement, FiveSUserAchievement, FiveSCompetition,
    FiveSImprovementAction, FiveSPointsHistory
)

class FiveSAuditTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FiveSAuditTemplate
        fields = '__all__'

class FiveSAuditSerializer(serializers.ModelSerializer):
    audited_by_name = serializers.CharField(source='audited_by.get_full_name', read_only=True)
    responsible_person_name = serializers.CharField(source='responsible_person.get_full_name', read_only=True)
    class Meta:
        model = FiveSAudit
        fields = '__all__'

class FiveSAuditCreateSerializer(serializers.Serializer):
    area_name = serializers.CharField(max_length=200)
    department = serializers.CharField(max_length=100, required=False, allow_blank=True)
    building = serializers.CharField(max_length=100, required=False, allow_blank=True)
    floor_level = serializers.CharField(max_length=50, required=False, allow_blank=True)
    team_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    responsible_person_id = serializers.IntegerField(required=False, allow_null=True)
    team_member_ids = serializers.ListField(child=serializers.IntegerField(), required=False, default=list)
    audit_date = serializers.DateField()
    audit_time = serializers.TimeField(required=False, allow_null=True)

class FiveSAuditCompleteSerializer(serializers.Serializer):
    checklist_responses = serializers.JSONField()
    observations = serializers.CharField(required=False, allow_blank=True)
    strengths = serializers.CharField(required=False, allow_blank=True)
    areas_for_improvement = serializers.CharField(required=False, allow_blank=True)
    action_items = serializers.ListField(required=False, default=list)

class FiveSLeaderboardSerializer(serializers.ModelSerializer):
    responsible_person_name = serializers.CharField(source='responsible_person.get_full_name', read_only=True)
    class Meta:
        model = FiveSLeaderboard
        fields = '__all__'

class FiveSAchievementSerializer(serializers.ModelSerializer):
    class Meta:
        model = FiveSAchievement
        fields = '__all__'

class FiveSUserAchievementSerializer(serializers.ModelSerializer):
    achievement_name = serializers.CharField(source='achievement.name', read_only=True)
    achievement_icon = serializers.CharField(source='achievement.icon', read_only=True)
    class Meta:
        model = FiveSUserAchievement
        fields = '__all__'

class FiveSPointsHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = FiveSPointsHistory
        fields = '__all__'

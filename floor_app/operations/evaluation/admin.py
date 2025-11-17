from django.contrib import admin
from .models import (
    BitType,
    BitSection,
    FeatureCode,
    CutterEvaluationCode,
    TechnicalInstructionTemplate,
    RequirementTemplate,
    EvaluationSession,
    EvaluationCell,
    ThreadInspection,
    NDTInspection,
    TechnicalInstructionInstance,
    RequirementInstance,
    EvaluationSessionHistory,
)


# ========== Reference/Configuration Models ==========

@admin.register(BitType)
class BitTypeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'is_active', 'sort_order']
    list_filter = ['is_active']
    search_fields = ['code', 'name', 'description']
    ordering = ['sort_order', 'name']
    list_editable = ['is_active', 'sort_order']


@admin.register(BitSection)
class BitSectionAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'is_active', 'sort_order']
    list_filter = ['is_active']
    search_fields = ['code', 'name', 'description']
    ordering = ['sort_order', 'name']
    list_editable = ['is_active', 'sort_order']


@admin.register(FeatureCode)
class FeatureCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'category', 'is_active', 'sort_order']
    list_filter = ['category', 'is_active']
    search_fields = ['code', 'name', 'description']
    ordering = ['sort_order', 'code']
    list_editable = ['is_active', 'sort_order']


@admin.register(CutterEvaluationCode)
class CutterEvaluationCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'action_required', 'color', 'is_active', 'sort_order']
    list_filter = ['action_required', 'is_active']
    search_fields = ['code', 'name', 'description']
    ordering = ['sort_order', 'code']
    list_editable = ['is_active', 'sort_order']
    fieldsets = (
        ('Code Information', {
            'fields': ('code', 'name', 'description')
        }),
        ('Display', {
            'fields': ('color', 'sort_order')
        }),
        ('Action', {
            'fields': ('action_required',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


# ========== Template Models ==========

@admin.register(TechnicalInstructionTemplate)
class TechnicalInstructionTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'title', 'applies_to_bit_type', 'applies_to_section',
        'priority', 'is_mandatory', 'auto_apply', 'is_active'
    ]
    list_filter = [
        'is_mandatory', 'requires_engineer_override', 'auto_apply',
        'is_active', 'applies_to_bit_type', 'applies_to_section'
    ]
    search_fields = ['code', 'title', 'description']
    ordering = ['-priority', 'code']
    list_editable = ['priority', 'is_mandatory', 'auto_apply', 'is_active']
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    fieldsets = (
        ('Instruction Details', {
            'fields': ('code', 'title', 'description')
        }),
        ('Application', {
            'fields': ('applies_to_bit_type', 'applies_to_section', 'auto_apply')
        }),
        ('Priority & Requirements', {
            'fields': ('priority', 'is_mandatory', 'requires_engineer_override')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Audit', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ['collapse']
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(RequirementTemplate)
class RequirementTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'title', 'category', 'applies_to_bit_type',
        'is_mandatory', 'auto_apply', 'is_active'
    ]
    list_filter = ['category', 'is_mandatory', 'auto_apply', 'is_active', 'applies_to_bit_type']
    search_fields = ['code', 'title', 'description', 'verification_method']
    ordering = ['category', 'code']
    list_editable = ['is_mandatory', 'auto_apply', 'is_active']
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    fieldsets = (
        ('Requirement Details', {
            'fields': ('code', 'title', 'description', 'category')
        }),
        ('Application', {
            'fields': ('applies_to_bit_type', 'verification_method', 'auto_apply')
        }),
        ('Priority', {
            'fields': ('is_mandatory',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Audit', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ['collapse']
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# ========== Main Evaluation Session ==========

class EvaluationCellInline(admin.TabularInline):
    model = EvaluationCell
    extra = 0
    fields = [
        'pocket_number', 'row', 'column', 'blade_number',
        'evaluation_code', 'feature_code', 'section', 'condition_description'
    ]
    ordering = ['row', 'column']
    can_delete = True
    show_change_link = False


class ThreadInspectionInline(admin.StackedInline):
    model = ThreadInspection
    extra = 0
    fields = [
        'thread_type', 'thread_size', 'result', 'damage_type',
        'pitch_diameter', 'lead', 'taper',
        'description', 'repair_action', 'repair_completed', 'inspected_by'
    ]
    readonly_fields = ['inspection_date', 'created_at']


class NDTInspectionInline(admin.StackedInline):
    model = NDTInspection
    extra = 0
    fields = [
        'test_type', 'test_procedure', 'test_area',
        'result', 'defect_severity',
        'defects_found', 'defect_locations', 'recommendations',
        'report_number', 'performed_by'
    ]
    readonly_fields = ['test_date', 'created_at']


class TechnicalInstructionInstanceInline(admin.TabularInline):
    model = TechnicalInstructionInstance
    extra = 0
    fields = ['code', 'title', 'is_mandatory', 'status', 'actioned_by', 'actioned_at']
    readonly_fields = ['code', 'title', 'is_mandatory', 'actioned_at']


class RequirementInstanceInline(admin.TabularInline):
    model = RequirementInstance
    extra = 0
    fields = ['code', 'title', 'category', 'is_mandatory', 'status', 'satisfied_by', 'satisfied_at']
    readonly_fields = ['code', 'title', 'category', 'is_mandatory', 'satisfied_at']


@admin.register(EvaluationSession)
class EvaluationSessionAdmin(admin.ModelAdmin):
    list_display = [
        'session_number', 'job_card', 'bit_type', 'status',
        'total_cutters', 'replace_count', 'repair_count', 'ok_count',
        'revision_number', 'is_locked', 'created_at'
    ]
    list_filter = ['status', 'bit_type', 'is_locked', 'evaluation_date']
    search_fields = [
        'session_number', 'job_card__job_card_number',
        'serial_unit__serial_number', 'evaluation_notes'
    ]
    date_hierarchy = 'created_at'
    readonly_fields = [
        'total_cutters', 'replace_count', 'repair_count', 'ok_count', 'rotate_count',
        'created_at', 'updated_at', 'locked_at'
    ]
    inlines = [
        EvaluationCellInline,
        ThreadInspectionInline,
        NDTInspectionInline,
        TechnicalInstructionInstanceInline,
        RequirementInstanceInline,
    ]
    fieldsets = (
        ('Session Information', {
            'fields': (
                'session_number', 'job_card', 'serial_unit', 'bit_type',
                'revision_number', 'status'
            )
        }),
        ('Grid Configuration', {
            'fields': ('total_pockets', 'total_rows', 'total_columns')
        }),
        ('Evaluation Details', {
            'fields': ('evaluated_by', 'evaluation_date', 'evaluation_notes')
        }),
        ('Summary Statistics', {
            'fields': (
                'total_cutters', 'replace_count', 'repair_count',
                'ok_count', 'rotate_count'
            ),
            'classes': ['collapse']
        }),
        ('Review & Approval', {
            'fields': (
                'reviewed_by', 'review_date', 'review_notes',
                'approved_by', 'approval_date', 'approval_notes'
            ),
            'classes': ['collapse']
        }),
        ('Lock Status', {
            'fields': ('is_locked', 'locked_at', 'locked_by'),
            'classes': ['collapse']
        }),
        ('Audit', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ['collapse']
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(EvaluationCell)
class EvaluationCellAdmin(admin.ModelAdmin):
    list_display = [
        'session', 'pocket_number', 'row', 'column',
        'evaluation_code', 'feature_code', 'section', 'wear_percentage'
    ]
    list_filter = ['evaluation_code', 'feature_code', 'section']
    search_fields = ['session__session_number', 'condition_description', 'notes']
    ordering = ['session', 'row', 'column']


# ========== Inspection Models ==========

@admin.register(ThreadInspection)
class ThreadInspectionAdmin(admin.ModelAdmin):
    list_display = [
        'session', 'thread_type', 'thread_size', 'result',
        'damage_type', 'repair_completed', 'inspected_by', 'inspection_date'
    ]
    list_filter = ['result', 'damage_type', 'repair_completed', 'thread_type']
    search_fields = ['session__session_number', 'description', 'repair_action']
    date_hierarchy = 'inspection_date'
    readonly_fields = ['inspection_date', 'created_at', 'updated_at']

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(NDTInspection)
class NDTInspectionAdmin(admin.ModelAdmin):
    list_display = [
        'session', 'test_type', 'test_area', 'result',
        'defect_severity', 'report_number', 'performed_by', 'test_date'
    ]
    list_filter = ['test_type', 'result', 'defect_severity']
    search_fields = ['session__session_number', 'report_number', 'defects_found']
    date_hierarchy = 'test_date'
    readonly_fields = ['test_date', 'created_at', 'updated_at']

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


# ========== Instance Models ==========

@admin.register(TechnicalInstructionInstance)
class TechnicalInstructionInstanceAdmin(admin.ModelAdmin):
    list_display = [
        'session', 'code', 'title', 'is_mandatory',
        'status', 'actioned_by', 'actioned_at'
    ]
    list_filter = ['status', 'is_mandatory']
    search_fields = ['session__session_number', 'code', 'title', 'description']
    readonly_fields = ['actioned_at', 'created_at', 'updated_at']


@admin.register(RequirementInstance)
class RequirementInstanceAdmin(admin.ModelAdmin):
    list_display = [
        'session', 'code', 'title', 'category', 'is_mandatory',
        'status', 'satisfied_by', 'satisfied_at'
    ]
    list_filter = ['status', 'category', 'is_mandatory']
    search_fields = ['session__session_number', 'code', 'title', 'description']
    readonly_fields = ['satisfied_at', 'created_at', 'updated_at']


# ========== History ==========

@admin.register(EvaluationSessionHistory)
class EvaluationSessionHistoryAdmin(admin.ModelAdmin):
    list_display = ['session', 'action', 'description', 'performed_by', 'performed_at']
    list_filter = ['action']
    search_fields = ['session__session_number', 'description']
    date_hierarchy = 'performed_at'
    readonly_fields = ['session', 'action', 'description', 'old_value', 'new_value', 'performed_by', 'performed_at']

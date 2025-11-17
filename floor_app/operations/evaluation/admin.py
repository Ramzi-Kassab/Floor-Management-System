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
    EvaluationChangeLog,
)


# ========== Reference/Configuration Models ==========

@admin.register(BitType)
class BitTypeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'manufacturer', 'is_active', 'sort_order']
    list_filter = ['is_active']
    search_fields = ['code', 'name', 'description', 'manufacturer']
    ordering = ['sort_order', 'name']
    list_editable = ['is_active', 'sort_order']


@admin.register(BitSection)
class BitSectionAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'sequence', 'is_active']
    list_filter = ['is_active']
    search_fields = ['code', 'name', 'description']
    ordering = ['sequence']
    list_editable = ['is_active']


@admin.register(FeatureCode)
class FeatureCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'geometry_type', 'is_active', 'sort_order']
    list_filter = ['geometry_type', 'is_active']
    search_fields = ['code', 'name', 'description']
    ordering = ['sort_order', 'code']
    list_editable = ['is_active', 'sort_order']


@admin.register(CutterEvaluationCode)
class CutterEvaluationCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'action', 'color_code', 'is_active', 'sort_order']
    list_filter = ['action', 'is_active']
    search_fields = ['code', 'name', 'description']
    ordering = ['sort_order', 'code']
    list_editable = ['is_active', 'sort_order']


# ========== Core Evaluation Models ==========

class EvaluationCellInline(admin.TabularInline):
    model = EvaluationCell
    extra = 0
    fields = ['blade_number', 'section', 'position_index', 'cutter_code', 'notes']
    ordering = ['blade_number', 'position_index']


class ThreadInspectionInline(admin.TabularInline):
    model = ThreadInspection
    extra = 0
    fields = ['connection_type', 'thread_type', 'result', 'description']
    readonly_fields = ['inspected_at']


class NDTInspectionInline(admin.TabularInline):
    model = NDTInspection
    extra = 0
    fields = ['method', 'result', 'areas_inspected', 'recommendations']
    readonly_fields = ['inspected_at']


class TechnicalInstructionInstanceInline(admin.TabularInline):
    model = TechnicalInstructionInstance
    extra = 0
    fields = ['template', 'stage', 'status', 'override_reason']
    readonly_fields = ['template', 'stage']


class RequirementInstanceInline(admin.TabularInline):
    model = RequirementInstance
    extra = 0
    fields = ['template', 'status', 'notes']
    readonly_fields = ['template']


@admin.register(EvaluationSession)
class EvaluationSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'serial_unit', 'context', 'status', 'total_cells', 'replace_count', 'evaluator', 'created_at']
    list_filter = ['status', 'context', 'created_at']
    search_fields = ['serial_unit__serial_number', 'customer_name', 'project_name']
    date_hierarchy = 'created_at'
    readonly_fields = ['total_cells', 'replace_count', 'ok_count', 'braze_count', 'rotate_count', 'lost_count', 'created_at', 'updated_at']
    inlines = [EvaluationCellInline, ThreadInspectionInline, NDTInspectionInline, TechnicalInstructionInstanceInline, RequirementInstanceInline]

    fieldsets = (
        ('Session Info', {
            'fields': ('serial_unit', 'mat_revision', 'job_card', 'batch_order', 'context')
        }),
        ('Customer/Project', {
            'fields': ('customer_name', 'project_name')
        }),
        ('Status & Personnel', {
            'fields': ('status', 'evaluator', 'reviewing_engineer')
        }),
        ('Summary Statistics', {
            'fields': ('total_cells', 'replace_count', 'ok_count', 'braze_count', 'rotate_count', 'lost_count'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('general_notes', 'wear_pattern_notes', 'damage_assessment', 'recommendations'),
            'classes': ('collapse',)
        }),
        ('Workflow', {
            'fields': ('submitted_at', 'approved_at', 'approved_by', 'locked_at', 'locked_by', 'is_last_known_state'),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(EvaluationCell)
class EvaluationCellAdmin(admin.ModelAdmin):
    list_display = ['evaluation_session', 'blade_number', 'section', 'position_index', 'cutter_code', 'is_primary']
    list_filter = ['cutter_code', 'section', 'is_primary']
    search_fields = ['evaluation_session__serial_unit__serial_number', 'notes']
    ordering = ['evaluation_session', 'blade_number', 'position_index']


@admin.register(ThreadInspection)
class ThreadInspectionAdmin(admin.ModelAdmin):
    list_display = ['evaluation_session', 'thread_type', 'connection_type', 'result', 'inspected_by', 'inspected_at']
    list_filter = ['thread_type', 'connection_type', 'result']
    search_fields = ['evaluation_session__serial_unit__serial_number', 'description']
    date_hierarchy = 'inspected_at'
    readonly_fields = ['inspected_at']


@admin.register(NDTInspection)
class NDTInspectionAdmin(admin.ModelAdmin):
    list_display = ['evaluation_session', 'method', 'result', 'meets_acceptance_criteria', 'inspector', 'inspected_at']
    list_filter = ['method', 'result', 'meets_acceptance_criteria']
    search_fields = ['evaluation_session__serial_unit__serial_number', 'areas_inspected', 'recommendations']
    date_hierarchy = 'inspected_at'
    readonly_fields = ['inspected_at']


# ========== Templates ==========

@admin.register(TechnicalInstructionTemplate)
class TechnicalInstructionTemplateAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'scope', 'stage', 'severity', 'priority', 'auto_generate', 'is_active']
    list_filter = ['scope', 'stage', 'severity', 'auto_generate', 'is_active']
    search_fields = ['code', 'name', 'description', 'output_template']
    ordering = ['-priority', 'code']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['priority', 'auto_generate', 'is_active']


@admin.register(RequirementTemplate)
class RequirementTemplateAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'stage', 'requirement_type', 'is_mandatory', 'can_be_waived', 'is_active']
    list_filter = ['stage', 'requirement_type', 'is_mandatory', 'can_be_waived', 'is_active']
    search_fields = ['code', 'name', 'description']
    ordering = ['stage', 'sort_order', 'code']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['is_mandatory', 'is_active']


# ========== Instances ==========

@admin.register(TechnicalInstructionInstance)
class TechnicalInstructionInstanceAdmin(admin.ModelAdmin):
    list_display = ['evaluation_session', 'template', 'stage', 'severity', 'status', 'acknowledged_by', 'acknowledged_at']
    list_filter = ['status', 'stage', 'severity']
    search_fields = ['evaluation_session__serial_unit__serial_number', 'resolved_text', 'override_reason']
    readonly_fields = ['acknowledged_at', 'generated_at', 'resolved_at']


@admin.register(RequirementInstance)
class RequirementInstanceAdmin(admin.ModelAdmin):
    list_display = ['evaluation_session', 'template', 'status', 'satisfied_by', 'satisfied_at']
    list_filter = ['status']
    search_fields = ['evaluation_session__serial_unit__serial_number', 'notes', 'waiver_reason']
    readonly_fields = ['satisfied_at', 'created_at', 'updated_at']


# ========== History ==========

@admin.register(EvaluationChangeLog)
class EvaluationChangeLogAdmin(admin.ModelAdmin):
    list_display = ['evaluation_session', 'change_type', 'change_stage', 'field_changed', 'changed_by', 'changed_at']
    list_filter = ['change_type', 'change_stage']
    search_fields = ['evaluation_session__serial_unit__serial_number', 'reason', 'field_changed']
    date_hierarchy = 'changed_at'
    readonly_fields = ['evaluation_session', 'evaluation_cell', 'change_type', 'change_stage', 'model_name',
                      'field_changed', 'old_value', 'new_value', 'reason', 'changed_by', 'changed_at']

from django.contrib import admin
from .models import (
    OperationDefinition,
    CutterSymbol,
    ChecklistTemplate,
    ChecklistItemTemplate,
    BatchOrder,
    JobCard,
    JobRoute,
    JobRouteStep,
    CutterLayout,
    CutterLocation,
    JobCutterEvaluationHeader,
    JobCutterEvaluationDetail,
    ApiThreadInspection,
    NdtReport,
    JobChecklistInstance,
    JobChecklistItem,
)


# Reference tables
@admin.register(OperationDefinition)
class OperationDefinitionAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'department', 'operation_group', 'default_sequence', 'is_active']
    list_filter = ['department', 'operation_group', 'is_active', 'is_quality_checkpoint']
    search_fields = ['code', 'name', 'description']
    ordering = ['sort_order', 'default_sequence']


@admin.register(CutterSymbol)
class CutterSymbolAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'name', 'action', 'is_replacement', 'is_repair', 'is_active']
    list_filter = ['action', 'is_replacement', 'is_repair', 'is_active']
    search_fields = ['symbol', 'name', 'description']
    ordering = ['sort_order', 'symbol']


class ChecklistItemTemplateInline(admin.TabularInline):
    model = ChecklistItemTemplate
    extra = 1
    fields = ['sequence', 'text', 'required_role', 'is_mandatory']


@admin.register(ChecklistTemplate)
class ChecklistTemplateAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'applies_to', 'required_for_release', 'auto_create_on_job', 'is_active']
    list_filter = ['applies_to', 'required_for_release', 'auto_create_on_job', 'is_active']
    search_fields = ['code', 'name', 'description']
    inlines = [ChecklistItemTemplateInline]
    ordering = ['sort_order', 'name']


# Batch & Job Card
@admin.register(BatchOrder)
class BatchOrderAdmin(admin.ModelAdmin):
    list_display = ['code', 'customer_name', 'bit_family', 'target_quantity', 'completed_quantity', 'status', 'priority', 'due_date']
    list_filter = ['status', 'priority', 'bit_family', 'customer_name']
    search_fields = ['code', 'customer_name', 'main_order_number', 'description']
    date_hierarchy = 'created_at'
    readonly_fields = ['completed_quantity', 'shipped_quantity']


class JobRouteInline(admin.StackedInline):
    model = JobRoute
    extra = 0
    can_delete = False
    show_change_link = True
    fields = ['template_used', 'total_planned_hours', 'total_actual_hours', 'is_complete']
    readonly_fields = ['total_planned_hours', 'total_actual_hours', 'is_complete']


@admin.register(JobCard)
class JobCardAdmin(admin.ModelAdmin):
    list_display = ['job_card_number', 'serial_unit', 'customer_name', 'job_type', 'status', 'priority', 'bit_size', 'bit_type']
    list_filter = ['status', 'job_type', 'priority', 'batch_order', 'customer_name']
    search_fields = ['job_card_number', 'serial_unit__serial_number', 'customer_name', 'well_name', 'rig_name']
    date_hierarchy = 'created_at'
    inlines = [JobRouteInline]
    readonly_fields = ['created_date', 'evaluation_started_at', 'evaluation_completed_at', 'released_at', 'production_started_at', 'qc_started_at', 'completed_at']
    fieldsets = (
        ('Core Information', {
            'fields': ('job_card_number', 'batch_order', 'serial_unit', 'job_type', 'status', 'priority')
        }),
        ('MAT/Design', {
            'fields': ('initial_mat', 'current_mat', 'bom_header')
        }),
        ('Customer Information', {
            'fields': ('customer_name', 'customer_order_ref', 'bit_size', 'bit_type')
        }),
        ('Location/Job', {
            'fields': ('well_name', 'rig_name', 'field_name')
        }),
        ('Workflow Timestamps', {
            'fields': ('created_date', 'evaluation_started_at', 'evaluation_completed_at', 'released_at', 'released_by', 'production_started_at', 'qc_started_at', 'completed_at', 'closed_by'),
            'classes': ['collapse']
        }),
        ('Scheduling', {
            'fields': ('planned_start_date', 'planned_end_date', 'actual_start_date', 'actual_end_date'),
            'classes': ['collapse']
        }),
        ('Costing', {
            'fields': ('estimated_cost', 'actual_cost', 'quoted_price'),
            'classes': ['collapse']
        }),
        ('Notes', {
            'fields': ('notes', 'special_instructions', 'customer_requirements'),
            'classes': ['collapse']
        }),
        ('Rework', {
            'fields': ('rework_of', 'rework_reason'),
            'classes': ['collapse']
        }),
    )


# Routing
class JobRouteStepInline(admin.TabularInline):
    model = JobRouteStep
    extra = 1
    fields = ['sequence', 'operation', 'status', 'operator', 'actual_start_at', 'actual_end_at']
    readonly_fields = ['actual_start_at', 'actual_end_at']
    ordering = ['sequence']


@admin.register(JobRoute)
class JobRouteAdmin(admin.ModelAdmin):
    list_display = ['job_card', 'template_used', 'total_planned_hours', 'total_actual_hours', 'is_complete']
    list_filter = ['is_complete']
    search_fields = ['job_card__job_card_number']
    inlines = [JobRouteStepInline]
    readonly_fields = ['total_planned_hours', 'total_actual_hours', 'is_complete']


@admin.register(JobRouteStep)
class JobRouteStepAdmin(admin.ModelAdmin):
    list_display = ['route', 'sequence', 'operation', 'status', 'operator', 'actual_start_at', 'actual_end_at']
    list_filter = ['status', 'operation', 'operator']
    search_fields = ['route__job_card__job_card_number', 'operation__name']
    readonly_fields = ['actual_duration_hours', 'wait_time_from_previous']


# Evaluation
class CutterLocationInline(admin.TabularInline):
    model = CutterLocation
    extra = 5
    fields = ['row', 'column', 'label', 'blade_number', 'position_on_blade', 'expected_cutter_type', 'is_critical']


@admin.register(CutterLayout)
class CutterLayoutAdmin(admin.ModelAdmin):
    list_display = ['design_revision', 'name', 'total_rows', 'total_columns', 'num_blades', 'is_active']
    list_filter = ['is_active']
    search_fields = ['design_revision__mat_number', 'name']
    inlines = [CutterLocationInline]


class JobCutterEvaluationDetailInline(admin.TabularInline):
    model = JobCutterEvaluationDetail
    extra = 0
    fields = ['row', 'column', 'symbol', 'condition_description', 'notes']
    ordering = ['row', 'column']


@admin.register(JobCutterEvaluationHeader)
class JobCutterEvaluationHeaderAdmin(admin.ModelAdmin):
    list_display = ['job_card', 'evaluation_type', 'revision_number', 'status', 'total_cutters', 'replace_count', 'repair_count', 'ok_count']
    list_filter = ['evaluation_type', 'status', 'evaluated_by']
    search_fields = ['job_card__job_card_number']
    inlines = [JobCutterEvaluationDetailInline]
    readonly_fields = ['total_cutters', 'replace_count', 'repair_count', 'ok_count', 'rotate_count', 'lost_count']


# Inspection
@admin.register(ApiThreadInspection)
class ApiThreadInspectionAdmin(admin.ModelAdmin):
    list_display = ['job_card', 'thread_type', 'result', 'damage_type', 'repair_completed', 'final_status', 'inspection_date']
    list_filter = ['result', 'damage_type', 'repair_completed', 'final_status', 'thread_type']
    search_fields = ['job_card__job_card_number']
    date_hierarchy = 'inspection_date'


@admin.register(NdtReport)
class NdtReportAdmin(admin.ModelAdmin):
    list_display = ['job_card', 'test_type', 'result', 'defect_severity', 'test_date', 'performed_by']
    list_filter = ['test_type', 'result', 'defect_severity']
    search_fields = ['job_card__job_card_number', 'report_number']
    date_hierarchy = 'test_date'


# Checklists
class JobChecklistItemInline(admin.TabularInline):
    model = JobChecklistItem
    extra = 0
    fields = ['sequence', 'text', 'is_mandatory', 'status', 'checked_by', 'checked_at']
    readonly_fields = ['checked_at']
    ordering = ['sequence']


@admin.register(JobChecklistInstance)
class JobChecklistInstanceAdmin(admin.ModelAdmin):
    list_display = ['job_card', 'name', 'status', 'completed_items', 'total_items', 'mandatory_completed', 'mandatory_items']
    list_filter = ['status', 'template']
    search_fields = ['job_card__job_card_number', 'name']
    inlines = [JobChecklistItemInline]
    readonly_fields = ['total_items', 'completed_items', 'mandatory_items', 'mandatory_completed']

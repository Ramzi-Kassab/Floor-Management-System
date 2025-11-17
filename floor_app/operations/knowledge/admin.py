"""
Admin interface for Knowledge & Instructions module.
Provides comprehensive management of articles, instructions, and training.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import (
    Category,
    Tag,
    Document,
    Article,
    ArticleAttachment,
    ArticleAcknowledgment,
    FAQGroup,
    FAQEntry,
    InstructionRule,
    RuleCondition,
    RuleAction,
    InstructionTargetScope,
    InstructionExecutionLog,
    TrainingCourse,
    TrainingLesson,
    TrainingEnrollment,
    TrainingLessonProgress,
    TrainingSchedule,
    TrainingScheduleRegistration,
)


# ========== Inlines ==========

class ArticleAttachmentInline(admin.TabularInline):
    model = ArticleAttachment
    extra = 1
    fields = ['document', 'usage_type', 'caption', 'order']
    autocomplete_fields = ['document']


class RuleConditionInline(admin.TabularInline):
    model = RuleCondition
    extra = 1
    fields = [
        'condition_group', 'order', 'target_model', 'field_path',
        'operator', 'value', 'value_max', 'logical_operator', 'case_sensitive'
    ]
    classes = ['collapse']


class RuleActionInline(admin.StackedInline):
    model = RuleAction
    extra = 1
    fields = [
        ('action_type', 'order', 'stop_propagation'),
        'message_template',
        ('target_field', 'value_expression'),
        'severity',
        'parameters',
        ('notify_users', 'notify_roles', 'notify_departments'),
    ]
    filter_horizontal = ['notify_users', 'notify_roles', 'notify_departments']
    classes = ['collapse']


class InstructionTargetScopeInline(admin.TabularInline):
    model = InstructionTargetScope
    extra = 1
    fields = [
        'scope_type', 'target_content_type', 'target_object_id',
        'field_filter', 'description', 'applies_to_new_only'
    ]
    classes = ['collapse']


class TrainingLessonInline(admin.TabularInline):
    model = TrainingLesson
    extra = 1
    fields = [
        'sequence', 'title', 'lesson_type', 'linked_article',
        'is_mandatory', 'estimated_minutes'
    ]
    autocomplete_fields = ['linked_article']
    show_change_link = True


class FAQEntryInline(admin.StackedInline):
    model = FAQEntry
    extra = 1
    fields = [
        ('question', 'order'),
        'answer',
        'short_answer',
        ('is_published', 'is_featured'),
        'keywords'
    ]


# ========== Category Admin ==========

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'parent', 'slug', 'icon', 'order', 'is_active',
        'article_count', 'is_deleted'
    ]
    list_filter = ['is_active', 'is_deleted', 'parent']
    search_fields = ['name', 'description', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['order', 'is_active']
    ordering = ['order', 'name']

    def article_count(self, obj):
        return obj.articles.filter(is_deleted=False).count()
    article_count.short_description = 'Articles'


# ========== Tag Admin ==========

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'color_badge', 'article_count', 'is_system']
    search_fields = ['name', 'slug', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ['is_system']

    def color_badge(self, obj):
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px;">{}</span>',
            obj.color, obj.name
        )
    color_badge.short_description = 'Color'


# ========== Document Admin ==========

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'file_type', 'version', 'file_size_display',
        'download_count', 'is_public', 'created_at', 'is_deleted'
    ]
    list_filter = ['file_type', 'is_public', 'is_deleted', 'created_at']
    search_fields = ['title', 'description', 'public_id']
    readonly_fields = [
        'public_id', 'file_size', 'file_size_display', 'mime_type',
        'checksum', 'download_count', 'created_at', 'updated_at',
        'created_by', 'updated_by'
    ]
    fieldsets = (
        ('Basic Info', {
            'fields': ('title', 'file', 'file_type', 'version', 'description')
        }),
        ('Access', {
            'fields': ('is_public', 'expires_at')
        }),
        ('Metadata', {
            'fields': (
                'public_id', 'file_size_display', 'mime_type',
                'checksum', 'source_system', 'external_url'
            ),
            'classes': ['collapse']
        }),
        ('Statistics', {
            'fields': ('download_count',),
            'classes': ['collapse']
        }),
        ('Audit', {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by'),
            'classes': ['collapse']
        }),
    )


# ========== Article Admin ==========

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'title', 'article_type', 'status_badge', 'priority_badge',
        'category', 'owner_department', 'view_count', 'is_featured',
        'published_at', 'needs_review_badge'
    ]
    list_filter = [
        'status', 'article_type', 'priority', 'is_featured', 'is_pinned',
        'category', 'owner_department', 'requires_acknowledgment',
        'created_at', 'published_at'
    ]
    search_fields = ['code', 'title', 'summary', 'body', 'public_id']
    prepopulated_fields = {'slug': ('code', 'title')}
    filter_horizontal = [
        'tags', 'related_articles', 'restricted_to_departments',
        'restricted_to_positions'
    ]
    autocomplete_fields = ['category', 'owner_department', 'previous_version']
    inlines = [ArticleAttachmentInline]
    date_hierarchy = 'created_at'
    list_editable = ['is_featured']
    actions = ['publish_articles', 'approve_articles', 'archive_articles']

    fieldsets = (
        ('Core Content', {
            'fields': (
                'code', 'slug', 'title', 'summary', 'body',
                'article_type', 'status', 'priority'
            )
        }),
        ('Organization', {
            'fields': ('category', 'tags', 'owner_department')
        }),
        ('Versioning', {
            'fields': ('version', 'previous_version', 'change_summary'),
            'classes': ['collapse']
        }),
        ('Workflow', {
            'fields': (
                ('reviewed_by', 'reviewed_at'),
                ('approved_by', 'approved_at'),
                'published_at'
            ),
            'classes': ['collapse']
        }),
        ('Validity', {
            'fields': ('effective_from', 'effective_until', 'review_due_date'),
            'classes': ['collapse']
        }),
        ('Display Options', {
            'fields': ('is_featured', 'is_pinned', 'view_count')
        }),
        ('Access Control', {
            'fields': (
                'requires_acknowledgment',
                'restricted_to_departments',
                'restricted_to_positions'
            ),
            'classes': ['collapse']
        }),
        ('Related Content', {
            'fields': ('related_articles',),
            'classes': ['collapse']
        }),
        ('Audit', {
            'fields': (
                'public_id', 'created_at', 'created_by',
                'updated_at', 'updated_by', 'remarks'
            ),
            'classes': ['collapse']
        }),
    )

    readonly_fields = [
        'public_id', 'view_count', 'created_at', 'created_by',
        'updated_at', 'updated_by'
    ]

    def status_badge(self, obj):
        colors = {
            'DRAFT': '#6b7280',
            'IN_REVIEW': '#f59e0b',
            'APPROVED': '#10b981',
            'PUBLISHED': '#3b82f6',
            'ARCHIVED': '#9ca3af',
            'SUPERSEDED': '#ef4444'
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def priority_badge(self, obj):
        colors = {
            'LOW': '#9ca3af',
            'NORMAL': '#3b82f6',
            'HIGH': '#f59e0b',
            'CRITICAL': '#ef4444'
        }
        color = colors.get(obj.priority, '#6b7280')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_priority_display()
        )
    priority_badge.short_description = 'Priority'

    def needs_review_badge(self, obj):
        if obj.needs_review:
            return format_html(
                '<span style="color: #ef4444; font-weight: bold;">REVIEW DUE</span>'
            )
        return '-'
    needs_review_badge.short_description = 'Review'

    def publish_articles(self, request, queryset):
        count = 0
        for article in queryset.filter(status='APPROVED'):
            article.status = 'PUBLISHED'
            article.published_at = timezone.now()
            article.save()
            count += 1
        self.message_user(request, f'{count} articles published.')
    publish_articles.short_description = 'Publish selected articles'

    def approve_articles(self, request, queryset):
        count = queryset.filter(status='IN_REVIEW').update(
            status='APPROVED',
            approved_by=request.user,
            approved_at=timezone.now()
        )
        self.message_user(request, f'{count} articles approved.')
    approve_articles.short_description = 'Approve selected articles'

    def archive_articles(self, request, queryset):
        count = queryset.update(status='ARCHIVED')
        self.message_user(request, f'{count} articles archived.')
    archive_articles.short_description = 'Archive selected articles'

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


# ========== FAQ Admin ==========

@admin.register(FAQGroup)
class FAQGroupAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'category', 'order', 'is_active',
        'active_entries_count', 'is_deleted'
    ]
    list_filter = ['is_active', 'is_deleted', 'category']
    search_fields = ['name', 'description']
    inlines = [FAQEntryInline]
    list_editable = ['order', 'is_active']


@admin.register(FAQEntry)
class FAQEntryAdmin(admin.ModelAdmin):
    list_display = [
        'question_short', 'group', 'is_published', 'is_featured',
        'view_count', 'helpfulness_score', 'order'
    ]
    list_filter = ['is_published', 'is_featured', 'group', 'is_deleted']
    search_fields = ['question', 'answer', 'keywords']
    list_editable = ['is_published', 'is_featured', 'order']

    def question_short(self, obj):
        return obj.question[:80] + '...' if len(obj.question) > 80 else obj.question
    question_short.short_description = 'Question'


# ========== Instruction Rule Admin (POWERFUL!) ==========

@admin.register(InstructionRule)
class InstructionRuleAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'title', 'instruction_type', 'priority_badge', 'status_badge',
        'is_default', 'is_temporary', 'validity_info', 'trigger_count',
        'last_triggered_at', 'execution_order'
    ]
    list_filter = [
        'status', 'instruction_type', 'priority', 'is_default',
        'is_temporary', 'owner_department', 'created_at'
    ]
    search_fields = ['code', 'title', 'description', 'short_description', 'public_id']
    filter_horizontal = ['attachments']
    autocomplete_fields = ['owner_department', 'source_article']
    inlines = [RuleConditionInline, RuleActionInline, InstructionTargetScopeInline]
    date_hierarchy = 'created_at'
    actions = ['activate_instructions', 'deactivate_instructions']
    list_editable = ['execution_order']

    fieldsets = (
        ('Basic Info', {
            'fields': (
                'code', 'title', 'short_description', 'description',
                'instruction_type', 'priority', 'status'
            )
        }),
        ('Validity', {
            'fields': (
                'is_default', 'is_temporary',
                ('valid_from', 'valid_until')
            )
        }),
        ('Organization', {
            'fields': ('owner_department', 'source_article', 'execution_order')
        }),
        ('Attachments', {
            'fields': ('attachments',),
            'classes': ['collapse']
        }),
        ('Approval', {
            'fields': (('approved_by', 'approved_at'),),
            'classes': ['collapse']
        }),
        ('Statistics', {
            'fields': ('trigger_count', 'last_triggered_at'),
            'classes': ['collapse']
        }),
        ('Audit', {
            'fields': (
                'public_id', 'created_at', 'created_by',
                'updated_at', 'updated_by', 'remarks'
            ),
            'classes': ['collapse']
        }),
    )

    readonly_fields = [
        'public_id', 'trigger_count', 'last_triggered_at',
        'created_at', 'created_by', 'updated_at', 'updated_by'
    ]

    def priority_badge(self, obj):
        colors = {
            'LOW': '#9ca3af',
            'NORMAL': '#3b82f6',
            'HIGH': '#f59e0b',
            'CRITICAL': '#ef4444',
            'MANDATORY': '#7c3aed'
        }
        color = colors.get(obj.priority, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_priority_display()
        )
    priority_badge.short_description = 'Priority'

    def status_badge(self, obj):
        colors = {
            'DRAFT': '#6b7280',
            'IN_REVIEW': '#f59e0b',
            'APPROVED': '#10b981',
            'ACTIVE': '#3b82f6',
            'INACTIVE': '#9ca3af',
            'ARCHIVED': '#ef4444'
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def validity_info(self, obj):
        if obj.is_temporary and obj.valid_until:
            days = obj.days_until_expiry
            if days == 0:
                return format_html('<span style="color: #ef4444;">EXPIRED</span>')
            elif days <= 7:
                return format_html(
                    '<span style="color: #f59e0b;">{}d left</span>', days
                )
            return f"{days}d left"
        elif obj.is_default:
            return "Default"
        return "-"
    validity_info.short_description = 'Validity'

    def activate_instructions(self, request, queryset):
        count = queryset.filter(status='APPROVED').update(status='ACTIVE')
        self.message_user(request, f'{count} instructions activated.')
    activate_instructions.short_description = 'Activate selected instructions'

    def deactivate_instructions(self, request, queryset):
        count = queryset.update(status='INACTIVE')
        self.message_user(request, f'{count} instructions deactivated.')
    deactivate_instructions.short_description = 'Deactivate selected instructions'

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(InstructionExecutionLog)
class InstructionExecutionLogAdmin(admin.ModelAdmin):
    list_display = [
        'instruction', 'executed_at', 'executed_by', 'trigger_event',
        'was_overridden', 'ip_address'
    ]
    list_filter = [
        'trigger_event', 'was_overridden', 'executed_at', 'instruction'
    ]
    search_fields = ['instruction__code', 'instruction__title', 'override_reason']
    readonly_fields = [
        'instruction', 'executed_at', 'executed_by', 'trigger_content_type',
        'trigger_object_id', 'trigger_event', 'conditions_evaluated',
        'actions_executed', 'was_overridden', 'override_reason',
        'override_approved_by', 'ip_address', 'user_agent'
    ]
    date_hierarchy = 'executed_at'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


# ========== Training Admin ==========

@admin.register(TrainingCourse)
class TrainingCourseAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'title', 'course_type', 'status', 'difficulty_level',
        'duration_display', 'is_mandatory', 'total_enrollments',
        'completion_rate_display', 'published_at'
    ]
    list_filter = [
        'status', 'course_type', 'difficulty_level', 'is_mandatory',
        'owner_department', 'created_at'
    ]
    search_fields = ['code', 'title', 'description', 'public_id']
    filter_horizontal = [
        'target_positions', 'target_departments', 'prerequisite_courses',
        'attachments'
    ]
    autocomplete_fields = ['owner_department', 'grants_qualification', 'cover_image']
    inlines = [TrainingLessonInline]
    date_hierarchy = 'created_at'
    list_editable = ['is_mandatory']

    fieldsets = (
        ('Basic Info', {
            'fields': (
                'code', 'title', 'description', 'objectives', 'prerequisites',
                'course_type', 'status', 'difficulty_level'
            )
        }),
        ('Timing', {
            'fields': ('estimated_duration_minutes', 'validity_months')
        }),
        ('Organization', {
            'fields': ('owner_department', 'cover_image')
        }),
        ('Target Audience', {
            'fields': ('target_positions', 'target_departments')
        }),
        ('Requirements', {
            'fields': (
                'is_mandatory', 'requires_assessment', 'passing_score',
                'max_attempts', 'allow_self_enrollment'
            )
        }),
        ('HR Integration', {
            'fields': ('grants_qualification',)
        }),
        ('Prerequisites', {
            'fields': ('prerequisite_courses',),
            'classes': ['collapse']
        }),
        ('Resources', {
            'fields': ('attachments',),
            'classes': ['collapse']
        }),
        ('Statistics', {
            'fields': (
                'total_enrollments', 'total_completions',
                'average_score', 'average_completion_time'
            ),
            'classes': ['collapse']
        }),
        ('Audit', {
            'fields': (
                'public_id', 'published_at', 'created_at', 'created_by',
                'updated_at', 'updated_by', 'remarks'
            ),
            'classes': ['collapse']
        }),
    )

    readonly_fields = [
        'public_id', 'total_enrollments', 'total_completions',
        'average_score', 'average_completion_time',
        'created_at', 'created_by', 'updated_at', 'updated_by'
    ]

    def completion_rate_display(self, obj):
        rate = obj.completion_rate
        color = '#10b981' if rate >= 70 else '#f59e0b' if rate >= 40 else '#ef4444'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color, rate
        )
    completion_rate_display.short_description = 'Completion'

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(TrainingLesson)
class TrainingLessonAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'course', 'sequence', 'lesson_type',
        'is_mandatory', 'estimated_minutes', 'linked_article'
    ]
    list_filter = ['lesson_type', 'is_mandatory', 'course']
    search_fields = ['title', 'description', 'course__code']
    autocomplete_fields = ['course', 'linked_article']
    filter_horizontal = ['attachments']


@admin.register(TrainingEnrollment)
class TrainingEnrollmentAdmin(admin.ModelAdmin):
    list_display = [
        'employee', 'course', 'status', 'progress_percentage',
        'final_score', 'enrolled_at', 'completed_at', 'expires_at',
        'certificate_issued'
    ]
    list_filter = [
        'status', 'certificate_issued', 'passed_assessment',
        'course', 'enrolled_at'
    ]
    search_fields = [
        'employee__user__username', 'course__code', 'course__title',
        'certificate_number'
    ]
    autocomplete_fields = ['employee', 'course']
    readonly_fields = [
        'enrolled_at', 'progress_percentage', 'lessons_completed',
        'total_time_spent_minutes', 'certificate_number', 'certificate_issued_at'
    ]
    date_hierarchy = 'enrolled_at'


@admin.register(TrainingSchedule)
class TrainingScheduleAdmin(admin.ModelAdmin):
    list_display = [
        'course', 'title', 'scheduled_date', 'start_time', 'end_time',
        'instructor', 'registered_count', 'available_spots', 'registration_open'
    ]
    list_filter = ['scheduled_date', 'registration_open', 'course']
    search_fields = ['title', 'course__code', 'location']
    autocomplete_fields = ['course', 'instructor']
    date_hierarchy = 'scheduled_date'

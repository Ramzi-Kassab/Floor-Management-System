# floor_app/operations/knowledge/views/__init__.py
"""
Views for Knowledge & Instructions module.
"""

from .dashboard import knowledge_dashboard, knowledge_stats_api
from .articles import (
    ArticleListView,
    ArticleDetailView,
    ArticleCreateView,
    ArticleUpdateView,
    article_acknowledge,
    article_publish,
    article_search_api,
)
from .categories import CategoryListView, category_detail
from .documents import (
    DocumentListView,
    DocumentUploadView,
    document_detail,
    document_download,
)
from .faq import faq_list, faq_mark_helpful
from .instructions import (
    InstructionListView,
    InstructionCreateView,
    InstructionUpdateView,
    instruction_detail,
    instruction_activate,
    get_available_models,
    get_model_fields,
    evaluate_instruction_preview,
    applicable_instructions_api,
)
from .training import (
    training_dashboard,
    TrainingCourseListView,
    course_detail,
    course_enroll,
    lesson_view,
    lesson_complete,
    my_training,
    enrollment_detail,
    TrainingScheduleListView,
    schedule_register,
)
from .search import global_search

__all__ = [
    # Dashboard
    'knowledge_dashboard',
    'knowledge_stats_api',
    # Articles
    'ArticleListView',
    'ArticleDetailView',
    'ArticleCreateView',
    'ArticleUpdateView',
    'article_acknowledge',
    'article_publish',
    'article_search_api',
    # Categories
    'CategoryListView',
    'category_detail',
    # Documents
    'DocumentListView',
    'DocumentUploadView',
    'document_detail',
    'document_download',
    # FAQ
    'faq_list',
    'faq_mark_helpful',
    # Instructions
    'InstructionListView',
    'InstructionCreateView',
    'InstructionUpdateView',
    'instruction_detail',
    'instruction_activate',
    'get_available_models',
    'get_model_fields',
    'evaluate_instruction_preview',
    'applicable_instructions_api',
    # Training
    'training_dashboard',
    'TrainingCourseListView',
    'course_detail',
    'course_enroll',
    'lesson_view',
    'lesson_complete',
    'my_training',
    'enrollment_detail',
    'TrainingScheduleListView',
    'schedule_register',
    # Search
    'global_search',
]

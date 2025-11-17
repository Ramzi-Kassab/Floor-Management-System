"""
URL configuration for Knowledge & Instructions module.
"""
from django.urls import path
from . import views

app_name = 'knowledge'

urlpatterns = [
    # ========== Dashboard ==========
    path('', views.knowledge_dashboard, name='dashboard'),

    # ========== Knowledge Center ==========
    path('articles/', views.ArticleListView.as_view(), name='article_list'),
    path('articles/create/', views.ArticleCreateView.as_view(), name='article_create'),
    path('articles/<slug:slug>/', views.ArticleDetailView.as_view(), name='article_detail'),
    path('articles/<slug:slug>/edit/', views.ArticleUpdateView.as_view(), name='article_edit'),
    path('articles/<int:pk>/acknowledge/', views.article_acknowledge, name='article_acknowledge'),
    path('articles/<int:pk>/publish/', views.article_publish, name='article_publish'),

    # ========== Categories ==========
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/<slug:slug>/', views.category_detail, name='category_detail'),

    # ========== FAQ ==========
    path('faq/', views.faq_list, name='faq_list'),
    path('faq/<int:pk>/helpful/', views.faq_mark_helpful, name='faq_mark_helpful'),

    # ========== Documents ==========
    path('documents/', views.DocumentListView.as_view(), name='document_list'),
    path('documents/upload/', views.DocumentUploadView.as_view(), name='document_upload'),
    path('documents/<uuid:public_id>/', views.document_detail, name='document_detail'),
    path('documents/<uuid:public_id>/download/', views.document_download, name='document_download'),

    # ========== Instructions Engine ==========
    path('instructions/', views.InstructionListView.as_view(), name='instruction_list'),
    path('instructions/create/', views.InstructionCreateView.as_view(), name='instruction_create'),
    path('instructions/<str:code>/', views.instruction_detail, name='instruction_detail'),
    path('instructions/<int:pk>/edit/', views.InstructionUpdateView.as_view(), name='instruction_edit'),
    path('instructions/<int:pk>/activate/', views.instruction_activate, name='instruction_activate'),

    # Instruction Builder (AJAX endpoints)
    path('api/models/', views.get_available_models, name='api_models'),
    path('api/models/<int:ct_id>/fields/', views.get_model_fields, name='api_model_fields'),
    path('api/instructions/evaluate/', views.evaluate_instruction_preview, name='api_evaluate'),

    # ========== Training Center ==========
    path('training/', views.training_dashboard, name='training_dashboard'),
    path('training/courses/', views.TrainingCourseListView.as_view(), name='course_list'),
    path('training/courses/<str:code>/', views.course_detail, name='course_detail'),
    path('training/courses/<str:code>/enroll/', views.course_enroll, name='course_enroll'),
    path('training/courses/<str:code>/lesson/<int:sequence>/', views.lesson_view, name='lesson_view'),
    path('training/courses/<str:code>/lesson/<int:sequence>/complete/', views.lesson_complete, name='lesson_complete'),

    path('training/my-courses/', views.my_training, name='my_training'),
    path('training/enrollment/<int:pk>/', views.enrollment_detail, name='enrollment_detail'),

    # Training Admin
    path('training/schedules/', views.TrainingScheduleListView.as_view(), name='schedule_list'),
    path('training/schedules/<int:pk>/register/', views.schedule_register, name='schedule_register'),

    # ========== Search ==========
    path('search/', views.global_search, name='search'),

    # ========== API Endpoints ==========
    path('api/stats/', views.knowledge_stats_api, name='api_stats'),
    path('api/articles/search/', views.article_search_api, name='api_article_search'),
    path('api/instructions/applicable/<str:model>/<int:object_id>/', views.applicable_instructions_api, name='api_applicable_instructions'),
]

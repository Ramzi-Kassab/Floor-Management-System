from django.urls import path
from . import views

app_name = 'evaluation'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Session CRUD
    path('sessions/', views.EvaluationSessionListView.as_view(), name='session_list'),
    path('sessions/create/', views.EvaluationSessionCreateView.as_view(), name='session_create'),
    path('sessions/<int:pk>/', views.EvaluationSessionDetailView.as_view(), name='session_detail'),
    path('sessions/<int:pk>/edit/', views.EvaluationSessionUpdateView.as_view(), name='session_edit'),

    # Cell grid editor
    path('sessions/<int:pk>/grid/', views.grid_editor, name='grid_editor'),
    path('sessions/<int:pk>/save-cell/', views.save_cell, name='save_cell'),

    # Thread inspection
    path('sessions/<int:pk>/thread/', views.thread_inspection, name='thread_inspection'),
    path('sessions/<int:pk>/thread/save/', views.save_thread_inspection, name='save_thread_inspection'),

    # NDT inspection
    path('sessions/<int:pk>/ndt/', views.ndt_inspection, name='ndt_inspection'),
    path('sessions/<int:pk>/ndt/save/', views.save_ndt_inspection, name='save_ndt_inspection'),

    # Technical Instructions
    path('sessions/<int:pk>/instructions/', views.instructions_list, name='instructions_list'),
    path('instructions/<int:inst_pk>/accept/', views.accept_instruction, name='accept_instruction'),
    path('instructions/<int:inst_pk>/reject/', views.reject_instruction, name='reject_instruction'),

    # Requirements
    path('sessions/<int:pk>/requirements/', views.requirements_list, name='requirements_list'),
    path('requirements/<int:req_pk>/satisfy/', views.satisfy_requirement, name='satisfy_requirement'),

    # Engineer review and approval
    path('sessions/<int:pk>/review/', views.engineer_review, name='engineer_review'),
    path('sessions/<int:pk>/approve/', views.approve_session, name='approve_session'),
    path('sessions/<int:pk>/lock/', views.lock_session, name='lock_session'),

    # Print views
    path('sessions/<int:pk>/print/', views.print_job_card, name='print_job_card'),
    path('sessions/<int:pk>/print/summary/', views.print_summary, name='print_summary'),

    # History
    path('sessions/<int:pk>/history/', views.history_view, name='history_view'),

    # Settings
    path('settings/', views.settings_dashboard, name='settings_dashboard'),
    path('settings/codes/', views.CodeListView.as_view(), name='code_list'),
    path('settings/features/', views.FeatureListView.as_view(), name='feature_list'),
    path('settings/sections/', views.SectionListView.as_view(), name='section_list'),
    path('settings/types/', views.TypeListView.as_view(), name='type_list'),
    path('settings/instruction-templates/', views.InstructionTemplateListView.as_view(), name='instruction_template_list'),
    path('settings/requirement-templates/', views.RequirementTemplateListView.as_view(), name='requirement_template_list'),
]

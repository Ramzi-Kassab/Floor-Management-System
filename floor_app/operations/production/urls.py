from django.urls import path
from . import views

app_name = 'production'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Batch Orders
    path('batches/', views.BatchListView.as_view(), name='batch_list'),
    path('batches/create/', views.BatchCreateView.as_view(), name='batch_create'),
    path('batches/<int:pk>/', views.BatchDetailView.as_view(), name='batch_detail'),
    path('batches/<int:pk>/edit/', views.BatchUpdateView.as_view(), name='batch_edit'),

    # Job Cards
    path('jobcards/', views.JobCardListView.as_view(), name='jobcard_list'),
    path('jobcards/create/', views.JobCardCreateView.as_view(), name='jobcard_create'),
    path('jobcards/<int:pk>/', views.JobCardDetailView.as_view(), name='jobcard_detail'),
    path('jobcards/<int:pk>/edit/', views.JobCardUpdateView.as_view(), name='jobcard_edit'),

    # Job Card Actions
    path('jobcards/<int:pk>/start-evaluation/', views.jobcard_start_evaluation, name='jobcard_start_evaluation'),
    path('jobcards/<int:pk>/complete-evaluation/', views.jobcard_complete_evaluation, name='jobcard_complete_evaluation'),
    path('jobcards/<int:pk>/release/', views.jobcard_release, name='jobcard_release'),
    path('jobcards/<int:pk>/start-production/', views.jobcard_start_production, name='jobcard_start_production'),
    path('jobcards/<int:pk>/complete/', views.jobcard_complete, name='jobcard_complete'),

    # Routing
    path('jobcards/<int:pk>/route/', views.route_editor, name='route_editor'),
    path('jobcards/<int:pk>/route/add-step/', views.route_add_step, name='route_add_step'),
    path('route-steps/<int:step_pk>/start/', views.route_step_start, name='route_step_start'),
    path('route-steps/<int:step_pk>/complete/', views.route_step_complete, name='route_step_complete'),
    path('route-steps/<int:step_pk>/skip/', views.route_step_skip, name='route_step_skip'),

    # Cutter Evaluation
    path('jobcards/<int:pk>/evaluation/', views.evaluation_list, name='evaluation_list'),
    path('jobcards/<int:pk>/evaluation/create/', views.evaluation_create, name='evaluation_create'),
    path('evaluations/<int:eval_pk>/', views.evaluation_detail, name='evaluation_detail'),
    path('evaluations/<int:eval_pk>/edit/', views.evaluation_edit, name='evaluation_edit'),
    path('evaluations/<int:eval_pk>/submit/', views.evaluation_submit, name='evaluation_submit'),
    path('evaluations/<int:eval_pk>/approve/', views.evaluation_approve, name='evaluation_approve'),

    # NDT & Thread Inspection
    path('jobcards/<int:pk>/ndt/', views.ndt_list, name='ndt_list'),
    path('jobcards/<int:pk>/ndt/create/', views.NdtCreateView.as_view(), name='ndt_create'),
    path('ndt/<int:ndt_pk>/', views.ndt_detail, name='ndt_detail'),
    path('ndt/<int:ndt_pk>/edit/', views.NdtUpdateView.as_view(), name='ndt_edit'),

    path('jobcards/<int:pk>/thread-inspection/', views.thread_inspection_list, name='thread_inspection_list'),
    path('jobcards/<int:pk>/thread-inspection/create/', views.ThreadInspectionCreateView.as_view(), name='thread_inspection_create'),
    path('thread-inspections/<int:insp_pk>/', views.thread_inspection_detail, name='thread_inspection_detail'),
    path('thread-inspections/<int:insp_pk>/edit/', views.ThreadInspectionUpdateView.as_view(), name='thread_inspection_edit'),
    path('thread-inspections/<int:insp_pk>/complete-repair/', views.thread_inspection_complete_repair, name='thread_inspection_complete_repair'),

    # Checklists
    path('jobcards/<int:pk>/checklists/', views.checklist_list, name='checklist_list'),
    path('checklists/<int:checklist_pk>/', views.checklist_detail, name='checklist_detail'),
    path('checklist-items/<int:item_pk>/complete/', views.checklist_item_complete, name='checklist_item_complete'),

    # Settings
    path('settings/', views.settings_dashboard, name='settings'),
    path('settings/operations/', views.OperationListView.as_view(), name='operation_list'),
    path('settings/symbols/', views.SymbolListView.as_view(), name='symbol_list'),
    path('settings/checklist-templates/', views.ChecklistTemplateListView.as_view(), name='checklist_template_list'),
]

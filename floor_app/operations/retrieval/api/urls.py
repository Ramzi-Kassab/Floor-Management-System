"""REST API URLs for Retrieval System"""
from django.urls import path
from . import views

urlpatterns = [
    # Retrieval requests
    path('requests/', views.RetrievalRequestListView.as_view(), name='retrieval-request-list'),
    path('requests/<int:pk>/', views.RetrievalRequestDetailView.as_view(), name='retrieval-request-detail'),
    path('requests/create/', views.CreateRetrievalRequestView.as_view(), name='create-retrieval-request'),
    path('requests/<int:pk>/approve/', views.ApproveRetrievalView.as_view(), name='approve-retrieval'),
    path('requests/<int:pk>/reject/', views.RejectRetrievalView.as_view(), name='reject-retrieval'),
    path('requests/<int:pk>/cancel/', views.CancelRetrievalView.as_view(), name='cancel-retrieval'),
    path('requests/<int:pk>/complete/', views.CompleteRetrievalView.as_view(), name='complete-retrieval'),

    # Supervisor endpoints
    path('supervisor/pending/', views.SupervisorPendingRequestsView.as_view(), name='supervisor-pending'),

    # Metrics
    path('metrics/employee/<int:user_id>/', views.EmployeeMetricsView.as_view(), name='employee-metrics'),
    path('metrics/department/<str:department>/', views.DepartmentMetricsView.as_view(), name='department-metrics'),

    # Check if object can be retrieved
    path('check/<str:content_type>/<int:object_id>/', views.CheckRetrievableView.as_view(), name='check-retrievable'),
]

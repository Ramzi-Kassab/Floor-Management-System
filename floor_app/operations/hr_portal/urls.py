"""
HR Portal URLs

URL patterns for employee self-service portal.
"""
from django.urls import path
from . import views

app_name = 'hr_portal'

urlpatterns = [
    # Portal Dashboard
    path('', views.portal_dashboard, name='dashboard'),

    # My Information
    path('my-leave/', views.my_leave, name='my_leave'),
    path('my-requests/', views.my_requests, name='my_requests'),
    path('my-requests/submit/', views.submit_request, name='submit_request'),
    path('my-documents/', views.my_documents, name='my_documents'),
    path('my-training/', views.my_training, name='my_training'),
]

"""
Hiring & Recruitment System URL Configuration
"""

from django.urls import path
from . import views

app_name = 'hiring'

urlpatterns = [
    # Job Postings
    path('jobs/', views.job_list, name='job_list'),

    # Candidates
    path('candidates/', views.candidate_list, name='candidate_list'),

    # Applications
    path('application/<int:pk>/', views.application_detail, name='application_detail'),

    # Interviews
    path('interviews/', views.interview_scheduler, name='interview_scheduler'),

    # Offers
    path('offers/', views.offer_list, name='offer_list'),
]

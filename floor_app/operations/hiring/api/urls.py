"""Hiring URLs"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import JobPostingViewSet, JobApplicationViewSet, InterviewViewSet, JobOfferViewSet

router = DefaultRouter()
router.register(r'jobs', JobPostingViewSet, basename='job')
router.register(r'applications', JobApplicationViewSet, basename='application')
router.register(r'interviews', InterviewViewSet, basename='interview')
router.register(r'offers', JobOfferViewSet, basename='offer')

urlpatterns = [path('', include(router.urls))]

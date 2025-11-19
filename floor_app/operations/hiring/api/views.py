"""Hiring Views"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from floor_app.operations.hiring.models import JobPosting, JobApplication, Interview, JobOffer
from floor_app.operations.hiring.services import HiringService
from .serializers import *

class JobPostingViewSet(viewsets.ModelViewSet):
    queryset = JobPosting.objects.filter(status='PUBLISHED')
    serializer_class = JobPostingSerializer

    def get_permissions(self):
        if self.action == 'list' or self.action == 'retrieve':
            return [AllowAny()]
        return [IsAuthenticated()]

class JobApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = JobApplicationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return JobApplication.objects.select_related('job_posting', 'candidate')

    @action(detail=False, methods=['post'], permission_classes=[AllowAny], url_path='submit/(?P<job_id>[^/.]+)')
    def submit_application(self, request, job_id=None):
        candidate_data = request.data.get('candidate', {})
        application_data = request.data.get('application', {})
        application = HiringService.submit_application(int(job_id), candidate_data, application_data)
        return Response(JobApplicationSerializer(application).data, status=status.HTTP_201_CREATED)

class InterviewViewSet(viewsets.ModelViewSet):
    queryset = Interview.objects.all()
    serializer_class = InterviewSerializer
    permission_classes = [IsAuthenticated]

class JobOfferViewSet(viewsets.ModelViewSet):
    queryset = JobOffer.objects.all()
    serializer_class = JobOfferSerializer
    permission_classes = [IsAuthenticated]

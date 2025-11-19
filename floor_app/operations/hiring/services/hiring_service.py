"""Hiring Service"""
from typing import Dict, Any
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from floor_app.operations.hiring.models import JobPosting, Candidate, JobApplication, Interview, JobOffer

User = get_user_model()

class HiringService:
    @classmethod
    def generate_job_code(cls) -> str:
        year = timezone.now().year
        prefix = f"JOB-{year}-"
        last_job = JobPosting.objects.filter(job_code__startswith=prefix).order_by('-job_code').first()
        new_number = 1 if not last_job else int(last_job.job_code.split('-')[-1]) + 1
        return f"{prefix}{new_number:04d}"

    @classmethod
    @transaction.atomic
    def create_job_posting(cls, posted_by: User, data: Dict[str, Any]) -> JobPosting:
        return JobPosting.objects.create(job_code=cls.generate_job_code(), posted_by=posted_by, **data)

    @classmethod
    @transaction.atomic
    def submit_application(cls, job_id: int, candidate_data: Dict[str, Any], application_data: Dict[str, Any]) -> JobApplication:
        candidate, _ = Candidate.objects.get_or_create(email=candidate_data['email'], defaults=candidate_data)
        job = JobPosting.objects.get(id=job_id)

        app_number = f"APP-{job.job_code}-{candidate.id}"
        return JobApplication.objects.create(
            application_number=app_number,
            job_posting=job,
            candidate=candidate,
            **application_data
        )

    @classmethod
    @transaction.atomic
    def schedule_interview(cls, application_id: int, interview_data: Dict[str, Any]) -> Interview:
        application = JobApplication.objects.get(id=application_id)
        interview = Interview.objects.create(application=application, **interview_data)
        application.status = 'INTERVIEW'
        application.save()
        return interview

    @classmethod
    @transaction.atomic
    def send_offer(cls, application_id: int, offer_data: Dict[str, Any]) -> JobOffer:
        application = JobApplication.objects.get(id=application_id)
        offer_number = f"OFFER-{application.application_number}"
        offer = JobOffer.objects.create(
            offer_number=offer_number,
            application=application,
            sent_date=timezone.now().date(),
            status='SENT',
            **offer_data
        )
        application.status = 'OFFER'
        application.save()
        return offer

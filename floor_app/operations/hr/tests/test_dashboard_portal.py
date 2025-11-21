from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from floor_app.operations.hr.models import HREmployee, Department, Position, HRPeople
from floor_app.operations.hr.models.training import TrainingSession


class HRDashboardAndPortalTests(TestCase):
    fixtures = ["hr_sample_data.json"]

    def setUp(self):
        self.client = Client()
        user = get_user_model().objects.get(username="hrdemo")
        self.client.force_login(user)

    def test_dashboard_context_counts(self):
        response = self.client.get(reverse("hr:dashboard"), follow=True)
        self.assertEqual(response.status_code, 200)

        context = response.context
        self.assertEqual(context["summary"]["total_employees"], HREmployee.objects.filter(is_deleted=False).count())
        self.assertEqual(context["org"]["departments"], Department.objects.count())
        self.assertGreaterEqual(len(context["pending_leave_requests"]), 1)

        upcoming = TrainingSession.objects.filter(start_date__gte=timezone.now().date())
        self.assertEqual(list(context["upcoming_trainings"]), list(upcoming[:4]))

    def test_employee_portal_profile(self):
        employee = HREmployee.objects.get(employee_no="EMP-9001")
        person = HRPeople.objects.get(pk=employee.person_id)
        position = Position.objects.get(pk=employee.position_id)

        response = self.client.get(reverse("hr:employee_portal"), follow=True)
        self.assertEqual(response.status_code, 200)

        context = response.context
        self.assertEqual(context["employee"].pk, employee.pk)
        self.assertEqual(context["person"].pk, person.pk)
        self.assertEqual(context["employee"].position, position)
        self.assertTrue(context["active_leave_requests"].exists())
        self.assertTrue(context["expiring_documents"].exists())

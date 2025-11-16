from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from floor_app.operations.hr.models import HREmployee, Department

@login_required
def main_dashboard(request):
    hr_summary = {
        "employees": HREmployee.objects.filter(is_deleted=False).count(),
        "departments": Department.objects.count(),
    }
    return render(request, "core/main_dashboard.html", {"hr_summary": hr_summary})



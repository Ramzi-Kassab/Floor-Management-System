from django.urls import path
from django.views.generic import TemplateView

app_name = "planning"

urlpatterns = [
    path("dashboard/", TemplateView.as_view(template_name="base.html"), name="dashboard"),
    path("schedules/", TemplateView.as_view(template_name="base.html"), name="schedule_list"),
    path("schedules/new/", TemplateView.as_view(template_name="base.html"), name="schedule_create"),
    path("resources/", TemplateView.as_view(template_name="base.html"), name="resource_list"),
    path("resources/new/", TemplateView.as_view(template_name="base.html"), name="resource_create"),
    path("resources/<int:pk>/", TemplateView.as_view(template_name="base.html"), name="resource_detail"),
    path("resources/<int:pk>/edit/", TemplateView.as_view(template_name="base.html"), name="resource_edit"),
    path("kpis/", TemplateView.as_view(template_name="base.html"), name="kpi_list"),
    path("kpis/new/", TemplateView.as_view(template_name="base.html"), name="kpi_create"),
    path("kpis/<int:pk>/", TemplateView.as_view(template_name="base.html"), name="kpi_detail"),
    path("kpis/<int:pk>/edit/", TemplateView.as_view(template_name="base.html"), name="kpi_edit"),
    path("kpis/dashboard/", TemplateView.as_view(template_name="base.html"), name="kpi_dashboard"),
    path("kpis/record/", TemplateView.as_view(template_name="base.html"), name="kpi_value_record"),
    path("capacity/", TemplateView.as_view(template_name="base.html"), name="capacity_overview"),
    path("wip/", TemplateView.as_view(template_name="base.html"), name="wip_board"),
    path("forecasts/", TemplateView.as_view(template_name="base.html"), name="forecast_list"),
    path("forecasts/new/", TemplateView.as_view(template_name="base.html"), name="forecast_create"),
    path("forecasts/<int:pk>/", TemplateView.as_view(template_name="base.html"), name="forecast_detail"),
    path("forecasts/<int:pk>/edit/", TemplateView.as_view(template_name="base.html"), name="forecast_edit"),
    path("reports/", TemplateView.as_view(template_name="base.html"), name="reports_dashboard"),
    path("settings/", TemplateView.as_view(template_name="base.html"), name="settings_dashboard"),
    path("bottleneck/", TemplateView.as_view(template_name="base.html"), name="bottleneck_analysis"),
]

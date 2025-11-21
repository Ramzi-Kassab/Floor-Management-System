from django.urls import path
from django.views.generic import TemplateView

app_name = "sales"

def stub_view():
    return TemplateView.as_view(template_name="base.html")

urlpatterns = [
    path("dashboard/", stub_view(), name="dashboard"),
    path("customers/", stub_view(), name="customer_list"),
    path("opportunities/", stub_view(), name="opportunity_list"),
    path("orders/", stub_view(), name="order_list"),
    path("rigs/", stub_view(), name="rig_list"),
    path("wells/", stub_view(), name="well_list"),
    path("drilling/", stub_view(), name="drilling_list"),
    path("dullgrades/", stub_view(), name="dullgrade_list"),
    path("lifecycle/", stub_view(), name="lifecycle_timeline"),
    path("shipments/", stub_view(), name="shipment_list"),
]

from django.urls import path
from . import views

app_name = "core"  # 🔑 this is the namespace used in {% url 'core:home' %}

urlpatterns = [
    path("", views.main_dashboard, name="home"),
]

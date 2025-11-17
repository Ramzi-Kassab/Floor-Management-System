from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from floor_app import views as floor_views

urlpatterns = [
    # === Main global dashboard (CORE) ===
    # "/" will now use core.main_dashboard and namespace "core"
    path("", include(("core.urls", "core"), namespace="core")),

    # === Authentication ===
    path("signup/", floor_views.signup, name="signup"),
    path("accounts/login/", floor_views.CustomLoginView.as_view(), name="login"),
    path("accounts/logout/", floor_views.CustomLogoutView.as_view(), name="logout"),
    path("accounts/password_reset/", floor_views.CustomPasswordResetView.as_view(), name="password_reset"),
    path("accounts/password_reset/done/", include("django.contrib.auth.urls")),
    path("accounts/reset/<uidb64>/<token>/", floor_views.CustomPasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("accounts/reset/done/", include("django.contrib.auth.urls")),
    path("accounts/", include("django.contrib.auth.urls")),

    # === (Legacy) Employee Management at /employees/ ===
    # These are your old floor_app views; you can keep them for now
    # while we migrate everything into the HR module.
    path("employees/", floor_views.employee_list, name="employee_list"),
    path("employees/<int:pk>/", floor_views.employee_detail, name="employee_detail"),

    # === Admin ===
    path("admin/", admin.site.urls),

    # === HR / Operations module ===
    # All HR URLs under "/hr/" and namespaced as "hr"
    path("hr/", include(("floor_app.operations.hr.urls", "hr"), namespace="hr")),

    # === Inventory / Materials Management ===
    path("inventory/", include(("floor_app.operations.inventory.urls", "inventory"), namespace="inventory")),

    # === Production & Evaluation ===
    path("production/", include(("floor_app.operations.production.urls", "production"), namespace="production")),

    # === Evaluation & Technical Instructions ===
    path("evaluation/", include(("floor_app.operations.evaluation.urls", "evaluation"), namespace="evaluation")),

    # === QR Codes & Scanning ===
    path("qrcodes/", include(("floor_app.operations.qrcodes.urls", "qrcodes"), namespace="qrcodes")),

    # === Purchasing & Logistics ===
    path("purchasing/", include(("floor_app.operations.purchasing.urls", "purchasing"), namespace="purchasing")),

    # === Knowledge & Instructions ===
    path("knowledge/", include(("floor_app.operations.knowledge.urls", "knowledge"), namespace="knowledge")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


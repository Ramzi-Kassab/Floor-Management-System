from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from floor_app import views as floor_views

urlpatterns = [
    # Home/Dashboard
    path("", floor_views.home, name="home"),

    # Authentication
    path("signup/", floor_views.signup, name="signup"),
    path("accounts/login/", floor_views.CustomLoginView.as_view(), name="login"),
    path("accounts/logout/", floor_views.CustomLogoutView.as_view(), name="logout"),
    path("accounts/password_reset/", floor_views.CustomPasswordResetView.as_view(), name="password_reset"),
    path("accounts/password_reset/done/", include("django.contrib.auth.urls")),
    path("accounts/reset/<uidb64>/<token>/", floor_views.CustomPasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("accounts/reset/done/", include("django.contrib.auth.urls")),
    path("accounts/", include("django.contrib.auth.urls")),

    # Employee Management
    path("employees/", floor_views.employee_list, name="employee_list"),
    path("employees/<int:pk>/", floor_views.employee_detail, name="employee_detail"),

    # Admin
    path("admin/", admin.site.urls),

    # Operations (HR) App
    path("hr/", include("floor_app.operations.hr.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

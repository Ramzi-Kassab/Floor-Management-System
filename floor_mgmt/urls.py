from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from floor_app import views as floor_views

urlpatterns = [
    # === Skeleton: Auth, Dashboard, Landing Page ===
    # Handles /, /dashboard/, /login/, /logout/, /account/, etc.
    path("", include(("skeleton.urls", "skeleton"), namespace="skeleton")),

    # === Admin ===
    path("admin/", admin.site.urls),

    # === Core utilities (if needed) ===
    path("core/", include(("core.urls", "core"), namespace="core")),

    # === Core System Monitoring & Audit ===
    # Dashboard, logs, monitoring, and system health
    path("system/", include(("floor_app.core.urls", "floor_core"), namespace="floor_core")),

    # === (Legacy) Employee Management at /employees/ ===
    # Keep for backwards compatibility during transition
    path("employees/", floor_views.employee_list, name="employee_list"),
    path("employees/<int:pk>/", floor_views.employee_detail, name="employee_detail"),

    # === HR / Operations module ===
    # All HR URLs under "/hr/" and namespaced as "hr"
    path("hr/", include(("floor_app.operations.hr.urls", "hr"), namespace="hr")),

    # === HR Employee Portal ===
    # Employee self-service portal under "/portal/"
    path("portal/", include(("floor_app.operations.hr_portal.urls", "hr_portal"), namespace="hr_portal")),

    # === Inventory / Materials Management ===
    path("inventory/", include(("floor_app.operations.inventory.urls", "inventory"), namespace="inventory")),

    # === Engineering / Design & BOM ===
    path("engineering/", include(("floor_app.operations.engineering.urls", "engineering"), namespace="engineering")),

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

    # === Maintenance & Asset Management ===
    path("maintenance/", include(("floor_app.operations.maintenance.urls", "maintenance"), namespace="maintenance")),

    # === Quality Management ===
    path("quality/", include(("floor_app.operations.quality.urls", "quality"), namespace="quality")),

    # === Planning & KPI ===
    path("planning/", include(("floor_app.operations.planning.urls", "planning"), namespace="planning")),

    # === Sales, Lifecycle & Drilling Operations ===
    path("sales/", include(("floor_app.operations.sales.urls", "sales"), namespace="sales")),

    # === Analytics & Activity Monitoring ===
    path("analytics/", include(("floor_app.operations.analytics.urls", "analytics"), namespace="analytics")),

    # === NEW SYSTEMS - Template-Based Views ===
    # Notifications System
    path("notifications/", include(("floor_app.operations.notifications.urls", "notifications"), namespace="notifications")),

    # Approval Workflows
    path("approvals/", include(("floor_app.operations.approvals.urls", "approvals"), namespace="approvals")),

    # Device Tracking
    path("devices/", include(("floor_app.operations.device_tracking.urls", "device_tracking"), namespace="device_tracking")),

    # GPS Verification System
    path("gps/", include(("floor_app.operations.gps_system.urls", "gps_system"), namespace="gps_system")),

    # QR Code System (Enhanced)
    path("qr/", include(("floor_app.operations.qr_system.urls", "qr_system"), namespace="qr_system")),

    # Chat & Messaging
    path("chat/", include(("floor_app.operations.chat.urls", "chat"), namespace="chat")),

    # Data Extraction
    path("data-extraction/", include(("floor_app.operations.data_extraction.urls", "data_extraction"), namespace="data_extraction")),

    # 5S/FIVES System
    path("fives/", include(("floor_app.operations.fives.urls", "fives"), namespace="fives")),

    # HR Assets Management
    path("hr-assets/", include(("floor_app.operations.hr_assets.urls", "hr_assets"), namespace="hr_assets")),

    # Hiring & Recruitment
    path("hiring/", include(("floor_app.operations.hiring.urls", "hiring"), namespace="hiring")),

    # Hazard Observation Cards (HOC)
    path("hoc/", include(("floor_app.operations.hoc.urls", "hoc"), namespace="hoc")),

    # Journey Management
    path("journey/", include(("floor_app.operations.journey_management.urls", "journey_management"), namespace="journey_management")),

    # Meetings
    path("meetings/", include(("floor_app.operations.meetings.urls", "meetings"), namespace="meetings")),

    # User Preferences
    path("preferences/", include(("floor_app.operations.user_preferences.urls", "user_preferences"), namespace="user_preferences")),

    # Utility Tools
    path("utils/", include(("floor_app.operations.utility_tools.urls", "utility_tools"), namespace="utility_tools")),

    # Vendor Portal
    path("vendors/", include(("floor_app.operations.vendor_portal.urls", "vendor_portal"), namespace="vendor_portal")),

    # Retrieval/Undo System (Cross-cutting feature)
    path("retrieval/", include(("floor_app.operations.retrieval.urls", "retrieval"), namespace="retrieval")),

    # === REST API Endpoints ===
    # Core System API (Audit, Activity, Monitoring, Notifications)
    path("api/core/", include("floor_app.core.api.urls")),

    # HR API
    path("api/hr/", include("floor_app.operations.hr.api.urls")),

    # Other APIs
    path("api/hoc/", include("floor_app.operations.hoc.api.urls")),
    path("api/journey-management/", include("floor_app.operations.journey_management.api.urls")),
    path("api/hr-assets/", include("floor_app.operations.hr_assets.api.urls")),
    path("api/meetings/", include("floor_app.operations.meetings.api.urls")),
    path("api/fives/", include("floor_app.operations.fives.api.urls")),
    path("api/vendor-portal/", include("floor_app.operations.vendor_portal.api.urls")),
    path("api/hiring/", include("floor_app.operations.hiring.api.urls")),
    path("api/chat/", include("floor_app.operations.chat.api.urls")),
    path("api/data-extraction/", include("floor_app.operations.data_extraction.api.urls")),
    path("api/notifications/", include("floor_app.operations.notifications.api.urls")),
    path("api/approvals/", include("floor_app.operations.approvals.api.urls")),
    path("api/device-tracking/", include("floor_app.operations.device_tracking.api.urls")),
    path("api/gps/", include("floor_app.operations.gps_system.api.urls")),
    path("api/qr/", include("floor_app.operations.qr_system.api.urls")),
    path("api/retrieval/", include("floor_app.operations.retrieval.api.urls")),
    # path("api/utility-tools/", include("floor_app.operations.utility_tools.api.urls")),  # TODO: Install openpyxl
    # path("api/user-preferences/", include("floor_app.operations.user_preferences.api.urls")),  # TODO: Check dependencies
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

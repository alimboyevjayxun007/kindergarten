from __future__ import annotations

from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("healthz/", views.health_check, name="health_check"),
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path(
        "kindergarten/location/",
        views.KindergartenLocationUpdateView.as_view(),
        name="kindergarten_location",
    ),
    path("classrooms/", views.ClassroomListView.as_view(), name="classroom_list"),
    path(
        "classrooms/create/",
        views.ClassroomCreateView.as_view(),
        name="classroom_create",
    ),
    path(
        "classrooms/<int:pk>/edit/",
        views.ClassroomUpdateView.as_view(),
        name="classroom_update",
    ),
    path(
        "classrooms/<int:pk>/delete/",
        views.ClassroomDeleteView.as_view(),
        name="classroom_delete",
    ),
    path("children/", views.ChildListView.as_view(), name="child_list"),
    path("children/create/", views.ChildCreateView.as_view(), name="child_create"),
    path("children/<int:pk>/edit/", views.ChildUpdateView.as_view(), name="child_update"),
    path(
        "children/<int:pk>/delete/",
        views.ChildDeleteView.as_view(),
        name="child_delete",
    ),
    path("guardians/", views.GuardianListView.as_view(), name="guardian_list"),
    path(
        "guardians/create/",
        views.GuardianCreateView.as_view(),
        name="guardian_create",
    ),
    path(
        "guardians/<int:pk>/edit/",
        views.GuardianUpdateView.as_view(),
        name="guardian_update",
    ),
    path(
        "guardians/<int:pk>/delete/",
        views.GuardianDeleteView.as_view(),
        name="guardian_delete",
    ),
	path("tariffs/", views.TariffListView.as_view(), name="tariff_list"),
	path("tariffs/create/", views.TariffCreateView.as_view(), name="tariff_create"),
	path("tariffs/<int:pk>/edit/", views.TariffUpdateView.as_view(), name="tariff_update"),
	path("tariffs/<int:pk>/delete/", views.TariffDeleteView.as_view(), name="tariff_delete"),
    path("attendance/", views.AttendanceListView.as_view(), name="attendance_list"),
    path(
        "attendance/<int:pk>/edit/",
        views.AttendanceUpdateView.as_view(),
        name="attendance_update",
    ),
    path(
        "attendance/<int:pk>/mark/<str:status>/",
        views.AttendanceQuickMarkView.as_view(),
        name="attendance_mark",
    ),
    path(
        "attendance/<int:pk>/time/<str:field>/",
        views.AttendanceSetTimeView.as_view(),
        name="attendance_set_time",
    ),
    path(
        "attendance/bulk/mark-present/",
        views.AttendanceBulkMarkPresentView.as_view(),
        name="attendance_bulk_mark_present",
    ),

    # Billing
    path("billing/monthly/", views.MonthlyBillingListView.as_view(), name="billing_monthly_list"),
    path(
        "billing/monthly/mark/<str:status>/",
        views.MonthlyBillingMarkView.as_view(),
        name="billing_monthly_mark",
    ),
]

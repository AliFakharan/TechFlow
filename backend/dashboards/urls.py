from django.urls import path

from . import views

urlpatterns = [
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("reports/weekly/", views.WeeklyReportView.as_view(), name="weekly-report"),
]

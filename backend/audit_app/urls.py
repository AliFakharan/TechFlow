from django.urls import path

from . import views

urlpatterns = [
    path("audit/", views.AuditLogList.as_view(), name="audit-list"),
    path(
        "priority-changes/",
        views.PriorityChangeList.as_view(),
        name="priority-changes-list",
    ),
]

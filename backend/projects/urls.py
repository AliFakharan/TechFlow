from django.urls import path

from . import views

urlpatterns = [
    path("projects/", views.ProjectList.as_view(), name="project-list"),
    path("projects/create/", views.ProjectCreate.as_view(), name="project-create"),
    path("projects/<int:pk>/", views.ProjectDetail.as_view(), name="project-detail"),
    path(
        "projects/<int:pk>/priority/",
        views.ChangePriorityView.as_view(),
        name="project-priority",
    ),
    path(
        "projects/<int:pk>/status/",
        views.ChangeStatusView.as_view(),
        name="project-status",
    ),
    path(
        "projects/<int:pk>/assign/",
        views.AssignMemberView.as_view(),
        name="project-assign",
    ),
    path(
        "projects/<int:pk>/remove/<int:member_pk>/",
        views.RemoveMemberView.as_view(),
        name="project-remove",
    ),
]

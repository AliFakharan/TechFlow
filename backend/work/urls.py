from django.urls import path

from . import views

urlpatterns = [
    path("tasks/", views.TaskList.as_view(), name="task-list"),
    path("tasks/create/", views.TaskCreate.as_view(), name="task-create"),
    path("tasks/<int:pk>/", views.TaskDetail.as_view(), name="task-detail"),
    path(
        "tasks/<int:pk>/status/",
        views.TaskQuickStatusView.as_view(),
        name="task-quick-status",
    ),
    path("tasks/<int:pk>/assign/", views.AssignTaskView.as_view(), name="task-assign"),
]

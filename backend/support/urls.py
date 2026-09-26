from django.urls import path

from . import views

urlpatterns = [
    path("support/", views.SupportList.as_view(), name="support-list"),
    path("support/create/", views.SupportCreate.as_view(), name="support-create"),
    path("support/<int:pk>/", views.SupportDetail.as_view(), name="support-detail"),
    path(
        "support/<int:pk>/status/",
        views.SupportStatusView.as_view(),
        name="support-status",
    ),
    path(
        "support/<int:pk>/assign/",
        views.SupportAssignView.as_view(),
        name="support-assign",
    ),
]

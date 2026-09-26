from django.urls import path

from . import views

urlpatterns = [
    path("incoming-work/", views.IncomingList.as_view(), name="incoming-list"),
    path(
        "incoming-work/create/", views.IncomingCreate.as_view(), name="incoming-create"
    ),
    path(
        "incoming-work/<int:pk>/",
        views.IncomingDetail.as_view(),
        name="incoming-detail",
    ),
    path(
        "incoming-work/<int:pk>/status/",
        views.IncomingStatusView.as_view(),
        name="incoming-status",
    ),
    path(
        "incoming-work/<int:pk>/convert/",
        views.IncomingConvertView.as_view(),
        name="incoming-convert",
    ),
]

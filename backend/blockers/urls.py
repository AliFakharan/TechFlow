from django.urls import path

from . import views

urlpatterns = [
    path("blockers/", views.BlockerList.as_view(), name="blocker-list"),
    path("blockers/create/", views.BlockerCreate.as_view(), name="blocker-create"),
    path("blockers/<int:pk>/", views.BlockerDetail.as_view(), name="blocker-detail"),
    path(
        "blockers/<int:pk>/resolve/",
        views.ResolveBlockerView.as_view(),
        name="blocker-resolve",
    ),
]

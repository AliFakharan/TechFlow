from django.urls import path

from . import views

urlpatterns = [
    path("organizations/", views.OrganizationList.as_view(), name="organization-list"),
]

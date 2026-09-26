from django.urls import path

from . import views

urlpatterns = [
    path("capacity/", views.CapacityList.as_view(), name="capacity-list"),
    path("capacity/summary/", views.CapacitySummary.as_view(), name="capacity-summary"),
    path("capacity/set/", views.CapacityUpsert.as_view(), name="capacity-set"),
]

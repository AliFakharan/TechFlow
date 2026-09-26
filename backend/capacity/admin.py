from django.contrib import admin

from .models import CapacityAllocation


@admin.register(CapacityAllocation)
class CapacityAllocationAdmin(admin.ModelAdmin):
    list_display = ["member", "project", "percent", "created_at"]
    list_filter = ["member__team"]

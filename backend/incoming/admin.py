from django.contrib import admin

from .models import IncomingWork


@admin.register(IncomingWork)
class IncomingWorkAdmin(admin.ModelAdmin):
    list_display = ["title", "team", "status", "source", "created_at"]
    list_filter = ["status", "team"]
    search_fields = ["title", "source"]

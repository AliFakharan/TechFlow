from django.contrib import admin

from .models import SupportTicket


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "project",
        "assignee",
        "severity",
        "status",
        "created_at",
    ]
    list_filter = ["status", "severity"]
    search_fields = ["title", "project__name"]

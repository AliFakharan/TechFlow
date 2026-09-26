from django.contrib import admin

from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "project",
        "assignee",
        "status",
        "work_type",
        "priority",
        "due_date",
    ]
    list_filter = ["status", "work_type", "priority"]
    search_fields = ["title", "project__name"]
    date_hierarchy = "created_at"

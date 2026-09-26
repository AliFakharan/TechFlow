from django.contrib import admin

from .models import Blocker


@admin.register(Blocker)
class BlockerAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "project",
        "task",
        "owner",
        "category",
        "status",
        "created_at",
    ]
    list_filter = ["status", "category"]
    search_fields = ["title", "project__name"]

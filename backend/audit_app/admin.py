from django.contrib import admin

from .models import AuditLog, PriorityChange


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["created_at", "action", "entity_type", "entity_label", "actor_name"]
    list_filter = ["action", "entity_type"]
    search_fields = ["entity_label", "note", "actor_name"]
    readonly_fields = [f.name for f in AuditLog._meta.get_fields() if f.name != "id"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(PriorityChange)
class PriorityChangeAdmin(admin.ModelAdmin):
    list_display = [
        "project",
        "old_priority",
        "new_priority",
        "created_at",
        "changed_by",
    ]
    list_filter = ["old_priority", "new_priority"]
    readonly_fields = [
        f.name for f in PriorityChange._meta.get_fields() if f.name != "id"
    ]

    def has_add_permission(self, request):
        return False

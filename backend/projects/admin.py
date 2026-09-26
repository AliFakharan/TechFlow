from django.contrib import admin

from .models import Project, ProjectMember, ProjectStatusHistory


class ProjectMemberInline(admin.TabularInline):
    model = ProjectMember
    extra = 0


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "team",
        "status",
        "priority",
        "risk_status",
        "expected_completion",
        "progress_percent",
    ]
    list_filter = ["status", "priority", "risk_status", "team"]
    search_fields = ["name", "client"]
    inlines = [ProjectMemberInline]


@admin.register(ProjectStatusHistory)
class ProjectStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ["project", "field", "old_value", "new_value", "created_at"]
    list_filter = ["field"]
    readonly_fields = [
        f.name for f in ProjectStatusHistory._meta.get_fields() if f.name != "id"
    ]

    def has_add_permission(self, request):
        return False

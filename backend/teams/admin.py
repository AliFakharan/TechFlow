from django.contrib import admin

from .models import Member, Team


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "organization", "manager", "scrum_master"]
    list_filter = ["organization"]


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ["full_name", "user", "team", "role", "is_active"]
    list_filter = ["role", "team", "is_active"]
    search_fields = ["full_name", "user__username"]

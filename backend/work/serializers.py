from rest_framework import serializers

from core.constants import TaskStatus
from teams.models import Member

from .models import Task


class TaskSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source="project.name", read_only=True)
    assignee_name = serializers.CharField(source="assignee.full_name", read_only=True)
    creator_name = serializers.CharField(source="creator.full_name", read_only=True)

    class Meta:
        model = Task
        fields = [
            "id",
            "project",
            "project_name",
            "title",
            "description",
            "assignee",
            "assignee_name",
            "creator",
            "creator_name",
            "status",
            "work_type",
            "priority",
            "started_at",
            "completed_at",
            "due_date",
            "blocked",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "creator",
            "started_at",
            "completed_at",
            "blocked",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {"assignee": {"required": False, "allow_null": True}}


class TaskListSerializer(serializers.ModelSerializer):
    """Compact rows for lists/boards."""

    project_name = serializers.CharField(source="project.name", read_only=True)
    assignee_name = serializers.CharField(source="assignee.full_name", read_only=True)

    class Meta:
        model = Task
        fields = [
            "id",
            "project",
            "project_name",
            "title",
            "status",
            "work_type",
            "priority",
            "assignee",
            "assignee_name",
            "due_date",
            "blocked",
            "updated_at",
        ]


class TaskQuickUpdateSerializer(serializers.Serializer):
    """Minimal payload for the fast developer flow: change status of my task."""

    status = serializers.ChoiceField(choices=TaskStatus.CHOICES)

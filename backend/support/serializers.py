from rest_framework import serializers

from core.constants import SupportStatus

from .models import SupportTicket


class SupportTicketSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source="project.name", read_only=True)
    assignee_name = serializers.CharField(source="assignee.full_name", read_only=True)

    class Meta:
        model = SupportTicket
        fields = [
            "id",
            "title",
            "description",
            "project",
            "project_name",
            "requester",
            "assignee",
            "assignee_name",
            "severity",
            "status",
            "work_type",
            "started_at",
            "resolved_at",
            "notes",
            "created_at",
        ]
        read_only_fields = ["id", "started_at", "resolved_at", "created_at"]
        extra_kwargs = {
            "project": {"required": False, "allow_null": True},
            "assignee": {"required": False, "allow_null": True},
            "requester": {"required": False},
        }


class SupportStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=SupportStatus.CHOICES)
    note = serializers.CharField(required=False, allow_blank=True, default="")

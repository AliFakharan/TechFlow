from rest_framework import serializers

from core.constants import IncomingWorkStatus

from .models import IncomingWork


class IncomingWorkSerializer(serializers.ModelSerializer):
    reported_by_name = serializers.SerializerMethodField()
    converted_project_name = serializers.CharField(
        source="converted_project.name", read_only=True
    )
    converted_task_title = serializers.CharField(
        source="converted_task.title", read_only=True
    )
    converted_support_title = serializers.CharField(
        source="converted_support.title", read_only=True
    )

    class Meta:
        model = IncomingWork
        fields = [
            "id",
            "team",
            "title",
            "description",
            "source",
            "reported_by",
            "reported_by_name",
            "status",
            "converted_project",
            "converted_project_name",
            "converted_task",
            "converted_task_title",
            "converted_support",
            "converted_support_title",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "reported_by",
            "converted_project",
            "converted_task",
            "converted_support",
            "created_at",
        ]
        extra_kwargs = {"team": {"required": False}}

    def get_reported_by_name(self, obj):
        if obj.reported_by_id and obj.reported_by is not None:
            member = getattr(obj.reported_by, "member", None)
            return member.full_name if member else obj.reported_by.get_full_name()
        return None


class IncomingWorkStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=IncomingWorkStatus.CHOICES)
    note = serializers.CharField(required=False, allow_blank=True, default="")


class IncomingWorkConvertSerializer(serializers.Serializer):
    convert_to = serializers.ChoiceField(
        choices=[("task", "task"), ("support", "support"), ("project", "project")]
    )
    title = serializers.CharField(required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    project = serializers.IntegerField(required=False, allow_null=True)

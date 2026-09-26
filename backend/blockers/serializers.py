from rest_framework import serializers

from .models import Blocker


class BlockerSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source="owner.full_name", read_only=True)
    creator_name = serializers.CharField(source="creator.full_name", read_only=True)
    project_name = serializers.CharField(source="project.name", read_only=True)
    task_title = serializers.CharField(source="task.title", read_only=True)
    age_days = serializers.IntegerField(read_only=True)

    class Meta:
        model = Blocker
        fields = [
            "id",
            "title",
            "description",
            "task",
            "task_title",
            "project",
            "project_name",
            "owner",
            "owner_name",
            "creator",
            "creator_name",
            "category",
            "priority",
            "status",
            "resolved_at",
            "age_days",
            "created_at",
        ]
        read_only_fields = ["id", "creator", "resolved_at", "created_at"]
        extra_kwargs = {
            "task": {"required": False, "allow_null": True},
            "project": {"required": False, "allow_null": True},
            "owner": {"required": False, "allow_null": True},
        }

    def validate(self, attrs):
        if attrs.get("task") is None and (
            self.instance is None
            or (self.instance.project_id is None and not attrs.get("project"))
        ):
            if attrs.get("project") is None:
                raise serializers.ValidationError(
                    "حداقل یکی از وظیفه یا پروژه باید مشخص باشد."
                )
        return attrs


class BlockerResolveSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[("resolved", "resolved")])
    note = serializers.CharField(required=False, allow_blank=True, default="")

from rest_framework import serializers

from .models import AuditLog, PriorityChange


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = [
            "id",
            "action",
            "actor_name",
            "entity_type",
            "entity_id",
            "entity_label",
            "old_value",
            "new_value",
            "note",
            "created_at",
        ]
        read_only_fields = fields


class PriorityChangeSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source="project.name", read_only=True)
    changed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = PriorityChange
        fields = [
            "id",
            "project",
            "project_name",
            "old_priority",
            "new_priority",
            "changed_by_name",
            "reason",
            "impact",
            "created_at",
        ]
        read_only_fields = fields

    def get_changed_by_name(self, obj):
        if obj.changed_by_id and obj.changed_by is not None:
            member = getattr(obj.changed_by, "member", None)
            return member.full_name if member else obj.changed_by.get_full_name()
        return None

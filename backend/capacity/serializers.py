from rest_framework import serializers

from .models import CapacityAllocation


class CapacityAllocationSerializer(serializers.ModelSerializer):
    project_name = serializers.SerializerMethodField()

    class Meta:
        model = CapacityAllocation
        fields = ["id", "member", "project", "project_name", "percent"]
        read_only_fields = ["id"]
        extra_kwargs = {
            "project": {"required": False, "allow_null": True},
        }

    def get_project_name(self, obj):
        return obj.project.name if obj.project_id else "پشتیبانی"

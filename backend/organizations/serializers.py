from rest_framework import serializers

from .models import Organization


class OrganizationSerializer(serializers.ModelSerializer):
    team_count = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = ["id", "name", "code", "team_count", "created_at"]
        read_only_fields = ["id", "created_at"]

    def get_team_count(self, obj):
        return obj.teams.count()

from rest_framework import serializers

from organizations.models import Organization

from .models import Member, Team


class MemberSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    role_label = serializers.CharField(read_only=True)
    team_name = serializers.CharField(source="team.name", read_only=True)

    class Meta:
        model = Member
        fields = [
            "id",
            "user",
            "username",
            "full_name",
            "email",
            "organization",
            "team",
            "team_name",
            "role",
            "role_label",
            "is_active",
        ]
        read_only_fields = ["id"]


class MemberCreateSerializer(serializers.Serializer):
    """Used to provision users + members in one call (admin only).

    Plain Serializer (not ModelSerializer) because ``username`` and
    ``password`` belong to the auth User, not to Member.
    """

    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=6)
    full_name = serializers.CharField(max_length=200)
    email = serializers.EmailField(required=False, allow_blank=True)
    organization = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.all(), required=False, allow_null=True
    )
    team = serializers.PrimaryKeyRelatedField(
        queryset=Team.objects.all(), required=False, allow_null=True
    )
    role = serializers.CharField(default="developer")
    is_active = serializers.BooleanField(default=True)

    def validate(self, attrs):
        from django.contrib.auth.models import User

        if User.objects.filter(username=attrs["username"]).exists():
            raise serializers.ValidationError(
                {"username": "این نام کاربری قبلاً گرفته شده است."}
            )
        from core.constants import Role

        if attrs.get("role") not in dict(Role.CHOICES):
            raise serializers.ValidationError({"role": "نقش نامعتبر است."})
        return attrs


class TeamSerializer(serializers.ModelSerializer):
    manager_name = serializers.CharField(source="manager.get_full_name", read_only=True)
    scrum_master_name = serializers.CharField(
        source="scrum_master.get_full_name", read_only=True
    )
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = [
            "id",
            "organization",
            "name",
            "code",
            "manager",
            "manager_name",
            "scrum_master",
            "scrum_master_name",
            "member_count",
        ]
        read_only_fields = ["id"]

    def get_member_count(self, obj):
        return obj.members.filter(is_active=True).count()

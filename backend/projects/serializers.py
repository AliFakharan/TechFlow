from django.db.models import Count
from rest_framework import serializers

from core.constants import Priority, ProjectStatus
from teams.models import Member

from .models import Project, ProjectMember, ProjectStatusHistory


class ProjectMemberSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source="member.full_name", read_only=True)

    class Meta:
        model = ProjectMember
        fields = ["id", "member", "member_name", "is_lead", "assigned_at"]
        read_only_fields = ["id", "assigned_at"]


class ProjectMemberIdsField(serializers.Field):
    """Writable list of member ids for a project.

    ``Project.members`` is an M2M with an explicit through table
    (``ProjectMember``), so a plain ``PrimaryKeyRelatedField(many=True)``
    cannot both read and write it. This field writes
    ``ProjectMember`` rows; reads go through the read-only
    ``members`` (ProjectMemberSerializer) field.
    """

    def to_internal_value(self, data):
        if not isinstance(data, list):
            raise serializers.ValidationError("Should be a list of member ids.")
        qs = Member.objects.filter(is_active=True, pk__in=data)
        found = {m.pk for m in qs}
        missing = set(data) - found
        if missing:
            raise serializers.ValidationError(f"عضو معتبر نیست: {sorted(missing)}")
        return list(qs)

    def to_representation(self, instance):
        return [pm.member_id for pm in instance.project_members.all()]


class ProjectStatusHistorySerializer(serializers.ModelSerializer):
    changed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = ProjectStatusHistory
        fields = [
            "id",
            "field",
            "old_value",
            "new_value",
            "changed_by_name",
            "note",
            "created_at",
        ]

    def get_changed_by_name(self, obj):
        if obj.changed_by_id and obj.changed_by is not None:
            member = getattr(obj.changed_by, "member", None)
            return member.full_name if member else obj.changed_by.get_full_name()
        return None


class ProjectSerializer(serializers.ModelSerializer):
    """Full project representation (detail view)."""

    team_name = serializers.CharField(source="team.name", read_only=True)
    owner_name = serializers.CharField(source="owner.full_name", read_only=True)
    # Note: ``project.members`` is an M2M (via ProjectMember) of Member
    # objects, so we expose the through rows through ``project_members``.
    members = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    project_members = ProjectMemberSerializer(many=True, read_only=True)
    member_ids = ProjectMemberIdsField(
        required=False,
        help_text="List of member ids assigned to the project.",
    )
    status_history = ProjectStatusHistorySerializer(many=True, read_only=True)
    days_to_expected_completion = serializers.IntegerField(read_only=True)
    open_blocker_count = serializers.IntegerField(read_only=True)
    task_stats = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            "id",
            "team",
            "team_name",
            "name",
            "description",
            "owner",
            "owner_name",
            "status",
            "priority",
            "risk_status",
            "start_date",
            "expected_completion",
            "actual_completion",
            "progress_percent",
            "client",
            "members",
            "project_members",
            "member_ids",
            "status_history",
            "days_to_expected_completion",
            "open_blocker_count",
            "task_stats",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "risk_status"]

    def get_task_stats(self, obj):
        rows = obj.tasks.values("status").annotate(count=Count("id"))
        result = {"total": 0, "todo": 0, "in_progress": 0, "blocked": 0, "done": 0}
        for row in rows:
            if row["status"] in result:
                result[row["status"]] = row["count"]
                result["total"] += row["count"]
        return result

    def create(self, validated_data):
        members = validated_data.pop("member_ids", [])
        project = Project.objects.create(**validated_data)
        for member in members:
            ProjectMember.objects.create(project=project, member=member)
        return project

    def update(self, instance, validated_data):
        members = validated_data.pop("member_ids", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if members is not None:
            current = {
                pm.member_id
                for pm in instance.project_members.filter(unassigned_at__isnull=True)
            }
            wanted = {m.pk for m in members}
            for member_id in current - wanted:
                ProjectMember.objects.filter(
                    project=instance, member_id=member_id, unassigned_at__isnull=True
                ).update(unassigned_at=_now())
            for member in members:
                if member.pk not in current:
                    ProjectMember.objects.create(project=instance, member=member)
        return instance


def _now():
    from django.utils import timezone

    return timezone.now()


class ProjectListSerializer(serializers.ModelSerializer):
    """Compact serializer for lists and dashboards."""

    team_name = serializers.CharField(source="team.name", read_only=True)
    owner_name = serializers.CharField(source="owner.full_name", read_only=True)
    member_count = serializers.SerializerMethodField()
    days_to_expected_completion = serializers.IntegerField(read_only=True)
    open_blocker_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Project
        fields = [
            "id",
            "team",
            "team_name",
            "name",
            "status",
            "priority",
            "risk_status",
            "owner_name",
            "start_date",
            "expected_completion",
            "actual_completion",
            "progress_percent",
            "client",
            "member_count",
            "days_to_expected_completion",
            "open_blocker_count",
            "updated_at",
        ]

    def get_member_count(self, obj):
        return obj.project_members.filter(unassigned_at__isnull=True).count()


class ChangePrioritySerializer(serializers.Serializer):
    new_priority = serializers.ChoiceField(choices=Priority.CHOICES)
    reason = serializers.CharField(required=False, allow_blank=True, default="")
    impact = serializers.CharField(required=False, allow_blank=True, default="")


class ChangeStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=ProjectStatus.CHOICES)
    note = serializers.CharField(required=False, allow_blank=True, default="")

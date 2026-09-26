"""Project CRUD + audited management operations.

Design notes
------------
* Priority changes ALWAYS go through ``ChangePriorityView`` (frontend uses
  it). It writes a ``PriorityChange`` narrative record, a status-history row
  and an audit entry. If a client PATCHes ``priority`` directly, the same
  records are written here as a fallback so history can never be lost.
* Status changes go through ``ChangeStatusView`` (or PATCH as fallback).
* Assignments/removals are explicit, audited endpoints.
"""

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import generics, serializers, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from audit_app.models import PriorityChange
from audit_app.services import record_audit
from core.constants import ProjectStatus, Role
from core.permissions import (
    IsManagementDecision,
    IsPriorityChange,
    get_member,
    has_role,
)
from teams.models import Member

from .models import Project, ProjectMember, ProjectStatusHistory
from .risk import refresh_risk_for_project
from .serializers import (
    ChangePrioritySerializer,
    ChangeStatusSerializer,
    ProjectListSerializer,
    ProjectSerializer,
)

# Fields that are "management decisions" (require manager/admin).
MANAGED_FIELDS = {
    "priority": "اولویت",
    "status": "وضعیت",
    "expected_completion": "تاریخ اتمام مورد انتظار",
    "start_date": "تاریخ شروع",
    "owner": "مالک پروژه",
    "client": "کلاینت",
}

# Fields a developer may update on a project (their own estimate only).
DEVELOPER_PROJECT_FIELDS = {"progress_percent", "description"}


class _TeamScopedMixin:
    """Restrict developers to projects they own or are invited to.

    Non-developers (admin, managers, scrum master, deputy) see everything.
    """

    def get_queryset(self):
        qs = Project.objects.select_related("team", "owner").prefetch_related(
            "project_members__member",
            "status_history__changed_by",
        )
        member = get_member(self.request.user)
        if member and member.role == Role.DEVELOPER:
            qs = qs.filter(
                Q(owner=member)
                | Q(
                    project_members__member=member,
                    project_members__unassigned_at__isnull=True,
                )
            )
        return qs.distinct()


class ProjectList(_TeamScopedMixin, generics.ListAPIView):
    serializer_class = ProjectListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        if params.get("team"):
            qs = qs.filter(team_id=params["team"])
        if params.get("status"):
            qs = qs.filter(status=params["status"])
        if params.get("priority"):
            qs = qs.filter(priority=params["priority"])
        if params.get("risk_status"):
            qs = qs.filter(risk_status=params["risk_status"])
        if params.get("q"):
            term = params["q"]
            qs = qs.filter(Q(name__icontains=term) | Q(client__icontains=term))
        return qs


class ProjectDetail(_TeamScopedMixin, generics.RetrieveUpdateAPIView):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer(self, *args, **kwargs):
        # Developers may only submit their own updatable fields.
        if has_role(self.request.user, {Role.DEVELOPER}):
            data = kwargs.get("data")
            if data is not None and set(data) - set(DEVELOPER_PROJECT_FIELDS):
                raise PermissionDenied(
                    "توسعه‌دهنده فقط می‌تواند درصد پیشرفت و توضیحات را تغییر دهد."
                )
        return super().get_serializer(*args, **kwargs)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        payload = dict(request.data)
        if not has_role(request.user, Role.DEVELOPER) and not has_role(
            request.user, Role.MANAGEMENT_DECISION_ROLES
        ):
            # Non-developers that are not management-decision roles (e.g.
            # the deputy) may change ONLY the priority.
            allowed_extra = (
                {"priority"}
                if has_role(request.user, Role.PRIORITY_CHANGE_ROLES)
                else set()
            )
            forbidden = set(payload) & (set(MANAGED_FIELDS) - allowed_extra)
            if forbidden:
                labels = ", ".join(MANAGED_FIELDS[f] for f in forbidden)
                raise PermissionDenied(
                    f"تغییر «{labels}» فقط توسط مدیر تیم یا مدیر سیستم مجاز است."
                )

        old_snapshot = {
            "priority": instance.priority,
            "status": instance.status,
            "expected_completion": str(instance.expected_completion or ""),
            "start_date": str(instance.start_date or ""),
            "progress_percent": instance.progress_percent,
        }

        response = super().update(request, *args, **kwargs)

        instance.refresh_from_db()
        _record_project_change(request, instance, old_snapshot)
        refresh_risk_for_project(instance)
        return response


class ProjectCreate(generics.CreateAPIView):
    serializer_class = ProjectSerializer
    permission_classes = [IsManagementDecision]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            project = serializer.save()
            record_audit(
                request,
                action="project_created",
                entity_type="project",
                entity_id=project.pk,
                entity_label=project.name,
                team=project.team,
                new_value={
                    "status": project.status,
                    "priority": project.priority,
                    "expected_completion": str(project.expected_completion or ""),
                },
            )
            ProjectStatusHistory.objects.create(
                project=project,
                field="status",
                old_value="",
                new_value=project.status,
                changed_by=request.user,
                note="ایجاد پروژه",
            )
        return Response(ProjectSerializer(project).data, status=status.HTTP_201_CREATED)


class ChangePriorityView(APIView):
    """Change a project's priority; always writes a PriorityChange record,
    a status-history row and an audit entry.

    Purpose: make management trade-offs visible (not to blame anyone).
    """

    permission_classes = [IsPriorityChange]

    @extend_schema(
        request=ChangePrioritySerializer,
        responses={200: OpenApiTypes.OBJECT},
    )
    def post(self, request, pk):
        project = Project.objects.filter(pk=pk).first()
        if project is None:
            return Response(
                {"detail": "پروژه یافت نشد."}, status=status.HTTP_404_NOT_FOUND
            )
        serializer = ChangePrioritySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_priority = serializer.validated_data["new_priority"]
        old_priority = project.priority
        if new_priority == old_priority:
            raise ValidationError({"new_priority": "اولویت جدید با فعلی یکسان است."})

        with transaction.atomic():
            project.priority = new_priority
            project.save(update_fields=["priority", "updated_at"])
            change = PriorityChange.objects.create(
                project=project,
                changed_by=request.user,
                old_priority=old_priority,
                new_priority=new_priority,
                reason=serializer.validated_data.get("reason", ""),
                impact=serializer.validated_data.get("impact", ""),
            )
            ProjectStatusHistory.objects.create(
                project=project,
                field="priority",
                old_value=old_priority,
                new_value=new_priority,
                changed_by=request.user,
                note=serializer.validated_data.get("reason", ""),
            )
            record_audit(
                request,
                action="priority_changed",
                entity_type="project",
                entity_id=project.pk,
                entity_label=project.name,
                team=project.team,
                old_value={"priority": old_priority},
                new_value={
                    "priority": new_priority,
                    "reason": serializer.validated_data.get("reason", ""),
                },
                note=serializer.validated_data.get("impact", ""),
            )
            refresh_risk_for_project(project)
        return Response(
            {
                "priority_change_id": change.pk,
                "detail": "اولویت با موفقیت تغییر کرد.",
            }
        )


class ChangeStatusView(APIView):
    """Change a project's status (audited)."""

    permission_classes = [IsManagementDecision]

    @extend_schema(
        request=ChangeStatusSerializer,
        responses={200: OpenApiTypes.OBJECT},
    )
    def post(self, request, pk):
        project = Project.objects.filter(pk=pk).first()
        if project is None:
            return Response(
                {"detail": "پروژه یافت نشد."}, status=status.HTTP_404_NOT_FOUND
            )
        serializer = ChangeStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data["status"]
        old_status = project.status
        if new_status == old_status:
            raise ValidationError({"status": "وضعیت جدید با فعلی یکسان است."})

        with transaction.atomic():
            project.status = new_status
            if new_status == ProjectStatus.DONE and not project.actual_completion:
                project.actual_completion = timezone.localdate()
            project.save(update_fields=["status", "actual_completion", "updated_at"])
            ProjectStatusHistory.objects.create(
                project=project,
                field="status",
                old_value=old_status,
                new_value=new_status,
                changed_by=request.user,
                note=serializer.validated_data.get("note", ""),
            )
            record_audit(
                request,
                action="project_status_changed",
                entity_type="project",
                entity_id=project.pk,
                entity_label=project.name,
                team=project.team,
                old_value={"status": old_status},
                new_value={"status": new_status},
                note=serializer.validated_data.get("note", ""),
            )
            refresh_risk_for_project(project)
        return Response({"detail": "وضعیت پروژه با موفقیت تغییر کرد."})


class AssignMemberView(APIView):
    """Assign a developer to a project (management decision, audited)."""

    permission_classes = [IsManagementDecision]

    @extend_schema(
        request=inline_serializer(
            name="AssignProjectMember",
            fields={
                "member": serializers.IntegerField(help_text="عضو تیم"),
                "is_lead": serializers.BooleanField(required=False, default=False),
            },
        ),
        responses={201: OpenApiTypes.OBJECT},
    )
    def post(self, request, pk):
        project = Project.objects.filter(pk=pk).first()
        if project is None:
            return Response(
                {"detail": "پروژه یافت نشد."}, status=status.HTTP_404_NOT_FOUND
            )
        member = Member.objects.filter(
            pk=request.data.get("member"), is_active=True
        ).first()
        if member is None:
            raise ValidationError({"member": "عضو معتبر نیست."})
        is_lead = bool(request.data.get("is_lead", False))
        membership, created = ProjectMember.objects.get_or_create(
            project=project, member=member, defaults={"is_lead": is_lead}
        )
        if not created and not membership.is_current:
            membership.unassigned_at = None
            membership.is_lead = is_lead
            membership.save(update_fields=["unassigned_at", "is_lead"])
        elif created:
            membership.is_lead = is_lead
            membership.save(update_fields=["is_lead"])
        record_audit(
            request,
            action="member_assigned",
            entity_type="project",
            entity_id=project.pk,
            entity_label=project.name,
            team=project.team,
            new_value={"member": member.full_name, "is_lead": membership.is_lead},
        )
        return Response(
            {"detail": "عضو به پروژه اضافه شد."}, status=status.HTTP_201_CREATED
        )


class RemoveMemberView(APIView):
    """Remove (soft) a developer from a project (audited)."""

    permission_classes = [IsManagementDecision]

    @extend_schema(request=None, responses={200: OpenApiTypes.OBJECT})
    def post(self, request, pk, member_pk):
        project = Project.objects.filter(pk=pk).first()
        if project is None:
            return Response(
                {"detail": "پروژه یافت نشد."}, status=status.HTTP_404_NOT_FOUND
            )
        membership = ProjectMember.objects.filter(
            project=project, member_id=member_pk, unassigned_at__isnull=True
        ).first()
        if membership is None:
            return Response(
                {"detail": "عضو در این پروژه نیست."}, status=status.HTTP_404_NOT_FOUND
            )
        membership.unassigned_at = timezone.now()
        membership.save(update_fields=["unassigned_at"])
        record_audit(
            request,
            action="member_removed",
            entity_type="project",
            entity_id=project.pk,
            entity_label=project.name,
            team=project.team,
            old_value={"member": membership.member.full_name},
        )
        return Response({"detail": "عضو از پروژه حذف شد."})


def _record_project_change(request, instance, old_snapshot):
    """Write ProjectStatusHistory + audit entries for changed fields.

    Priority changes made via PATCH (instead of the dedicated endpoint) are
    also captured here so the priority history is never lost.
    """
    if old_snapshot is None:
        return
    for field, old in old_snapshot.items():
        new = getattr(instance, field)
        old_str = str(old or "")
        new_str = str(new or "")
        if old_str == new_str:
            continue
        user = getattr(request, "user", None)
        if field == "priority":
            # Fallback capture (dedicated endpoint already writes these).
            exists = PriorityChange.objects.filter(
                project=instance,
                old_priority=old_str,
                new_priority=new_str,
                created_at__year=timezone.localdate().year,
            ).count()
            if not exists:
                PriorityChange.objects.create(
                    project=instance,
                    changed_by=user,
                    old_priority=old_str,
                    new_priority=new_str,
                )
            ProjectStatusHistory.objects.create(
                project=instance,
                field="priority",
                old_value=old_str,
                new_value=new_str,
                changed_by=user,
            )
            record_audit(
                request,
                action="priority_changed",
                entity_type="project",
                entity_id=instance.pk,
                entity_label=instance.name,
                team=instance.team,
                old_value={"priority": old_str},
                new_value={"priority": new_str},
            )
            continue
        history_field = {
            "status": "status",
            "expected_completion": "expected_completion",
            "start_date": "start_date",
            "progress_percent": "progress",
        }[field]
        ProjectStatusHistory.objects.create(
            project=instance,
            field=history_field,
            old_value=old_str,
            new_value=new_str,
            changed_by=user,
        )
        action = (
            "expected_completion_changed"
            if field == "expected_completion"
            else "project_updated"
        )
        record_audit(
            request,
            action=action,
            entity_type="project",
            entity_id=instance.pk,
            entity_label=instance.name,
            team=instance.team,
            old_value={history_field: old_str},
            new_value={history_field: new_str},
        )

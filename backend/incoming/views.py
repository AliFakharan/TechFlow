"""Incoming work endpoints: capture unplanned work, evaluate it, and
convert it into a task / support ticket / project (all audited)."""

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from audit_app.services import record_audit
from core.constants import IncomingWorkStatus, Role
from core.permissions import get_member, has_role
from projects.models import Project
from support.models import SupportTicket
from teams.models import Team
from work.models import Task

from .models import IncomingWork
from .serializers import (
    IncomingWorkConvertSerializer,
    IncomingWorkSerializer,
    IncomingWorkStatusSerializer,
)


class IncomingList(generics.ListAPIView):
    serializer_class = IncomingWorkSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = IncomingWork.objects.select_related(
            "team",
            "reported_by",
            "converted_project",
            "converted_task",
            "converted_support",
        )
        params = self.request.query_params
        member = get_member(self.request.user)
        if member and member.role == Role.DEVELOPER:
            qs = qs.filter(team_id=member.team_id)
        if params.get("status"):
            qs = qs.filter(status=params["status"])
        if params.get("team"):
            qs = qs.filter(team_id=params["team"])
        return qs


class IncomingCreate(generics.CreateAPIView):
    serializer_class = IncomingWorkSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        member = get_member(request.user)
        if member is None or member.team is None:
            raise PermissionDenied("عضو شما به تیمی متصل نیست.")
        data = request.data.copy()
        # Default to the user's team; ops roles may specify another team.
        data["team"] = data.get("team") or member.team_id
        if not has_role(request.user, Role.OPERATIONS_ROLES):
            data["team"] = member.team_id
        serializer = self.get_serializer(data=dict(data))
        serializer.is_valid(raise_exception=True)
        item = serializer.save()
        item.reported_by = request.user
        item.save(update_fields=["reported_by", "updated_at"])
        record_audit(
            request,
            action="incoming_work_created",
            entity_type="incoming_work",
            entity_id=item.pk,
            entity_label=item.title,
            team=item.team,
            new_value={"status": item.status, "source": item.source},
        )
        return Response(
            IncomingWorkSerializer(item).data, status=status.HTTP_201_CREATED
        )


class IncomingDetail(generics.RetrieveUpdateAPIView):
    serializer_class = IncomingWorkSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return IncomingWork.objects.all()

    def update(self, request, *args, **kwargs):
        item = self.get_object()
        member = get_member(request.user)
        if not has_role(request.user, Role.OPERATIONS_ROLES):
            if member is None or item.team_id != member.team_id:
                raise PermissionDenied("دسترسی ندارید.")
        old_status = item.status
        response = super().update(request, *args, **kwargs)
        if item.status != old_status:
            record_audit(
                request,
                action=(
                    "incoming_work_converted"
                    if item.status.startswith("converted")
                    else "incoming_work_created"
                ),
                entity_type="incoming_work",
                entity_id=item.pk,
                entity_label=item.title,
                team=item.team,
                old_value={"status": old_status},
                new_value={"status": item.status},
            )
        return response


class IncomingStatusView(APIView):
    """POST /api/incoming-work/{id}/status/ {status} — quick state change."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=IncomingWorkStatusSerializer,
        responses={200: IncomingWorkSerializer},
    )
    def post(self, request, pk):
        item = IncomingWork.objects.filter(pk=pk).first()
        if item is None:
            return Response({"detail": "یافت نشد."}, status=status.HTTP_404_NOT_FOUND)
        member = get_member(request.user)
        if not has_role(request.user, Role.OPERATIONS_ROLES):
            if member is None or item.team_id != member.team_id:
                raise PermissionDenied("دسترسی ندارید.")
        serializer = IncomingWorkStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data["status"]
        old_status = item.status
        if new_status == old_status:
            return Response({"detail": "وضعیت بدون تغییر است."})
        item.status = new_status
        item.save(update_fields=["status", "updated_at"])
        record_audit(
            request,
            action=(
                "incoming_work_converted"
                if new_status.startswith("converted")
                else "incoming_work_created"
            ),
            entity_type="incoming_work",
            entity_id=item.pk,
            entity_label=item.title,
            team=item.team,
            old_value={"status": old_status},
            new_value={"status": new_status},
            note=serializer.validated_data.get("note", ""),
        )
        return Response(IncomingWorkSerializer(item).data)


class IncomingConvertView(APIView):
    """POST /api/incoming-work/{id}/convert/ — turn incoming work into a
    real task / support ticket / project (audited)."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=IncomingWorkConvertSerializer,
        responses={200: OpenApiTypes.OBJECT},
    )
    def post(self, request, pk):
        item = IncomingWork.objects.filter(pk=pk).first()
        if item is None:
            return Response({"detail": "یافت نشد."}, status=status.HTTP_404_NOT_FOUND)
        if not has_role(request.user, Role.OPERATIONS_ROLES):
            raise PermissionDenied("تبدیل کار ورودی نیاز به نقش عملیاتی دارد.")
        serializer = IncomingWorkConvertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        target = data["convert_to"]
        title = data.get("title") or item.title
        description = data.get("description") or item.description

        from django.utils import timezone

        if target == "task":
            project_id = data.get("project")
            if not project_id:
                return Response(
                    {"detail": "برای تبدیل به وظیفه، پروژه الزامی است."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            project = Project.objects.filter(pk=project_id).first()
            if project is None:
                return Response(
                    {"detail": "پروژه معتبر نیست."}, status=status.HTTP_400_BAD_REQUEST
                )
            task = Task.objects.create(
                project=project,
                title=title,
                description=description
                + ("\n\n" + item.title if description else "\n" + item.title),
                work_type="change_request",
                creator_id=None,
            )
            item.converted_task = task
            item.status = IncomingWorkStatus.CONVERTED_TASK
        elif target == "support":
            ticket = SupportTicket.objects.create(
                title=title,
                description=description,
                project_id=data.get("project"),
                requester=item.source,
            )
            item.converted_support = ticket
            item.status = IncomingWorkStatus.CONVERTED_SUPPORT
        else:  # project
            team = item.team
            project = Project.objects.create(
                team=team,
                name=title,
                description=description,
                status="planned",
            )
            item.converted_project = project
            item.status = IncomingWorkStatus.CONVERTED_PROJECT
            record_audit(
                request,
                action="project_created",
                entity_type="project",
                entity_id=project.pk,
                entity_label=project.name,
                team=team,
                new_value={"status": project.status, "from_incoming_work": item.pk},
            )
        item.save()
        record_audit(
            request,
            action="incoming_work_converted",
            entity_type="incoming_work",
            entity_id=item.pk,
            entity_label=item.title,
            team=item.team,
            new_value={"converted_to": target},
        )
        return Response(IncomingWorkSerializer(item).data, status=status.HTTP_200_OK)

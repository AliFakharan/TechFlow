"""Support ticket endpoints.

Developers record their own support work; operations roles can triage,
assign and resolve for the whole team.
"""

from django.db.models import Q
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import generics, serializers, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from audit_app.services import record_audit
from core.constants import Role, SupportStatus
from core.permissions import get_member, has_role
from teams.models import Member

from .models import SupportTicket
from .serializers import SupportStatusSerializer, SupportTicketSerializer


class SupportList(generics.ListAPIView):
    serializer_class = SupportTicketSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = SupportTicket.objects.select_related("project", "assignee").all()
        params = self.request.query_params
        member = get_member(self.request.user)
        if params.get("open") in ("1", "true"):
            qs = qs.filter(status__in=SupportStatus.OPEN_STATUSES)
        if params.get("status"):
            qs = qs.filter(status=params["status"])
        if params.get("project"):
            qs = qs.filter(project_id=params["project"])
        if params.get("mine") in ("1", "true") and member:
            qs = qs.filter(assignee=member)
        if member and member.role == Role.DEVELOPER:
            qs = qs.filter(
                Q(assignee=member) | Q(project__team_id=member.team_id)
            ).distinct()
        return qs


class SupportCreate(generics.CreateAPIView):
    serializer_class = SupportTicketSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        member = get_member(request.user)
        if member is None:
            raise PermissionDenied("حساب شما متصل به عضوی نیست.")
        data = request.data.copy()
        if not has_role(request.user, Role.OPERATIONS_ROLES):
            # Developers default-assign to themselves (fast flow).
            if not data.get("assignee"):
                data["assignee"] = member.pk
            if data.get("assignee") and int(data["assignee"]) != member.id:
                raise PermissionDenied("توسعه‌دهنده تیکت را فقط برای خودش ثبت می‌کند.")
        serializer = self.get_serializer(data=dict(data))
        serializer.is_valid(raise_exception=True)
        ticket = serializer.save()
        record_audit(
            request,
            action="support_created",
            entity_type="support",
            entity_id=ticket.pk,
            entity_label=ticket.title,
            team=ticket.project.team if ticket.project_id else None,
            new_value={"severity": ticket.severity, "assignee": ticket.assignee_id},
        )
        return Response(
            SupportTicketSerializer(ticket).data, status=status.HTTP_201_CREATED
        )


class SupportDetail(generics.RetrieveUpdateAPIView):
    serializer_class = SupportTicketSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SupportTicket.objects.select_related("project", "assignee")

    def update(self, request, *args, **kwargs):
        ticket = self.get_object()
        member = get_member(request.user)
        if not has_role(request.user, Role.OPERATIONS_ROLES):
            if member is None or ticket.assignee_id != member.id:
                raise PermissionDenied("شما مسئول این تیکت نیستید.")
        old_status = ticket.status
        response = super().update(request, *args, **kwargs)
        if ticket.status != old_status:
            record_audit(
                request,
                action="support_status_changed",
                entity_type="support",
                entity_id=ticket.pk,
                entity_label=ticket.title,
                team=ticket.project.team if ticket.project_id else None,
                old_value={"status": old_status},
                new_value={"status": ticket.status},
            )
        return response


class SupportStatusView(APIView):
    """POST /api/support/{id}/status/ {"status": "resolved"} — fast path."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=SupportStatusSerializer, responses={200: SupportTicketSerializer}
    )
    def post(self, request, pk):
        ticket = SupportTicket.objects.filter(pk=pk).first()
        if ticket is None:
            return Response(
                {"detail": "تیکت یافت نشد."}, status=status.HTTP_404_NOT_FOUND
            )
        member = get_member(request.user)
        if not has_role(request.user, Role.OPERATIONS_ROLES):
            if member is None or ticket.assignee_id != member.id:
                raise PermissionDenied("شما مسئول این تیکت نیستید.")
        serializer = SupportStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data["status"]
        old_status = ticket.status
        if new_status == old_status:
            return Response({"detail": "وضعیت بدون تغییر است."})
        ticket.status = new_status
        ticket.save(update_fields=["status", "started_at", "resolved_at", "updated_at"])
        record_audit(
            request,
            action="support_status_changed",
            entity_type="support",
            entity_id=ticket.pk,
            entity_label=ticket.title,
            team=ticket.project.team if ticket.project_id else None,
            old_value={"status": old_status},
            new_value={"status": new_status},
            note=serializer.validated_data.get("note", ""),
        )
        return Response(SupportTicketSerializer(ticket).data)


class SupportAssignView(APIView):
    """Assign a developer to a ticket (operations roles, audited)."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=inline_serializer(
            name="AssignSupportTicket",
            fields={
                "assignee": serializers.IntegerField(
                    required=False, allow_null=True, help_text="توسعه‌دهنده مسئول"
                )
            },
        ),
        responses={200: SupportTicketSerializer},
    )
    def post(self, request, pk):
        if not has_role(request.user, Role.OPERATIONS_ROLES):
            raise PermissionDenied("تعیین مسئول فقط توسط نقش‌های عملیاتی مجاز است.")
        ticket = SupportTicket.objects.filter(pk=pk).first()
        if ticket is None:
            return Response(
                {"detail": "تیکت یافت نشد."}, status=status.HTTP_404_NOT_FOUND
            )
        member = Member.objects.filter(
            pk=request.data.get("assignee"), is_active=True
        ).first()
        if member is None:
            return Response(
                {"detail": "عضو معتبر نیست."}, status=status.HTTP_400_BAD_REQUEST
            )
        ticket.assignee = member
        if ticket.status == SupportStatus.NEW:
            ticket.status = SupportStatus.ASSIGNED
        ticket.save(update_fields=["assignee", "status", "started_at", "updated_at"])
        record_audit(
            request,
            action="support_status_changed",
            entity_type="support",
            entity_id=ticket.pk,
            entity_label=ticket.title,
            team=ticket.project.team if ticket.project_id else None,
            old_value={"assignee": None},
            new_value={"assignee": member.full_name, "status": ticket.status},
        )
        return Response(SupportTicketSerializer(ticket).data)

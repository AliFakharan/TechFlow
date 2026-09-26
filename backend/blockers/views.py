"""Blocker endpoints — the fast path for "work is stuck".

A developer can create a blocker from the dashboard in a couple of clicks:
title + category (+ optional project/task). Resolving is one click.
"""

from django.db.models import Q
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from audit_app.services import record_audit
from core.constants import BlockerStatus, Role
from core.permissions import get_member, has_role, visible_project_ids

from .models import Blocker
from .serializers import BlockerResolveSerializer, BlockerSerializer


class BlockerList(generics.ListAPIView):
    serializer_class = BlockerSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Blocker.objects.select_related("owner", "project", "task").all()
        params = self.request.query_params
        member = get_member(self.request.user)
        if params.get("open") in ("1", "true"):
            qs = qs.filter(status=BlockerStatus.OPEN)
        if params.get("status"):
            qs = qs.filter(status=params["status"])
        if params.get("project"):
            qs = qs.filter(project_id=params["project"])
        if params.get("category"):
            qs = qs.filter(category=params["category"])
        if params.get("mine") in ("1", "true") and member:
            qs = qs.filter(owner=member)
        if member and member.role == Role.DEVELOPER:
            qs = qs.filter(
                Q(owner=member)
                | Q(project_id__in=visible_project_ids(member))
            ).distinct()
        return qs


class BlockerCreate(generics.CreateAPIView):
    serializer_class = BlockerSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        member = get_member(request.user)
        if member is None:
            raise PermissionDenied("حساب شما متصل به عضوی نیست.")
        data = request.data.copy()
        if not has_role(request.user, Role.OPERATIONS_ROLES):
            if data.get("owner") and int(data["owner"]) != member.id:
                raise PermissionDenied(
                    "توسعه‌دهنده می‌تواند مانع را فقط برای خودش ثبت کند."
                )
            data["owner"] = member.pk
        else:
            if not data.get("owner") and member is not None:
                data["owner"] = member.pk

        serializer = self.get_serializer(data=dict(data))
        serializer.is_valid(raise_exception=True)
        blocker = serializer.save()
        record_audit(
            request,
            action="blocker_created",
            entity_type="blocker",
            entity_id=blocker.pk,
            entity_label=blocker.title,
            team=blocker.project.team if blocker.project_id else None,
            new_value={
                "category": blocker.category,
                "project": blocker.project_id,
                "task": blocker.task_id,
            },
        )
        return Response(BlockerSerializer(blocker).data, status=status.HTTP_201_CREATED)


class BlockerDetail(generics.RetrieveUpdateAPIView):
    serializer_class = BlockerSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Blocker.objects.select_related("owner", "project", "task")

    def update(self, request, *args, **kwargs):
        blocker = self.get_object()
        member = get_member(request.user)
        is_ops = has_role(request.user, Role.OPERATIONS_ROLES)
        if not is_ops and blocker.owner_id != (member.id if member else None):
            raise PermissionDenied("شما صاحب این مانع نیستید.")
        response = super().update(request, *args, **kwargs)
        return response


class ResolveBlockerView(APIView):
    """One-click resolve (audited)."""

    permission_classes = [IsAuthenticated]

    @extend_schema(request=BlockerResolveSerializer, responses={200: BlockerSerializer})
    def post(self, request, pk):
        blocker = Blocker.objects.filter(pk=pk).first()
        if blocker is None:
            return Response(
                {"detail": "مانع یافت نشد."}, status=status.HTTP_404_NOT_FOUND
            )
        member = get_member(request.user)
        is_ops = has_role(request.user, Role.OPERATIONS_ROLES)
        if not is_ops and blocker.owner_id != (member.id if member else None):
            raise PermissionDenied("شما صاحب این مانع نیستید.")
        old_status = blocker.status
        blocker.status = BlockerStatus.RESOLVED
        blocker.save(update_fields=["status", "resolved_at", "updated_at"])
        record_audit(
            request,
            action="blocker_resolved",
            entity_type="blocker",
            entity_id=blocker.pk,
            entity_label=blocker.title,
            team=blocker.project.team if blocker.project_id else None,
            old_value={"status": old_status},
            new_value={"status": blocker.status},
            note=request.data.get("note", ""),
        )
        return Response(BlockerSerializer(blocker).data)

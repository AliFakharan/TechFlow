"""Capacity allocation endpoints.

Who may set allocations:
* Operations roles (admin/manager/scrum master) set for any member.
* Developers may adjust their own allocations (self-visibility of "where is
  my capacity going").

Totals above 100% are allowed; the response and dashboard surface a warning.
"""

from django.db.models import Q, Sum
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import generics, serializers, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from audit_app.services import record_audit
from core.constants import Role
from core.permissions import get_member, has_role
from teams.models import Team

from .models import CapacityAllocation
from .serializers import CapacityAllocationSerializer


def _team_for_user(user):
    member = get_member(user)
    if member is None:
        return None
    return member.team


class CapacityList(generics.ListAPIView):
    serializer_class = CapacityAllocationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = CapacityAllocation.objects.select_related("member", "project")
        team = _team_for_user(self.request.user)
        if team is not None and (
            not has_role(self.request.user, Role.OPERATIONS_ROLES)
        ):
            # Developers see only their own team's allocations (and their own).
            member = get_member(self.request.user)
            qs = qs.filter(Q(member=member) | Q(member__team=team)).distinct()
        elif team is not None:
            qs = qs.filter(member__team=team)
        if self.request.query_params.get("member"):
            qs = qs.filter(member_id=self.request.query_params["member"])
        return qs


class CapacityUpsert(APIView):
    """POST /api/capacity/  {member, project?, percent} — set a member's
    allocation to a project (or the support bucket when project is null)."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=inline_serializer(
            name="CapacityUpsert",
            fields={
                "member": serializers.IntegerField(help_text="عضو"),
                "project": serializers.IntegerField(
                    required=False, allow_null=True, help_text="پروژه (null = پشتیبانی)"
                ),
                "percent": serializers.IntegerField(
                    min_value=0, max_value=200, help_text="درصد تخصیص"
                ),
            },
        ),
        responses={200: OpenApiTypes.OBJECT},
    )
    def post(self, request):
        member_id = request.data.get("member")
        project_id = request.data.get("project")
        try:
            percent = int(request.data.get("percent", 0))
        except (TypeError, ValueError):
            return Response(
                {"detail": "درصد نامعتبر است."}, status=status.HTTP_400_BAD_REQUEST
            )
        if not 0 <= percent <= 200:
            return Response(
                {"detail": "درصد باید بین 0 و 200 باشد."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from teams.models import Member

        member = Member.objects.filter(pk=member_id, is_active=True).first()
        if member is None:
            return Response(
                {"detail": "عضو معتبر نیست."}, status=status.HTTP_400_BAD_REQUEST
            )

        actor = get_member(request.user)
        is_ops = has_role(request.user, Role.OPERATIONS_ROLES)
        if not is_ops and (actor is None or actor.id != member.id):
            raise PermissionDenied("شما فقط تخصیص ظرفیت خودتان را تغییر می‌دهید.")

        if project_id is not None:
            from projects.models import Project

            if not Project.objects.filter(pk=project_id).exists():
                return Response(
                    {"detail": "پروژه معتبر نیست."}, status=status.HTTP_400_BAD_REQUEST
                )
            if (
                member.team_id
                and not Project.objects.filter(
                    pk=project_id, team_id=member.team_id
                ).exists()
            ):
                return Response(
                    {"detail": "پروژه به تیم شما تعلق ندارد."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            project_id = int(project_id)

        allocation, created = CapacityAllocation.objects.update_or_create(
            member=member,
            project_id=project_id,
            defaults={"percent": percent},
        )
        team = member.team
        record_audit(
            request,
            action="capacity_updated",
            entity_type="capacity",
            entity_id=str(member.pk),
            entity_label=member.full_name,
            team=team,
            new_value={"project": project_id, "percent": percent},
        )
        total = (
            CapacityAllocation.objects.filter(member=member).aggregate(
                total=Sum("percent")
            )["total"]
            or 0
        )
        return Response(
            {
                "allocation": CapacityAllocationSerializer(allocation).data,
                "member_total_percent": total,
                "overallocated": total > 100,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class CapacitySummary(APIView):
    """GET /api/capacity/summary/ — per-member totals + per-project totals
    for the user's team (the "Where is our capacity going?" answer)."""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: OpenApiTypes.OBJECT})
    def get(self, request):
        team = _team_for_user(request.user)
        if team is None:
            return Response(
                {"detail": "عضو شما به تیمی متصل نیست."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        from teams.models import Member

        members = {
            m.id: m.full_name
            for m in team.members.filter(is_active=True, role=Role.DEVELOPER)
        }
        totals = CapacityAllocation.totals_for_team(team)
        per_member = []
        for member_id, name in members.items():
            entry = totals.get(member_id, {"total": 0, "support": 0, "projects": []})
            per_member.append(
                {
                    "member_id": member_id,
                    "full_name": name,
                    "total_percent": entry["total"],
                    "support_percent": entry["support"],
                    "projects": entry["projects"],
                    "overallocated": entry["total"] > 100,
                    "underallocated": entry["total"] < 50,
                }
            )
        per_project = CapacityAllocation.per_project_for_team(team)
        from projects.models import Project

        project_names = {
            p.id: p.name
            for p in Project.objects.filter(
                team=team,
                id__in=[r["project_id"] for r in per_project if r["project_id"]],
            )
        }
        for row in per_project:
            if row["project_id"] is not None:
                row["label"] = project_names.get(row["project_id"], "؟")
        team_size = len(members)
        return Response(
            {
                "team_id": team.id,
                "team_name": team.name,
                "per_member": per_member,
                "per_project": per_project,
                "overallocated_members": [m for m in per_member if m["overallocated"]],
                "team_average_percent": (
                    sum(m["total_percent"] for m in per_member) / team_size
                    if team_size
                    else 0
                ),
            }
        )

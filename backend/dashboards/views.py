"""Dashboard + report endpoints.

All dashboards are read-only and scoped by the user's role/team:
* developer — everyone
* manager / scrum — operations roles
* deputy — deputy (and above)
"""

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import get_member, has_role
from core.constants import Role

from . import services


class DashboardView(APIView):
    """GET /api/dashboard/?view=developer|manager|scrum|deputy"""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: OpenApiTypes.OBJECT})
    def get(self, request):
        view = request.query_params.get("view", "developer")
        if view == "developer":
            data = services.developer_dashboard(request)
        elif view in ("manager", "scrum"):
            member = get_member(request.user)
            if member is None or not has_role(request.user, Role.OPERATIONS_ROLES):
                return Response(
                    {"detail": "دسترسی شما به این داشبورد نیست."}, status=403
                )
            data = (
                services.manager_dashboard(request)
                if view == "manager"
                else services.scrum_dashboard(request)
            )
        elif view == "deputy":
            member = get_member(request.user)
            if member is None or member.role not in {
                Role.ADMIN,
                Role.DEPUTY,
                Role.TEAM_MANAGER,
                Role.SCRUM_MASTER,
            }:
                return Response(
                    {"detail": "دسترسی شما به این داشبورد نیست."}, status=403
                )
            data = services.deputy_dashboard(request)
        else:
            return Response({"detail": "نمای نامعتبر است."}, status=400)
        if "error" in data:
            return Response({"detail": "داده تیم شما یافت نشد."}, status=400)
        return Response(data)


class WeeklyReportView(APIView):
    """GET /api/reports/weekly/ — the weekly team report."""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: OpenApiTypes.OBJECT})
    def get(self, request):
        member = get_member(request.user)
        if member is None or member.role not in {
            Role.ADMIN,
            Role.DEPUTY,
            Role.TEAM_MANAGER,
            Role.SCRUM_MASTER,
        }:
            return Response(
                {"detail": "گزارش هفتگی برای نقش‌های مدیریتی در دسترس است."},
                status=403,
            )
        data = services.weekly_report(request)
        if "error" in data:
            return Response({"detail": "داده تیم شما یافت نشد."}, status=400)
        return Response(data)

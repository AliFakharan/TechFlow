from django.contrib.auth.models import User
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import generics, serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.constants import Role
from core.permissions import IsOperations, get_member, is_admin_user

from .models import Member, Team
from .serializers import (
    MemberCreateSerializer,
    MemberSerializer,
    TeamSerializer,
)


class TeamList(generics.ListAPIView):
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Team.objects.all()
        member = get_member(self.request.user)
        if member and member.team_id and member.role == "developer":
            # Developers only see their own team.
            qs = qs.filter(id=member.team_id)
        return qs


class TeamDetail(generics.RetrieveAPIView):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated]


class MemberList(generics.ListAPIView):
    serializer_class = MemberSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Member.objects.select_related("user", "team", "organization").all()
        member = get_member(self.request.user)
        if member and member.team_id and member.role == "developer":
            qs = qs.filter(team_id=member.team_id, is_active=True)
        return qs


class MemberDetail(generics.RetrieveUpdateAPIView):
    queryset = Member.objects.select_related("user", "team")
    serializer_class = MemberSerializer
    permission_classes = [IsOperations]

    def update(self, request, *args, **kwargs):
        # Role changes are admin-only (system admin role / superuser).
        instance = self.get_object()
        if (
            "role" in request.data
            and request.data.get("role") != instance.role
            and not is_admin_user(request.user)
        ):
            raise ValidationError({"role": "تغییر نقش فقط توسط مدیر سیستم مجاز است."})
        if (
            "is_active" in request.data
            and request.data.get("is_active") is False
            and instance.user_id == request.user.id
        ):
            raise ValidationError({"is_active": "نمی‌توانید خود را غیرفعال کنید."})
        return super().update(request, *args, **kwargs)


class MemberCreateView(generics.CreateAPIView):
    """Admin-only provisioning of a user + member."""

    serializer_class = MemberCreateSerializer
    permission_classes = [IsOperations]

    def create(self, request, *args, **kwargs):
        if not is_admin_user(request.user):
            return Response(
                {"detail": "فقط مدیر سیستم می‌تواند کاربر جدید ایجاد کند."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = User.objects.create_user(
            username=data["username"],
            password=data["password"],
            email=data.get("email") or "",
        )
        # The post_save signal created a Member profile; fill it in.
        member = user.member
        member.full_name = data["full_name"]
        member.email = data.get("email") or ""
        member.role = data.get("role", "developer")
        member.is_active = data.get("is_active", True)
        member.team = data.get("team")
        member.organization = data.get("organization")
        member.save()
        return Response(MemberSerializer(member).data, status=status.HTTP_201_CREATED)


class ChangeRoleView(APIView):
    """Admin-only role change (audited)."""

    permission_classes = [IsOperations]

    @extend_schema(
        request=inline_serializer(
            name="ChangeRole",
            fields={
                "role": serializers.ChoiceField(
                    choices=Role.CHOICES, help_text="نقش جدید عضو"
                )
            },
        ),
        responses={200: MemberSerializer},
    )
    def post(self, request, pk):
        if not is_admin_user(request.user):
            return Response(
                {"detail": "فقط مدیر سیستم می‌تواند نقش تغییر دهد."},
                status=status.HTTP_403_FORBIDDEN,
            )
        member = Member.objects.filter(pk=pk).first()
        if member is None:
            return Response(
                {"detail": "عضو یافت نشد."}, status=status.HTTP_404_NOT_FOUND
            )
        from audit_app.services import record_audit

        old_role = member.role
        new_role = request.data.get("role")
        if new_role not in dict(Role.CHOICES):
            return Response(
                {"detail": "نقش نامعتبر است."}, status=status.HTTP_400_BAD_REQUEST
            )
        member.role = new_role
        member.save(update_fields=["role", "updated_at"])
        record_audit(
            request,
            action="member_role_changed",
            entity_type="member",
            entity_id=str(member.pk),
            old_value={"role": old_role},
            new_value={"role": new_role},
        )
        return Response(MemberSerializer(member).data)

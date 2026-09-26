"""Authentication endpoints: login, logout, register, current user, csrf."""

from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(style={"input_type": "password"})


class SessionUserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    full_name = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    role_label = serializers.SerializerMethodField()
    team_name = serializers.SerializerMethodField()

    def get_member(self, obj):
        try:
            return obj.member
        except Exception:
            return None

    def get_full_name(self, obj):
        member = self.get_member(obj)
        return member.full_name if member else (obj.get_full_name() or obj.username)

    def get_role(self, obj):
        member = self.get_member(obj)
        return member.role if member else "developer"

    def get_role_label(self, obj):
        member = self.get_member(obj)
        return member.role_label if member else "توسعه‌دهنده"

    def get_team_name(self, obj):
        member = self.get_member(obj)
        team = getattr(member, "team", None)
        return team.name if team else None


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(style={"input_type": "password"}, write_only=True)
    full_name = serializers.CharField(max_length=200)
    email = serializers.EmailField(allow_blank=True, required=False)

    def validate_username(self, value):
        value = value.strip()
        if len(value) < 3:
            raise serializers.ValidationError("نام کاربری باید حداقل ۳ حرف باشد.")
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("این نام کاربری قبلاً گرفته شده است.")
        return value

    def validate_password(self, value):
        try:
            validate_password(value)
        except Exception:
            raise serializers.ValidationError(
                "رمز عبور بسیار ضعیف است (حداقل ۸ کاراکتر)."
            )
        return value


class RegisterView(APIView):
    """Public self-service registration. New users join the first team
    (if one exists) with the default developer role."""

    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(request=RegisterSerializer, responses={201: OpenApiTypes.OBJECT})
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = User.objects.create_user(
            username=data["username"],
            password=data["password"],
            email=data.get("email", ""),
            first_name=data["full_name"],
        )
        from teams.models import Member, Team

        member = user.member
        member.full_name = data["full_name"]
        if data.get("email"):
            member.email = data["email"]
        if member.team_id is None:
            team = Team.objects.first()
            if team:
                member.team = team
        member.save()
        login(request, user)
        return Response(
            {
                "user": SessionUserSerializer(user).data,
                "detail": "ثبت‌نام با موفقیت انجام شد.",
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(request=LoginSerializer, responses={200: OpenApiTypes.OBJECT})
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate_for_login(
            request,
            serializer.validated_data["username"],
            serializer.validated_data["password"],
        )
        if user is None:
            return Response(
                {"detail": "نام کاربری یا رمز عبور نادرست است."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        login(request, user)
        return Response(
            {
                "user": SessionUserSerializer(user).data,
                "detail": "ورود با موفقیت انجام شد.",
            }
        )


def authenticate_for_login(request, username, password):
    from django.contrib.auth import authenticate

    user = authenticate(request, username=username, password=password)
    if user is not None and not user.is_active:
        return None
    return user


class LogoutView(APIView):
    @extend_schema(request=None, responses={200: OpenApiTypes.OBJECT})
    def post(self, request):
        logout(request)
        return Response({"detail": "از حساب خارج شدید."})


class MeView(APIView):
    @extend_schema(responses={200: OpenApiTypes.OBJECT})
    def get(self, request):
        return Response({"user": SessionUserSerializer(request.user).data})


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CsrfTokenView(APIView):
    """Bootstraps the CSRF cookie so the SPA can send X-CSRFToken on POSTs."""

    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(responses={200: OpenApiTypes.OBJECT})
    def get(self, request):
        return Response({"detail": "ok"})

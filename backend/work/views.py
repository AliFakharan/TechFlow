"""Task endpoints.

Developer flow (minimal clicks):
* list my tasks        -> GET /api/tasks/?mine=1
* change status        -> PATCH /api/tasks/{id}/  {"status": "..."}
* create a task        -> POST /api/tasks/  (developer: own team projects;
                              can assign themselves by default)
* operations roles may reassign and create for anyone.
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
from core.constants import Role, TaskStatus
from core.permissions import IsOperations, get_member, has_role, visible_project_ids
from projects.models import Project
from teams.models import Member

from .models import Task
from .serializers import TaskListSerializer, TaskQuickUpdateSerializer, TaskSerializer


class TaskList(generics.ListAPIView):
    serializer_class = TaskListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Task.objects.select_related("project", "assignee", "creator").all()
        params = self.request.query_params
        member = get_member(self.request.user)
        if params.get("mine") in ("1", "true") and member:
            qs = qs.filter(assignee=member)
        if params.get("project"):
            qs = qs.filter(project_id=params["project"])
        if params.get("status"):
            qs = qs.filter(status=params["status"])
        if params.get("work_type"):
            qs = qs.filter(work_type=params["work_type"])
        if params.get("assignee"):
            qs = qs.filter(assignee_id=params["assignee"])
        # Developers only see tasks assigned to them OR tasks in projects
        # they own / are invited to.
        if member and member.role == Role.DEVELOPER:
            qs = qs.filter(
                Q(assignee=member) | Q(project_id__in=visible_project_ids(member))
            ).distinct()
        return qs


class TaskDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Task.objects.select_related("project", "assignee", "creator")

    def update(self, request, *args, **kwargs):
        task = self.get_object()
        member = get_member(request.user)
        payload = dict(request.data)
        is_ops = has_role(request.user, Role.OPERATIONS_ROLES)

        # Developers can only update their own tasks, and only limited fields.
        if not is_ops:
            if member is None or task.assignee_id != member.id:
                raise PermissionDenied(
                    "فقط توسعه‌دهنده مسئول وظیفه می‌تواند آن را ویرایش کند."
                )
            allowed = {"status", "notes", "blocked"}
            if set(payload) - allowed:
                raise PermissionDenied(
                    "توسعه‌دهنده فقط می‌تواند وضعیت، یادداشت و مسدودی وظیفه خود را تغییر دهد."
                )

        old_status = task.status
        response = super().update(request, *args, **kwargs)
        if task.status != old_status:
            record_audit(
                request,
                action="task_status_changed",
                entity_type="task",
                entity_id=task.pk,
                entity_label=task.title,
                team=task.project.team,
                old_value={"status": old_status},
                new_value={"status": task.status},
            )
        return response

    def destroy(self, request, *args, **kwargs):
        # Only operations roles may delete; developers can not.
        if not has_role(request.user, Role.OPERATIONS_ROLES):
            raise PermissionDenied("حذف وظیفه فقط توسط نقش‌های عملیاتی مجاز است.")
        return super().destroy(request, *args, **kwargs)


class TaskCreate(generics.CreateAPIView):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        member = get_member(request.user)
        data = request.data.copy()
        if not has_role(request.user, Role.OPERATIONS_ROLES):
            # Developers: only inside their team's projects.
            if member is None or not member.team_id:
                raise PermissionDenied("عضو شما به تیمی متصل نیست.")
            project = Project.objects.filter(
                pk=data.get("project"), team_id=member.team_id
            ).first()
            if project is None:
                raise PermissionDenied(
                    "می‌توانید وظیفه فقط در پروژه‌های تیم خود ایجاد کنید."
                )
            data["project"] = project.pk
            # Default assignee is themselves (fast flow).
            if not data.get("assignee"):
                data["assignee"] = member.pk
        else:
            if (
                data.get("assignee")
                and not Member.objects.filter(
                    pk=data["assignee"], is_active=True
                ).exists()
            ):
                data["assignee"] = None
        if member is not None and not data.get("creator"):
            data["creator"] = member.pk

        serializer = self.get_serializer(data=dict(data))
        serializer.is_valid(raise_exception=True)
        task = serializer.save()
        record_audit(
            request,
            action="task_created",
            entity_type="task",
            entity_id=task.pk,
            entity_label=task.title,
            team=task.project.team,
            new_value={"status": task.status, "work_type": task.work_type},
        )
        return Response(TaskSerializer(task).data, status=status.HTTP_201_CREATED)


class TaskQuickStatusView(APIView):
    """POST /api/tasks/{id}/status/ {"status": "in_progress"} — the fast path
    developers use to flip a task without opening a form."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=TaskQuickUpdateSerializer,
        responses={200: TaskSerializer},
    )
    def post(self, request, pk):
        task = Task.objects.filter(pk=pk).first()
        if task is None:
            return Response(
                {"detail": "وظیفه یافت نشد."}, status=status.HTTP_404_NOT_FOUND
            )
        member = get_member(request.user)
        if not has_role(request.user, Role.OPERATIONS_ROLES):
            if member is None or task.assignee_id != member.id:
                raise PermissionDenied("شما مسئول این وظیفه نیستید.")
        serializer = TaskQuickUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data["status"]
        if new_status == task.status:
            return Response({"detail": "وضعیت بدون تغییر است."})
        old_status = task.status
        task.status = new_status
        task.save(
            update_fields=[
                "status",
                "blocked",
                "started_at",
                "completed_at",
                "updated_at",
            ]
        )
        record_audit(
            request,
            action="task_status_changed",
            entity_type="task",
            entity_id=task.pk,
            entity_label=task.title,
            team=task.project.team,
            old_value={"status": old_status},
            new_value={"status": new_status},
        )
        return Response(TaskSerializer(task).data)


class AssignTaskView(APIView):
    """Reassign a task (operations roles only, audited)."""

    permission_classes = [IsOperations]

    @extend_schema(
        request=inline_serializer(
            name="AssignTask",
            fields={
                "assignee": serializers.IntegerField(
                    required=False, allow_null=True, help_text="عضو مسئول"
                )
            },
        ),
        responses={200: TaskSerializer},
    )
    def post(self, request, pk):
        task = Task.objects.filter(pk=pk).first()
        if task is None:
            return Response(
                {"detail": "وظیفه یافت نشد."}, status=status.HTTP_404_NOT_FOUND
            )
        member = Member.objects.filter(
            pk=request.data.get("assignee"), is_active=True
        ).first()
        old_name = task.assignee.full_name if task.assignee else None
        task.assignee = member
        task.save(update_fields=["assignee", "updated_at"])
        record_audit(
            request,
            action="task_assigned",
            entity_type="task",
            entity_id=task.pk,
            entity_label=task.title,
            team=task.project.team,
            old_value={"assignee": old_name},
            new_value={"assignee": member.full_name if member else None},
        )
        return Response(TaskSerializer(task).data)

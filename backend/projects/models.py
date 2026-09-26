from django.conf import settings
from django.db import models

from core.constants import Priority, ProjectRisk, ProjectStatus
from core.models import BaseModel


class Project(BaseModel):
    """A project owned by a team.

    ``risk_status`` is derived from transparent, configurable rules (see
    ``projects.risk``) and refreshed periodically; it is never a
    subjective productivity judgement.
    """

    team = models.ForeignKey(
        "teams.Team",
        on_delete=models.CASCADE,
        related_name="projects",
        verbose_name="تیم",
    )
    name = models.CharField("نام پروژه", max_length=300)
    description = models.TextField("توضیحات", blank=True)
    owner = models.ForeignKey(
        "teams.Member",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="owned_projects",
        verbose_name="مالک/مدبر پروژه",
    )
    status = models.CharField(
        "وضعیت",
        max_length=20,
        choices=ProjectStatus.CHOICES,
        default=ProjectStatus.PLANNED,
        db_index=True,
    )
    priority = models.CharField(
        "اولویت",
        max_length=20,
        choices=Priority.CHOICES,
        default=Priority.MEDIUM,
        db_index=True,
    )
    risk_status = models.CharField(
        "وضعیت ریسک",
        max_length=20,
        choices=ProjectRisk.CHOICES,
        default=ProjectRisk.ON_TRACK,
        db_index=True,
    )
    start_date = models.DateField("تاریخ شروع", null=True, blank=True)
    expected_completion = models.DateField(
        "تاریخ اتمام مورد انتظار", null=True, blank=True
    )
    actual_completion = models.DateField("تاریخ اتمام واقعی", null=True, blank=True)
    progress_percent = models.PositiveIntegerField("درصد پیشرفت", default=0)
    client = models.CharField("کلاینت/دستگاه درخواست‌کننده", max_length=200, blank=True)

    members = models.ManyToManyField(
        "teams.Member",
        through="ProjectMember",
        related_name="projects",
        verbose_name="اعضا",
    )

    class Meta:
        verbose_name = "پروژه"
        verbose_name_plural = "پروژه‌ها"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["team", "status"]),
            models.Index(fields=["team", "priority"]),
        ]

    def __str__(self):
        return self.name

    # --- Derived helpers ---------------------------------------------------
    @property
    def is_active(self):
        return self.status in ProjectStatus.ACTIVE_STATUSES

    @property
    def open_blocker_count(self):
        return self.blockers.filter(status="open").count()

    @property
    def days_to_expected_completion(self):
        if not self.expected_completion:
            return None
        from django.utils import timezone

        delta = (self.expected_completion - timezone.localdate()).days
        return delta


class ProjectMember(models.Model):
    """Assignment of a member to a project (with role on the project)."""

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="project_members"
    )
    member = models.ForeignKey(
        "teams.Member", on_delete=models.CASCADE, related_name="project_memberships"
    )
    is_lead = models.BooleanField("مسئول پروژه", default=False)
    assigned_at = models.DateTimeField(auto_now_add=True)
    unassigned_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "عضو پروژه"
        verbose_name_plural = "اعضای پروژه"
        unique_together = [("project", "member")]
        indexes = [models.Index(fields=["member", "project"])]

    @property
    def is_current(self):
        return self.unassigned_at is None

    def __str__(self):
        return f"{self.member} @ {self.project}"


class ProjectStatusHistory(BaseModel):
    """History of project status and key-field changes (status, expected
    completion, progress). Complements the audit log with a project-scoped
    timeline that managers read directly on the project page.
    """

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="status_history"
    )
    field = models.CharField(
        "فیلد", max_length=30
    )  # status / expected_completion / ...
    old_value = models.CharField("مقدار قبل", max_length=200, blank=True)
    new_value = models.CharField("مقدار بعد", max_length=200, blank=True)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name="تغییردهنده",
    )
    note = models.TextField("توضیح", blank=True)

    class Meta:
        verbose_name = "تاریخچه وضعیت پروژه"
        verbose_name_plural = "تاریخچه وضعیت پروژه"
        ordering = ["-created_at", "-id"]
        indexes = [models.Index(fields=["project", "-created_at"])]

    def __str__(self):
        return f"{self.project_id}:{self.field} {self.old_value}->{self.new_value}"

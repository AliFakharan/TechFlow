from django.conf import settings
from django.db import models

from core.constants import Priority, TaskStatus, WorkType
from core.models import BaseModel


class Task(BaseModel):
    """A unit of work inside a project.

    ``work_type`` distinguishes project features from bugs, support, change
    requests and emergencies — a core product requirement so that "a defect
    in delivered work" is never silently booked as "a new feature".
    """

    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="tasks",
        verbose_name="پروژه",
    )
    title = models.CharField("عنوان", max_length=300)
    description = models.TextField("توضیحات", blank=True)
    assignee = models.ForeignKey(
        "teams.Member",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_tasks",
        verbose_name="مسئول",
    )
    creator = models.ForeignKey(
        "teams.Member",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_tasks",
        verbose_name="ایجادکننده",
    )
    status = models.CharField(
        "وضعیت",
        max_length=20,
        choices=TaskStatus.CHOICES,
        default=TaskStatus.TODO,
        db_index=True,
    )
    work_type = models.CharField(
        "نوع کار",
        max_length=30,
        choices=WorkType.CHOICES,
        default=WorkType.FEATURE,
    )
    priority = models.CharField(
        "اولویت",
        max_length=20,
        choices=Priority.CHOICES,
        default=Priority.MEDIUM,
    )
    started_at = models.DateTimeField("شروع", null=True, blank=True)
    completed_at = models.DateTimeField("تکمیل", null=True, blank=True)
    due_date = models.DateField("تاریخ سررسید", null=True, blank=True)
    blocked = models.BooleanField("مسدود", default=False)
    notes = models.TextField("یادداشت‌ها", blank=True)

    class Meta:
        verbose_name = "وظیفه"
        verbose_name_plural = "وظایف"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["project", "status"]),
            models.Index(fields=["assignee", "status"]),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Keep status/blocked and timestamps consistent.
        if self.status == TaskStatus.IN_PROGRESS and self.started_at is None:
            from django.utils import timezone

            self.started_at = timezone.now()
        if self.status == TaskStatus.DONE and self.completed_at is None:
            from django.utils import timezone

            self.completed_at = timezone.now()
        if self.status != TaskStatus.DONE and self.completed_at is not None:
            self.completed_at = None
        self.blocked = self.blocked or self.status == TaskStatus.BLOCKED
        super().save(*args, **kwargs)

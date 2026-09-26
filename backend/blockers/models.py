from django.db import models

from core.constants import BlockerCategory, BlockerStatus, Priority
from core.models import BaseModel


class Blocker(BaseModel):
    """Something that is preventing work from progressing.

    Blockers are first-class, highly visible on dashboards. A blocker can
    attach to a task, a project, or both — the developer picks whichever is
    most useful in 3 clicks.
    """

    title = models.CharField("عنوان", max_length=300)
    description = models.TextField("توضیحات", blank=True)
    task = models.ForeignKey(
        "work.Task",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="blockers",
        verbose_name="وظیفه",
    )
    project = models.ForeignKey(
        "projects.Project",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="blockers",
        verbose_name="پروژه",
    )
    owner = models.ForeignKey(
        "teams.Member",
        on_delete=models.CASCADE,
        related_name="blockers",
        verbose_name="صاحب مانع",
    )
    category = models.CharField(
        "دسته",
        max_length=40,
        choices=BlockerCategory.CHOICES,
        default=BlockerCategory.OTHER,
    )
    priority = models.CharField(
        "اهمیت",
        max_length=20,
        choices=Priority.CHOICES,
        default=Priority.MEDIUM,
    )
    status = models.CharField(
        "وضعیت",
        max_length=20,
        choices=BlockerStatus.CHOICES,
        default=BlockerStatus.OPEN,
        db_index=True,
    )
    resolved_at = models.DateTimeField("زمان رفع", null=True, blank=True)

    class Meta:
        verbose_name = "مانع"
        verbose_name_plural = "موانع"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["project", "status"]),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.status == BlockerStatus.RESOLVED and self.resolved_at is None:
            from django.utils import timezone

            self.resolved_at = timezone.now()
        if self.status == BlockerStatus.OPEN:
            self.resolved_at = None
        super().save(*args, **kwargs)

    @property
    def age_days(self):
        from django.utils import timezone

        return max((timezone.now() - self.created_at).days, 0)

from django.db import models

from core.constants import Priority, SupportStatus, WorkType
from core.models import BaseModel


class SupportTicket(BaseModel):
    """A first-class workload category: customer / internal support.

    No minute-by-minute time tracking: a ticket has a status, severity and
    timestamps only. This makes it possible to answer "how much capacity is
    support consuming?" without surveillance.
    """

    title = models.CharField("عنوان", max_length=300)
    description = models.TextField("توضیحات", blank=True)
    project = models.ForeignKey(
        "projects.Project",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="support_tickets",
        verbose_name="پروژه",
    )
    requester = models.CharField("درخواست‌دهنده", max_length=200, blank=True)
    assignee = models.ForeignKey(
        "teams.Member",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="support_tickets",
        verbose_name="توسعه‌دهنده مسئول",
    )
    severity = models.CharField(
        "شدت",
        max_length=20,
        choices=Priority.CHOICES,
        default=Priority.MEDIUM,
    )
    status = models.CharField(
        "وضعیت",
        max_length=20,
        choices=SupportStatus.CHOICES,
        default=SupportStatus.NEW,
        db_index=True,
    )
    work_type = models.CharField(
        "نوع کار",
        max_length=30,
        choices=WorkType.CHOICES,
        default=WorkType.SUPPORT,
    )
    started_at = models.DateTimeField("شروع", null=True, blank=True)
    resolved_at = models.DateTimeField("حل‌شدن", null=True, blank=True)
    notes = models.TextField("یادداشت‌ها", blank=True)

    class Meta:
        verbose_name = "تیکت پشتیبانی"
        verbose_name_plural = "تیکت‌های پشتیبانی"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["assignee", "status"]),
            models.Index(fields=["project", "status"]),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.status in ("assigned", "in_progress") and self.started_at is None:
            from django.utils import timezone

            self.started_at = timezone.now()
        if self.status in ("resolved", "closed") and self.resolved_at is None:
            from django.utils import timezone

            self.resolved_at = timezone.now()
        super().save(*args, **kwargs)

    @property
    def is_open(self):
        return self.status in SupportStatus.OPEN_STATUSES

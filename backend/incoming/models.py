from django.conf import settings
from django.db import models

from core.constants import IncomingWorkStatus
from core.models import BaseModel


class IncomingWork(BaseModel):
    """Unexpected / unplanned work that arrives at the team.

    Recording incoming work here prevents it from disappearing into
    conversations and makes it possible to explain later why projects were
    delayed ("we absorbed N unplanned items this week").
    """

    team = models.ForeignKey(
        "teams.Team",
        on_delete=models.CASCADE,
        related_name="incoming_work",
        verbose_name="تیم",
    )
    title = models.CharField("عنوان", max_length=300)
    description = models.TextField("توضیحات", blank=True)
    source = models.CharField("منبع/درخواست‌کننده", max_length=200, blank=True)
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name="ثبت‌کننده",
    )
    status = models.CharField(
        "وضعیت",
        max_length=30,
        choices=IncomingWorkStatus.CHOICES,
        default=IncomingWorkStatus.NEW,
        db_index=True,
    )
    # Where it ended up, if converted.
    converted_project = models.ForeignKey(
        "projects.Project",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="incoming_conversions",
        verbose_name="پروژه هدف",
    )
    converted_task = models.ForeignKey(
        "work.Task",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="incoming_conversions",
        verbose_name="وظیفه هدف",
    )
    converted_support = models.ForeignKey(
        "support.SupportTicket",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="incoming_conversions",
        verbose_name="تیکت هدف",
    )

    class Meta:
        verbose_name = "کار ورودی"
        verbose_name_plural = "کارهای ورودی"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["team", "status"]),
        ]

    def __str__(self):
        return self.title

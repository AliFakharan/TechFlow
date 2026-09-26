from django.conf import settings
from django.db import models

from core.constants import Role
from core.models import BaseModel


class Team(BaseModel):
    """A delivery team inside an organization.

    MVP deploys one team; the model supports many.
    """

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="teams",
        verbose_name="سازمان",
    )
    name = models.CharField("نام تیم", max_length=200)
    code = models.SlugField("کد تیم", max_length=50)
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="managed_teams",
        verbose_name="مدیر تیم",
    )
    scrum_master = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="scrum_master_teams",
        verbose_name="اسکرم مستر",
    )

    class Meta:
        verbose_name = "تیم"
        verbose_name_plural = "تیم‌ها"
        unique_together = [("organization", "code")]

    def __str__(self):
        return f"{self.name} ({self.code})"


class Member(BaseModel):
    """A person attached to the system with a role and a home team.

    ``user`` is the authentication identity. ``team`` is the team the
    person belongs to (capacity and allocations are scoped by team).
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="member",
        verbose_name="کاربر",
    )
    full_name = models.CharField("نام و نام خانوادگی", max_length=200)
    email = models.EmailField("ایمیل", blank=True)
    organization = models.ForeignKey(
        "organizations.Organization",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="members",
        verbose_name="سازمان",
    )
    team = models.ForeignKey(
        Team,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="members",
        verbose_name="تیم",
    )
    role = models.CharField(
        "نقش",
        max_length=20,
        choices=Role.CHOICES,
        default=Role.DEVELOPER,
    )
    is_active = models.BooleanField("فعال", default=True)

    class Meta:
        verbose_name = "عضو"
        verbose_name_plural = "اعضا"

    def __str__(self):
        return self.full_name

    # --- Convenience -----------------------------------------------------
    @property
    def role_label(self):
        return Role.ROLE_LABELS.get(self.role, self.role)

from django.db import models

from core.models import BaseModel


class Organization(BaseModel):
    """Top-level container (e.g. the Technology department).

    The data model is built multi-team / multi-department from day one,
    even though the MVP deploys a single team.
    """

    name = models.CharField("نام سازمان", max_length=200)
    code = models.SlugField("کد سازمان", max_length=50, unique=True)

    class Meta:
        verbose_name = "سازمان"
        verbose_name_plural = "سازمان‌ها"

    def __str__(self):
        return self.name

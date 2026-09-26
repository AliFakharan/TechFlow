from django.db import models
from django.db.models import Sum

from core.models import BaseModel


class CapacityAllocation(BaseModel):
    """Lightweight, percentage-based capacity allocation.

    Answers "Where is this developer's working capacity going?" without
    timesheets. A developer is allocated to projects + a global "support"
    bucket (project=None). The system does NOT force totals to 100%; totals
    above 100% are surfaced as an overallocation warning on dashboards.
    """

    SUPPORT_BUCKET = "support"  # reserved project_id semantics

    member = models.ForeignKey(
        "teams.Member",
        on_delete=models.CASCADE,
        related_name="allocations",
        verbose_name="عضو",
    )
    project = models.ForeignKey(
        "projects.Project",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="allocations",
        verbose_name="پروژه",
        help_text="برای سهم «پشتیبانی» خالی بگذارید.",
    )
    percent = models.PositiveIntegerField("درصد", default=10)

    class Meta:
        verbose_name = "تخصیص ظرفیت"
        verbose_name_plural = "تخصیص‌های ظرفیت"
        unique_together = [("member", "project")]
        ordering = ["member", "-percent"]

    def __str__(self):
        target = self.project.name if self.project_id else "پشتیبانی"
        return f"{self.member} → {target}: {self.percent}%"

    # --- Queries -----------------------------------------------------------
    @classmethod
    def totals_for_team(cls, team):
        """Per-member allocation totals for a team (developers only),
        including the support bucket.

        Returns a dict: {member_id: {"total": int, "support": int,
        "projects": [{project_id, percent}]}}
        """
        from core.constants import Role

        rows = (
            cls.objects.filter(
                member__team=team, member__is_active=True, member__role=Role.DEVELOPER
            )
            .select_related("project")
            .values_list("member_id", "project_id", "percent")
        )
        result = {}
        for member_id, project_id, percent in rows:
            entry = result.setdefault(
                member_id, {"total": 0, "support": 0, "projects": []}
            )
            entry["total"] += percent
            if project_id is None:
                entry["support"] += percent
            else:
                entry["projects"].append({"project_id": project_id, "percent": percent})
        return result

    @classmethod
    def per_project_for_team(cls, team):
        """Total percent of team capacity consumed per project + support."""
        from core.constants import Role

        rows = (
            cls.objects.filter(
                member__team=team, member__is_active=True, member__role=Role.DEVELOPER
            )
            .values("project")
            .annotate(total=Sum("percent"))
            .order_by("-total")
        )
        out = []
        for row in rows:
            out.append(
                {
                    "project_id": row["project"],
                    "total_percent": row["total"],
                    "label": ("پشتیبانی" if row["project"] is None else None),
                }
            )
        return out

    @classmethod
    def overallocated_members(cls, team, threshold=100):
        from core.constants import Role

        totals = cls.totals_for_team(team)
        members = list(
            team.members.filter(is_active=True, role=Role.DEVELOPER).values_list(
                "id", "full_name"
            )
        )
        out = []
        for member_id, full_name in members:
            total = totals.get(member_id, {}).get("total", 0)
            if total > threshold:
                out.append(
                    {"member_id": member_id, "full_name": full_name, "total": total}
                )
        return out

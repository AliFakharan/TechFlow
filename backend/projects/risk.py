"""Transparent, configurable project risk rules.

Deliberate product decision: NO subjective risk scores. A project is
"at risk" or "blocked" only when one of the documented rules fires, and
each firing rule is reported so a manager can see *why*.

Rules (thresholds are configurable in settings / env):

1. BLOCKED — the project has at least one open critical blocker, or its
   status is ``blocked``.
2. AT RISK — expected completion is within RISK_DEADLINE_SOON_DAYS and
   progress is below 100% (work remains while the deadline approaches).
3. AT RISK — the project has no update (task/project change) for
   RISK_STALE_UPDATE_DAYS while it is active.
4. AT RISK — the project's allocation total exceeds
   RISK_OVERALLOCATION_THRESHOLD percent (capacity warning).

These rules answer "Why isn't this project moving?" with auditable
evidence, not an opaque score.
"""

from django.conf import settings
from django.utils import timezone


def evaluate_project(project, now=None):
    """Return (risk_status, [reason strings]) for a project."""
    now = now or timezone.now()
    reasons = []
    blocked = False

    # Rule 1: open critical blocker or blocked status.
    open_critical_blockers = (
        project.blockers.filter(status="open").count()
        if hasattr(project, "blockers")
        else 0
    )
    from .models import ProjectStatus  # local import to avoid cycle

    if project.status == ProjectStatus.BLOCKED:
        blocked = True
        reasons.append("وضعیت پروژه «مسدود» است.")
    if open_critical_blockers and project.priority in ("critical",):
        reasons.append("پروژه دارای مانع باز و اولویت بحرانی است.")

    # Rule 2: deadline approaching with remaining work.
    if project.is_active:
        delta = project.days_to_expected_completion
        if delta is not None:
            threshold = settings.RISK_DEADLINE_SOON_DAYS
            if 0 <= delta <= threshold and project.progress_percent < 100:
                reasons.append(
                    f"تاریخ اتمام نزدیک است (حدود {delta} روز) و هنوز کار باقی مانده است."
                )

        # Rule 3: stale updates.
        stale_days = settings.RISK_STALE_UPDATE_DAYS
        last_activity = _last_activity(project)
        if last_activity is not None:
            idle_days = (now - last_activity).days
            if idle_days >= stale_days:
                reasons.append(f"پروژه بیش از {stale_days} روز به‌روزرسانی نشده است.")

        # Rule 4: overallocation.
        total = _allocation_total(project)
        if total is not None and total > settings.RISK_OVERALLOCATION_THRESHOLD:
            reasons.append(
                f"ظرفیت تخصیص داده‌شده ({total}٪) از حد هشدار فراتر رفته است."
            )

    if blocked:
        return "blocked", reasons
    if reasons:
        return "at_risk", reasons
    return "on_track", []


def _last_activity(project):
    """Most recent meaningful activity: task update, project update."""
    candidates = []
    if project.updated_at:
        candidates.append(project.updated_at)
    task_qs = project.tasks.all()
    if task_qs.exists():
        last_task = task_qs.order_by("-updated_at").first()
        if last_task and last_task.updated_at:
            candidates.append(last_task.updated_at)
    return max(candidates) if candidates else None


def _allocation_total(project):
    from capacity.models import CapacityAllocation

    rows = CapacityAllocation.objects.filter(project=project).values_list(
        "percent", flat=True
    )
    total = sum(rows)
    return total if rows else None


def refresh_risk_for_project(project, save=True):
    """Recompute and persist risk_status; return (status, reasons)."""
    status, reasons = evaluate_project(project)
    if save and project.risk_status != status:
        from audit_app.services import record_audit

        record_audit(
            None,
            action="project_updated",
            entity_type="project",
            entity_id=project.pk,
            entity_label=project.name,
            team=project.team,
            old_value={"risk_status": project.risk_status},
            new_value={"risk_status": status},
            note="؛ ".join(reasons),
        )
        project.risk_status = status
        project.save(update_fields=["risk_status", "updated_at"])
    return status, reasons


def refresh_all_risks(teams=None):
    """Refresh risk status for all active projects (called by API/views)."""
    from .models import Project

    qs = Project.objects.filter(status__in=_active_statuses())
    if teams is not None:
        qs = qs.filter(team_id__in=teams)
    count = 0
    for project in qs.prefetch_related("blockers", "tasks"):
        refresh_risk_for_project(project)
        count += 1
    return count


def _active_statuses():
    from .models import ProjectStatus

    return ProjectStatus.ACTIVE_STATUSES

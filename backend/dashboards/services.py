"""Dashboard data builders.

The frontend renders four dashboards from these builders:

* developer  — "what is on me right now"
* manager    — "what is the team doing / what is stuck"
* scrum      — "the operational cockpit (manager + operations signals)"
* deputy     — "high-level: projects, capacity, risks, priority changes"

All risk signals come from ``projects.risk`` (transparent, configurable
rules). No subjective productivity scores are computed here.
"""

from django.conf import settings
from django.db.models import Count, Q, Sum
from django.utils import timezone

from audit_app.models import PriorityChange
from core.constants import (
    BlockerStatus,
    IncomingWorkStatus,
    Priority,
    ProjectStatus,
    Role,
    SupportStatus,
    TaskStatus,
)
from core.permissions import get_member
from projects.models import Project
from projects.risk import evaluate_project, refresh_risk_for_project
from teams.models import Member

from capacity.models import CapacityAllocation
from blockers.models import Blocker
from incoming.models import IncomingWork
from support.models import SupportTicket
from work.models import Task


def _member(request):
    return get_member(request.user)


# ---------------------------------------------------------------------------
# Shared fragments
# ---------------------------------------------------------------------------
def _active_projects(team):
    return Project.objects.filter(team=team, status__in=ProjectStatus.ACTIVE_STATUSES)


def _project_row(project):
    return {
        "id": project.id,
        "name": project.name,
        "status": project.status,
        "priority": project.priority,
        "risk_status": project.risk_status,
        "expected_completion": (
            project.expected_completion.isoformat()
            if project.expected_completion
            else None
        ),
        "progress_percent": project.progress_percent,
        "owner_name": project.owner.full_name if project.owner else None,
        "member_count": project.project_members.filter(
            unassigned_at__isnull=True
        ).count(),
        "days_to_expected_completion": project.days_to_expected_completion,
        "open_blocker_count": project.blockers.filter(
            status=BlockerStatus.OPEN
        ).count(),
        "updated_at": project.updated_at,
    }


def _blocker_row(blocker):
    return {
        "id": blocker.id,
        "title": blocker.title,
        "category": blocker.category,
        "priority": blocker.priority,
        "status": blocker.status,
        "owner_name": blocker.owner.full_name if blocker.owner else None,
        "project_name": blocker.project.name if blocker.project_id else None,
        "created_at": blocker.created_at,
        "age_days": blocker.age_days,
    }


def _support_summary(team):
    open_qs = SupportTicket.objects.filter(
        status__in=SupportStatus.OPEN_STATUSES, project__team=team
    )
    rows = open_qs.values("project").annotate(total=Count("id")).order_by("-total")
    project_names = {
        p.id: p.name
        for p in Project.objects.filter(team=team, id__in=[r["project"] for r in rows])
    }
    by_project = []
    for r in rows:
        by_project.append(
            {
                "project_id": r["project"],
                "project_name": (
                    project_names.get(r["project"], "؟") if r["project"] else "عمومی"
                ),
                "open_count": r["total"],
            }
        )
    return {
        "open_total": open_qs.count(),
        "by_project": by_project,
        "created_last_7_days": SupportTicket.objects.filter(
            project__team=team,
            created_at__gte=timezone.now() - timezone.timedelta(days=7),
        ).count(),
        "resolved_last_7_days": SupportTicket.objects.filter(
            project__team=team,
            resolved_at__gte=timezone.now() - timezone.timedelta(days=7),
        ).count(),
    }


def _capacity_by_project(team):
    rows = (
        CapacityAllocation.objects.filter(member__team=team, member__is_active=True)
        .values("project")
        .annotate(total=Sum("percent"))
    )
    names = {
        p.id: p.name
        for p in Project.objects.filter(
            team=team, id__in=[r["project"] for r in rows if r["project"]]
        )
    }
    out = []
    for r in rows:
        out.append(
            {
                "project_id": r["project"],
                "label": (
                    names.get(r["project"], "پشتیبانی") if r["project"] else "پشتیبانی"
                ),
                "total_percent": r["total"],
            }
        )
    return out


def _priority_changes(team, days=14):
    rows = (
        PriorityChange.objects.filter(project__team=team)
        .filter(created_at__gte=timezone.now() - timezone.timedelta(days=days))
        .select_related("project", "changed_by")
    )
    out = []
    for pc in rows:
        actor = pc.changed_by
        member = getattr(actor, "member", None) if actor else None
        out.append(
            {
                "id": pc.id,
                "project_id": pc.project_id,
                "project_name": pc.project.name,
                "old_priority": pc.old_priority,
                "new_priority": pc.new_priority,
                "changed_by": (
                    member.full_name
                    if member
                    else (actor.get_full_name() or actor.username if actor else None)
                ),
                "reason": pc.reason,
                "impact": pc.impact,
                "created_at": pc.created_at,
            }
        )
    return out


def _incoming_summary(team, days=14):
    qs = IncomingWork.objects.filter(
        team=team, created_at__gte=timezone.now() - timezone.timedelta(days=days)
    )
    open_qs = IncomingWork.objects.filter(
        team=team,
        status__in=[
            IncomingWorkStatus.NEW,
            IncomingWorkStatus.EVALUATING,
            IncomingWorkStatus.ACCEPTED,
        ],
    )
    recent = [
        {
            "id": w.id,
            "title": w.title,
            "source": w.source,
            "status": w.status,
            "created_at": w.created_at,
        }
        for w in open_qs[:10]
    ]
    return {
        "open_count": open_qs.count(),
        "created_last_7_days": qs.filter(
            created_at__gte=timezone.now() - timezone.timedelta(days=7)
        ).count(),
        "converted_last_14_days": qs.filter(status__startswith="converted").count(),
        "rejected_last_14_days": qs.filter(status=IncomingWorkStatus.REJECTED).count(),
        "recent": recent,
    }


# ---------------------------------------------------------------------------
# Developer dashboard
# ---------------------------------------------------------------------------
def developer_dashboard(request):
    member = _member(request)
    if member is None:
        return {"error": "no_member"}
    now = timezone.now()
    my_tasks = (
        Task.objects.filter(assignee=member)
        .exclude(status=TaskStatus.DONE)
        .select_related("project")
        .order_by("-updated_at")
    )
    return {
        "view": "developer",
        "member": {"id": member.id, "full_name": member.full_name, "role": member.role},
        "my_tasks": [
            {
                "id": t.id,
                "title": t.title,
                "status": t.status,
                "work_type": t.work_type,
                "priority": t.priority,
                "project_name": t.project.name,
                "due_date": t.due_date.isoformat() if t.due_date else None,
                "updated_at": t.updated_at,
            }
            for t in my_tasks[:30]
        ],
        "my_tasks_by_status": {
            s: Task.objects.filter(assignee=member, status=s).count()
            for s in dict(TaskStatus.CHOICES)
        },
        "my_projects": [
            {
                "id": p.id,
                "name": p.name,
                "status": p.status,
                "priority": p.priority,
                "progress_percent": p.progress_percent,
            }
            for p in member.projects.filter(status__in=ProjectStatus.ACTIVE_STATUSES)
        ],
        "my_blockers": [
            _blocker_row(b)
            for b in Blocker.objects.filter(
                owner=member, status=BlockerStatus.OPEN
            ).select_related("project")[:20]
        ],
        "my_support": [
            {
                "id": t.id,
                "title": t.title,
                "severity": t.severity,
                "status": t.status,
                "project_name": t.project.name if t.project_id else None,
            }
            for t in SupportTicket.objects.filter(
                assignee=member, status__in=SupportStatus.OPEN_STATUSES
            )[:20]
        ],
        "my_workload": {
            "total_percent": sum(a.percent for a in member.allocations.all()),
            "allocations": [
                {
                    "project_id": a.project_id,
                    "project_name": a.project.name if a.project_id else "پشتیبانی",
                    "percent": a.percent,
                }
                for a in member.allocations.select_related("project")
            ],
        },
    }


# ---------------------------------------------------------------------------
# Manager + Scrum master dashboards
# ---------------------------------------------------------------------------
def _team_dashboard_base(request, team):
    """Shared data for manager & scrum dashboards."""
    # Refresh risks for all active projects so signals are current.
    from projects.risk import refresh_risk_for_project

    for p in _active_projects(team).prefetch_related("blockers", "tasks"):
        refresh_risk_for_project(p)
    projects = list(Project.objects.filter(team=team).select_related("owner"))
    active = [p for p in projects if p.status in ProjectStatus.ACTIVE_STATUSES]
    at_risk = [p for p in active if p.risk_status == "at_risk"]
    blocked = [p for p in active if p.risk_status == "blocked"]
    deadline_soon = [
        p
        for p in active
        if p.days_to_expected_completion is not None
        and 0 <= p.days_to_expected_completion <= 14
    ]
    open_blockers = (
        Blocker.objects.filter(project__team=team, status=BlockerStatus.OPEN)
        .select_related("owner", "project")
        .order_by("-created_at")
    )
    aging = [b for b in open_blockers if b.age_days >= settings.BLOCKER_AGING_DAYS]
    # Work distribution by type (active projects only).
    work_dist = (
        Task.objects.filter(
            project__team=team, project__status__in=ProjectStatus.ACTIVE_STATUSES
        )
        .values("work_type")
        .annotate(total=Count("id"))
    )
    # Overloaded / underallocated developers.
    from capacity.models import CapacityAllocation

    totals = CapacityAllocation.totals_for_team(team)
    members = list(
        team.members.filter(is_active=True, role=Role.DEVELOPER).order_by("full_name")
    )
    overloaded = [
        {
            "member_id": m.id,
            "full_name": m.full_name,
            "total_percent": totals.get(m.id, {}).get("total", 0),
        }
        for m in members
        if totals.get(m.id, {}).get("total", 0) > settings.RISK_OVERALLOCATION_THRESHOLD
    ]
    underloaded = [
        {
            "member_id": m.id,
            "full_name": m.full_name,
            "total_percent": totals.get(m.id, {}).get("total", 0),
        }
        for m in members
        if totals.get(m.id, {}).get("total", 0) < 50
    ]
    # Stale projects (active, no activity for threshold days).
    from projects.risk import _last_activity

    stale = []
    for p in active:
        last = _last_activity(p)
        if last is None:
            continue
        idle = (timezone.now() - last).days
        if idle >= settings.RISK_STALE_UPDATE_DAYS:
            stale.append({"id": p.id, "name": p.name, "idle_days": idle})
    return {
        "projects": [
            _project_row(p)
            for p in sorted(
                active, key=lambda x: Priority.WEIGHT.get(x.priority, 0), reverse=True
            )
        ],
        "at_risk_projects": [_project_row(p) for p in at_risk],
        "blocked_projects": [_project_row(p) for p in blocked],
        "deadline_soon_projects": [_project_row(p) for p in deadline_soon],
        "open_blockers": [_blocker_row(b) for b in open_blockers[:30]],
        "aging_blockers": [_blocker_row(b) for b in aging[:20]],
        "work_distribution": {r["work_type"]: r["total"] for r in work_dist},
        "support": _support_summary(team),
        "capacity_by_project": _capacity_by_project(team),
        "priority_changes": _priority_changes(team),
        "incoming": _incoming_summary(team),
        "overloaded_developers": overloaded,
        "underloaded_developers": underloaded,
        "stale_projects": stale,
        "members": [
            {
                "id": m.id,
                "full_name": m.full_name,
                "role": m.role,
                "allocated_percent": totals.get(m.id, {}).get("total", 0),
            }
            for m in members
        ],
    }


def manager_dashboard(request):
    member = _member(request)
    if member is None or member.team is None:
        return {"error": "no_team"}
    data = _team_dashboard_base(request, member.team)
    data["view"] = "manager"
    return data


def scrum_dashboard(request):
    member = _member(request)
    if member is None or member.team is None:
        return {"error": "no_team"}
    data = _team_dashboard_base(request, member.team)
    data["view"] = "scrum"
    # Recent operational changes (audit) for the operations cockpit.
    from audit_app.models import AuditLog

    recent = AuditLog.objects.filter(
        team=member.team,
        created_at__gte=timezone.now()
        - timezone.timedelta(days=settings.RECENT_EVENTS_DAYS),
    ).select_related("actor")[:40]
    data["recent_events"] = [
        {
            "id": a.id,
            "action": a.action,
            "actor_name": a.actor_name,
            "entity_type": a.entity_type,
            "entity_label": a.entity_label,
            "old_value": a.old_value,
            "new_value": a.new_value,
            "note": a.note,
            "created_at": a.created_at,
        }
        for a in recent
    ]
    return data


# ---------------------------------------------------------------------------
# Deputy (executive) dashboard — high level only
# ---------------------------------------------------------------------------
def deputy_dashboard(request):
    member = _member(request)
    if member is None or member.team is None:
        return {"error": "no_team"}
    team = member.team
    from projects.risk import refresh_risk_for_project

    for p in _active_projects(team).prefetch_related("blockers", "tasks"):
        refresh_risk_for_project(p)
    active = list(_active_projects(team).select_related("owner"))
    # Only important blockers: open, high/critical, or on at-risk/blocked projects.
    important = Blocker.objects.filter(
        Q(priority__in=["high", "critical"])
        | Q(project__risk_status__in=["at_risk", "blocked"]),
        status=BlockerStatus.OPEN,
        project__team=team,
    ).select_related("owner", "project")
    return {
        "view": "deputy",
        "team_name": team.name,
        "active_projects": [
            _project_row(p)
            for p in sorted(
                active, key=lambda x: Priority.WEIGHT.get(x.priority, 0), reverse=True
            )
        ],
        "projects_at_risk": [
            _project_row(p) for p in active if p.risk_status != "on_track"
        ],
        "important_blockers": [_blocker_row(b) for b in important[:15]],
        "capacity_by_project": _capacity_by_project(team),
        "support_load": _support_summary(team),
        "priority_changes": _priority_changes(team),
        "incoming": _incoming_summary(team),
    }


# ---------------------------------------------------------------------------
# Weekly team report
# ---------------------------------------------------------------------------
def weekly_report(request):
    member = _member(request)
    if member is None or member.team is None:
        return {"error": "no_team"}
    team = member.team
    now = timezone.now()
    week_ago = now - timezone.timedelta(days=7)

    active = list(_active_projects(team).select_related("owner"))
    for p in active:
        refresh_risk_for_project(p)

    tasks_done = Task.objects.filter(project__team=team, completed_at__gte=week_ago)
    done_by_type = {
        r["work_type"]: r["total"]
        for r in tasks_done.values("work_type").annotate(total=Count("id"))
    }
    open_blockers = Blocker.objects.filter(
        project__team=team, status=BlockerStatus.OPEN
    ).select_related("owner", "project")
    support = _support_summary(team)

    return {
        "view": "weekly_report",
        "team_name": team.name,
        "period": {"from": week_ago.date().isoformat(), "to": now.date().isoformat()},
        "summary": {
            "active_projects": len(active),
            "at_risk_projects": sum(1 for p in active if p.risk_status == "at_risk"),
            "blocked_projects": sum(1 for p in active if p.risk_status == "blocked"),
            "open_blockers": open_blockers.count(),
            "open_support_tickets": support["open_total"],
        },
        "active_projects": [
            _project_row(p)
            for p in sorted(
                active, key=lambda x: Priority.WEIGHT.get(x.priority, 0), reverse=True
            )
        ],
        "work_completed": {
            "total": tasks_done.count(),
            "by_type": done_by_type,
            "items": [
                {
                    "id": t.id,
                    "title": t.title,
                    "work_type": t.work_type,
                    "project_name": t.project.name,
                    "assignee_name": t.assignee.full_name if t.assignee else None,
                    "completed_at": t.completed_at,
                }
                for t in tasks_done.select_related("project", "assignee")[:50]
            ],
        },
        "current_blockers": [_blocker_row(b) for b in open_blockers[:30]],
        "support": support,
        "priority_changes": _priority_changes(team, days=7),
        "incoming": _incoming_summary(team, days=7),
        "projects_at_risk": [
            _project_row(p) for p in active if p.risk_status != "on_track"
        ],
        "capacity_distribution": _capacity_by_project(team),
    }

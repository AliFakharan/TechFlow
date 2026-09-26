from django.conf import settings
from django.db import models

from core.models import BaseModel


class AuditAction(models.TextChoices):
    PROJECT_CREATED = "project_created", "project created"
    PROJECT_UPDATED = "project_updated", "project updated"
    PROJECT_STATUS_CHANGED = "project_status_changed", "project status changed"
    PRIORITY_CHANGED = "priority_changed", "priority changed"
    EXPECTED_COMPLETION_CHANGED = (
        "expected_completion_changed",
        "expected completion changed",
    )
    MEMBER_ASSIGNED = "member_assigned", "member assigned"
    MEMBER_REMOVED = "member_removed", "member removed"
    TASK_CREATED = "task_created", "task created"
    TASK_STATUS_CHANGED = "task_status_changed", "task status changed"
    TASK_ASSIGNED = "task_assigned", "task assigned"
    BLOCKER_CREATED = "blocker_created", "blocker created"
    BLOCKER_RESOLVED = "blocker_resolved", "blocker resolved"
    SUPPORT_CREATED = "support_created", "support ticket created"
    SUPPORT_STATUS_CHANGED = "support_status_changed", "support status changed"
    CAPACITY_UPDATED = "capacity_updated", "capacity updated"
    INCOMING_WORK_CREATED = "incoming_work_created", "incoming work created"
    INCOMING_WORK_CONVERTED = "incoming_work_converted", "incoming work converted"
    MEMBER_ROLE_CHANGED = "member_role_changed", "member role changed"


class AuditLog(BaseModel):
    """Generic, append-only audit trail of important operational events.

    Trivial UI interactions are NOT logged — only decisions and state
    changes that a manager would want to reconstruct later ("what changed,
    when, and by whom?").
    """

    action = models.CharField(
        "action", max_length=50, choices=AuditAction.choices, db_index=True
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
        verbose_name="executor",
    )
    actor_name = models.CharField("executor name", max_length=200, blank=True)
    entity_type = models.CharField("entity type", max_length=50, db_index=True)
    entity_id = models.CharField("entity ID", max_length=64)
    entity_label = models.CharField("entity title", max_length=300, blank=True)
    team = models.ForeignKey(
        "teams.Team",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="audit_logs",
        verbose_name="team",
    )
    old_value = models.JSONField("old value", null=True, blank=True)
    new_value = models.JSONField("new value", null=True, blank=True)
    note = models.TextField("notes", blank=True)

    class Meta:
        verbose_name = "change record"
        verbose_name_plural = "change records"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["entity_type", "entity_id"]),
        ]

    def __str__(self):
        return f"{self.action} [{self.entity_type}:{self.entity_id}]"


class PriorityChange(BaseModel):
    """Dedicated history of project priority changes.

    The audit log records *that* a change happened; this table records the
    full narrative: old/new priority, who changed it, why, and the stated
    impact. The purpose is to make trade-offs visible — not to blame
    management.
    """

    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="priority_changes",
        verbose_name="project",
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name="changed by",
    )
    old_priority = models.CharField("old priority", max_length=20)
    new_priority = models.CharField("new priority", max_length=20)
    reason = models.TextField("reason", blank=True)
    impact = models.TextField("impact", blank=True)

    class Meta:
        verbose_name = "priority change"
        verbose_name_plural = "priority changes"
        ordering = ["-created_at", "-id"]
        indexes = [models.Index(fields=["project", "-created_at"])]

    def __str__(self):
        return (
            f"{self.project_id}: {self.old_priority} -> {self.new_priority} "
            f"({self.created_at:%Y-%m-%d})"
        )

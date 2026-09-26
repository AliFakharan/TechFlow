"""Audit service: single entry point for writing audit entries.

Usage::

    record_audit(request, action="priority_changed",
                 entity_type="project", entity_id=project.pk,
                 entity_label=project.name, team=project.team,
                 old_value={...}, new_value={...}, note="...")

Keeping one function means every app logs the same shape, and the audit
list endpoint stays simple.
"""

from django.utils import timezone


def record_audit(
    request,
    *,
    action,
    entity_type,
    entity_id,
    entity_label="",
    team=None,
    old_value=None,
    new_value=None,
    note=""
):
    """Write an audit log entry for an important event.

    ``request`` may be None (e.g. in seed scripts) — actor is left null.
    """
    from .models import AuditLog

    user = None
    if request is not None and getattr(request, "user", None) is not None:
        if request.user.is_authenticated:
            user = request.user

    actor_name = ""
    if user is not None:
        member = getattr(user, "member", None)
        actor_name = (
            member.full_name
            if member is not None
            else (user.get_full_name() or user.username)
        )

    return AuditLog.objects.create(
        action=action,
        actor=user,
        actor_name=actor_name,
        entity_type=entity_type,
        entity_id=str(entity_id),
        entity_label=entity_label,
        team=team,
        old_value=old_value,
        new_value=new_value,
        note=note,
    )

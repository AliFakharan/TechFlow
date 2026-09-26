"""Role-based permission classes for the TechFlow API.

Roles live on ``Member.role``. A request user is resolved to their Member
profile via the ``User.member`` reverse relation (set by a signal on user
creation).

Permission model:

* ``IsManagementDecision``  — admin / team manager. May change project
  priority, status, expected completion, and assignments.
* ``IsOperations``          — admin / team manager / scrum master. May record
  operational information and view all team data.
* ``IsExecutiveRead``       — admin / deputy / team manager / scrum master.
  Read access to management dashboards and history.
* Developers may always manage their own work items (own tasks, own
  blockers, own support tickets).
"""

from rest_framework.permissions import BasePermission, IsAuthenticated

from .constants import Role


def get_member(user):
    """Return the Member profile for a user, or None."""
    if user is None or not user.is_authenticated:
        return None
    try:
        return user.member
    except Exception:
        return None


def has_role(user, roles):
    member = get_member(user)
    return member is not None and member.role in roles


def is_admin_user(user):
    """System administrator: superuser flag OR the admin role."""
    return bool(
        user
        and user.is_authenticated
        and (user.is_superuser or has_role(user, {Role.ADMIN}))
    )


class IsAuthenticatedOrNone(BasePermission):
    """Placeholder to keep imports tidy; standard IsAuthenticated is used."""

    def has_permission(self, request, view):
        return IsAuthenticated().has_permission(request, view)


class IsManagementDecision(BasePermission):
    """Changing priorities / statuses / assignments (audited decisions)."""

    message = "فقط مدیر تیم یا مدیر سیستم می‌تواند این تغییر مدیریتی را انجام دهد."

    def has_permission(self, request, view):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return request.user and request.user.is_authenticated
        return has_role(request.user, Role.MANAGEMENT_DECISION_ROLES)


class IsPriorityChange(BasePermission):
    """Change a project's priority.

    Management roles plus the deputy (the deputy is executive/read-oriented
    but is explicitly allowed to change management priorities).
    """

    message = "تغییر اولویت فقط برای مدیر سیستم، مدیر تیم و معاون فناوری مجاز است."

    def has_permission(self, request, view):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return request.user and request.user.is_authenticated
        return has_role(request.user, Role.PRIORITY_CHANGE_ROLES)


class IsOperations(BasePermission):
    """Team-level operational data (blockers, incoming work, capacity...)."""

    def has_permission(self, request, view):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return request.user and request.user.is_authenticated
        return has_role(request.user, Role.OPERATIONS_ROLES)


class IsExecutiveRead(BasePermission):
    """Dashboards, reports, priority history, audit history."""

    def has_permission(self, request, view):
        return has_role(
            request.user,
            {Role.ADMIN, Role.DEPUTY, Role.TEAM_MANAGER, Role.SCRUM_MASTER},
        )


class IsOperationsOrOwner(BasePermission):
    """Operations roles for any item; developers only for their own items."""

    def has_permission(self, request, view):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return request.user and request.user.is_authenticated
        if has_role(request.user, Role.OPERATIONS_ROLES):
            return True
        # Developers can create items (blockers/support) for their own use.
        return has_role(request.user, {Role.DEVELOPER})

    def has_object_permission(self, request, view, obj):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        if has_role(request.user, Role.OPERATIONS_ROLES):
            return True
        owner_field = getattr(view, "owner_field", "owner")
        owner = getattr(obj, owner_field, None)
        return owner == request.user

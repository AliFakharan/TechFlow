"""Shared enums/constants for the TechFlow domain.

These are plain Python constants used across models, serializers, and the
risk engine. Values are English-safe; the frontend maps them to Persian.
"""


# --- Organization roles -----------------------------------------------------
class Role:
    ADMIN = "admin"
    DEPUTY = "deputy"
    TEAM_MANAGER = "team_manager"
    SCRUM_MASTER = "scrum_master"
    DEVELOPER = "developer"

    CHOICES = [
        (ADMIN, "admin"),
        (DEPUTY, "deputy"),
        (TEAM_MANAGER, "team_manager"),
        (SCRUM_MASTER, "scrum_master"),
        (DEVELOPER, "developer"),
    ]

    ROLE_LABELS = {
        ADMIN: "مدیر سیستم",
        DEPUTY: "معاون فناوری",
        TEAM_MANAGER: "مدیر تیم",
        SCRUM_MASTER: "اسکرم مستر",
        DEVELOPER: "توسعه‌دهنده",
    }

    # Read-only executive roles.
    EXECUTIVE_ROLES = {ADMIN, DEPUTY}
    # Roles allowed to change management decisions (priority, status,
    # expected completion, assignments).
    MANAGEMENT_DECISION_ROLES = {ADMIN, TEAM_MANAGER}
    # Roles that may change a project's priority. The deputy is executive and
    # read-oriented but is explicitly allowed to change management priorities.
    PRIORITY_CHANGE_ROLES = {ADMIN, DEPUTY, TEAM_MANAGER}
    # Roles that aggregate/operate the team (may record operational data).
    OPERATIONS_ROLES = {ADMIN, TEAM_MANAGER, SCRUM_MASTER}


# --- Projects ----------------------------------------------------------------
class ProjectStatus:
    PLANNED = "planned"
    ACTIVE = "active"
    BLOCKED = "blocked"
    TESTING = "testing"
    BUG_FIXING = "bug_fixing"
    DONE = "done"
    PAUSED = "paused"
    CANCELLED = "cancelled"

    CHOICES = [
        (PLANNED, "planned"),
        (ACTIVE, "active"),
        (BLOCKED, "blocked"),
        (TESTING, "testing"),
        (BUG_FIXING, "bug_fixing"),
        (DONE, "done"),
        (PAUSED, "paused"),
        (CANCELLED, "cancelled"),
    ]

    ACTIVE_STATUSES = [PLANNED, ACTIVE, BLOCKED, TESTING, BUG_FIXING]
    CLOSED_STATUSES = [DONE, CANCELLED]


class ProjectRisk:
    ON_TRACK = "on_track"
    AT_RISK = "at_risk"
    BLOCKED = "blocked"

    CHOICES = [
        (ON_TRACK, "on_track"),
        (AT_RISK, "at_risk"),
        (BLOCKED, "blocked"),
    ]


# --- Priority (shared by projects, tasks, support) ----------------------------
class Priority:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    CHOICES = [
        (LOW, "low"),
        (MEDIUM, "medium"),
        (HIGH, "high"),
        (CRITICAL, "critical"),
    ]

    # Higher weight = more urgent.
    WEIGHT = {LOW: 1, MEDIUM: 2, HIGH: 3, CRITICAL: 4}


# --- Tasks --------------------------------------------------------------------
class TaskStatus:
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    DONE = "done"

    CHOICES = [
        (TODO, "todo"),
        (IN_PROGRESS, "in_progress"),
        (BLOCKED, "blocked"),
        (DONE, "done"),
    ]


class WorkType:
    FEATURE = "feature"
    BUG = "bug"
    SUPPORT = "support"
    CHANGE_REQUEST = "change_request"
    EMERGENCY = "emergency"

    CHOICES = [
        (FEATURE, "feature"),
        (BUG, "bug"),
        (SUPPORT, "support"),
        (CHANGE_REQUEST, "change_request"),
        (EMERGENCY, "emergency"),
    ]


# --- Blockers -----------------------------------------------------------------
class BlockerStatus:
    OPEN = "open"
    RESOLVED = "resolved"

    CHOICES = [
        (OPEN, "open"),
        (RESOLVED, "resolved"),
    ]


class BlockerCategory:
    REQUIREMENT_AMBIGUITY = "requirement_ambiguity"
    WAITING_ANALYSIS = "waiting_analysis"
    WAITING_CLIENT = "waiting_client"
    TECHNICAL = "technical"
    ENVIRONMENT = "environment"
    DEPENDENCY = "dependency"
    MANAGEMENT_DECISION = "management_decision"
    OTHER = "other"

    CHOICES = [
        (REQUIREMENT_AMBIGUITY, "requirement_ambiguity"),
        (WAITING_ANALYSIS, "waiting_analysis"),
        (WAITING_CLIENT, "waiting_client"),
        (TECHNICAL, "technical"),
        (ENVIRONMENT, "environment"),
        (DEPENDENCY, "dependency"),
        (MANAGEMENT_DECISION, "management_decision"),
        (OTHER, "other"),
    ]


# --- Support --------------------------------------------------------------------
class SupportStatus:
    NEW = "new"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    WAITING = "waiting"
    RESOLVED = "resolved"
    CLOSED = "closed"

    CHOICES = [
        (NEW, "new"),
        (ASSIGNED, "assigned"),
        (IN_PROGRESS, "in_progress"),
        (WAITING, "waiting"),
        (RESOLVED, "resolved"),
        (CLOSED, "closed"),
    ]

    OPEN_STATUSES = [NEW, ASSIGNED, IN_PROGRESS, WAITING]


# --- Incoming work ----------------------------------------------------------------
class IncomingWorkStatus:
    NEW = "new"
    EVALUATING = "evaluating"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CONVERTED_TASK = "converted_task"
    CONVERTED_SUPPORT = "converted_support"
    CONVERTED_PROJECT = "converted_project"

    CHOICES = [
        (NEW, "new"),
        (EVALUATING, "evaluating"),
        (ACCEPTED, "accepted"),
        (REJECTED, "rejected"),
        (CONVERTED_TASK, "converted_task"),
        (CONVERTED_SUPPORT, "converted_support"),
        (CONVERTED_PROJECT, "converted_project"),
    ]

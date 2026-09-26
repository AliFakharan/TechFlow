"""Seed realistic demo data for TechFlow.

Usage:
    python manage.py seed_demo            # aborts if data already exists
    python manage.py seed_demo --if-empty # skips silently when data exists
    python manage.py seed_demo --force    # wipes and re-seeds

The demo set is designed so that every dashboard looks meaningful
immediately: one high-priority project approaching its deadline, one
blocked project, one paused project, one support-heavy project, an
overallocated developer, aging blockers, and a full priority-change
history.
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from audit_app.models import PriorityChange
from audit_app.services import record_audit
from capacity.models import CapacityAllocation
from blockers.models import Blocker
from core.constants import (
    BlockerCategory,
    BlockerStatus,
    IncomingWorkStatus,
    Priority,
    ProjectStatus,
    Role,
    SupportStatus,
    TaskStatus,
    WorkType,
)
from incoming.models import IncomingWork
from organizations.models import Organization
from projects.models import Project, ProjectMember, ProjectStatusHistory
from support.models import SupportTicket
from teams.models import Member, Team
from work.models import Task

PASSWORD = "techflow123"


class Command(BaseCommand):
    help = "Seed realistic demo data for TechFlow."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Wipe existing domain data and re-seed.",
        )
        parser.add_argument(
            "--if-empty",
            action="store_true",
            help="Only seed when no data exists (used by Docker).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if Organization.objects.exists():
            if options["force"]:
                self.stdout.write("Wiping existing demo data...")
                self._wipe()
            elif options["if_empty"]:
                self.stdout.write("Data already exists; skipping seed.")
                return
            else:
                self.stdout.write(
                    self.style.ERROR(
                        "Data already exists. Use --force to wipe and re-seed."
                    )
                )
                return

        today = timezone.localdate()

        # --- Organization + team -------------------------------------------
        org = Organization.objects.create(
            name="Technology Department", code="technology"
        )
        team = Team.objects.create(
            organization=org, name="Software Development Team", code="dev-team"
        )

        # --- Users + members -------------------------------------------------
        def make_user(username, full_name, role):
            from django.contrib.auth.models import User

            user = User.objects.create_user(
                username=username,
                password=PASSWORD,
                email=f"{username}@techflow.local",
            )
            member = user.member  # created by the post_save signal
            member.full_name = full_name
            member.email = f"{username}@techflow.local"
            member.organization = org
            member.team = team
            member.role = role
            member.save()
            return user, member

        self.stdout.write("Creating users...")
        admin_u, admin_m = make_user("admin", "System Administrator", Role.ADMIN)
        deputy_u, deputy_m = make_user("deputy", "Dr. Reza Karimi", Role.DEPUTY)
        manager_u, manager_m = make_user(
            "manager", "Mohammad Reza Ahmadi", Role.TEAM_MANAGER
        )
        scrum_u, scrum_m = make_user("scrum", "Sara Mohammadi", Role.SCRUM_MASTER)
        developers = []
        for username, name in [
            ("ali", "Ali Jafari"),
            ("reza", "Reza Nasiri"),
            ("mehdi", "Mehdi Rahimi"),
            ("nima", "Nima Kavousi"),
            ("arash", "Arash Yazdani"),
            ("kaveh", "Kaveh Sadeghi"),
            ("shayan", "Shayan Farhang"),
            ("behnam", "Behnam Ghasemi"),
        ]:
            _, member = make_user(username, name, Role.DEVELOPER)
            developers.append(member)
        ali, reza, mehdi, nima, arash, kaveh, shayan, behnam = developers
        team.manager = manager_u
        team.scrum_master = scrum_u
        team.save(update_fields=["manager", "scrum_master"])

        # --- Projects ---------------------------------------------------------
        self.stdout.write("Creating projects...")
        p_portal = Project.objects.create(
            team=team,
            name="Student Portal",
            description="New student self-service portal replacing the legacy system.",
            owner=manager_m,
            status=ProjectStatus.ACTIVE,
            priority=Priority.CRITICAL,
            start_date=today - timedelta(days=60),
            expected_completion=today + timedelta(days=10),
            progress_percent=70,
            client="University Administration",
        )
        p_finance = Project.objects.create(
            team=team,
            name="Financial Reporting System",
            description="Consolidated financial reporting for the finance department.",
            owner=manager_m,
            status=ProjectStatus.ACTIVE,
            priority=Priority.HIGH,
            start_date=today - timedelta(days=90),
            expected_completion=today + timedelta(days=45),
            progress_percent=55,
            client="Finance Department",
        )
        p_mobile = Project.objects.create(
            team=team,
            name="Mobile Field Support App",
            description="Mobile app for field technicians to log and resolve issues.",
            owner=scrum_m,
            status=ProjectStatus.TESTING,
            priority=Priority.MEDIUM,
            start_date=today - timedelta(days=120),
            expected_completion=today + timedelta(days=25),
            progress_percent=85,
            client="Operations",
        )
        p_docs = Project.objects.create(
            team=team,
            name="Document Archive Migration",
            description="Migrate 10 years of paper and legacy electronic documents.",
            owner=manager_m,
            status=ProjectStatus.BLOCKED,
            priority=Priority.MEDIUM,
            start_date=today - timedelta(days=40),
            expected_completion=today + timedelta(days=70),
            progress_percent=30,
            client="IT Services",
        )
        p_crm = Project.objects.create(
            team=team,
            name="Customer Relationship System",
            description="CRM for customer service; in bug-fixing phase after v1 launch.",
            owner=manager_m,
            status=ProjectStatus.BUG_FIXING,
            priority=Priority.MEDIUM,
            start_date=today - timedelta(days=200),
            expected_completion=today + timedelta(days=15),
            progress_percent=90,
            client="Customer Service",
        )
        p_legacy = Project.objects.create(
            team=team,
            name="Legacy HR System Replacement",
            description="Replace the 15-year-old HR system; paused due to priority change.",
            owner=manager_m,
            status=ProjectStatus.PAUSED,
            priority=Priority.LOW,
            start_date=today - timedelta(days=150),
            expected_completion=today + timedelta(days=120),
            progress_percent=40,
            client="HR Department",
        )

        # Project membership
        def assign(project, *members, lead=None):
            for m in members:
                ProjectMember.objects.create(
                    project=project, member=m, is_lead=(m == lead)
                )

        assign(p_portal, ali, reza, mehdi, nima, lead=ali)
        assign(p_finance, kaveh, arash, lead=kaveh)
        assign(p_mobile, shayan, behnam, arash, lead=shayan)
        assign(p_docs, nima, behnam, lead=nima)
        assign(p_crm, reza, kaveh, lead=reza)

        # Baseline status history
        for p in [p_portal, p_finance, p_mobile, p_docs, p_crm, p_legacy]:
            ProjectStatusHistory.objects.create(
                project=p,
                field="status",
                old_value="",
                new_value=p.status,
                changed_by=manager_u,
                note="ایجاد پروژه",
            )

        # --- Tasks --------------------------------------------------------------
        self.stdout.write("Creating tasks...")

        def task(
            project,
            title,
            assignee,
            status,
            work_type,
            priority,
            due_days=None,
            done_days_ago=None,
            start_days_ago=None,
            desc="",
        ):
            t = Task.objects.create(
                project=project,
                title=title,
                description=desc,
                assignee=assignee,
                creator=scrum_m,
                status=status,
                work_type=work_type,
                priority=priority,
                due_date=(
                    (today + timedelta(days=due_days)) if due_days is not None else None
                ),
            )
            if start_days_ago is not None:
                t.started_at = timezone.now() - timedelta(days=start_days_ago)
                t.save(update_fields=["started_at"])
            if done_days_ago is not None:
                t.completed_at = timezone.now() - timedelta(days=done_days_ago)
                t.save(update_fields=["completed_at"])
            return t

        # Student Portal (critical, at risk: deadline in 10 days, 70%)
        task(
            p_portal,
            "Login & SSO integration",
            ali,
            TaskStatus.IN_PROGRESS,
            WorkType.FEATURE,
            Priority.HIGH,
            due_days=7,
            start_days_ago=20,
        )
        task(
            p_portal,
            "Grade transcript page",
            ali,
            TaskStatus.TODO,
            WorkType.FEATURE,
            Priority.HIGH,
            due_days=9,
            start_days_ago=0,
        )
        task(
            p_portal,
            "Course registration flow",
            reza,
            TaskStatus.IN_PROGRESS,
            WorkType.FEATURE,
            Priority.CRITICAL,
            due_days=6,
            start_days_ago=15,
        )
        task(
            p_portal,
            "Registration deadline race condition",
            reza,
            TaskStatus.BLOCKED,
            WorkType.BUG,
            Priority.CRITICAL,
            due_days=5,
            start_days_ago=10,
        )
        task(
            p_portal,
            "Notification emails on registration",
            mehdi,
            TaskStatus.TODO,
            WorkType.FEATURE,
            Priority.MEDIUM,
            due_days=9,
        )
        task(
            p_portal,
            "Performance tuning of student search",
            nima,
            TaskStatus.IN_PROGRESS,
            WorkType.FEATURE,
            Priority.MEDIUM,
            due_days=8,
            start_days_ago=5,
        )
        task(
            p_portal,
            "Fix login failure on Safari",
            nima,
            TaskStatus.DONE,
            WorkType.BUG,
            Priority.HIGH,
            done_days_ago=3,
            start_days_ago=8,
        )
        task(
            p_portal,
            "Portal accessibility (WCAG) fixes",
            mehdi,
            TaskStatus.DONE,
            WorkType.FEATURE,
            Priority.LOW,
            done_days_ago=2,
            start_days_ago=12,
        )

        # Financial reporting (high)
        task(
            p_finance,
            "Consolidation engine",
            kaveh,
            TaskStatus.IN_PROGRESS,
            WorkType.FEATURE,
            Priority.HIGH,
            due_days=20,
            start_days_ago=30,
        )
        task(
            p_finance,
            "Excel export for monthly report",
            arash,
            TaskStatus.IN_PROGRESS,
            WorkType.FEATURE,
            Priority.MEDIUM,
            due_days=14,
            start_days_ago=10,
        )
        task(
            p_finance,
            "Currency rounding errors in totals",
            kaveh,
            TaskStatus.DONE,
            WorkType.BUG,
            Priority.HIGH,
            done_days_ago=5,
            start_days_ago=9,
        )
        task(
            p_finance,
            "Quarterly report template changes",
            arash,
            TaskStatus.TODO,
            WorkType.CHANGE_REQUEST,
            Priority.MEDIUM,
            due_days=25,
        )

        # Mobile app (testing)
        task(
            p_mobile,
            "UAT defect triage",
            shayan,
            TaskStatus.IN_PROGRESS,
            WorkType.BUG,
            Priority.HIGH,
            due_days=10,
            start_days_ago=12,
        )
        task(
            p_mobile,
            "Offline mode for ticket capture",
            behnam,
            TaskStatus.IN_PROGRESS,
            WorkType.FEATURE,
            Priority.MEDIUM,
            due_days=12,
            start_days_ago=8,
        )
        task(
            p_mobile,
            "Push notification integration",
            shayan,
            TaskStatus.DONE,
            WorkType.FEATURE,
            Priority.MEDIUM,
            done_days_ago=1,
            start_days_ago=15,
        )

        # Document archive (blocked)
        task(
            p_docs,
            "Document classification rules",
            nima,
            TaskStatus.BLOCKED,
            WorkType.FEATURE,
            Priority.MEDIUM,
            due_days=30,
            start_days_ago=25,
        )
        task(
            p_docs,
            "Scanner integration",
            behnam,
            TaskStatus.TODO,
            WorkType.FEATURE,
            Priority.MEDIUM,
            due_days=40,
        )

        # CRM (bug fixing)
        task(
            p_crm,
            "Dashboard filter regression",
            reza,
            TaskStatus.IN_PROGRESS,
            WorkType.BUG,
            Priority.HIGH,
            due_days=4,
            start_days_ago=6,
        )
        task(
            p_crm,
            "Customer merge tool",
            kaveh,
            TaskStatus.TODO,
            WorkType.FEATURE,
            Priority.LOW,
            due_days=12,
        )
        task(
            p_crm,
            "Fix CSV import encoding",
            kaveh,
            TaskStatus.DONE,
            WorkType.BUG,
            Priority.MEDIUM,
            done_days_ago=6,
            start_days_ago=10,
        )

        # Legacy (paused) — stale, no recent activity
        task(
            p_legacy,
            "HR data model mapping",
            arash,
            TaskStatus.TODO,
            WorkType.FEATURE,
            Priority.LOW,
            desc="Paused with the project.",
        )

        # --- Blockers -------------------------------------------------------------
        self.stdout.write("Creating blockers...")
        Blocker.objects.create(
            title="Registration deadline rules are ambiguous",
            description="The client has not confirmed whether deadlines are calendar-based or working-day based; registration flow cannot be finalized.",
            task=Task.objects.filter(
                title="Registration deadline race condition"
            ).first(),
            project=p_portal,
            owner=reza,
            category=BlockerCategory.REQUIREMENT_AMBIGUITY,
            priority=Priority.CRITICAL,
            status=BlockerStatus.OPEN,
        )
        Blocker.objects.create(
            title="Client approval for archive classification pending",
            description="The classification rules document has been sent to the client 9 days ago; no response.",
            project=p_docs,
            owner=nima,
            category=BlockerCategory.WAITING_CLIENT,
            priority=Priority.HIGH,
            status=BlockerStatus.OPEN,
        )
        # Make it "aging": backdate creation 12 days.
        Blocker.objects.filter(
            title="Client approval for archive classification pending"
        ).update(created_at=timezone.now() - timedelta(days=12))
        Blocker.objects.create(
            title="Staging environment database access revoked",
            description="Security team revoked DB credentials for the staging environment; integration tests cannot run.",
            project=p_mobile,
            owner=shayan,
            category=BlockerCategory.ENVIRONMENT,
            priority=Priority.HIGH,
            status=BlockerStatus.OPEN,
        )
        Blocker.objects.create(
            title="Figma designs for portal not delivered",
            description="Frontend is building the transcript page without approved designs.",
            project=p_portal,
            owner=ali,
            category=BlockerCategory.WAITING_ANALYSIS,
            priority=Priority.MEDIUM,
            status=BlockerStatus.RESOLVED,
        )
        Blocker.objects.filter(title="Figma designs for portal not delivered").update(
            created_at=timezone.now() - timedelta(days=20)
        )
        Blocker.objects.filter(title="Figma designs for portal not delivered").update(
            resolved_at=timezone.now() - timedelta(days=10)
        )

        # --- Support tickets ---------------------------------------------------------
        self.stdout.write("Creating support tickets...")

        def ticket(
            project,
            title,
            assignee,
            severity,
            status,
            requester,
            created_days_ago=5,
            resolved_days_ago=None,
            work_type="support",
            desc="",
        ):
            t = SupportTicket(
                title=title,
                description=desc,
                project=project,
                requester=requester,
                assignee=assignee,
                severity=severity,
                status=status,
                work_type=work_type,
            )
            t.save()
            t.created_at = timezone.now() - timedelta(days=created_days_ago)
            if resolved_days_ago is not None:
                t.resolved_at = timezone.now() - timedelta(days=resolved_days_ago)
            t.save(update_fields=["created_at", "resolved_at", "updated_at"])
            return t

        # Financial reporting is the support-heavy project.
        ticket(
            p_finance,
            "Cannot access monthly report module",
            kaveh,
            Priority.HIGH,
            SupportStatus.IN_PROGRESS,
            "Finance dept.",
            created_days_ago=2,
            desc="Users in the finance group get 403.",
        )
        ticket(
            p_finance,
            "Duplicate entries after bulk import",
            arash,
            Priority.MEDIUM,
            SupportStatus.ASSIGNED,
            "Finance dept.",
            created_days_ago=3,
        )
        ticket(
            p_finance,
            "Report PDF garbled in Arabic",
            kaveh,
            Priority.MEDIUM,
            SupportStatus.NEW,
            "Finance dept.",
            created_days_ago=1,
        )
        ticket(
            p_finance,
            "Export takes over 10 minutes",
            arash,
            Priority.HIGH,
            SupportStatus.IN_PROGRESS,
            "CFO office",
            created_days_ago=6,
        )
        ticket(
            p_finance,
            "Wrong tax rate in Q2 report",
            kaveh,
            Priority.CRITICAL,
            SupportStatus.RESOLVED,
            "Finance dept.",
            created_days_ago=8,
            resolved_days_ago=4,
        )
        ticket(
            p_finance,
            "Password reset email not arriving",
            kaveh,
            Priority.LOW,
            SupportStatus.CLOSED,
            "IT helpdesk",
            created_days_ago=15,
            resolved_days_ago=12,
        )
        # Student portal support
        ticket(
            p_portal,
            "Portal login loop for new students",
            nima,
            Priority.HIGH,
            SupportStatus.ASSIGNED,
            "Registrar office",
            created_days_ago=1,
        )
        ticket(
            p_portal,
            "Transcript print layout broken",
            mehdi,
            Priority.MEDIUM,
            SupportStatus.RESOLVED,
            "Registrar office",
            created_days_ago=5,
            resolved_days_ago=2,
        )
        # CRM support
        ticket(
            p_crm,
            "Customer search returns wrong branch",
            reza,
            Priority.MEDIUM,
            SupportStatus.IN_PROGRESS,
            "Customer service",
            created_days_ago=2,
        )
        ticket(
            p_crm,
            "Call log missing after agent switch",
            kaveh,
            Priority.LOW,
            SupportStatus.WAITING,
            "Customer service",
            created_days_ago=7,
        )
        # Mobile app support
        ticket(
            p_mobile,
            "Crash when attaching photos on Android 13",
            behnam,
            Priority.HIGH,
            SupportStatus.IN_PROGRESS,
            "Field operations",
            created_days_ago=3,
        )

        # --- Capacity allocation --------------------------------------------------------
        self.stdout.write("Creating capacity allocations...")

        def alloc(member, project, percent):
            CapacityAllocation.objects.update_or_create(
                member=member, project=project, defaults={"percent": percent}
            )

        # Ali: OVERALLOCATED (110%) — deliberate demo of the warning.
        alloc(ali, p_portal, 70)
        alloc(ali, p_finance, 40)
        # Reza: portal + CRM
        alloc(reza, p_portal, 60)
        alloc(reza, p_crm, 20)
        alloc(reza, None, 10)  # support bucket
        # Mehdi: portal + support
        alloc(mehdi, p_portal, 60)
        alloc(mehdi, None, 40)
        # Nima: portal + docs
        alloc(nima, p_portal, 50)
        alloc(nima, p_docs, 40)
        # Kaveh: finance (support-heavy)
        alloc(kaveh, p_finance, 70)
        alloc(kaveh, p_crm, 10)
        alloc(kaveh, None, 20)
        # Arash: finance + mobile
        alloc(arash, p_finance, 50)
        alloc(arash, p_mobile, 30)
        alloc(arash, None, 20)
        # Shayan: mobile
        alloc(shayan, p_mobile, 80)
        alloc(shayan, None, 20)
        # Behnam: mobile + docs
        alloc(behnam, p_mobile, 50)
        alloc(behnam, p_docs, 30)
        alloc(behnam, None, 20)

        # --- Priority change history ---------------------------------------------------------
        self.stdout.write("Creating priority change history...")
        pc1 = PriorityChange.objects.create(
            project=p_finance,
            changed_by=deputy_u,
            old_priority=Priority.MEDIUM,
            new_priority=Priority.HIGH,
            reason="Finance department reporting deadline moved up.",
            impact="One developer (Kaveh) took a larger share of his capacity for this project.",
        )
        PriorityChange.objects.create(
            project=p_portal,
            changed_by=deputy_u,
            old_priority=Priority.HIGH,
            new_priority=Priority.CRITICAL,
            reason="Urgent organizational requirement: portal must be live before semester start.",
            impact="Two developers temporarily moved from Financial Reporting; Nima pulled from Document Archive.",
        )
        pc3 = PriorityChange.objects.create(
            project=p_legacy,
            changed_by=manager_u,
            old_priority=Priority.MEDIUM,
            new_priority=Priority.LOW,
            reason="HR deferred the replacement scope to next fiscal year.",
            impact="Project paused; Arash returned to Financial Reporting.",
        )
        # Backdate priority changes so history spans the last two weeks.
        PriorityChange.objects.filter(pk=pc1.pk).update(
            created_at=timezone.now() - timedelta(days=12)
        )
        PriorityChange.objects.filter(pk=pc3.pk).update(
            created_at=timezone.now() - timedelta(days=18)
        )

        # --- Incoming work --------------------------------------------------------------------
        self.stdout.write("Creating incoming work...")
        w1 = IncomingWork.objects.create(
            team=team,
            title="New audit requirement from regulator",
            description="Regulator requires quarterly audit logs export by end of month.",
            source="Compliance",
            reported_by=manager_u,
            status=IncomingWorkStatus.EVALUATING,
        )
        IncomingWork.objects.create(
            team=team,
            title="Ad-hoc request: export 2024 payroll data",
            description="One-off data export requested by finance.",
            source="Finance dept.",
            reported_by=manager_u,
            status=IncomingWorkStatus.CONVERTED_SUPPORT,
            converted_support=SupportTicket.objects.filter(
                title="Export takes over 10 minutes"
            ).first(),
        )
        IncomingWork.objects.create(
            team=team,
            title="Management request: dashboard for CEO",
            description="Build a custom CEO dashboard.",
            source="Executive office",
            reported_by=manager_u,
            status=IncomingWorkStatus.REJECTED,
        )
        IncomingWork.objects.create(
            team=team,
            title="Helpdesk: integrate with new VPN",
            description="VPN vendor changed; developer access is affected.",
            source="IT helpdesk",
            reported_by=scrum_u,
            status=IncomingWorkStatus.NEW,
        )
        IncomingWork.objects.filter(pk=w1.pk).update(
            created_at=timezone.now() - timedelta(days=4)
        )

        # --- Audit trail for seeded history ------------------------------------------------------
        self.stdout.write("Writing audit entries for seeded history...")
        for pc in PriorityChange.objects.filter(project__team=team):
            record_audit(
                None,
                action="priority_changed",
                entity_type="project",
                entity_id=pc.project_id,
                entity_label=pc.project.name,
                team=team,
                old_value={"priority": pc.old_priority},
                new_value={"priority": pc.new_priority, "reason": pc.reason},
                note=pc.impact,
            )
        # Backdate audit entries to match the priority change timestamps.
        from audit_app.models import AuditLog

        AuditLog.objects.filter(
            action="priority_changed",
            entity_type="project",
            entity_id=str(p_finance.pk),
        ).update(created_at=timezone.now() - timedelta(days=12))
        AuditLog.objects.filter(
            action="priority_changed",
            entity_type="project",
            entity_id=str(p_legacy.pk),
        ).update(created_at=timezone.now() - timedelta(days=18))
        # Status history backdates for the paused project.
        ProjectStatusHistory.objects.filter(project=p_legacy).update(
            created_at=timezone.now() - timedelta(days=18)
        )

        # Refresh risk statuses so dashboards show computed risk.
        from projects.risk import refresh_risk_for_project

        for p in Project.objects.filter(team=team):
            refresh_risk_for_project(p)

        # --- Summary -------------------------------------------------------------------------
        self.stdout.write(self.style.SUCCESS("Demo data seeded successfully."))
        self.stdout.write("")
        self.stdout.write("Demo accounts (password for all: techflow123):")
        for username, name, role in [
            ("admin", "System Administrator", "admin"),
            ("deputy", "Dr. Reza Karimi", "deputy"),
            ("manager", "Mohammad Reza Ahmadi", "team_manager"),
            ("scrum", "Sara Mohammadi", "scrum_master"),
            ("ali", "Ali Jafari", "developer"),
            ("reza", "Reza Nasiri", "developer"),
            ("mehdi", "Mehdi Rahimi", "developer"),
            ("nima", "Nima Kavousi", "developer"),
            ("arash", "Arash Yazdani", "developer"),
            ("kaveh", "Kaveh Sadeghi", "developer"),
            ("shayan", "Shayan Farhang", "developer"),
            ("behnam", "Behnam Ghasemi", "developer"),
        ]:
            self.stdout.write(f"  {username:<10} {name:<24} ({role})")

    def _wipe(self):
        from django.contrib.auth.models import User

        from audit_app.models import AuditLog, PriorityChange
        from projects.models import Project, ProjectMember, ProjectStatusHistory
        from work.models import Task
        from blockers.models import Blocker
        from support.models import SupportTicket
        from capacity.models import CapacityAllocation
        from incoming.models import IncomingWork
        from teams.models import Member, Team
        from organizations.models import Organization

        AuditLog.objects.all().delete()
        PriorityChange.objects.all().delete()
        ProjectMember.objects.all().delete()
        ProjectStatusHistory.objects.all().delete()
        Task.objects.all().delete()
        Blocker.objects.all().delete()
        SupportTicket.objects.all().delete()
        CapacityAllocation.objects.all().delete()
        IncomingWork.objects.all().delete()
        Member.objects.all().delete()
        Team.objects.all().delete()
        Organization.objects.all().delete()
        User.objects.filter(
            username__in=[
                "admin",
                "deputy",
                "manager",
                "scrum",
                "ali",
                "reza",
                "mehdi",
                "nima",
                "arash",
                "kaveh",
                "shayan",
                "behnam",
            ]
        ).delete()

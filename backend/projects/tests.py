"""Project creation, management decisions, and priority history tests."""

from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from audit_app.models import PriorityChange
from core.constants import Priority, ProjectStatus, Role
from core.test_utils import build_base, build_developer
from projects.models import Project, ProjectMember, ProjectStatusHistory


def make_project(team, **kwargs):
    defaults = dict(
        team=team,
        name="Test Project",
        status=ProjectStatus.ACTIVE,
        priority=Priority.MEDIUM,
    )
    defaults.update(kwargs)
    return Project.objects.create(**defaults)


class ProjectPermissionTests(APITestCase):
    def setUp(self):
        self.user, self.member, self.team, self.org = build_base(role=Role.TEAM_MANAGER)
        self.client.force_authenticate(self.user)

    def test_manager_can_create_project(self):
        resp = self.client.post(
            "/api/projects/create/",
            {
                "team": self.team.pk,
                "name": "New Project",
                "priority": Priority.LOW,
                "start_date": timezone.localdate().isoformat(),
                "expected_completion": (
                    timezone.localdate() + timedelta(days=30)
                ).isoformat(),
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Project.objects.filter(name="New Project").exists())

    def test_developer_cannot_create_project(self):
        self.client.force_authenticate(None)
        dev_user, dev_member = build_developer("dev2", team=self.team, org=self.org)
        self.client.force_authenticate(dev_user)
        resp = self.client.post(
            "/api/projects/create/",
            {"team": self.team.pk, "name": "Hacker Project"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Project.objects.filter(name="Hacker Project").exists())

    def test_developer_cannot_change_priority_via_patch(self):
        project = make_project(self.team)
        dev_user, dev_member = build_developer("dev2", team=self.team, org=self.org)
        ProjectMember.objects.create(project=project, member=dev_member)
        self.client.force_authenticate(dev_user)
        resp = self.client.patch(
            f"/api/projects/{project.pk}/",
            {"priority": Priority.CRITICAL},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        project.refresh_from_db()
        self.assertEqual(project.priority, Priority.MEDIUM)

    def test_developer_can_update_progress(self):
        project = make_project(self.team)
        dev_user, dev_member = build_developer("dev2", team=self.team, org=self.org)
        ProjectMember.objects.create(project=project, member=dev_member)
        self.client.force_authenticate(dev_user)
        resp = self.client.patch(
            f"/api/projects/{project.pk}/", {"progress_percent": 45}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        project.refresh_from_db()
        self.assertEqual(project.progress_percent, 45)

    def test_scrum_master_cannot_change_expected_completion(self):
        sm_user, sm_member = build_developer("sm2", team=self.team, org=self.org)
        sm_member.role = Role.SCRUM_MASTER
        sm_member.save()
        project = make_project(self.team)
        self.client.force_authenticate(sm_user)
        resp = self.client.patch(
            f"/api/projects/{project.pk}/",
            {
                "expected_completion": (
                    timezone.localdate() + timedelta(days=10)
                ).isoformat()
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


class PriorityHistoryTests(APITestCase):
    def setUp(self):
        self.user, self.member, self.team, self.org = build_base(role=Role.TEAM_MANAGER)
        self.client.force_authenticate(self.user)
        self.project = make_project(self.team, priority=Priority.MEDIUM)

    def test_priority_change_creates_history(self):
        resp = self.client.post(
            f"/api/projects/{self.project.pk}/priority/",
            {
                "new_priority": Priority.CRITICAL,
                "reason": "Urgent organizational requirement",
                "impact": "Two developers moved from Project A.",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.project.refresh_from_db()
        self.assertEqual(self.project.priority, Priority.CRITICAL)
        change = PriorityChange.objects.get(project=self.project)
        self.assertEqual(change.old_priority, Priority.MEDIUM)
        self.assertEqual(change.new_priority, Priority.CRITICAL)
        self.assertEqual(change.changed_by, self.user)
        self.assertIn("Urgent", change.reason)
        # Status history row also written.
        self.assertTrue(
            ProjectStatusHistory.objects.filter(
                project=self.project, field="priority"
            ).exists()
        )
        # Audit log entry written.
        from audit_app.models import AuditLog

        self.assertTrue(
            AuditLog.objects.filter(
                action="priority_changed", entity_id=str(self.project.pk)
            ).exists()
        )

    def test_priority_change_forbidden_for_developer(self):
        dev_user, _ = build_developer("dev2", team=self.team, org=self.org)
        self.client.force_authenticate(dev_user)
        resp = self.client.post(
            f"/api/projects/{self.project.pk}/priority/",
            {"new_priority": Priority.CRITICAL},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_deputy_can_change_priority(self):
        deputy_user, _ = build_developer("deputy2", team=self.team, org=self.org)
        from core.constants import Role

        member = deputy_user.member
        member.role = Role.DEPUTY
        member.save()
        self.client.force_authenticate(deputy_user)
        resp = self.client.post(
            f"/api/projects/{self.project.pk}/priority/",
            {"new_priority": Priority.CRITICAL, "reason": "Executive directive"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.project.refresh_from_db()
        self.assertEqual(self.project.priority, Priority.CRITICAL)
        self.assertTrue(PriorityChange.objects.filter(project=self.project).exists())

    def test_deputy_cannot_change_status(self):
        deputy_user, _ = build_developer("deputy3", team=self.team, org=self.org)
        from core.constants import Role

        member = deputy_user.member
        member.role = Role.DEPUTY
        member.save()
        self.client.force_authenticate(deputy_user)
        resp = self.client.post(
            f"/api/projects/{self.project.pk}/status/",
            {"status": ProjectStatus.DONE},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, ProjectStatus.ACTIVE)

    def test_deputy_cannot_patch_expected_completion(self):
        deputy_user, _ = build_developer("deputy4", team=self.team, org=self.org)
        from core.constants import Role

        member = deputy_user.member
        member.role = Role.DEPUTY
        member.save()
        self.client.force_authenticate(deputy_user)
        resp = self.client.patch(
            f"/api/projects/{self.project.pk}/",
            {
                "expected_completion": (
                    timezone.localdate() + timedelta(days=9)
                ).isoformat()
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_deputy_can_patch_priority(self):
        deputy_user, _ = build_developer("deputy5", team=self.team, org=self.org)
        from core.constants import Role

        member = deputy_user.member
        member.role = Role.DEPUTY
        member.save()
        self.client.force_authenticate(deputy_user)
        resp = self.client.patch(
            f"/api/projects/{self.project.pk}/",
            {"priority": Priority.LOW},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.project.refresh_from_db()
        self.assertEqual(self.project.priority, Priority.LOW)

    def test_priority_change_same_priority_rejected(self):
        resp = self.client.post(
            f"/api/projects/{self.project.pk}/priority/",
            {"new_priority": Priority.MEDIUM},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class StatusChangeTests(APITestCase):
    def setUp(self):
        self.user, _, self.team, self.org = build_base(role=Role.TEAM_MANAGER)
        self.client.force_authenticate(self.user)
        self.project = make_project(self.team)

    def test_status_change_audited_and_sets_completion(self):
        resp = self.client.post(
            f"/api/projects/{self.project.pk}/status/",
            {"status": ProjectStatus.DONE, "note": "shipped"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, ProjectStatus.DONE)
        self.assertIsNotNone(self.project.actual_completion)
        self.assertTrue(
            ProjectStatusHistory.objects.filter(
                project=self.project, field="status", new_value=ProjectStatus.DONE
            ).exists()
        )

    def test_assign_and_remove_member_audited(self):
        dev_user, dev_member = build_developer("dev2", team=self.team, org=self.org)
        resp = self.client.post(
            f"/api/projects/{self.project.pk}/assign/",
            {"member": dev_member.pk, "is_lead": True},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            ProjectMember.objects.filter(
                project=self.project, member=dev_member, is_lead=True
            ).exists()
        )
        resp = self.client.post(
            f"/api/projects/{self.project.pk}/remove/{dev_member.pk}/"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        pm = ProjectMember.objects.get(project=self.project, member=dev_member)
        self.assertIsNotNone(pm.unassigned_at)
        from audit_app.models import AuditLog

        self.assertTrue(AuditLog.objects.filter(action="member_assigned").exists())
        self.assertTrue(AuditLog.objects.filter(action="member_removed").exists())


class RiskEngineTests(APITestCase):
    def test_deadline_approaching_marks_at_risk(self):
        _, _, team, _ = build_base()
        project = make_project(
            team,
            expected_completion=timezone.localdate() + timedelta(days=5),
            progress_percent=40,
        )
        from projects.risk import refresh_risk_for_project

        status, reasons = refresh_risk_for_project(project)
        self.assertEqual(status, "at_risk")
        self.assertTrue(any("اتمام" in r for r in reasons))

    def test_open_critical_blocker_marks_at_risk(self):
        """Spec: 'unresolved critical blockers' => At Risk (reason reported)."""
        from blockers.models import Blocker

        _, _, team, org = build_base()
        project = make_project(team, priority=Priority.CRITICAL)
        _, owner = build_developer("dev2", team=team, org=org)
        Blocker.objects.create(
            title="Critical blocker",
            project=project,
            owner=owner,
            priority=Priority.CRITICAL,
            status="open",
        )
        from projects.risk import refresh_risk_for_project

        status, reasons = refresh_risk_for_project(project)
        self.assertEqual(status, "at_risk")
        self.assertTrue(any("مانع" in r for r in reasons))

    def test_blocked_project_status_marks_blocked(self):
        _, _, team, _ = build_base()
        project = make_project(team, status=ProjectStatus.BLOCKED)
        from projects.risk import refresh_risk_for_project

        status, reasons = refresh_risk_for_project(project)
        self.assertEqual(status, "blocked")
        self.assertTrue(any("مسدود" in r for r in reasons))

    def test_healthy_project_on_track(self):
        _, _, team, _ = build_base()
        project = make_project(
            team,
            expected_completion=timezone.localdate() + timedelta(days=60),
            progress_percent=50,
        )
        from projects.risk import refresh_risk_for_project

        status, reasons = refresh_risk_for_project(project)
        self.assertEqual(status, "on_track")
        self.assertEqual(reasons, [])

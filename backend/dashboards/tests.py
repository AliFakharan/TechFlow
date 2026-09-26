"""Dashboard + weekly report tests."""

from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from core.constants import (
    BlockerStatus,
    Priority,
    ProjectStatus,
    Role,
    SupportStatus,
    TaskStatus,
    WorkType,
)
from core.test_utils import build_base, build_developer
from projects.models import Project, ProjectMember
from work.models import Task


class DashboardTestBase(APITestCase):
    def setUp(self):
        self.user, self.member, self.team, self.org = build_base(role=Role.TEAM_MANAGER)
        self.deputy_user, self.deputy_member = build_developer(
            "dep1", team=self.team, org=self.org
        )
        self.deputy_member.role = Role.DEPUTY
        self.deputy_member.save()
        self.scrum_user, self.scrum_member = build_developer(
            "sm1", team=self.team, org=self.org
        )
        self.scrum_member.role = Role.SCRUM_MASTER
        self.scrum_member.save()
        self.dev_user, self.dev_member = build_developer(
            "dev2", team=self.team, org=self.org
        )
        self.project = Project.objects.create(
            team=self.team,
            name="DashP",
            status=ProjectStatus.ACTIVE,
            priority=Priority.HIGH,
            expected_completion=timezone.localdate() + timedelta(days=5),
            progress_percent=40,
        )
        ProjectMember.objects.create(project=self.project, member=self.dev_member)


class DeveloperDashboardTests(DashboardTestBase):
    def test_developer_sees_own_items(self):
        Task.objects.create(
            project=self.project,
            title="Mine",
            assignee=self.dev_member,
            status=TaskStatus.IN_PROGRESS,
        )
        self.client.force_authenticate(self.dev_user)
        resp = self.client.get("/api/dashboard/?view=developer")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["view"], "developer")
        self.assertEqual(resp.data["my_tasks_by_status"]["in_progress"], 1)
        self.assertEqual(resp.data["my_workload"]["total_percent"], 0)

    def test_developer_cannot_open_manager_dashboard(self):
        self.client.force_authenticate(self.dev_user)
        resp = self.client.get("/api/dashboard/?view=manager")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


class ManagerDashboardTests(DashboardTestBase):
    def test_manager_dashboard_shows_risk_and_blockers(self):
        from blockers.models import Blocker

        Blocker.objects.create(
            title="Blocked work",
            project=self.project,
            owner=self.dev_member,
            priority=Priority.HIGH,
            status=BlockerStatus.OPEN,
        )
        self.client.force_authenticate(self.user)
        resp = self.client.get("/api/dashboard/?view=manager")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        project = resp.data["projects"][0]
        # Deadline in 5 days + progress 40% => at risk.
        self.assertEqual(project["risk_status"], "at_risk")
        self.assertEqual(len(resp.data["open_blockers"]), 1)
        self.assertEqual(resp.data["open_blockers"][0]["title"], "Blocked work")
        self.assertIn("work_distribution", resp.data)
        self.assertIn("support", resp.data)
        self.assertIn("incoming", resp.data)
        self.assertIn("priority_changes", resp.data)

    def test_developer_cannot_open_manager_dashboard(self):
        self.client.force_authenticate(self.dev_user)
        resp = self.client.get("/api/dashboard/?view=manager")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


class ScrumDashboardTests(DashboardTestBase):
    def test_scrum_dashboard_includes_recent_events_and_overload(self):
        from capacity.models import CapacityAllocation

        CapacityAllocation.objects.create(
            member=self.dev_member, project=self.project, percent=120
        )
        self.client.force_authenticate(self.scrum_user)
        resp = self.client.get("/api/dashboard/?view=scrum")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["view"], "scrum")
        self.assertIn("recent_events", resp.data)
        names = [m["full_name"] for m in resp.data["overloaded_developers"]]
        self.assertIn(self.dev_member.full_name, names)


class DeputyDashboardTests(DashboardTestBase):
    def test_deputy_dashboard_high_level(self):
        self.client.force_authenticate(self.deputy_user)
        resp = self.client.get("/api/dashboard/?view=deputy")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["view"], "deputy")
        self.assertTrue(any(p["name"] == "DashP" for p in resp.data["active_projects"]))
        self.assertEqual(resp.data["active_projects"][0]["risk_status"], "at_risk")
        self.assertIn("capacity_by_project", resp.data)
        self.assertIn("support_load", resp.data)
        self.assertIn("priority_changes", resp.data)

    def test_developer_cannot_open_deputy_dashboard(self):
        self.client.force_authenticate(self.dev_user)
        resp = self.client.get("/api/dashboard/?view=deputy")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


class WeeklyReportTests(DashboardTestBase):
    def test_weekly_report_content(self):
        Task.objects.create(
            project=self.project,
            title="Done work",
            assignee=self.dev_member,
            status=TaskStatus.DONE,
            work_type=WorkType.BUG,
        )
        from support.models import SupportTicket

        SupportTicket.objects.create(
            title="Open ticket",
            project=self.project,
            assignee=self.dev_member,
            severity=Priority.HIGH,
            status=SupportStatus.IN_PROGRESS,
        )
        self.client.force_authenticate(self.user)
        resp = self.client.get("/api/reports/weekly/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["summary"]["open_support_tickets"], 1)
        self.assertEqual(resp.data["work_completed"]["by_type"].get("bug"), 1)
        self.assertIn("projects_at_risk", resp.data)
        self.assertIn("capacity_distribution", resp.data)

    def test_weekly_report_forbidden_for_developer(self):
        self.client.force_authenticate(self.dev_user)
        resp = self.client.get("/api/reports/weekly/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

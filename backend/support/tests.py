"""Support workflow tests."""

from rest_framework import status
from rest_framework.test import APITestCase

from audit_app.models import AuditLog
from core.constants import Priority, ProjectStatus, Role, SupportStatus
from core.test_utils import build_base, build_developer
from projects.models import Project
from support.models import SupportTicket


class SupportTests(APITestCase):
    def setUp(self):
        self.user, self.member, self.team, self.org = build_base(role=Role.TEAM_MANAGER)
        self.project = Project.objects.create(
            team=self.team, name="SP", status=ProjectStatus.ACTIVE
        )
        self.dev_user, self.dev_member = build_developer(
            "dev2", team=self.team, org=self.org
        )

    def test_developer_creates_ticket_for_self(self):
        self.client.force_authenticate(self.dev_user)
        resp = self.client.post(
            "/api/support/create/",
            {
                "title": "Cannot export report",
                "project": self.project.pk,
                "severity": Priority.HIGH,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        ticket = SupportTicket.objects.get(title="Cannot export report")
        self.assertEqual(ticket.assignee, self.dev_member)
        self.assertEqual(ticket.status, SupportStatus.NEW)

    def test_developer_cannot_create_for_other(self):
        other_user, other_member = build_developer("dev3", team=self.team, org=self.org)
        self.client.force_authenticate(self.dev_user)
        resp = self.client.post(
            "/api/support/create/",
            {
                "title": "Someone else's",
                "project": self.project.pk,
                "assignee": other_member.pk,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_manager_assigns_ticket(self):
        ticket = SupportTicket.objects.create(
            title="T1",
            project=self.project,
            severity=Priority.MEDIUM,
            status=SupportStatus.NEW,
        )
        self.client.force_authenticate(self.user)
        resp = self.client.post(
            f"/api/support/{ticket.pk}/assign/",
            {"assignee": self.dev_member.pk},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        ticket.refresh_from_db()
        self.assertEqual(ticket.assignee, self.dev_member)
        self.assertEqual(ticket.status, SupportStatus.ASSIGNED)

    def test_status_change_sets_timestamps_audited(self):
        ticket = SupportTicket.objects.create(
            title="T2",
            project=self.project,
            assignee=self.dev_member,
            severity=Priority.MEDIUM,
            status=SupportStatus.ASSIGNED,
        )
        self.client.force_authenticate(self.dev_user)
        resp = self.client.post(
            f"/api/support/{ticket.pk}/status/",
            {"status": SupportStatus.RESOLVED},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, SupportStatus.RESOLVED)
        self.assertIsNotNone(ticket.resolved_at)
        self.assertTrue(
            AuditLog.objects.filter(
                action="support_status_changed", entity_id=str(ticket.pk)
            ).exists()
        )

    def test_developer_cannot_touch_others_ticket(self):
        other_user, other_member = build_developer("dev3", team=self.team, org=self.org)
        ticket = SupportTicket.objects.create(
            title="T3",
            project=self.project,
            assignee=other_member,
            severity=Priority.LOW,
            status=SupportStatus.NEW,
        )
        self.client.force_authenticate(self.dev_user)
        resp = self.client.post(
            f"/api/support/{ticket.pk}/status/",
            {"status": SupportStatus.RESOLVED},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_open_filter(self):
        SupportTicket.objects.create(
            title="Open T",
            project=self.project,
            assignee=self.dev_member,
            status=SupportStatus.NEW,
        )
        SupportTicket.objects.create(
            title="Closed T",
            project=self.project,
            assignee=self.dev_member,
            status=SupportStatus.CLOSED,
        )
        self.client.force_authenticate(self.dev_user)
        resp = self.client.get("/api/support/?open=1")
        titles = [r["title"] for r in resp.data["results"]]
        self.assertIn("Open T", titles)
        self.assertNotIn("Closed T", titles)

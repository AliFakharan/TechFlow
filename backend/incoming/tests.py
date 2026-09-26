"""Incoming work capture + conversion tests."""

from rest_framework import status
from rest_framework.test import APITestCase

from audit_app.models import AuditLog
from core.constants import IncomingWorkStatus, Priority, ProjectStatus, Role
from core.test_utils import build_base, build_developer
from incoming.models import IncomingWork
from projects.models import Project
from support.models import SupportTicket
from work.models import Task


class IncomingWorkTests(APITestCase):
    def setUp(self):
        self.user, self.member, self.team, self.org = build_base(role=Role.TEAM_MANAGER)
        self.project = Project.objects.create(
            team=self.team, name="IW-P", status=ProjectStatus.ACTIVE
        )

    def test_developer_records_incoming_work(self):
        dev_user, dev_member = build_developer("dev2", team=self.team, org=self.org)
        self.client.force_authenticate(dev_user)
        resp = self.client.post(
            "/api/incoming-work/create/",
            {"title": "Urgent fix requested", "source": "Helpdesk"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        item = IncomingWork.objects.get(title="Urgent fix requested")
        self.assertEqual(item.team, self.team)
        self.assertEqual(item.status, IncomingWorkStatus.NEW)
        self.assertEqual(item.reported_by, dev_user)

    def test_convert_to_task(self):
        item = IncomingWork.objects.create(
            team=self.team,
            title="New behavior",
            source="Client",
            status=IncomingWorkStatus.EVALUATING,
        )
        self.client.force_authenticate(self.user)
        resp = self.client.post(
            f"/api/incoming-work/{item.pk}/convert/",
            {"convert_to": "task", "project": self.project.pk},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        item.refresh_from_db()
        self.assertEqual(item.status, IncomingWorkStatus.CONVERTED_TASK)
        self.assertIsNotNone(item.converted_task)
        task = Task.objects.get(pk=item.converted_task_id)
        self.assertEqual(task.work_type, "change_request")
        self.assertTrue(
            AuditLog.objects.filter(
                action="incoming_work_converted", entity_id=str(item.pk)
            ).exists()
        )

    def test_convert_to_project(self):
        item = IncomingWork.objects.create(
            team=self.team,
            title="New system",
            source="Exec",
            status=IncomingWorkStatus.ACCEPTED,
        )
        self.client.force_authenticate(self.user)
        resp = self.client.post(
            f"/api/incoming-work/{item.pk}/convert/",
            {"convert_to": "project", "title": "New System Project"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        item.refresh_from_db()
        self.assertEqual(item.status, IncomingWorkStatus.CONVERTED_PROJECT)
        self.assertIsNotNone(item.converted_project)
        self.assertTrue(Project.objects.filter(pk=item.converted_project_id).exists())

    def test_convert_to_support(self):
        item = IncomingWork.objects.create(
            team=self.team,
            title="Data export needed",
            source="Finance",
            status=IncomingWorkStatus.ACCEPTED,
        )
        self.client.force_authenticate(self.user)
        resp = self.client.post(
            f"/api/incoming-work/{item.pk}/convert/",
            {"convert_to": "support", "project": self.project.pk},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        item.refresh_from_db()
        self.assertEqual(item.status, IncomingWorkStatus.CONVERTED_SUPPORT)
        self.assertIsNotNone(item.converted_support)

    def test_developer_cannot_convert(self):
        dev_user, dev_member = build_developer("dev2", team=self.team, org=self.org)
        item = IncomingWork.objects.create(
            team=self.team, title="X", status=IncomingWorkStatus.NEW
        )
        self.client.force_authenticate(dev_user)
        resp = self.client.post(
            f"/api/incoming-work/{item.pk}/convert/",
            {"convert_to": "task", "project": self.project.pk},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_status_transition(self):
        item = IncomingWork.objects.create(
            team=self.team, title="Eval me", status=IncomingWorkStatus.NEW
        )
        self.client.force_authenticate(self.user)
        resp = self.client.post(
            f"/api/incoming-work/{item.pk}/status/",
            {"status": IncomingWorkStatus.REJECTED},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        item.refresh_from_db()
        self.assertEqual(item.status, IncomingWorkStatus.REJECTED)

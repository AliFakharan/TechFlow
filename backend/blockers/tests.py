"""Blocker creation / resolution tests."""

from rest_framework import status
from rest_framework.test import APITestCase

from audit_app.models import AuditLog
from blockers.models import Blocker
from core.constants import BlockerCategory, BlockerStatus, Priority, ProjectStatus, Role
from core.test_utils import build_base, build_developer
from projects.models import Project, ProjectMember


class BlockerTests(APITestCase):
    def setUp(self):
        self.user, self.member, self.team, self.org = build_base(role=Role.TEAM_MANAGER)
        self.project = Project.objects.create(
            team=self.team, name="BP", status=ProjectStatus.ACTIVE
        )
        self.dev_user, self.dev_member = build_developer(
            "dev2", team=self.team, org=self.org
        )
        ProjectMember.objects.create(project=self.project, member=self.dev_member)

    def test_developer_creates_blocker(self):
        self.client.force_authenticate(self.dev_user)
        resp = self.client.post(
            "/api/blockers/create/",
            {
                "title": "No Figma designs",
                "project": self.project.pk,
                "category": BlockerCategory.WAITING_ANALYSIS,
                "priority": Priority.MEDIUM,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        blocker = Blocker.objects.get(title="No Figma designs")
        # Owner is optional; when omitted it stays unset. Creator is recorded.
        self.assertIsNone(blocker.owner)
        self.assertEqual(blocker.creator, self.dev_member)
        self.assertEqual(blocker.status, BlockerStatus.OPEN)
        self.assertTrue(
            AuditLog.objects.filter(
                action="blocker_created", entity_id=str(blocker.pk)
            ).exists()
        )

    def test_developer_can_set_owner(self):
        self.client.force_authenticate(self.dev_user)
        resp = self.client.post(
            "/api/blockers/create/",
            {
                "title": "Fake",
                "project": self.project.pk,
                "owner": self.member.pk,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        blocker = Blocker.objects.get(title="Fake")
        self.assertEqual(blocker.owner, self.member)
        self.assertEqual(blocker.creator, self.dev_member)

    def test_blocker_requires_project_or_task(self):
        self.client.force_authenticate(self.dev_user)
        resp = self.client.post(
            "/api/blockers/create/",
            {"title": "No target"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_resolve_blocker_audited(self):
        blocker = Blocker.objects.create(
            title="B",
            project=self.project,
            owner=self.dev_member,
            category=BlockerCategory.OTHER,
            status=BlockerStatus.OPEN,
        )
        self.client.force_authenticate(self.dev_user)
        resp = self.client.post(
            f"/api/blockers/{blocker.pk}/resolve/", {}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        blocker.refresh_from_db()
        self.assertEqual(blocker.status, BlockerStatus.RESOLVED)
        self.assertIsNotNone(blocker.resolved_at)
        self.assertTrue(
            AuditLog.objects.filter(
                action="blocker_resolved", entity_id=str(blocker.pk)
            ).exists()
        )

    def test_cannot_resolve_others_blocker(self):
        other_user, other_member = build_developer("dev3", team=self.team, org=self.org)
        blocker = Blocker.objects.create(
            title="B2",
            project=self.project,
            owner=other_member,
            status=BlockerStatus.OPEN,
        )
        self.client.force_authenticate(self.dev_user)
        resp = self.client.post(
            f"/api/blockers/{blocker.pk}/resolve/", {}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_open_blocker_filter(self):
        Blocker.objects.create(
            title="Open B",
            project=self.project,
            owner=self.dev_member,
            status=BlockerStatus.OPEN,
        )
        Blocker.objects.create(
            title="Done B",
            project=self.project,
            owner=self.dev_member,
            status=BlockerStatus.RESOLVED,
        )
        self.client.force_authenticate(self.dev_user)
        resp = self.client.get("/api/blockers/?open=1")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        titles = [r["title"] for r in resp.data["results"]]
        self.assertIn("Open B", titles)
        self.assertNotIn("Done B", titles)

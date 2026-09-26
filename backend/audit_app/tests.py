"""Audit log visibility tests."""

from rest_framework import status
from rest_framework.test import APITestCase

from core.constants import Role
from core.test_utils import build_base
from audit_app.models import AuditLog


class AuditTests(APITestCase):
    def setUp(self):
        self.user, self.member, self.team, self.org = build_base(role=Role.TEAM_MANAGER)

    def test_manager_sees_audit_log(self):
        AuditLog.objects.create(
            action="project_created",
            entity_type="project",
            entity_id="1",
            entity_label="P",
            team=self.team,
            actor_name="manager",
        )
        self.client.force_authenticate(self.user)
        resp = self.client.get("/api/audit/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 1)

    def test_developer_cannot_see_audit_log(self):
        dev_user = build_developer_local(self.team, self.org)
        self.client.force_authenticate(dev_user)
        resp = self.client.get("/api/audit/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_audit_filter_by_entity(self):
        AuditLog.objects.create(
            action="task_created", entity_type="task", entity_id="9", team=self.team
        )
        AuditLog.objects.create(
            action="project_created",
            entity_type="project",
            entity_id="9",
            team=self.team,
        )
        self.client.force_authenticate(self.user)
        resp = self.client.get("/api/audit/?entity_type=task&entity_id=9")
        self.assertEqual(resp.data["count"], 1)
        self.assertEqual(resp.data["results"][0]["action"], "task_created")


def build_developer_local(team, org):
    from core.test_utils import build_developer

    user, _ = build_developer("dev9", team=team, org=org)
    return user

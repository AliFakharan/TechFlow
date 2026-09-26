"""Capacity allocation calculation tests."""

from rest_framework import status
from rest_framework.test import APITestCase

from capacity.models import CapacityAllocation
from core.constants import Role
from core.test_utils import build_base, build_developer
from projects.models import Project, ProjectStatus
from audit_app.models import AuditLog


class CapacityTests(APITestCase):
    def setUp(self):
        self.user, self.member, self.team, self.org = build_base(role=Role.TEAM_MANAGER)
        self.project = Project.objects.create(
            team=self.team, name="CP", status=ProjectStatus.ACTIVE
        )
        self.dev_user, self.dev_member = build_developer(
            "dev2", team=self.team, org=self.org
        )

    def test_set_allocation_and_warning(self):
        self.client.force_authenticate(self.dev_user)
        resp = self.client.post(
            "/api/capacity/set/",
            {"member": self.dev_member.pk, "project": self.project.pk, "percent": 70},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["member_total_percent"], 70)
        self.assertFalse(resp.data["overallocated"])

        # Push over 100% -> warning.
        from projects.models import Project as P

        p2 = P.objects.create(team=self.team, name="CP2", status=ProjectStatus.ACTIVE)
        resp = self.client.post(
            "/api/capacity/set/",
            {"member": self.dev_member.pk, "project": p2.pk, "percent": 50},
            format="json",
        )
        self.assertEqual(resp.data["member_total_percent"], 120)
        self.assertTrue(resp.data["overallocated"])

    def test_developer_cannot_set_for_other(self):
        other_user, other_member = build_developer("dev3", team=self.team, org=self.org)
        self.client.force_authenticate(self.dev_user)
        resp = self.client.post(
            "/api/capacity/set/",
            {"member": other_member.pk, "project": self.project.pk, "percent": 40},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_summary_totals_and_overallocation(self):
        CapacityAllocation.objects.create(
            member=self.dev_member, project=self.project, percent=70
        )
        CapacityAllocation.objects.create(
            member=self.dev_member, project=None, percent=40
        )  # support bucket
        self.client.force_authenticate(self.user)
        resp = self.client.get("/api/capacity/summary/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        dev = next(
            m for m in resp.data["per_member"] if m["member_id"] == self.dev_member.pk
        )
        self.assertEqual(dev["total_percent"], 110)
        self.assertEqual(dev["support_percent"], 40)
        self.assertTrue(dev["overallocated"])
        overloaded = next(
            (
                m
                for m in resp.data["overallocated_members"]
                if m["member_id"] == self.dev_member.pk
            ),
            None,
        )
        self.assertIsNotNone(overloaded)
        self.assertEqual(overloaded["total_percent"], 110)
        self.assertEqual(overloaded["full_name"], self.dev_member.full_name)

    def test_capacity_update_audited(self):
        self.client.force_authenticate(self.dev_user)
        self.client.post(
            "/api/capacity/set/",
            {"member": self.dev_member.pk, "project": self.project.pk, "percent": 30},
            format="json",
        )
        self.assertTrue(AuditLog.objects.filter(action="capacity_updated").exists())

    def test_invalid_percent_rejected(self):
        self.client.force_authenticate(self.dev_user)
        resp = self.client.post(
            "/api/capacity/set/",
            {"member": self.dev_member.pk, "project": self.project.pk, "percent": 500},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

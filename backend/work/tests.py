"""Task workflow + assignment tests."""

from rest_framework import status
from rest_framework.test import APITestCase

from core.constants import Priority, ProjectStatus, Role, TaskStatus, WorkType
from core.test_utils import build_base, build_developer
from projects.models import Project, ProjectMember
from work.models import Task


class TaskTestBase(APITestCase):
    def setUp(self):
        self.user, self.member, self.team, self.org = build_base(role=Role.TEAM_MANAGER)
        self.project = Project.objects.create(
            team=self.team,
            name="P1",
            status=ProjectStatus.ACTIVE,
            priority=Priority.MEDIUM,
        )
        self.dev_user, self.dev_member = build_developer(
            "dev2", team=self.team, org=self.org
        )
        ProjectMember.objects.create(project=self.project, member=self.dev_member)


class TaskCreationTests(TaskTestBase):
    def test_manager_creates_task(self):
        self.client.force_authenticate(self.user)
        resp = self.client.post(
            "/api/tasks/create/",
            {
                "project": self.project.pk,
                "title": "Build X",
                "assignee": self.dev_member.pk,
                "work_type": WorkType.FEATURE,
                "priority": Priority.HIGH,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        task = Task.objects.get(title="Build X")
        self.assertEqual(task.assignee, self.dev_member)
        self.assertEqual(task.status, TaskStatus.TODO)

    def test_developer_creates_task_in_own_team_only(self):
        self.client.force_authenticate(self.dev_user)
        # Another team's project is not allowed.
        from organizations.models import Organization
        from teams.models import Team

        other_org = Organization.objects.create(name="Other", code="other")
        other_team = Team.objects.create(organization=other_org, name="T2", code="t2")
        other_project = Project.objects.create(
            team=other_team, name="Other P", status=ProjectStatus.ACTIVE
        )
        resp = self.client.post(
            "/api/tasks/create/",
            {"project": other_project.pk, "title": "Hijack"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_developer_task_defaults_assignee_to_self(self):
        self.client.force_authenticate(self.dev_user)
        resp = self.client.post(
            "/api/tasks/create/",
            {"project": self.project.pk, "title": "My task"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        task = Task.objects.get(title="My task")
        self.assertEqual(task.assignee, self.dev_member)

    def test_developer_can_assign_task_to_team_member(self):
        other_user, other_member = build_developer("dev3", team=self.team, org=self.org)
        self.client.force_authenticate(self.dev_user)
        resp = self.client.post(
            "/api/tasks/create/",
            {
                "project": self.project.pk,
                "title": "For teammate",
                "assignee": other_member.pk,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        task = Task.objects.get(title="For teammate")
        self.assertEqual(task.assignee, other_member)
        self.assertEqual(task.creator, self.dev_member)
        from audit_app.models import AuditLog

        log = AuditLog.objects.filter(
            action="task_created", entity_id=str(task.pk)
        ).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.new_value.get("creator"), self.dev_member.pk)
        self.assertEqual(log.new_value.get("assignee"), other_member.pk)


class TaskStatusTests(TaskTestBase):
    def test_developer_quick_status_change_own_task(self):
        task = Task.objects.create(
            project=self.project,
            title="T",
            assignee=self.dev_member,
            status=TaskStatus.TODO,
        )
        self.client.force_authenticate(self.dev_user)
        resp = self.client.post(
            f"/api/tasks/{task.pk}/status/",
            {"status": TaskStatus.IN_PROGRESS},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(task.status, TaskStatus.IN_PROGRESS)
        self.assertIsNotNone(task.started_at)

    def test_developer_cannot_change_others_task(self):
        other_user, other_member = build_developer("dev3", team=self.team, org=self.org)
        task = Task.objects.create(
            project=self.project,
            title="T2",
            assignee=other_member,
            status=TaskStatus.TODO,
        )
        self.client.force_authenticate(self.dev_user)
        resp = self.client.post(
            f"/api/tasks/{task.pk}/status/", {"status": TaskStatus.DONE}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_done_sets_completed_at(self):
        task = Task.objects.create(
            project=self.project,
            title="T3",
            assignee=self.dev_member,
            status=TaskStatus.TODO,
        )
        self.client.force_authenticate(self.dev_user)
        self.client.post(
            f"/api/tasks/{task.pk}/status/", {"status": TaskStatus.DONE}, format="json"
        )
        task.refresh_from_db()
        self.assertIsNotNone(task.completed_at)

    def test_manager_reassigns_task_audited(self):
        task = Task.objects.create(
            project=self.project,
            title="T4",
            assignee=self.dev_member,
            status=TaskStatus.TODO,
        )
        other_user, other_member = build_developer("dev3", team=self.team, org=self.org)
        self.client.force_authenticate(self.user)
        resp = self.client.post(
            f"/api/tasks/{task.pk}/assign/",
            {"assignee": other_member.pk},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(task.assignee, other_member)
        from audit_app.models import AuditLog

        self.assertTrue(AuditLog.objects.filter(action="task_assigned").exists())

    def test_developer_cannot_delete_task(self):
        task = Task.objects.create(
            project=self.project,
            title="T5",
            assignee=self.dev_member,
            status=TaskStatus.TODO,
        )
        self.client.force_authenticate(self.dev_user)
        resp = self.client.delete(f"/api/tasks/{task.pk}/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Task.objects.filter(pk=task.pk).exists())

    def test_developer_cannot_patch_other_fields(self):
        task = Task.objects.create(
            project=self.project,
            title="T6",
            assignee=self.dev_member,
            status=TaskStatus.TODO,
        )
        self.client.force_authenticate(self.dev_user)
        resp = self.client.patch(
            f"/api/tasks/{task.pk}/", {"priority": Priority.CRITICAL}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

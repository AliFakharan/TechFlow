"""Authentication + basic permission tests."""

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from core.constants import Role
from core.test_utils import build_base, build_developer


class AuthTests(APITestCase):
    def test_login_success(self):
        build_base(role=Role.DEVELOPER)
        resp = self.client.post(
            "/api/auth/login/",
            {"username": "dev1", "password": "pass12345"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["user"]["role"], Role.DEVELOPER)
        self.assertIn("team_name", resp.data["user"])

    def test_login_wrong_password(self):
        build_base()
        resp = self.client.post(
            "/api/auth/login/",
            {"username": "dev1", "password": "wrong"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_requires_login(self):
        resp = self.client.get("/api/auth/me/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_me_after_login(self):
        build_base(role=Role.TEAM_MANAGER)
        self.client.post(
            "/api/auth/login/",
            {"username": "dev1", "password": "pass12345"},
            format="json",
        )
        resp = self.client.get("/api/auth/me/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["user"]["role"], Role.TEAM_MANAGER)

    def test_logout(self):
        build_base()
        self.client.post(
            "/api/auth/login/",
            {"username": "dev1", "password": "pass12345"},
            format="json",
        )
        resp = self.client.post("/api/auth/logout/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        resp = self.client.get("/api/auth/me/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_api_requires_authentication(self):
        resp = self.client.get("/api/projects/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


class RegisterTests(APITestCase):
    def test_register_success_and_join_first_team(self):
        build_base()  # org + team exist; new member should join it
        resp = self.client.post(
            "/api/auth/register/",
            {
                "username": "newdev",
                "password": "pass12345",
                "full_name": "New Developer",
                "email": "newdev@test.local",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["user"]["username"], "newdev")
        self.assertEqual(resp.data["user"]["role"], Role.DEVELOPER)
        self.assertTrue(resp.data["user"]["team_name"])
        # The session is already logged in.
        resp = self.client.get("/api/auth/me/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_register_duplicate_username(self):
        build_base()
        resp = self.client.post(
            "/api/auth/register/",
            {"username": "dev1", "password": "pass12345", "full_name": "Dup"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_weak_password(self):
        resp = self.client.post(
            "/api/auth/register/",
            {"username": "weak", "password": "123", "full_name": "Weak"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_csrf_token_sets_cookie(self):
        resp = self.client.get("/api/auth/csrf/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("csrftoken", resp.cookies)


class RoleProvisioningTests(APITestCase):
    def test_admin_creates_member(self):
        admin_user, _, team, org = build_base(role=Role.ADMIN, username="admin1")
        self.client.force_authenticate(admin_user)
        resp = self.client.post(
            "/api/members/create/",
            {
                "username": "newdev",
                "password": "secret123",
                "full_name": "New Dev",
                "team": team.pk,
                "organization": org.pk,
                "role": Role.DEVELOPER,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="newdev").exists())

    def test_developer_cannot_create_member(self):
        user, _, _, _ = build_base(role=Role.DEVELOPER)
        self.client.force_authenticate(user)
        resp = self.client.post(
            "/api/members/create/",
            {"username": "x", "password": "secret123", "full_name": "X"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_change_role(self):
        admin_user, _, team, _ = build_base(role=Role.ADMIN, username="admin1")
        _, dev = build_developer("dev2", team=team)
        self.client.force_authenticate(admin_user)
        resp = self.client.post(
            f"/api/members/{dev.pk}/role/", {"role": Role.SCRUM_MASTER}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        dev.refresh_from_db()
        self.assertEqual(dev.role, Role.SCRUM_MASTER)

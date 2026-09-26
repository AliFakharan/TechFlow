"""Shared test fixtures for TechFlow backend tests."""

from django.contrib.auth.models import User

from core.constants import Role
from organizations.models import Organization
from teams.models import Member, Team

ORG_NAME = "Test Tech Dept"
TEAM_NAME = "Test Team"


def build_base(role=Role.DEVELOPER, username="dev1"):
    """Create an organization, team, user and member for tests.

    Returns (user, member, team, org).
    """
    org = Organization.objects.create(name=ORG_NAME, code="test-org")
    team = Team.objects.create(organization=org, name=TEAM_NAME, code="test-team")
    user = User.objects.create_user(
        username=username, password="pass12345", email=f"{username}@test.local"
    )
    member = user.member
    member.full_name = f"Full {username}"
    member.team = team
    member.organization = org
    member.role = role
    member.save()
    return user, member, team, org


def build_developer(username="dev2", team=None, org=None):
    user = User.objects.create_user(
        username=username, password="pass12345", email=f"{username}@test.local"
    )
    member = user.member
    member.full_name = f"Full {username}"
    member.team = team
    member.organization = org
    member.role = Role.DEVELOPER
    member.save()
    return user, member

"""Create the default system-admin user.

Usage:
    python manage.py create_admin

Behavior:
    * Username from --username (default: env TECHFLOW_ADMIN_USERNAME or "admin").
    * Password from env TECHFLOW_ADMIN_PASSWORD. If unset, a strong random
      password is generated and printed once.
    * The user becomes a Django superuser/staff (so Django admin works) and
      their Member profile is set to the "admin" role.
    * Idempotent: re-running updates the password and keeps the profile.
"""

import os
import secrets
import string

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from core.constants import Role
from organizations.models import Organization
from teams.models import Member, Team


def _strong_password(length: int = 16) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(secrets.choice(alphabet) for _ in range(length))


class Command(BaseCommand):
    help = "Create (or reset) the default TechFlow admin user."

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            default=os.environ.get("TECHFLOW_ADMIN_USERNAME", "admin"),
            help="Admin username (default: env TECHFLOW_ADMIN_USERNAME or 'admin').",
        )
        parser.add_argument(
            "--password",
            default=None,
            help="Admin password (default: env TECHFLOW_ADMIN_PASSWORD, else generated).",
        )
        parser.add_argument(
            "--print-password",
            action="store_true",
            help="Always print the password (default: print only when generated).",
        )

    def _ensure_workspace(self):
        """Create a default org + team if none exist; backfill teamless members.

        On a fresh database there is no way to create an org/team through the
        UI, so the bootstrap command also guarantees a workspace exists
        (idempotent — never touches existing orgs/teams).
        """
        org = Organization.objects.first()
        if org is None:
            org = Organization.objects.create(
                name="Technology Department", code="technology"
            )
            self.stdout.write("Created default organization.")
        team = Team.objects.first()
        if team is None:
            team = Team.objects.create(
                organization=org,
                name="Software Development Team",
                code="dev-team",
            )
            self.stdout.write("Created default team.")
        # Members registered before the first team existed have no team;
        # attach them (mirrors the signup behavior).
        orphaned = Member.objects.filter(team__isnull=True)
        if orphaned.exists():
            for member in orphaned:
                member.team = team
                if member.organization_id is None:
                    member.organization = org
                member.save()
            self.stdout.write(
                f"Attached {orphaned.count()} teamless member(s) to the default team."
            )
        return org, team

    def handle(self, *args, **options):
        username = options["username"]
        password = options["password"] or os.environ.get("TECHFLOW_ADMIN_PASSWORD", "")
        generated = False

        # Deployment hint: without trusted origins, POSTs from any host other
        # than the auto-trusted dev origins will be rejected by CSRF checks.
        if (
            os.environ.get("TECHFLOW_DEBUG", "1") != "1"
            and not os.environ.get("TECHFLOW_CSRF_TRUSTED_ORIGINS", "").strip()
        ):
            self.stdout.write(
                self.style.WARNING(
                    "TECHFLOW_CSRF_TRUSTED_ORIGINS is empty. If users reach the "
                    "UI via a non-localhost host (server IP / domain), set e.g. "
                    "TECHFLOW_CSRF_TRUSTED_ORIGINS=http://<host>:5173 "
                    "or POST requests will fail CSRF origin checks."
                )
            )

        if not password:
            password = _strong_password()
            generated = True

        org, team = self._ensure_workspace()

        user, _created = User.objects.get_or_create(
            username=username,
            defaults={
                "is_superuser": True,
                "is_staff": True,
                "first_name": "System",
                "email": f"{username}@techflow.local",
            },
        )
        # Always (re)set the password — get_or_create cannot set it on create.
        user.set_password(password)
        user.is_superuser = True
        user.is_staff = True
        user.save()

        # Ensure the Member profile carries the admin role and belongs to the
        # workspace (signal creates it as a developer with no team).
        member = user.member
        changed = False
        if member.role != Role.ADMIN:
            member.role = Role.ADMIN
            changed = True
        if member.team_id is None:
            member.team = team
            member.organization = org
            changed = True
        if not member.full_name:
            member.full_name = "System Administrator"
            changed = True
        if changed:
            member.save()

        self.stdout.write(
            self.style.SUCCESS(
                f"Admin user '{username}' is ready (superuser + admin role)."
            )
        )
        if generated or options["print_password"]:
            self.stdout.write(
                self.style.WARNING(
                    f"Password: {password}\n"
                    "Save it now — it is not stored in plain text."
                )
            )

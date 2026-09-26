"""Ensure every new user gets a Member profile (default: developer)."""

from django.conf import settings
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=User)
def create_member_profile(sender, instance, created, **kwargs):
    if created:
        from organizations.models import Organization
        from teams.models import Member

        member, _ = Member.objects.get_or_create(
            user=instance,
            defaults={"full_name": instance.get_full_name() or instance.username},
        )
        # Attach to the first organization if there is only one.
        if not member.organization_id:
            org = Organization.objects.first()
            if org and member.organization is None:
                member.organization = org
                member.save(update_fields=["organization"])

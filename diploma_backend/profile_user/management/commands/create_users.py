from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction

from profile_user.models import Profile


STANDARD_USERS = [
    {
        "username": "luna_mark",
        "password": "Test12345!",
        "profile": {
            "full_name": "Mark Luna",
            "email": "luna_m@example.com",
            "phone": "+77923456789",
        },
    },
    {
        "username": "standard_user",
        "password": "Test12345!",
        "profile": {
            "full_name": "Standard User",
            "email": "standard_user@example.com",
            "phone": "+70000000001",
        },
    },
    {
        "username": "buyer",
        "password": "Test12345!",
        "profile": {
            "full_name": "Buyer User",
            "email": "buyer@example.com",
            "phone": "+70000000002",
        },
    },
]


class Command(BaseCommand):
    help = "Create standard users for tests / demo data"

    @transaction.atomic
    def handle(self, *args, **options):
        created = 0
        updated = 0

        for u in STANDARD_USERS:
            username = u["username"]
            password = u["password"]
            p = u["profile"]

            user, was_created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": p.get("email", ""),
                    "first_name": "",
                    "last_name": "",
                },
            )

            if was_created:
                user.set_password(password)
                user.save(update_fields=["password"])
                created += 1
            else:
                user.set_password(password)
                user.email = p.get("email", user.email)
                user.save(update_fields=["password", "email"])
                updated += 1

            profile, _ = Profile.objects.get_or_create(user=user)
            profile.full_name = p.get("full_name", profile.full_name)
            profile.email = p.get("email", profile.email)
            profile.phone = p.get("phone", profile.phone)
            profile.save(update_fields=["full_name", "email", "phone"])

        self.stdout.write(self.style.SUCCESS(
            f"Done. Created: {created}, Updated: {updated}"
        ))

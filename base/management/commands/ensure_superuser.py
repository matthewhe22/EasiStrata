"""Create or update a Django superuser idempotently.

Reads credentials from environment variables so no secret is committed:

    DJANGO_SUPERUSER_USERNAME   (e.g. matthew.he@tocs.co)
    DJANGO_SUPERUSER_EMAIL      (optional; defaults to the username)
    DJANGO_SUPERUSER_PASSWORD

Run it once against the target database after `migrate`:

    python manage.py migrate
    python manage.py ensure_superuser

You can also pass values as flags (handy for a one-off):

    python manage.py ensure_superuser --username matthew.he@tocs.co --password '...'
"""
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create or update a superuser from env vars or flags (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument('--username', default=None)
        parser.add_argument('--email', default=None)
        parser.add_argument('--password', default=None)

    def handle(self, *args, **options):
        username = (options['username']
                    or os.environ.get('DJANGO_SUPERUSER_USERNAME', '')).strip()
        email = (options['email']
                 or os.environ.get('DJANGO_SUPERUSER_EMAIL', '')).strip() or username
        password = (options['password']
                    or os.environ.get('DJANGO_SUPERUSER_PASSWORD', ''))

        if not username:
            raise CommandError('Username required (DJANGO_SUPERUSER_USERNAME or --username).')
        if not password:
            raise CommandError('Password required (DJANGO_SUPERUSER_PASSWORD or --password).')

        User = get_user_model()
        user, created = User.objects.get_or_create(username=username, defaults={'email': email})
        user.email = email
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.set_password(password)
        user.save()

        action = 'Created' if created else 'Updated'
        self.stdout.write(self.style.SUCCESS(
            f"{action} superuser '{username}' (email: {email})."
        ))

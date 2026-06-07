"""Reset a user's password from the command line.

Usage (run where the database is reachable, e.g. the production server):

    python manage.py set_password matthew.he@topocs.com.au "NewStrongPassword123!"

The identifier is matched against the username first, then the email address.
If you omit the password argument you will be prompted for it (hidden input).
"""
from getpass import getpass

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Set/reset a user's password, matching by username or email."

    def add_arguments(self, parser):
        parser.add_argument('identifier', help='username or email of the user')
        parser.add_argument(
            'password',
            nargs='?',
            default=None,
            help='new password (omit to be prompted securely)',
        )

    def handle(self, *args, **options):
        User = get_user_model()
        identifier = options['identifier'].strip()

        user = User.objects.filter(username=identifier).first()
        if user is None:
            user = User.objects.filter(email__iexact=identifier).first()
        if user is None:
            raise CommandError(
                f"No user found with username or email '{identifier}'."
            )

        password = options['password']
        if not password:
            password = getpass('New password: ')
            if password != getpass('Confirm password: '):
                raise CommandError('Passwords did not match.')
        if not password:
            raise CommandError('Password must not be empty.')

        user.set_password(password)
        user.is_active = True
        user.save(update_fields=['password', 'is_active'])

        self.stdout.write(self.style.SUCCESS(
            f"Password updated for user '{user.username}' (email: {user.email})."
        ))

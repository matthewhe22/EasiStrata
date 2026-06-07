"""
WSGI config for my_project project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/howto/deployment/wsgi/
"""

import logging
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'my_project.settings')

application = get_wsgi_application()


# One-time database bootstrap for environments without shell access (e.g.
# Vercel serverless). When RUN_DB_INIT=True, apply migrations and, if superuser
# credentials are present, create/update the superuser. This runs in the Vercel
# runtime, which has Python and can reach the database. Set RUN_DB_INIT=True for
# the first deploy against a fresh database, then REMOVE it (and the
# DJANGO_SUPERUSER_* vars) and redeploy. It is idempotent and never blocks app
# startup on failure.
if os.environ.get('RUN_DB_INIT', 'False').strip() == 'True':
    try:
        from django.core.management import call_command
        call_command('migrate', '--noinput')
        if (os.environ.get('DJANGO_SUPERUSER_USERNAME')
                and os.environ.get('DJANGO_SUPERUSER_PASSWORD')):
            call_command('ensure_superuser')
        logging.warning('RUN_DB_INIT completed. Remove RUN_DB_INIT and '
                        'DJANGO_SUPERUSER_* env vars, then redeploy.')
    except Exception:
        logging.exception('RUN_DB_INIT failed')

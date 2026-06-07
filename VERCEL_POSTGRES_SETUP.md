# Vercel Postgres (Neon) setup

The app now runs on Postgres when `DATABASE_URL` uses a `postgres://` scheme.
`settings.py` auto-detects the engine via dj-database-url, so no code change is
needed to switch between MySQL and Postgres.

> Note: the raw-SQL data-import / some report features in `scripts/DB/` are
> written for MySQL (`mysql.connector`) and stay inert on Postgres until ported.
> The core app, admin, login and the superuser all work on Postgres.

## 1. Create the database

In the Vercel dashboard → **Storage** → create a **Postgres** (Neon) database
and connect it to the EasiStrata project. Vercel exposes a `POSTGRES_URL` /
`DATABASE_URL` connection string, e.g.:

```
postgres://USER:PASSWORD@ep-xxxx.ap-southeast-2.aws.neon.tech/dbname?sslmode=require
```

## 2. Set Vercel environment variables

Project → **Settings → Environment Variables**:

| Variable | Value |
|---|---|
| `DATABASE_URL` | the Postgres connection string above |
| `SECRET_KEY` | a strong random key |
| `DISABLE_SCHEDULER` | `True` |
| `DJANGO_SETTINGS_MODULE` | `my_project.settings` |

(If Vercel only created `POSTGRES_URL`, copy its value into `DATABASE_URL`.)

## 3. Pull env vars locally (optional, needs Vercel CLI + Node)

```bash
npm i -g vercel
vercel link            # link to the EasiStrata project
vercel env pull .env.development.local
```

## 4. Create the schema and superuser

Run from any machine that has Python 3.12 (Neon is publicly reachable, so this
works from anywhere — no firewall whitelist needed). Use the SAME `DATABASE_URL`.

```bash
pip install -r requirements.txt

export DATABASE_URL='postgres://USER:PASSWORD@ep-xxxx.../dbname?sslmode=require'

python manage.py migrate

# superuser credentials via env (no secret stored in the repo)
export DJANGO_SUPERUSER_USERNAME='matthew.he@tocs.co'
export DJANGO_SUPERUSER_EMAIL='matthew.he@tocs.co'
export DJANGO_SUPERUSER_PASSWORD='<your password>'
python manage.py ensure_superuser
```

`ensure_superuser` is idempotent — re-running it updates the password/flags.

## 5. Verify

- Visit the Vercel URL → `/base/user_login/` and log in with the superuser, or
- Visit `/admin/` for the Django admin.

## Bringing over existing data (optional)

The current data lives in the firewalled Aliyun **MySQL**. Moving it to Postgres
is a cross-engine conversion (not a plain dump/restore): export per-table to CSV
or use a tool like `pgloader`. If you need this, say so and we'll script it —
otherwise the app starts with a fresh Postgres schema + the superuser above.

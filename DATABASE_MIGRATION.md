# Database migration — Aliyun RDS → Vercel-reachable MySQL

The app currently points at an Aliyun RDS MySQL instance whose firewall only
allows specific IPs. Vercel's serverless functions use dynamic IPs and cannot
reach it, which is why the deployed site returns 500 on every DB query.

This guide moves the data to a MySQL host that Vercel can reach. **Railway** is
the recommended target because it is standard MySQL 8 (keeps foreign keys,
unlike PlanetScale) and exposes a public endpoint.

> The export step must run from a machine that can already reach Aliyun — your
> production server `portal.topocs.com.au` (47.74.86.36) is whitelisted, so run
> it there.

---

## 1. Export the current database (on the whitelisted prod server)

```bash
mysqldump \
  -h rm-j0b9z69u968t7av0yuo.mysql.australia.rds.aliyuncs.com \
  -u capconnex_db_user -p \
  --single-transaction --default-character-set=utf8mb4 \
  --no-tablespaces \
  strata > strata_dump.sql
# enter the Aliyun DB password when prompted (the DB_PASSWORD value)
```

Copy `strata_dump.sql` to wherever you'll run the import.

## 2. Provision the new MySQL (Railway)

1. Create an account at https://railway.app and a new project.
2. Add a **MySQL** database service.
3. Open the service → **Variables** / **Connect** tab and note the public
   connection details. Railway gives you a ready-made URL like:
   ```
   mysql://root:PASSWORD@containers-xxx.railway.app:7777/railway
   ```

## 3. Import the dump into Railway

```bash
mysql -h <railway-host> -P <railway-port> -u root -p railway < strata_dump.sql
# password = the Railway MySQL password
```

(If you prefer the DB to be named `strata`, create it first with
`CREATE DATABASE strata;` and import into that instead of `railway`.)

## 4. Point the app at the new database (Vercel env vars)

In the Vercel project → **Settings → Environment Variables**, add **one** of:

**Option A — single URL (simplest):**

| Variable | Value |
|---|---|
| `DATABASE_URL` | `mysql://root:PASSWORD@containers-xxx.railway.app:7777/railway` |
| `DB_SSL_REQUIRE` | `True` (set only if the host requires TLS) |

**Option B — discrete vars:**

| Variable | Value |
|---|---|
| `DB_HOST` | Railway host |
| `DB_PORT` | Railway port |
| `DB_NAME` | `railway` (or `strata`) |
| `DB_USER` | `root` |
| `DB_PASSWORD` | Railway password |

Also keep:

| Variable | Value |
|---|---|
| `SECRET_KEY` | a strong random key |
| `DISABLE_SCHEDULER` | `True` |
| `DJANGO_SETTINGS_MODULE` | `my_project.settings` |

Redeploy (Vercel does not auto-redeploy on env-var changes).

## 5. Reset the login password

Once the app can reach the new DB, from any machine that can reach it (or via a
local checkout pointed at the same `DATABASE_URL`):

```bash
python manage.py set_password matthew.he@topocs.com.au "YourNewPassword123!"
```

## Notes

- `settings.py` reads `DATABASE_URL` first and falls back to `DB_*`, so no code
  change is needed to switch hosts.
- The app still patches PyMySQL as MySQLdb in `my_project/__init__.py`, so
  Django talks to MySQL without native libraries.
- WeasyPrint PDF generation and the APScheduler jobs remain disabled on Vercel
  (serverless limitations); those features need a persistent host.

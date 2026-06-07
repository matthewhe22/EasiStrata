"""
Django management command: restore_db

Restores application data from the Excel exports in the "DB migration" folder
into the configured database.

Usage:
    python manage.py migrate            # create schema first
    python manage.py restore_db         # import data
    python manage.py restore_db --clear # truncate tables then import
    python manage.py restore_db --table property_lot  # single table

NOTES:
  • Three tables have NO Excel exports and must be restored separately:
      - property_property  (Property records)
      - property_ocmaster  (OCMaster records)
      - finance_supplier   (Supplier records)
    Use mysqldump from the original Aliyun RDS for those.

  • base_userprofile is corrupted in the export.  This command reconstructs
    it: staff users (id 1–5) get role='staff'; all others get role='owner'.
    Adjust manually afterwards if any users need 'manager' or 'committee'.

  • strata_coa.xlsx has a broken header structure (column names C1–C11 with
    a stray header row mid-file).  The canonical COA is in
    strata_finance_coa.xlsx which is imported instead.

  • Several files are corrupt/empty and are skipped automatically.
"""

import math
import os

import numpy as np
import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            )
        )
    )
)
MIGRATION_DIR = os.path.join(BASE_DIR, "DB migration")

# Ordered import plan: (excel_filename, db_table_name)
# Order matters for readability; FK checks are disabled so order is not
# strictly required for constraint satisfaction.
IMPORT_PLAN = [
    # --- Auth / users ---
    ("strata_auth_user.xlsx",              "auth_user"),
    ("strata_auth_user_groups.xlsx",       "auth_user_groups"),
    # --- Core client ---
    ("strata_base_client.xlsx",            "base_client"),
    # --- Finance reference data (no FK to property) ---
    ("strata_finance_coa.xlsx",            "finance_coa"),
    ("strata_finance_incomeexp.xlsx",      "finance_incomeexp"),
    # --- Base config ---
    ("strata_base_sequence.xlsx",          "base_sequence"),
    ("strata_base_datasource.xlsx",        "base_datasource"),
    ("strata_base_datasourcerule.xlsx",    "base_datasourcerule"),
    ("strata_base_importlog.xlsx",         "base_importlog"),
    ("strata_base_notification.xlsx",      "base_notification"),
    # --- Property data (FK to property_property & property_ocmaster, which
    #     are missing from Excel — imported with FK checks disabled) ---
    ("strata_property_lot.xlsx",           "property_lot"),
    ("strata_property_lotocmap.xlsx",      "property_lotocmap"),
    ("strata_property_ocbudget.xlsx",      "property_ocbudget"),
    # --- Finance transactional ---
    ("strata_finance_gl.xlsx",             "finance_gl"),
    ("strata_finance_banktrans.xlsx",      "finance_banktrans"),
    ("strata_finance_billing.xlsx",        "finance_billing"),
    ("strata_finance_cashreceipt.xlsx",    "finance_cashreceipt"),
    ("strata_finance_clientledger.xlsx",   "finance_clientledger"),
    ("strata_finance_fs.xlsx",             "finance_fs"),
    ("strata_finance_invoice.xlsx",        "finance_invoice"),
    ("strata_finance_occertificate.xlsx",  "finance_occertificate"),
    # --- Strata governance ---
    ("strata_strata_agm.xlsx",             "strata_agm"),
    ("strata_strata_agmdetail.xlsx",       "strata_agmdetail"),
    ("strata_strata_insurance.xlsx",       "strata_insurance"),
    ("strata_strata_ownerrequest.xlsx",    "strata_ownerrequest"),
]

# Excel files intentionally skipped and why
SKIPPED_EXPLANATION = {
    "strata_coa.xlsx": (
        "STRUCTURAL FIX: this file has corrupt headers (columns C1–C11, "
        "header row embedded mid-file with different names: 'Code Number', "
        "'Account Name', 'AccountLevel2', 'AccountLevel1'). "
        "The canonical COA data is in strata_finance_coa.xlsx which is "
        "imported instead."
    ),
    "strata_django_migrations.xlsx":     "managed by 'manage.py migrate'",
    "strata_django_content_type.xlsx":   "managed by 'manage.py migrate'",
    "strata_auth_permission.xlsx":       "managed by 'manage.py migrate'",
    "strata_django_session.xlsx":        "expired sessions, not needed",
    "strata_django_apscheduler_djangojob.xlsx": (
        "scheduler jobs are re-registered at startup by apscheduler"
    ),
    "strata_django_admin_log.xlsx":      "admin audit log, not required",
    "strata_tmp_table.xlsx":             "temporary table, not a Django model",
    "strata_base_userprofile.xlsx":      "CORRUPT — reconstructed programmatically",
    "strata_base_errorconfig.xlsx":      "CORRUPT",
    "strata_base_tb.xlsx":               "CORRUPT",
    "strata_auth_group.xlsx":            "empty file (0 bytes)",
    "strata_auth_group_permissions.xlsx":"CORRUPT",
    "strata_auth_user_user_permissions.xlsx": "CORRUPT",
    "strata_background_task.xlsx":       "CORRUPT (not a current Django app)",
    "strata_background_task_completedtask.xlsx": "CORRUPT (not a current Django app)",
    "strata_django_apscheduler_djangojobexecution.xlsx": "CORRUPT",
    "strata_finance_invoicepay.xlsx":    "CORRUPT",
    "strata_finance_recondetail.xlsx":   "CORRUPT",
    "strata_finance_reconlist.xlsx":     "CORRUPT",
}

MISSING_TABLES = [
    ("property_property", "Property records — needed by Lot, Insurance, AGM, FS"),
    ("property_ocmaster", "OCMaster records — needed by GL, Billing, BankTrans, etc."),
    ("finance_supplier",  "Supplier records — needed by Invoice"),
]

# User IDs that are staff accounts (not owner portal accounts)
STAFF_USER_IDS = {1, 2, 3, 4, 5}


def clean_value(v):
    """Convert a pandas/numpy cell value to a Python primitive safe for DB insertion."""
    if v is None:
        return None
    if isinstance(v, float) and math.isnan(v):
        return None
    if isinstance(v, np.integer):
        return int(v)
    if isinstance(v, np.floating):
        return None if math.isnan(float(v)) else float(v)
    if isinstance(v, np.bool_):
        return bool(v)
    if isinstance(v, np.ndarray):
        return v.tolist()
    if hasattr(v, "isoformat"):
        return v.isoformat()
    return v


class Command(BaseCommand):
    help = (
        "Restore database from Excel exports in the 'DB migration' folder. "
        "Run 'manage.py migrate' first to create the schema."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing rows from each table before importing",
        )
        parser.add_argument(
            "--table",
            metavar="DB_TABLE",
            default=None,
            help="Import only this table (e.g. --table property_lot)",
        )
        parser.add_argument(
            "--no-userprofile",
            action="store_true",
            help="Skip the userprofile reconstruction step",
        )

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def handle(self, *args, **options):
        if not os.path.isdir(MIGRATION_DIR):
            raise CommandError(
                f"Migration folder not found: {MIGRATION_DIR}\n"
                "Make sure the 'DB migration' folder is present at the project root."
            )

        target_table = options["table"]

        self.stdout.write(f"Migration folder : {MIGRATION_DIR}")
        self.stdout.write("")

        counts = {"imported": 0, "skipped": 0, "errors": 0}

        with connection.cursor() as cursor:
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            self.stdout.write("  [info] FK constraint checks disabled")
            self.stdout.write("")

            for filename, table in IMPORT_PLAN:
                if target_table and table != target_table:
                    continue
                filepath = os.path.join(MIGRATION_DIR, filename)
                result = self._import_table(
                    cursor, filepath, filename, table, options["clear"]
                )
                counts[result] += 1

            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
            self.stdout.write("")
            self.stdout.write("  [info] FK constraint checks re-enabled")

        # Reconstruct userprofile unless skipped or targeting a specific table
        if not options["no_userprofile"] and not target_table:
            self._reconstruct_userprofiles()

        # Summary
        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Import complete — "
                f"{counts['imported']} tables imported, "
                f"{counts['skipped']} skipped, "
                f"{counts['errors']} errors"
            )
        )

        self._print_notices()

    # ------------------------------------------------------------------
    # Per-table import
    # ------------------------------------------------------------------

    def _import_table(self, cursor, filepath, filename, table, clear):
        label = f"{filename:<55}"

        if not os.path.exists(filepath):
            self.stdout.write(f"  SKIP  {label}  (file not found)")
            return "skipped"

        if os.path.getsize(filepath) == 0:
            self.stdout.write(f"  SKIP  {label}  (empty file)")
            return "skipped"

        try:
            df = pd.read_excel(filepath)
        except Exception as exc:
            self.stdout.write(f"  ERROR {label}  (unreadable: {exc})")
            return "errors"

        if df.empty:
            self.stdout.write(f"  SKIP  {label}  (no data rows)")
            return "skipped"

        if clear:
            cursor.execute(f"DELETE FROM `{table}`")

        cols = list(df.columns)
        col_sql = ", ".join(f"`{c}`" for c in cols)
        placeholders = ", ".join(["%s"] * len(cols))
        sql = (
            f"INSERT IGNORE INTO `{table}` ({col_sql}) VALUES ({placeholders})"
        )

        rows = [
            tuple(clean_value(v) for v in row)
            for _, row in df.iterrows()
        ]

        try:
            cursor.executemany(sql, rows)
            self.stdout.write(
                f"  OK    {label}  → {table} ({len(rows)} rows)"
            )
            return "imported"
        except Exception as exc:
            self.stdout.write(f"  ERROR {label}  ({exc})")
            return "errors"

    # ------------------------------------------------------------------
    # Reconstruct base_userprofile (file was corrupt in export)
    # ------------------------------------------------------------------

    def _reconstruct_userprofiles(self):
        self.stdout.write("")
        self.stdout.write("  Reconstructing base_userprofile …")

        with connection.cursor() as cursor:
            # Read existing user IDs from auth_user
            cursor.execute("SELECT id FROM auth_user")
            user_ids = {row[0] for row in cursor.fetchall()}

            if not user_ids:
                self.stdout.write(
                    "  SKIP  base_userprofile reconstruction (no users in DB)"
                )
                return

            # Read already-existing profiles so we don't duplicate
            cursor.execute("SELECT user_id FROM base_userprofile")
            existing = {row[0] for row in cursor.fetchall()}

            to_insert = []
            for uid in sorted(user_ids):
                if uid in existing:
                    continue
                role = "staff" if uid in STAFF_USER_IDS else "owner"
                to_insert.append((uid, role))

            if not to_insert:
                self.stdout.write("  SKIP  base_userprofile (all profiles already exist)")
                return

            cursor.executemany(
                "INSERT IGNORE INTO base_userprofile (user_id, role) VALUES (%s, %s)",
                to_insert,
            )
            staff_count = sum(1 for _, r in to_insert if r == "staff")
            owner_count = sum(1 for _, r in to_insert if r == "owner")
            self.stdout.write(
                f"  OK    base_userprofile — "
                f"{len(to_insert)} profiles created "
                f"({staff_count} staff, {owner_count} owner)"
            )
            self.stdout.write(
                "  [warn] Review manager/committee roles manually "
                "(original file was corrupt)"
            )

    # ------------------------------------------------------------------
    # Post-import notices
    # ------------------------------------------------------------------

    def _print_notices(self):
        self.stdout.write("")
        self.stdout.write("=" * 68)
        self.stdout.write(self.style.WARNING("SKIPPED FILES (with reasons):"))
        for fname, reason in sorted(SKIPPED_EXPLANATION.items()):
            self.stdout.write(f"  {fname}")
            self.stdout.write(f"    → {reason}")

        self.stdout.write("")
        self.stdout.write(self.style.ERROR("MISSING TABLE EXPORTS (no Excel file found):"))
        for table, desc in MISSING_TABLES:
            self.stdout.write(f"  {table:<30}  {desc}")
        self.stdout.write(
            "\n  All imported rows that reference these tables have dangling FKs."
            "\n  Restore them via mysqldump from the original Aliyun RDS, then re-run:"
            "\n    python manage.py restore_db --table <table>"
        )
        self.stdout.write("=" * 68)

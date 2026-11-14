"""
Automated Migration Script: SQLite -> PostgreSQL for MeetFlow
Verifies PostgreSQL connection, creates database if needed, runs migrations,
loads all 40 meeting records, and verifies data integrity.
"""
import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

DB_NAME = os.getenv("DB_NAME", "meetflow_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DATABASE_URL = os.getenv("DATABASE_URL")

print("=" * 70)
print(" MeetFlow PostgreSQL Migration Runner")
print("=" * 70)

try:
    import psycopg
except ImportError:
    print("[ERROR] psycopg is not installed. Please run: pip install 'psycopg[binary]>=3.2.0'")
    sys.exit(1)

# Step 1: Connect to PostgreSQL server
print(f"\n1. Connecting to PostgreSQL server ({DB_HOST}:{DB_PORT})...")
try:
    if DATABASE_URL:
        conn = psycopg.connect(DATABASE_URL, autocommit=True)
    else:
        # Connect to default 'postgres' database to check/create target database
        conn = psycopg.connect(
            dbname="postgres",
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            autocommit=True
        )
    print("   [OK] Connected to PostgreSQL server successfully!")
except Exception as e:
    print(f"   [FAILED] Could not connect to PostgreSQL: {e}")
    print("\nPlease verify:")
    print(f" - Is PostgreSQL server running on {DB_HOST}:{DB_PORT}?")
    print(" - Are your credentials in .env correct?")
    sys.exit(1)

# Step 2: Ensure database exists
if not DATABASE_URL:
    try:
        cur = conn.cursor()
        cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'")
        exists = cur.fetchone()
        if not exists:
            print(f"\n2. Creating database '{DB_NAME}'...")
            cur.execute(f'CREATE DATABASE "{DB_NAME}"')
            print(f"   [OK] Database '{DB_NAME}' created successfully.")
        else:
            print(f"\n2. Database '{DB_NAME}' already exists.")
        conn.close()
    except Exception as e:
        print(f"   [WARN] Could not verify/create database: {e}")

# Step 3: Run Django migrations
print("\n3. Running Django migrations against PostgreSQL...")
res = subprocess.run([sys.executable, "manage.py", "migrate"], cwd=BASE_DIR)
if res.returncode != 0:
    print("   [FAILED] Django migration failed.")
    sys.exit(1)
print("   [OK] Migrations completed successfully.")

# Step 4: Load existing fixture data
fixture_path = BASE_DIR / "database_exports" / "meetflow_reminders_fixture.json"
print(f"\n4. Loading existing records from {fixture_path.name}...")
res = subprocess.run([sys.executable, "manage.py", "loaddata", str(fixture_path)], cwd=BASE_DIR)
if res.returncode != 0:
    print("   [FAILED] Could not load data fixture.")
    sys.exit(1)
print("   [OK] Data loaded successfully.")

# Step 5: Verify records in PostgreSQL
print("\n5. Verifying transferred records in PostgreSQL...")
try:
    import django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "meetflow_core.settings")
    django.setup()
    from reminders.models import Meeting, ScheduledReminder, NotificationLog

    m_count = Meeting.objects.count()
    r_count = ScheduledReminder.objects.count()
    n_count = NotificationLog.objects.count()

    print(f"   - Total Meetings in PostgreSQL: {m_count} (Expected: 40)")
    print(f"   - Total Scheduled Reminders:   {r_count} (Expected: 264)")
    print(f"   - Total Notification Logs:     {n_count} (Expected: 10)")

    if m_count == 40:
        print("\n" + "=" * 70)
        print(" [SUCCESS] PostgreSQL Migration Completed Successfully!")
        print("=" * 70)
    else:
        print(f"\n [WARN] Meeting count is {m_count}, expected 40.")
except Exception as e:
    print(f"   [ERROR] Error checking records: {e}")

import os
import sqlite3
from dotenv import load_dotenv

load_dotenv()

_raw_path = os.getenv("DB_PATH", "./data/jobs.db")
# Prevent path traversal - restrict to project directory
DB_PATH = os.path.normpath(_raw_path)
if not DB_PATH.startswith(os.path.normpath("./data")):
    raise ValueError(f"DB_PATH outside allowed directory: {DB_PATH}")
_INITIALIZED = False  # Flag - run migrations only once per process


def get_connection():
    """Create and return a connection to the SQLite database."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    return conn


def _run_migrations(cursor):
    """
    Apply schema migrations in order.
    Each migration runs only if not already applied.
    migrations table tracks what has been applied.
    """
    # Create migrations tracker first
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS migrations (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT UNIQUE NOT NULL,
            applied_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # List all migrations in order
    migrations = [
        ("001_create_jobs", """
            CREATE TABLE IF NOT EXISTS jobs (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT NOT NULL,
                company     TEXT,
                city        TEXT,
                region      TEXT,
                contract    TEXT,
                skills      TEXT,
                salary      TEXT,
                source      TEXT NOT NULL,
                url         TEXT UNIQUE,
                posted_at   TEXT,
                scraped_at  TEXT DEFAULT (datetime('now'))
            )
        """),
        ("002_add_index_source", """
            CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(source)
        """),
        ("003_add_index_city", """
            CREATE INDEX IF NOT EXISTS idx_jobs_city ON jobs(city)
        """),
    ]

    for name, sql in migrations:
        # Check if already applied
        cursor.execute("SELECT 1 FROM migrations WHERE name = ?", (name,))
        if cursor.fetchone():
            continue  # Already applied - skip

        cursor.execute(sql)
        cursor.execute("INSERT INTO migrations (name) VALUES (?)", (name,))


def init_db():
    """
    Initialize database - run migrations once per process.
    Safe to call multiple times - will skip if already done.
    """
    global _INITIALIZED
    if _INITIALIZED:
        return

    conn = get_connection()
    cursor = conn.cursor()
    _run_migrations(cursor)
    conn.commit()
    conn.close()
    _INITIALIZED = True


def job_exists(url: str) -> bool:
    """Check if a job with this URL already exists."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM jobs WHERE url = ?", (url,))
    result = cursor.fetchone()
    conn.close()
    return result is not None


def insert_job(job: dict) -> bool:
    """
    Insert one job into the database.
    Returns True if inserted, False if already exists.
    """
    # Validate required fields
    url = job.get("url", "")
    if not url or not url.startswith(("http://", "https://")):
        return False
    if not job.get("title"):
        return False
    init_db()
    if job_exists(job.get("url", "")):
        return False

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO jobs (title, company, city, region, contract, skills, salary, source, url, posted_at)
        VALUES (:title, :company, :city, :region, :contract, :skills, :salary, :source, :url, :posted_at)
    """, job)
    conn.commit()
    conn.close()
    return True


if __name__ == "__main__":
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, applied_at FROM migrations")
    print("Applied migrations:")
    for row in cursor.fetchall():
        print(f"  ✓ {row[0]} — {row[1]}")
    conn.close()

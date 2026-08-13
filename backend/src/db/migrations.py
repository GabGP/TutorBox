import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)


def get_migrations_dir() -> Path:
    base_dir = Path(__file__).resolve().parent.parent.parent
    return base_dir / "migrations"


def apply_migrations(db_path: str) -> None:
    """
    Applies numbered SQL migration files idempotently to the SQLite database.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Ensure schema_migrations table exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()

    # Get already applied versions
    cursor.execute("SELECT version FROM schema_migrations")
    applied_versions = {row[0] for row in cursor.fetchall()}

    migrations_dir = get_migrations_dir()
    if not migrations_dir.exists():
        logger.warning(f"Migrations directory not found at {migrations_dir}")
        conn.close()
        return

    sql_files = sorted(migrations_dir.glob("*.sql"))

    for sql_file in sql_files:
        try:
            version_str = sql_file.name.split("_")[0]
            version = int(version_str)
        except (ValueError, IndexError):
            logger.warning(
                f"Skipping migration file with invalid name format: {sql_file.name}"
            )
            continue

        if version in applied_versions:
            continue

        logger.info(f"Applying migration {sql_file.name} (version {version})...")
        sql_script = sql_file.read_text(encoding="utf-8")

        cursor.executescript(sql_script)
        cursor.execute("INSERT INTO schema_migrations (version) VALUES (?)", (version,))
        conn.commit()
        logger.info(f"Migration {sql_file.name} applied successfully.")

    conn.close()

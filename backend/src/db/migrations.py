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
    try:
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
            logger.warning("Migrations directory not found at %s", migrations_dir)
            return

        sql_files = sorted(migrations_dir.glob("*.sql"))

        for sql_file in sql_files:
            try:
                version_str = sql_file.name.split("_")[0]
                version = int(version_str)
            except (ValueError, IndexError):
                logger.warning(
                    "Skipping migration file with invalid name format: %s",
                    sql_file.name,
                )
                continue

            if version in applied_versions:
                continue

            logger.info("Applying migration %s (version %d)...", sql_file.name, version)
            sql_script = sql_file.read_text(encoding="utf-8")

            try:
                conn.execute("BEGIN")
                statements = [s.strip() for s in sql_script.split(";") if s.strip()]
                for statement in statements:
                    cursor.execute(statement)
                cursor.execute(
                    "INSERT INTO schema_migrations (version) VALUES (?)", (version,)
                )
                conn.commit()
                logger.info("Migration %s applied successfully.", sql_file.name)
            except Exception:
                conn.rollback()
                logger.exception("Migration %s FAILED. Rolled back.", sql_file.name)
                raise
    finally:
        conn.close()

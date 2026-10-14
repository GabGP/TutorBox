"""One-time move of the database file from its pre-rename name to the current default.

The appliance stored its data in `tutorbox.db` before the product became Utz'tutor,
and its default is now `utztutor.db`. Without this step the first start after the
rename would create an empty database next to the real one, and every user and record
would look lost. The move runs only when the default location is in use, the new file
does not exist yet and the old file does, so it happens at most once.
"""

import logging
import os
import sqlite3
from pathlib import Path

from core.config.constants import DEFAULT_DB_PATH, LEGACY_DB_PATH

__all__ = ["adopt_legacy_database"]

logger = logging.getLogger(__name__)


def adopt_legacy_database(
    db_path: str,
    *,
    default_path: str = DEFAULT_DB_PATH,
    legacy_path: str = LEGACY_DB_PATH,
) -> bool:
    """Moves the legacy database file to db_path and returns True when it did.

    Nothing is changed when db_path is not the default location (an explicit
    DATABASE_PATH is never touched), when db_path already exists, or when there is no
    legacy file. Raises RuntimeError, before anything is moved or created, when SQLite
    cannot switch the legacy file out of WAL mode.
    """
    target = Path(db_path)
    legacy = Path(legacy_path)
    if target.resolve() != Path(default_path).resolve():
        return False
    if target.exists():
        if legacy.exists():
            logger.warning(
                "Both %s and %s exist; %s is left as it is.",
                legacy.name,
                target.name,
                legacy.name,
            )
        return False
    if not legacy.exists():
        return False
    if not _switch_to_rollback_journal(legacy_path):
        # Returning here would let the migrations create an empty new file, and the
        # old one would never be moved. Stopping the start-up keeps it retryable.
        raise RuntimeError(
            f"Could not switch {legacy.name} out of WAL mode (is another process "
            f"using it?), so it was not moved to {target.name}."
        )
    os.replace(legacy_path, db_path)
    logger.info("Moved the database from %s to %s.", legacy.name, target.name)
    return True


def _switch_to_rollback_journal(database_path: str) -> bool:
    """Folds the write-ahead log into the main file and removes the -wal and -shm files.

    SQLite keeps WAL mode while another connection still has the file open, so the
    journal mode SQLite reports is checked before the file is moved.
    """
    connection = sqlite3.connect(database_path)
    try:
        journal_mode = connection.execute("PRAGMA journal_mode = DELETE;").fetchone()[0]
    finally:
        connection.close()
    return str(journal_mode).lower() == "delete"

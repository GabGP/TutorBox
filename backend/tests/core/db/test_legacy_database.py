"""Tests for moving the pre-rename database file to the current default name."""

import asyncio
import logging
import shutil
import sqlite3
from pathlib import Path

import pytest

from core.db import legacy_database
from core.db.legacy_database import adopt_legacy_database
from src import main as app_main

LEGACY_NAME = "tutorbox.db"
DEFAULT_NAME = "utztutor.db"


def create_database(database_path: Path, note_bodies: list[str]) -> None:
    """Creates a WAL-mode database with a notes table, as the appliance does, then closes it."""
    connection = sqlite3.connect(database_path)
    try:
        connection.execute("PRAGMA journal_mode = WAL;")
        connection.execute("CREATE TABLE notes (body TEXT NOT NULL)")
        connection.executemany(
            "INSERT INTO notes (body) VALUES (?)", [(body,) for body in note_bodies]
        )
        connection.commit()
    finally:
        connection.close()


def read_note_bodies(database_path: Path) -> list[str]:
    """Returns the note bodies of a database in a stable order."""
    connection = sqlite3.connect(database_path)
    try:
        rows = connection.execute("SELECT body FROM notes ORDER BY body").fetchall()
    finally:
        connection.close()
    return [row[0] for row in rows]


def test_moves_legacy_file_to_default_name(tmp_path: Path):
    """Verifies rows of the old file are readable under the new name and no old files remain."""
    legacy_db = tmp_path / LEGACY_NAME
    create_database(legacy_db, ["ana", "luis"])
    target_db = tmp_path / DEFAULT_NAME

    moved = adopt_legacy_database(
        str(target_db), default_path=str(target_db), legacy_path=str(legacy_db)
    )

    assert moved is True
    assert read_note_bodies(target_db) == ["ana", "luis"]
    assert not legacy_db.exists()
    assert not Path(f"{legacy_db}-wal").exists()
    assert not Path(f"{legacy_db}-shm").exists()


def test_keeps_rows_that_are_only_in_the_write_ahead_log(tmp_path: Path):
    """Verifies rows that were never checkpointed into the main file survive the move."""
    source_folder = tmp_path / "source"
    source_folder.mkdir()
    source_db = source_folder / LEGACY_NAME
    connection = sqlite3.connect(source_db)
    connection.execute("PRAGMA journal_mode = WAL;")
    connection.execute("PRAGMA wal_autocheckpoint = 0;")
    connection.execute("CREATE TABLE notes (body TEXT NOT NULL)")
    connection.executemany(
        "INSERT INTO notes (body) VALUES (?)", [("kept",), ("only_in_wal",)]
    )
    connection.commit()
    # Copied while the connection is open: the rows exist only in the copied -wal file.
    legacy_folder = tmp_path / "legacy_copy"
    legacy_folder.mkdir()
    legacy_db = legacy_folder / LEGACY_NAME
    shutil.copyfile(source_db, legacy_db)
    shutil.copyfile(f"{source_db}-wal", f"{legacy_db}-wal")
    connection.close()
    target_db = legacy_folder / DEFAULT_NAME
    assert Path(f"{legacy_db}-wal").exists()

    moved = adopt_legacy_database(
        str(target_db), default_path=str(target_db), legacy_path=str(legacy_db)
    )

    assert moved is True
    assert read_note_bodies(target_db) == ["kept", "only_in_wal"]
    assert not Path(f"{legacy_db}-wal").exists()


def test_explicit_database_path_is_never_touched(tmp_path: Path):
    """Verifies a DATABASE_PATH naming another file leaves the legacy file in place."""
    default_folder = tmp_path / "default"
    default_folder.mkdir()
    legacy_db = default_folder / LEGACY_NAME
    create_database(legacy_db, ["kept"])
    custom_db = tmp_path / "custom" / "classroom.db"

    moved = adopt_legacy_database(
        str(custom_db),
        default_path=str(default_folder / DEFAULT_NAME),
        legacy_path=str(legacy_db),
    )

    assert moved is False
    assert legacy_db.exists()
    assert not custom_db.exists()


def test_existing_new_file_is_left_alone_with_a_warning(tmp_path: Path, caplog):
    """Verifies that when both files exist neither changes and a warning names them."""
    legacy_db = tmp_path / LEGACY_NAME
    target_db = tmp_path / DEFAULT_NAME
    create_database(legacy_db, ["old"])
    create_database(target_db, ["new"])
    legacy_bytes = legacy_db.read_bytes()
    target_bytes = target_db.read_bytes()

    with caplog.at_level(logging.WARNING, logger="core.db.legacy_database"):
        moved = adopt_legacy_database(
            str(target_db), default_path=str(target_db), legacy_path=str(legacy_db)
        )

    assert moved is False
    assert legacy_db.read_bytes() == legacy_bytes
    assert target_db.read_bytes() == target_bytes
    assert "Both tutorbox.db and utztutor.db exist" in caplog.text


def test_no_legacy_file_creates_nothing(tmp_path: Path):
    """Verifies a fresh install neither moves anything nor creates the database early."""
    target_db = tmp_path / DEFAULT_NAME

    moved = adopt_legacy_database(
        str(target_db),
        default_path=str(target_db),
        legacy_path=str(tmp_path / LEGACY_NAME),
    )

    assert moved is False
    assert list(tmp_path.iterdir()) == []


class _FakeCursor:
    def __init__(self, journal_mode: str) -> None:
        self._journal_mode = journal_mode

    def fetchone(self) -> tuple[str]:
        return (self._journal_mode,)


class _FakeConnection:
    """Stands in for a connection that SQLite refuses to switch out of WAL mode."""

    def __init__(self) -> None:
        self.closed = False
        self.statements: list[str] = []

    def execute(self, statement: str) -> _FakeCursor:
        self.statements.append(statement)
        return _FakeCursor("wal")

    def close(self) -> None:
        self.closed = True


def test_start_up_stops_when_sqlite_keeps_wal_mode(tmp_path: Path, monkeypatch):
    """Verifies that a journal mode other than delete raises and moves nothing.

    Returning instead would let the migrations create an empty new file next to the
    real data, and the old file would never be moved.
    """
    legacy_db = tmp_path / LEGACY_NAME
    create_database(legacy_db, ["kept"])
    fake_connection = _FakeConnection()
    monkeypatch.setattr(
        legacy_database.sqlite3, "connect", lambda _path: fake_connection
    )
    target_db = tmp_path / DEFAULT_NAME

    with pytest.raises(RuntimeError, match="out of WAL mode"):
        adopt_legacy_database(
            str(target_db), default_path=str(target_db), legacy_path=str(legacy_db)
        )

    assert fake_connection.closed
    assert fake_connection.statements == ["PRAGMA journal_mode = DELETE;"]
    assert legacy_db.exists()
    assert not target_db.exists()


def test_app_startup_adopts_legacy_database_before_migrating(
    tmp_path: Path, monkeypatch
):
    """Verifies lifespan moves the legacy file before migrations open the database."""
    calls: list[tuple[str, str]] = []
    target_path = str(tmp_path / DEFAULT_NAME)
    monkeypatch.setattr(app_main, "get_db_path", lambda: target_path)
    monkeypatch.setattr(
        app_main,
        "adopt_legacy_database",
        lambda path: calls.append(("adopt", path)),
    )
    monkeypatch.setattr(
        app_main,
        "apply_migrations",
        lambda path: calls.append(("migrate", path)),
    )
    monkeypatch.setattr(app_main, "seed_question_bank", lambda path: 0)
    monkeypatch.setattr(app_main, "seed_teacher", lambda path: False)

    async def run_lifespan() -> None:
        async with app_main.lifespan(app_main.app):
            pass

    asyncio.run(run_lifespan())

    assert calls == [("adopt", target_path), ("migrate", target_path)]

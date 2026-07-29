"""SQLite persistence layer using only the standard library."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import streamlit as st

DB_PATH = Path(__file__).resolve().parent / "rome_lads.sqlite3"

SCHEMA = """
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS lads (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL UNIQUE,
    nickname   TEXT NOT NULL DEFAULT '',
    home_town  TEXT NOT NULL DEFAULT '',
    accent     TEXT NOT NULL DEFAULT '#C7512F',
    notes      TEXT NOT NULL DEFAULT '',
    avatar_png BLOB
);

CREATE TABLE IF NOT EXISTS pints (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    lad_id      INTEGER NOT NULL REFERENCES lads(id) ON DELETE CASCADE,
    consumed_at TEXT NOT NULL,
    venue       TEXT NOT NULL DEFAULT '',
    beer        TEXT NOT NULL DEFAULT '',
    note        TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_pints_lad ON pints(lad_id, consumed_at);

CREATE TABLE IF NOT EXISTS media (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    kind         TEXT NOT NULL CHECK (kind IN ('photo','video')),
    owner_id     INTEGER NOT NULL REFERENCES lads(id) ON DELETE CASCADE,
    caption      TEXT NOT NULL DEFAULT '',
    day          TEXT NOT NULL,
    location     TEXT NOT NULL DEFAULT '',
    url          TEXT,
    blob         BLOB,
    thumb        BLOB,
    mime         TEXT NOT NULL DEFAULT 'image/jpeg',
    is_highlight INTEGER NOT NULL DEFAULT 0,
    created_at   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_media_day ON media(day);

CREATE TABLE IF NOT EXISTS media_likes (
    media_id INTEGER NOT NULL REFERENCES media(id) ON DELETE CASCADE,
    lad_id   INTEGER NOT NULL REFERENCES lads(id) ON DELETE CASCADE,
    PRIMARY KEY (media_id, lad_id)
);

CREATE TABLE IF NOT EXISTS comments (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    media_id   INTEGER NOT NULL REFERENCES media(id) ON DELETE CASCADE,
    author_id  INTEGER NOT NULL REFERENCES lads(id) ON DELETE CASCADE,
    body       TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS activities (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    day         TEXT NOT NULL,
    start_time  TEXT NOT NULL,
    end_time    TEXT NOT NULL,
    title       TEXT NOT NULL,
    category    TEXT NOT NULL DEFAULT 'Sightseeing',
    location    TEXT NOT NULL DEFAULT '',
    cost_eur    REAL NOT NULL DEFAULT 0,
    status      TEXT NOT NULL DEFAULT 'planned',
    booking_ref TEXT NOT NULL DEFAULT '',
    notes       TEXT NOT NULL DEFAULT '',
    image_url   TEXT NOT NULL DEFAULT '',
    sort_order  INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_activities_day ON activities(day, sort_order);

CREATE TABLE IF NOT EXISTS activity_votes (
    activity_id INTEGER NOT NULL REFERENCES activities(id) ON DELETE CASCADE,
    lad_id      INTEGER NOT NULL REFERENCES lads(id) ON DELETE CASCADE,
    value       INTEGER NOT NULL CHECK (value IN (-1, 1)),
    PRIMARY KEY (activity_id, lad_id)
);
"""


@st.cache_resource(show_spinner=False)
def get_connection(db_path: str | None = None) -> sqlite3.Connection:
    """Return a cached, row-factory-enabled SQLite connection.

    The connection is shared across Streamlit reruns via ``st.cache_resource``
    and allows cross-thread use because Streamlit serves each session from a
    script-runner thread.

    Args:
        db_path: Optional override, primarily for tests.

    Returns:
        An initialised :class:`sqlite3.Connection`.
    """
    path = Path(db_path) if db_path else DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
    connection.row_factory = sqlite3.Row
    connection.executescript(SCHEMA)
    return connection


def reset_database(connection: sqlite3.Connection) -> None:
    """Drop all trip data and recreate the schema (used by 'Reset trip data')."""
    tables = ("activity_votes", "activities", "comments", "media_likes", "media", "pints", "lads", "settings")
    for table in tables:
        connection.execute(f"DROP TABLE IF EXISTS {table}")
    connection.executescript(SCHEMA)

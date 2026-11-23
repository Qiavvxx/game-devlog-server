from contextlib import contextmanager
import os
from pathlib import Path
import sqlite3


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "data" / "devlog.sqlite3"

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL COLLATE NOCASE UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    genre TEXT NOT NULL DEFAULT '',
    engine TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'in_development',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    entry_date TEXT NOT NULL,
    completed TEXT NOT NULL,
    difficulties TEXT NOT NULL DEFAULT '',
    next_step TEXT NOT NULL DEFAULT '',
    category TEXT NOT NULL DEFAULT 'other',
    minutes_spent INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'planned',
    priority TEXT NOT NULL DEFAULT 'medium',
    due_date TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);
CREATE INDEX IF NOT EXISTS idx_entries_project_date
    ON entries(project_id, entry_date DESC, id DESC);
CREATE INDEX IF NOT EXISTS idx_tasks_project_status_due
    ON tasks(project_id, status, due_date);
"""


def _add_column_if_missing(connection: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    columns = {
        row["name"]
        for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
    }
    if column not in columns:
        connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def _database_path() -> Path:
    configured_path = os.getenv("DATABASE_PATH")
    return Path(configured_path).expanduser() if configured_path else DEFAULT_DATABASE_PATH


@contextmanager
def get_connection():
    database_path = _database_path()
    database_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(database_path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_database() -> None:
    with get_connection() as connection:
        connection.executescript(SCHEMA)
        _add_column_if_missing(connection, "projects", "genre", "TEXT NOT NULL DEFAULT ''")
        _add_column_if_missing(connection, "projects", "engine", "TEXT NOT NULL DEFAULT ''")
        _add_column_if_missing(
            connection,
            "projects",
            "status",
            "TEXT NOT NULL DEFAULT 'in_development'",
        )
        _add_column_if_missing(connection, "entries", "category", "TEXT NOT NULL DEFAULT 'other'")
        _add_column_if_missing(connection, "entries", "minutes_spent", "INTEGER NOT NULL DEFAULT 0")

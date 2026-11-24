from datetime import datetime, timezone

from app.database import get_connection


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _as_dict(row):
    return dict(row) if row is not None else None


def get_user_by_id(user_id: int):
    with get_connection() as connection:
        row = connection.execute(
            "SELECT id, username, password_hash, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    return _as_dict(row)


def get_user_by_username(username: str):
    with get_connection() as connection:
        row = connection.execute(
            "SELECT id, username, password_hash, created_at "
            "FROM users WHERE username = ? COLLATE NOCASE",
            (username,),
        ).fetchone()
    return _as_dict(row)


def create_user(username: str, password_hash: str):
    with get_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
            (username, password_hash, _now()),
        )
        user_id = cursor.lastrowid
    return get_user_by_id(user_id)

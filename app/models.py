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


def list_projects(user_id: int) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT id, title, description, genre, engine, status, created_at, updated_at "
            "FROM projects WHERE user_id = ? ORDER BY id DESC",
            (user_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_project_for_user(project_id: int, user_id: int):
    with get_connection() as connection:
        row = connection.execute(
            "SELECT id, user_id, title, description, genre, engine, status, created_at, updated_at "
            "FROM projects WHERE id = ? AND user_id = ?",
            (project_id, user_id),
        ).fetchone()
    return _as_dict(row)


def create_project(
    user_id: int,
    title: str,
    description: str,
    genre: str,
    engine: str,
    status: str,
):
    now = _now()
    with get_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO projects "
            "(user_id, title, description, genre, engine, status, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, title, description, genre, engine, status, now, now),
        )
        project_id = cursor.lastrowid
    return get_project_for_user(project_id, user_id)


def update_project(
    project_id: int,
    user_id: int,
    title: str,
    description: str,
    genre: str,
    engine: str,
    status: str,
) -> bool:
    with get_connection() as connection:
        cursor = connection.execute(
            "UPDATE projects SET title = ?, description = ?, genre = ?, engine = ?, "
            "status = ?, updated_at = ? "
            "WHERE id = ? AND user_id = ?",
            (title, description, genre, engine, status, _now(), project_id, user_id),
        )
    return cursor.rowcount > 0


def delete_project(project_id: int, user_id: int) -> bool:
    with get_connection() as connection:
        cursor = connection.execute(
            "DELETE FROM projects WHERE id = ? AND user_id = ?",
            (project_id, user_id),
        )
    return cursor.rowcount > 0

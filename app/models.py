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


def list_entries(
    project_id: int,
    category: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict]:
    conditions = ["project_id = ?"]
    parameters: list[str | int] = [project_id]
    if category is not None:
        conditions.append("category = ?")
        parameters.append(category)
    if date_from is not None:
        conditions.append("entry_date >= ?")
        parameters.append(date_from)
    if date_to is not None:
        conditions.append("entry_date <= ?")
        parameters.append(date_to)

    with get_connection() as connection:
        rows = connection.execute(
            "SELECT id, project_id, entry_date, completed, difficulties, next_step, "
            "category, minutes_spent, created_at, updated_at FROM entries WHERE "
            + " AND ".join(conditions)
            + " ORDER BY entry_date DESC, id DESC",
            parameters,
        ).fetchall()
    return [dict(row) for row in rows]


def get_entry_for_user(entry_id: int, user_id: int):
    with get_connection() as connection:
        row = connection.execute(
            "SELECT entries.id, entries.project_id, entries.entry_date, "
            "entries.completed, entries.difficulties, entries.next_step, "
            "entries.category, entries.minutes_spent, entries.created_at, entries.updated_at "
            "FROM entries JOIN projects ON projects.id = entries.project_id "
            "WHERE entries.id = ? AND projects.user_id = ?",
            (entry_id, user_id),
        ).fetchone()
    return _as_dict(row)


def create_entry(
    project_id: int,
    entry_date: str,
    completed: str,
    difficulties: str,
    next_step: str,
    category: str,
    minutes_spent: int,
):
    now = _now()
    with get_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO entries "
            "(project_id, entry_date, completed, difficulties, next_step, category, "
            "minutes_spent, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                project_id,
                entry_date,
                completed,
                difficulties,
                next_step,
                category,
                minutes_spent,
                now,
                now,
            ),
        )
        entry_id = cursor.lastrowid
    return get_entry_for_project(entry_id, project_id)


def get_entry_for_project(entry_id: int, project_id: int):
    with get_connection() as connection:
        row = connection.execute(
            "SELECT id, project_id, entry_date, completed, difficulties, next_step, "
            "category, minutes_spent, created_at, updated_at "
            "FROM entries WHERE id = ? AND project_id = ?",
            (entry_id, project_id),
        ).fetchone()
    return _as_dict(row)


def update_entry(
    entry_id: int,
    user_id: int,
    entry_date: str,
    completed: str,
    difficulties: str,
    next_step: str,
    category: str,
    minutes_spent: int,
) -> bool:
    with get_connection() as connection:
        cursor = connection.execute(
            "UPDATE entries SET entry_date = ?, completed = ?, difficulties = ?, "
            "next_step = ?, category = ?, minutes_spent = ?, updated_at = ? "
            "WHERE id = ? AND project_id IN "
            "(SELECT id FROM projects WHERE user_id = ?)",
            (
                entry_date,
                completed,
                difficulties,
                next_step,
                category,
                minutes_spent,
                _now(),
                entry_id,
                user_id,
            ),
        )
    return cursor.rowcount > 0


def delete_entry(entry_id: int, user_id: int) -> bool:
    with get_connection() as connection:
        cursor = connection.execute(
            "DELETE FROM entries WHERE id = ? AND project_id IN "
            "(SELECT id FROM projects WHERE user_id = ?)",
            (entry_id, user_id),
        )
    return cursor.rowcount > 0

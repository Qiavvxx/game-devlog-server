import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "test.sqlite3"))
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-local-api-tests-only-123456")

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


def register_and_login(client: TestClient, username: str) -> str:
    response = client.post(
        "/auth/register",
        json={"username": username, "password": "safe-password-123"},
    )
    assert response.status_code == 201

    response = client.post(
        "/auth/token",
        data={"username": username, "password": "safe-password-123"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_api_requires_login(client: TestClient):
    response = client.get("/projects")
    assert response.status_code == 401


def test_register_login_and_reject_duplicate_username(client: TestClient):
    token = register_and_login(client, "samir")
    assert token

    user_response = client.post(
        "/auth/register",
        json={"username": "hidden_password", "password": "safe-password-123"},
    )
    assert user_response.status_code == 201
    assert "password_hash" not in user_response.json()
    assert "password" not in user_response.json()

    response = client.post(
        "/auth/register",
        json={"username": "SAMIR", "password": "another-password"},
    )
    assert response.status_code == 409


def test_project_and_entry_crud(client: TestClient):
    token = register_and_login(client, "developer")
    headers = {"Authorization": f"Bearer {token}"}

    project_response = client.post(
        "/projects",
        headers=headers,
        json={
            "title": "Первый проект",
            "description": "Прототип игры",
            "genre": "Приключение",
            "engine": "Godot",
            "status": "in_development",
        },
    )
    assert project_response.status_code == 201
    project_id = project_response.json()["id"]
    assert project_response.json()["engine"] == "Godot"
    assert project_response.json()["status"] == "in_development"

    project_list = client.get("/projects", headers=headers)
    assert project_list.status_code == 200
    assert [item["id"] for item in project_list.json()] == [project_id]

    project_update = client.put(
        f"/projects/{project_id}",
        headers=headers,
        json={
            "title": "Первый проект после правки",
            "description": "Новая версия",
            "genre": "Приключение",
            "engine": "Godot",
            "status": "testing",
        },
    )
    assert project_update.status_code == 200
    assert project_update.json()["title"] == "Первый проект после правки"
    assert project_update.json()["status"] == "testing"

    project_detail = client.get(f"/projects/{project_id}", headers=headers)
    assert project_detail.status_code == 200
    assert project_detail.json()["description"] == "Новая версия"

    entry_response = client.post(
        f"/projects/{project_id}/entries",
        headers=headers,
        json={
            "entry_date": "2026-11-22",
            "completed": "Собрал первый уровень",
            "difficulties": "Не сработал переход между сценами",
            "next_step": "Проверить загрузку следующей сцены",
            "category": "programming",
            "minutes_spent": 90,
        },
    )
    assert entry_response.status_code == 201
    entry_id = entry_response.json()["id"]

    entries_response = client.get(
        f"/projects/{project_id}/entries",
        headers=headers,
    )
    assert entries_response.status_code == 200
    assert [item["id"] for item in entries_response.json()] == [entry_id]
    assert entries_response.json()[0]["minutes_spent"] == 90

    update_response = client.put(
        f"/entries/{entry_id}",
        headers=headers,
        json={
            "entry_date": "2026-11-23",
            "completed": "Исправил переход между сценами",
            "difficulties": "",
            "next_step": "Добавить экран паузы",
            "category": "testing",
            "minutes_spent": 45,
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["entry_date"] == "2026-11-23"
    assert update_response.json()["category"] == "testing"
    assert update_response.json()["minutes_spent"] == 45

    delete_response = client.delete(f"/entries/{entry_id}", headers=headers)
    assert delete_response.status_code == 204

    project_delete = client.delete(f"/projects/{project_id}", headers=headers)
    assert project_delete.status_code == 204


def test_users_cannot_read_each_others_projects(client: TestClient):
    first_token = register_and_login(client, "first_user")
    first_headers = {"Authorization": f"Bearer {first_token}"}
    project = client.post(
        "/projects",
        headers=first_headers,
        json={"title": "Чужой проект", "description": ""},
    ).json()
    entry_response = client.post(
        f"/projects/{project['id']}/entries",
        headers=first_headers,
        json={"entry_date": "2026-11-22", "completed": "Заметка первого автора"},
    )
    assert entry_response.status_code == 201
    entry_id = entry_response.json()["id"]
    task_response = client.post(
        f"/projects/{project['id']}/tasks",
        headers=first_headers,
        json={"title": "Чужая задача"},
    )
    assert task_response.status_code == 201
    task_id = task_response.json()["id"]

    second_token = register_and_login(client, "second_user")
    second_headers = {"Authorization": f"Bearer {second_token}"}

    response = client.get(f"/projects/{project['id']}", headers=second_headers)
    assert response.status_code == 404

    response = client.get(f"/entries/{entry_id}", headers=second_headers)
    assert response.status_code == 404

    response = client.get(f"/tasks/{task_id}", headers=second_headers)
    assert response.status_code == 404


def test_entries_are_returned_newest_first(client: TestClient):
    token = register_and_login(client, "chronology")
    headers = {"Authorization": f"Bearer {token}"}
    project = client.post(
        "/projects",
        headers=headers,
        json={"title": "Хронология", "description": ""},
    ).json()

    for entry_date in ("2026-11-20", "2026-11-22", "2026-11-21"):
        response = client.post(
            f"/projects/{project['id']}/entries",
            headers=headers,
            json={"entry_date": entry_date, "completed": f"Работа за {entry_date}"},
        )
        assert response.status_code == 201

    response = client.get(f"/projects/{project['id']}/entries", headers=headers)
    assert response.status_code == 200
    assert [item["entry_date"] for item in response.json()] == [
        "2026-11-22",
        "2026-11-21",
        "2026-11-20",
    ]


def test_diary_filters_and_project_summary(client: TestClient):
    token = register_and_login(client, "progress_report")
    headers = {"Authorization": f"Bearer {token}"}
    project_response = client.post(
        "/projects",
        headers=headers,
        json={
            "title": "RPG",
            "description": "Проверка сводки",
            "genre": "RPG",
            "engine": "Godot",
            "status": "testing",
        },
    )
    assert project_response.status_code == 201
    project_id = project_response.json()["id"]

    entries = (
        ("2026-11-20", "Исправил бой", "programming", 120),
        ("2026-11-21", "Нарисовал иконки", "graphics", 30),
        ("2026-11-22", "Проверил бой", "programming", 45),
    )
    for entry_date, completed, category, minutes_spent in entries:
        response = client.post(
            f"/projects/{project_id}/entries",
            headers=headers,
            json={
                "entry_date": entry_date,
                "completed": completed,
                "category": category,
                "minutes_spent": minutes_spent,
            },
        )
        assert response.status_code == 201

    filtered = client.get(
        f"/projects/{project_id}/entries?category=programming&date_from=2026-11-21",
        headers=headers,
    )
    assert filtered.status_code == 200
    assert [item["entry_date"] for item in filtered.json()] == ["2026-11-22"]

    summary = client.get(f"/projects/{project_id}/summary", headers=headers)
    assert summary.status_code == 200
    assert summary.json()["project_title"] == "RPG"
    assert summary.json()["status"] == "testing"
    assert summary.json()["entries_count"] == 3
    assert summary.json()["minutes_spent"] == 195
    assert summary.json()["last_entry_date"] == "2026-11-22"
    assert summary.json()["category_counts"] == {"graphics": 1, "programming": 2}

    invalid_range = client.get(
        f"/projects/{project_id}/entries?date_from=2026-11-23&date_to=2026-11-20",
        headers=headers,
    )
    assert invalid_range.status_code == 422


def test_project_tasks_crud_and_summary(client: TestClient):
    token = register_and_login(client, "task_manager")
    headers = {"Authorization": f"Bearer {token}"}
    project = client.post(
        "/projects",
        headers=headers,
        json={"title": "Платформер", "engine": "Godot"},
    ).json()
    project_id = project["id"]

    created = client.post(
        f"/projects/{project_id}/tasks",
        headers=headers,
        json={
            "title": "Собрать экран паузы",
            "description": "Добавить кнопки продолжения и выхода",
            "status": "planned",
            "priority": "high",
            "due_date": "2026-11-30",
        },
    )
    assert created.status_code == 201
    task_id = created.json()["id"]

    planned_tasks = client.get(
        f"/projects/{project_id}/tasks?status=planned",
        headers=headers,
    )
    assert planned_tasks.status_code == 200
    assert [item["id"] for item in planned_tasks.json()] == [task_id]

    updated = client.put(
        f"/tasks/{task_id}",
        headers=headers,
        json={
            "title": "Готовый экран паузы",
            "description": "Кнопки проверены",
            "status": "done",
            "priority": "medium",
            "due_date": None,
        },
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "done"
    assert updated.json()["due_date"] is None

    summary = client.get(f"/projects/{project_id}/summary", headers=headers)
    assert summary.status_code == 200
    assert summary.json()["tasks_count"] == 1
    assert summary.json()["tasks_by_status"] == {
        "planned": 0,
        "in_progress": 0,
        "done": 1,
    }

    deleted = client.delete(f"/tasks/{task_id}", headers=headers)
    assert deleted.status_code == 204


def test_reject_invalid_project_status_and_negative_work_time(client: TestClient):
    token = register_and_login(client, "validation_user")
    headers = {"Authorization": f"Bearer {token}"}

    invalid_project = client.post(
        "/projects",
        headers=headers,
        json={"title": "Проект", "status": "finished"},
    )
    assert invalid_project.status_code == 422

    project = client.post(
        "/projects",
        headers=headers,
        json={"title": "Проект"},
    ).json()
    invalid_task = client.post(
        f"/projects/{project['id']}/tasks",
        headers=headers,
        json={"title": "Задача", "status": "complete"},
    )
    assert invalid_task.status_code == 422

    invalid_entry = client.post(
        f"/projects/{project['id']}/entries",
        headers=headers,
        json={
            "entry_date": "2026-11-22",
            "completed": "Проверка поля времени",
            "minutes_spent": -5,
        },
    )
    assert invalid_entry.status_code == 422


def test_database_migration_preserves_existing_data(tmp_path, monkeypatch):
    import sqlite3

    from app.database import init_database

    database_path = tmp_path / "old-version.sqlite3"
    monkeypatch.setenv("DATABASE_PATH", str(database_path))
    with sqlite3.connect(database_path) as connection:
        connection.executescript(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                title TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL REFERENCES projects(id),
                entry_date TEXT NOT NULL,
                completed TEXT NOT NULL,
                difficulties TEXT NOT NULL DEFAULT '',
                next_step TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            INSERT INTO users (username, password_hash, created_at)
                VALUES ('old_user', 'hash', '2026-11-22T00:00:00+00:00');
            INSERT INTO projects (user_id, title, description, created_at, updated_at)
                VALUES (1, 'Старый проект', '', '2026-11-22T00:00:00+00:00', '2026-11-22T00:00:00+00:00');
            INSERT INTO entries (project_id, entry_date, completed, created_at, updated_at)
                VALUES (1, '2026-11-22', 'Старая запись', '2026-11-22T00:00:00+00:00', '2026-11-22T00:00:00+00:00');
            """
        )

    init_database()
    with sqlite3.connect(database_path) as connection:
        project = connection.execute(
            "SELECT title, genre, engine, status FROM projects WHERE id = 1"
        ).fetchone()
        entry = connection.execute(
            "SELECT completed, category, minutes_spent FROM entries WHERE id = 1"
        ).fetchone()

    assert project == ("Старый проект", "", "", "in_development")
    assert entry == ("Старая запись", "other", 0)


def test_openapi_docs_are_available(client: TestClient):
    docs_response = client.get("/docs")
    schema_response = client.get("/openapi.json")

    assert docs_response.status_code == 200
    assert schema_response.status_code == 200
    assert "/projects" in schema_response.json()["paths"]
    assert "/projects/{project_id}/entries" in schema_response.json()["paths"]
    assert "/projects/{project_id}/tasks" in schema_response.json()["paths"]
    assert "/projects/{project_id}/summary" in schema_response.json()["paths"]

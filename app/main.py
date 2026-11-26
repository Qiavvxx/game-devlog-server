from contextlib import asynccontextmanager
from datetime import date
import sqlite3

from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from app.database import init_database
from app.models import (
    create_entry,
    create_project,
    create_user,
    delete_entry,
    delete_project,
    get_entry_for_user,
    get_project_for_user,
    get_user_by_username,
    list_entries,
    list_projects,
    update_entry,
    update_project,
)
from app.schemas import (
    EntryCategory,
    EntryInput,
    EntryPublic,
    ProjectInput,
    ProjectPublic,
    TokenResponse,
    UserCreate,
    UserPublic,
)
from app.security import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_database()
    yield


app = FastAPI(
    title="Дневники разработки игр",
    description="API для игровых проектов и записей о ходе их разработки.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.post("/auth/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED, tags=["Вход"])
def register(payload: UserCreate):
    if get_user_by_username(payload.username) is not None:
        raise HTTPException(status_code=409, detail="Это имя пользователя уже занято")

    try:
        return create_user(payload.username, hash_password(payload.password))
    except sqlite3.IntegrityError as error:
        raise HTTPException(status_code=409, detail="Это имя пользователя уже занято") from error


@app.post("/auth/token", response_model=TokenResponse, tags=["Вход"])
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user_by_username(form_data.username)
    if user is None or not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenResponse(access_token=create_access_token(user["id"]))


def _project_or_404(project_id: int, user_id: int):
    project = get_project_for_user(project_id, user_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Проект не найден")
    return project


@app.get("/projects", response_model=list[ProjectPublic], tags=["Проекты"])
def get_projects(user: dict = Depends(get_current_user)):
    return list_projects(user["id"])


@app.post("/projects", response_model=ProjectPublic, status_code=201, tags=["Проекты"])
def add_project(payload: ProjectInput, user: dict = Depends(get_current_user)):
    return create_project(
        user["id"],
        payload.title,
        payload.description,
        payload.genre,
        payload.engine,
        payload.status,
    )


@app.get("/projects/{project_id}", response_model=ProjectPublic, tags=["Проекты"])
def get_project(project_id: int, user: dict = Depends(get_current_user)):
    return _project_or_404(project_id, user["id"])


@app.put("/projects/{project_id}", response_model=ProjectPublic, tags=["Проекты"])
def edit_project(
    project_id: int,
    payload: ProjectInput,
    user: dict = Depends(get_current_user),
):
    _project_or_404(project_id, user["id"])
    update_project(
        project_id,
        user["id"],
        payload.title,
        payload.description,
        payload.genre,
        payload.engine,
        payload.status,
    )
    return _project_or_404(project_id, user["id"])


@app.delete("/projects/{project_id}", status_code=204, tags=["Проекты"])
def remove_project(project_id: int, user: dict = Depends(get_current_user)):
    if not delete_project(project_id, user["id"]):
        raise HTTPException(status_code=404, detail="Проект не найден")
    return Response(status_code=204)



def _entry_or_404(entry_id: int, user_id: int):
    entry = get_entry_for_user(entry_id, user_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    return entry


@app.get(
    "/projects/{project_id}/entries",
    response_model=list[EntryPublic],
    tags=["Записи дневника"],
)
def get_project_entries(
    project_id: int,
    category: EntryCategory | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    user: dict = Depends(get_current_user),
):
    _project_or_404(project_id, user["id"])
    if date_from is not None and date_to is not None and date_from > date_to:
        raise HTTPException(status_code=422, detail="Начальная дата позже конечной")
    return list_entries(
        project_id,
        category,
        date_from.isoformat() if date_from else None,
        date_to.isoformat() if date_to else None,
    )


@app.post(
    "/projects/{project_id}/entries",
    response_model=EntryPublic,
    status_code=201,
    tags=["Записи дневника"],
)
def add_project_entry(
    project_id: int,
    payload: EntryInput,
    user: dict = Depends(get_current_user),
):
    _project_or_404(project_id, user["id"])
    return create_entry(
        project_id,
        payload.entry_date.isoformat(),
        payload.completed,
        payload.difficulties,
        payload.next_step,
        payload.category,
        payload.minutes_spent,
    )


@app.get("/entries/{entry_id}", response_model=EntryPublic, tags=["Записи дневника"])
def get_entry(entry_id: int, user: dict = Depends(get_current_user)):
    return _entry_or_404(entry_id, user["id"])


@app.put("/entries/{entry_id}", response_model=EntryPublic, tags=["Записи дневника"])
def edit_entry(
    entry_id: int,
    payload: EntryInput,
    user: dict = Depends(get_current_user),
):
    _entry_or_404(entry_id, user["id"])
    update_entry(
        entry_id,
        user["id"],
        payload.entry_date.isoformat(),
        payload.completed,
        payload.difficulties,
        payload.next_step,
        payload.category,
        payload.minutes_spent,
    )
    return _entry_or_404(entry_id, user["id"])


@app.delete("/entries/{entry_id}", status_code=204, tags=["Записи дневника"])
def remove_entry(entry_id: int, user: dict = Depends(get_current_user)):
    if not delete_entry(entry_id, user["id"]):
        raise HTTPException(status_code=404, detail="Запись не найдена")
    return Response(status_code=204)

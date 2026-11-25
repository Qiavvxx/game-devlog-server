from contextlib import asynccontextmanager
import sqlite3

from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from app.database import init_database
from app.models import (
    create_project,
    create_user,
    delete_project,
    get_project_for_user,
    get_user_by_username,
    list_projects,
    update_project,
)
from app.schemas import (
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

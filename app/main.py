from contextlib import asynccontextmanager
import sqlite3

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.database import init_database
from app.models import create_user, get_user_by_username
from app.schemas import TokenResponse, UserCreate, UserPublic
from app.security import create_access_token, hash_password, verify_password


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

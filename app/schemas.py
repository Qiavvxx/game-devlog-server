from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator


ProjectStatus = Literal["idea", "in_development", "testing", "released", "paused"]
EntryCategory = Literal["game_design", "programming", "graphics", "audio", "testing", "other"]


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("username")
    @classmethod
    def clean_username(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 3:
            raise ValueError("Имя пользователя должно содержать не менее 3 символов")
        return value


class UserPublic(BaseModel):
    id: int
    username: str
    created_at: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ProjectInput(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=4000)
    genre: str = Field(default="", max_length=80)
    engine: str = Field(default="", max_length=80)
    status: ProjectStatus = Field(
        default="in_development",
        description="idea, in_development, testing, released или paused",
    )

    @field_validator("title")
    @classmethod
    def clean_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Название проекта не может быть пустым")
        return value


class ProjectPublic(BaseModel):
    id: int
    title: str
    description: str
    genre: str
    engine: str
    status: ProjectStatus
    created_at: str
    updated_at: str


class EntryInput(BaseModel):
    entry_date: date
    completed: str = Field(min_length=1, max_length=10000)
    difficulties: str = Field(default="", max_length=10000)
    next_step: str = Field(default="", max_length=10000)
    category: EntryCategory = Field(
        default="other",
        description="game_design, programming, graphics, audio, testing или other",
    )
    minutes_spent: int = Field(
        default=0,
        ge=0,
        le=1440,
        description="Время на работу в минутах",
    )

    @field_validator("completed")
    @classmethod
    def clean_completed(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Заполни поле о выполненной работе")
        return value

    @field_validator("difficulties", "next_step")
    @classmethod
    def clean_optional_text(cls, value: str) -> str:
        return value.strip()


class EntryPublic(BaseModel):
    id: int
    project_id: int
    entry_date: date
    completed: str
    difficulties: str
    next_step: str
    category: EntryCategory
    minutes_spent: int
    created_at: str
    updated_at: str

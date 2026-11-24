from pydantic import BaseModel, Field, field_validator


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

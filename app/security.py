from datetime import datetime, timedelta, timezone
import os

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

from app.models import get_user_by_id


load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("Укажи SECRET_KEY в файле .env перед запуском сервера")

ALGORITHM = "HS256"
TOKEN_LIFETIME = timedelta(days=7)
password_hasher = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_hasher.verify(password, password_hash)


def create_access_token(user_id: int) -> str:
    expires_at = datetime.now(timezone.utc) + TOKEN_LIFETIME
    payload = {"sub": str(user_id), "exp": expires_at}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить токен",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload["sub"])
    except (InvalidTokenError, KeyError, TypeError, ValueError) as error:
        raise credentials_error from error

    user = get_user_by_id(user_id)
    if user is None:
        raise credentials_error
    return user

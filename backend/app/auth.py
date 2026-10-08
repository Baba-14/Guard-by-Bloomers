"""Password authentication and signed access-token helpers."""

from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .config import get_settings
from .database import get_db
from .models import User


password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/login", auto_error=False)


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, encoded: str) -> bool:
    return password_hash.verify(password, encoded)


def create_access_token(user: User) -> tuple[str, int]:
    settings = get_settings()
    expires_in = settings.access_token_expire_minutes * 60
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    token = jwt.encode(
        {"sub": str(user.id), "role": user.profile.role.value, "exp": expires_at},
        settings.require_jwt_secret(),
        algorithm=settings.jwt_algorithm,
    )
    return token, expires_in


def _user_from_token(token: str | None, db: Session, *, required: bool) -> User | None:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired access token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if token is None:
        if required:
            raise credentials_error
        return None
    try:
        settings = get_settings()
        payload = jwt.decode(
            token,
            settings.require_jwt_secret(),
            algorithms=[settings.jwt_algorithm],
        )
        user_id = UUID(payload["sub"])
    except (InvalidTokenError, KeyError, ValueError):
        raise credentials_error

    user = db.scalar(
        select(User).options(selectinload(User.profile)).where(User.id == user_id)
    )
    if user is None or not user.is_active:
        raise credentials_error
    return user


def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    user = _user_from_token(token, db, required=True)
    assert user is not None
    return user


def get_optional_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User | None:
    return _user_from_token(token, db, required=False)

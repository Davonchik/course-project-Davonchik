import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from passlib.context import CryptContext

from config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    print("!!!!!!!!!!!")
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(*, subject: int | str, role: str, device: str) -> str:
    now = _now()
    payload: dict[str, Any] = {
        "sub": str(subject),
        "role": role,
        "type": "access",
        "device": device,  # привязка к устройству
        "jti": uuid.uuid4().hex,  # уникальный ID токена
        "iss": settings.JWT_ISSUER,
        "iat": int(now.timestamp()),
        "exp": int(
            (now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp()
        ),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_payload(*, subject: int | str, device: str) -> dict[str, Any]:
    now = _now()
    return {
        "sub": str(subject),
        "type": "refresh",
        "device": device,  # привязка к устройству
        "jti": uuid.uuid4().hex,
        "iss": settings.JWT_ISSUER,
        "iat": int(now.timestamp()),
        "exp": int(
            (now + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)).timestamp()
        ),
    }


def encode_token(payload: dict[str, Any]) -> str:
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(
        token,
        settings.JWT_SECRET,
        algorithms=[settings.JWT_ALGORITHM],
        options={"require": ["exp", "iat", "sub", "iss", "type", "jti"]},
        issuer=settings.JWT_ISSUER,
    )

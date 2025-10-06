from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from adapters.db import get_db_session
from adapters.security import decode_token
from services.tokens import is_jti_blacklisted


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, prefixes: list[str]):
        super().__init__(app)
        self.prefixes = prefixes

    async def dispatch(self, request: Request, call_next):
        # служебные/публичные пути
        if request.method == "OPTIONS" or request.url.path in (
            "/docs",
            "/openapi.json",
            "/redoc",
        ):
            return await call_next(request)

        # если путь не защищён — пропускаем
        if not any(request.url.path.startswith(p) for p in self.prefixes):
            return await call_next(request)

        # Authorization: Bearer <token>
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing Authorization header"},
            )

        parts = auth_header.split(" ", 1)
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid Authorization scheme"},
            )

        token = parts[1].strip()
        if not token:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Empty bearer token"},
            )

        # валидация токена
        try:
            payload = decode_token(token)
        except Exception:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid or expired token"},
            )

        if payload.get("type") != "access":
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Access token required"},
            )

        jti = payload.get("jti")
        sub = payload.get("sub")
        role = payload.get("role") or "user"

        # проверка блэклиста (аккуратно закрываем генератор-сессию)
        agen = get_db_session()
        try:
            session = await agen.__anext__()  # взять первую yield-сессию
            blacklisted = await is_jti_blacklisted(session, jti)
        finally:
            await agen.aclose()

        if blacklisted:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Token revoked"},
            )

        try:
            user_id = int(sub)
        except Exception:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid token subject"},
            )

        # кладём компактного пользователя в state
        request.state.user = {"id": user_id, "role": role, "claims": payload}

        return await call_next(request)

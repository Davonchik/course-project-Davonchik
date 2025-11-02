import logging

from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware

from adapters.db import get_db_session
from adapters.security import decode_token
from app.errors import problem
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
            cid = getattr(request.state, "correlation_id", None)
            return problem(
                status.HTTP_401_UNAUTHORIZED,
                "Unauthorized",
                "Missing Authorization header",
                type_="urn:errors:auth:missing-authorization",
                cid=cid,
            )

        parts = auth_header.split(" ", 1)
        if len(parts) != 2 or parts[0].lower() != "bearer":
            cid = getattr(request.state, "correlation_id", None)
            return problem(
                status.HTTP_401_UNAUTHORIZED,
                "Unauthorized",
                "Invalid Authorization scheme",
                type_="urn:errors:auth:invalid-scheme",
                cid=cid,
            )

        token = parts[1].strip()
        if not token:
            cid = getattr(request.state, "correlation_id", None)
            return problem(
                status.HTTP_401_UNAUTHORIZED,
                "Unauthorized",
                "Empty bearer token",
                type_="urn:errors:auth:empty-bearer",
                cid=cid,
            )

        # валидация токена
        try:
            payload = decode_token(token)
        except Exception:
            cid = getattr(request.state, "correlation_id", None)
            return problem(
                status.HTTP_401_UNAUTHORIZED,
                "Unauthorized",
                "Invalid or expired token",
                type_="urn:errors:auth:invalid-token",
                cid=cid,
            )

        if payload.get("type") != "access":
            cid = getattr(request.state, "correlation_id", None)
            return problem(
                status.HTTP_401_UNAUTHORIZED,
                "Unauthorized",
                "Access token required",
                type_="urn:errors:auth:access-required",
                cid=cid,
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
            cid = getattr(request.state, "correlation_id", None)
            return problem(
                status.HTTP_401_UNAUTHORIZED,
                "Unauthorized",
                "Token revoked",
                type_="urn:errors:auth:revoked",
                cid=cid,
            )

        try:
            user_id = int(sub)
        except Exception:
            cid = getattr(request.state, "correlation_id", None)
            return problem(
                status.HTTP_401_UNAUTHORIZED,
                "Unauthorized",
                "Invalid token subject",
                type_="urn:errors:auth:invalid-subject",
                cid=cid,
            )

        # кладём компактного пользователя в state
        request.state.user = {"id": user_id, "role": role, "claims": payload}

        return await call_next(request)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.logger = logging.getLogger("app.request")

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        cid = getattr(request.state, "correlation_id", None)
        user = getattr(request.state, "user", None)
        user_id = user.get("id") if isinstance(user, dict) else None
        self.logger.info(
            "method=%s path=%s status=%s cid=%s user_id=%s",
            request.method,
            request.url.path,
            response.status_code,
            cid,
            user_id,
        )
        return response

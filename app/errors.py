import logging
import uuid
from typing import Any, Dict

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        cid = request.headers.get("X-Correlation-ID") or uuid.uuid4().hex
        request.state.correlation_id = cid
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = cid
        return response


def problem(
    status_code: int,
    title: str,
    detail: str,
    type_: str = "about:blank",
    extras: Dict[str, Any] | None = None,
    cid: str | None = None,
):
    payload = {
        "type": type_,
        "title": title,
        "status": status_code,
        "detail": detail,
        "correlation_id": cid,
    }
    if extras:
        payload.update(extras)
    headers = {"X-Correlation-ID": cid} if cid else None
    return JSONResponse(
        payload,
        status_code=status_code,
        media_type="application/problem+json",
        headers=headers,
    )


def http_exc_handler(request: Request, exc: HTTPException):
    cid = getattr(request.state, "correlation_id", None)
    title = {401: "Unauthorized", 403: "Forbidden"}.get(exc.status_code, "Error")
    # сохраняем исходный detail для совместимости с существующими контрактами
    detail = str(exc.detail)
    logging.getLogger("app.errors").warning(
        "http_exception status=%s title=%s cid=%s", exc.status_code, title, cid
    )
    return problem(exc.status_code, title, detail, type_="urn:errors:http", cid=cid)


def validation_exc_handler(request: Request, exc: RequestValidationError):
    cid = getattr(request.state, "correlation_id", None)
    extras = {"errors": exc.errors()}
    return problem(
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        "Unprocessable Entity",
        "Validation failed",
        type_="urn:errors:validation",
        extras=extras,
        cid=cid,
    )


def generic_exc_handler(request: Request, exc: Exception):
    cid = getattr(request.state, "correlation_id", None)
    logging.getLogger("app.errors").exception("unhandled_exception cid=%s", cid)
    return problem(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "Internal Server Error",
        "Internal server error",
        type_="urn:errors:internal",
        cid=cid,
    )

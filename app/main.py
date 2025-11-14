import logging

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.errors import (
    CorrelationIdMiddleware,
    generic_exc_handler,
    http_exc_handler,
    validation_exc_handler,
)
from app.middleware import AuthMiddleware, RequestLoggingMiddleware
from app.routers import admin as admin_router
from app.routers import auth as auth_router
from app.routers import entries as entries_router
from config import settings

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

app = FastAPI(title="Reading List API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# Middleware stack (executed in reverse order: last added = outermost)
app.add_middleware(
    AuthMiddleware,
    prefixes=[
        f"{entries_router.router.prefix}",
        f"{admin_router.router.prefix}",
        f"{auth_router.router.prefix}/me",
        f"{auth_router.router.prefix}/logout",
    ],
)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(CorrelationIdMiddleware)  # outermost: runs first
app.add_exception_handler(HTTPException, http_exc_handler)
app.add_exception_handler(RequestValidationError, validation_exc_handler)
app.add_exception_handler(Exception, generic_exc_handler)

app.include_router(auth_router.router)
app.include_router(entries_router.router)
app.include_router(admin_router.router)


@app.get("/health")
async def health_check():
    """Health check endpoint for container orchestration"""
    return {"status": "healthy", "service": "reading-list-api"}

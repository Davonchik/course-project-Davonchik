from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.middleware import AuthMiddleware
from app.routers import admin as admin_router
from app.routers import auth as auth_router
from app.routers import entries as entries_router

app = FastAPI(title="Reading List API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)


app.add_middleware(
    AuthMiddleware,
    prefixes=[
        f"{entries_router.router.prefix}",  # /api/v1/entries...
        f"{admin_router.router.prefix}",  # /api/v1/admin...
        f"{auth_router.router.prefix}/me",  # /api/v1/auth/me
        f"{auth_router.router.prefix}/logout",  # /api/v1/auth/logout
    ],
)

app.include_router(auth_router.router)
app.include_router(entries_router.router)
app.include_router(admin_router.router)

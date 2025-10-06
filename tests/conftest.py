# ruff: noqa: E402
import asyncio
import os
import sys
from typing import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from adapters import models
from adapters.db import Base, get_db_session
from adapters.security import hash_password
from app.main import app


# ------------------------
# anyio / loop
# ------------------------
@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ------------------------
# ENGINE
# ------------------------
@pytest.fixture(scope="session")
async def engine():
    url = "sqlite+aiosqlite:///:memory:?cache=shared"
    eng = create_async_engine(
        url,
        connect_args={"uri": True},
        poolclass=StaticPool,
        future=True,
    )
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    try:
        yield eng
    finally:
        await eng.dispose()


# ------------------------
# SESSION (nested tx)
# ------------------------
@pytest.fixture()
async def session(engine) -> AsyncGenerator[AsyncSession, None]:
    # Внешняя транзакция на каждый тест
    async with engine.connect() as conn:
        outer = await conn.begin()

        maker = async_sessionmaker(
            bind=conn, expire_on_commit=False, class_=AsyncSession
        )
        async with maker() as s:
            # ВАЖНО: nested именно от Session, чтобы SQLAlchemy сам вёл savepoint
            await s.begin_nested()

            @event.listens_for(s.sync_session, "after_transaction_end")
            def _restart_savepoint(sess, trans_):
                # Перезапускаем ТОЛЬКО когда завершилась nested-транзакция
                # и её родитель больше не активен
                if (
                    trans_.nested
                    and trans_._parent is not None
                    and not trans_._parent.is_active
                ):
                    # создаём новый savepoint снова через Session
                    sess.begin_nested()

            try:
                yield s
            finally:
                # Закрываем сессию (savepoint уже не «теряется»)
                await s.close()
                # Откатываем внешний транзакшен — чистая БД на следующий тест
                if outer.is_active:
                    await outer.rollback()


# ------------------------
# Override get_session
# ------------------------
@pytest.fixture(autouse=True)
def override_get_session(session: AsyncSession):
    async def _dep():
        # отдаём РОВНО тот же объект сессии, что в фикстуре
        yield session

    app.dependency_overrides[get_db_session] = _dep
    yield
    app.dependency_overrides.pop(get_db_session, None)


@pytest.fixture()
async def client(session):
    """
    HTTP-клиент с переопределённой зависимостью get_session,
    чтобы эндпоинты использовали ту же транзакцию, что и тест.
    """

    async def override_get_session():
        yield session

    app.dependency_overrides[get_db_session] = override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    app.dependency_overrides.pop(get_db_session, None)


# ------------------------
# Factories
# ------------------------
@pytest.fixture()
def user_factory():
    async def _create(
        session: AsyncSession,
        email: str,
        password: str = "secret",
        role: str = "user",
        is_active: bool = True,
    ):
        u = models.User(
            email=email,
            hashed_password=hash_password(password),
            role=role,
            is_active=is_active,
        )
        session.add(u)
        await session.commit()
        await session.refresh(u)
        return u

    return _create


@pytest.fixture()
def entry_factory():
    async def _create(
        session: AsyncSession,
        owner_id: int,
        title: str = "t",
        kind: str = "article",
        link: str | None = None,
        status: str = "planned",
    ):
        e = models.Entry(
            title=title,
            kind=kind,
            link=link,
            status=status,
            owner_id=owner_id,
        )
        session.add(e)
        await session.commit()
        await session.refresh(e)
        return e

    return _create

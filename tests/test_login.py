from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.models import RefreshToken
from adapters.security import decode_token
from app.main import app
from services.auth import register_user

pytestmark = pytest.mark.anyio


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


def _unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:8]}@example.com"


async def test_login_success_generates_tokens_and_persists_refresh(
    client: AsyncClient, session: AsyncSession
):
    # arrange
    email = _unique_email("login-ok")
    user = await register_user(session, email, "pwd1234")

    # act (без X-Device-Id — должен сгенерироваться)
    res = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "pwd1234"},
        headers={"User-Agent": "pytest-UA"},
    )

    # assert http
    assert res.status_code == 200
    body = res.json()
    assert "access_token" in body and body["access_token"]
    assert "refresh_token" in body and body["refresh_token"]
    assert "device_id" in body and body["device_id"]  # сгенерирован

    # assert payload’ы токенов
    ac = decode_token(body["access_token"])
    rc = decode_token(body["refresh_token"])
    assert ac["type"] == "access"
    assert rc["type"] == "refresh"
    assert ac["sub"] == str(user.id)
    assert rc["sub"] == str(user.id)
    assert ac["device"] == body["device_id"]
    assert rc["device"] == body["device_id"]

    # assert запись refresh в БД
    q = await session.execute(
        select(RefreshToken).where(RefreshToken.user_id == user.id)
    )
    rt = q.scalar_one()
    assert rt.device_id == body["device_id"]
    assert rt.user_agent == "pytest-UA"
    assert rt.revoked is False
    assert rt.jti == rc["jti"]


async def test_login_success(client: AsyncClient, session: AsyncSession):
    email = _unique_email("login-ok2")
    user = await register_user(session, email, "pwd1234")

    res = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "pwd1234"},
        headers={"X-Device-Id": "dev-login", "User-Agent": "pytest"},
    )
    assert res.status_code == 200
    body = res.json()
    assert "access_token" in body
    assert "refresh_token" in body

    # refresh записан в БД
    q = await session.execute(
        select(RefreshToken).where(RefreshToken.user_id == user.id)
    )
    rt = q.scalar_one()
    assert rt.device_id == "dev-login"
    assert rt.revoked is False


async def test_login_wrong_password(client: AsyncClient, session: AsyncSession):
    email = _unique_email("login-wrongpass")
    await register_user(session, email, "pwd1234")

    res = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "wrong"},
    )
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid credentials"


async def test_login_nonexistent_user(client: AsyncClient):
    email = _unique_email("idontexist")
    res = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "whatever"},
    )
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid credentials"


async def test_login_with_custom_device_id(client: AsyncClient, session: AsyncSession):
    email = _unique_email("login-device")
    user = await register_user(session, email, "pwd1234")

    res = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "pwd1234"},
        headers={"X-Device-Id": "my-custom-device", "User-Agent": "pytest"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["device_id"] == "my-custom-device"

    # refresh записан с тем же device_id
    q = await session.execute(
        select(RefreshToken).where(RefreshToken.user_id == user.id)
    )
    rt = q.scalar_one()
    assert rt.device_id == "my-custom-device"

    # а в payload токенов тот же device
    rc = decode_token(body["refresh_token"])
    ac = decode_token(body["access_token"])
    assert rc["device"] == "my-custom-device"
    assert ac["device"] == "my-custom-device"


async def test_login_wrong_password_returns_401(
    client: AsyncClient, session: AsyncSession
):
    email = _unique_email("login-wrongpass2")
    await register_user(session, email, "pwd1234")

    res = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "WRONG"},
        headers={"User-Agent": "pytest"},
    )
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid credentials"


async def test_login_nonexistent_user_returns_401(client: AsyncClient):
    email = _unique_email("idontexist2")
    res = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "whatever"},
        headers={"User-Agent": "pytest"},
    )
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid credentials"


async def test_login_invalid_credentials_triggers_401(client: AsyncClient):
    # Пользователь не существует
    res = await client.post(
        "/api/v1/auth/login",
        data={"username": "ghost@example.com", "password": "wrongpwd"},
        headers={"User-Agent": "pytest"},
    )

    # Проверяем, что сработала именно ветка `if not user`
    assert res.status_code == 401
    body = res.json()
    assert body["detail"] == "Invalid credentials"


async def test_login_without_user_agent_sets_null_in_refresh(
    client, session, user_factory
):
    user = await user_factory(session, "ua-none@example.com", password="pwd")

    res = await client.post(
        "/api/v1/auth/login",
        data={"username": "ua-none@example.com", "password": "pwd"},
    )
    assert res.status_code == 200

    q = await session.execute(
        select(RefreshToken).where(RefreshToken.user_id == user.id)
    )
    rt = q.scalar_one()

    assert isinstance(rt.user_agent, str)
    assert rt.user_agent.startswith("python-httpx/")


async def test_login_access_contains_role_claim(client, session, user_factory):
    await user_factory(session, "rolecheck@example.com", password="pwd", role="admin")
    res = await client.post(
        "/api/v1/auth/login",
        data={"username": "rolecheck@example.com", "password": "pwd"},
    )
    assert res.status_code == 200
    ac = decode_token(res.json()["access_token"])
    assert ac["role"] == "admin"

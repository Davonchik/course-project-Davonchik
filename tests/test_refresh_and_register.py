import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.models import RefreshToken, User
from adapters.security import create_access_token, create_refresh_payload, encode_token
from app.main import app
from services.tokens import create_refresh_record

pytestmark = pytest.mark.anyio


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def test_refresh_invalid_token(client: AsyncClient):
    res = await client.post("/api/v1/auth/refresh", json={"refresh_token": "broken"})
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid refresh token"


async def test_refresh_wrong_type_token(
    client: AsyncClient, session: AsyncSession, user_factory
):
    user = await user_factory(session, "refresh-wrong@example.com")
    bad_access = create_access_token(
        subject=str(user.id), role=user.role, device="dev1"
    )
    res = await client.post("/api/v1/auth/refresh", json={"refresh_token": bad_access})
    assert res.status_code == 400
    assert res.json()["detail"] == "Not a refresh token"


async def test_refresh_revoked_token(
    client: AsyncClient, session: AsyncSession, user_factory
):
    user = await user_factory(session, "refresh-revoked@example.com")
    payload = create_refresh_payload(subject=user.id, device="dev2")
    token = encode_token(payload)

    await create_refresh_record(
        session,
        user_id=user.id,
        jti=payload["jti"],
        exp_ts=payload["exp"],
        device_id="dev2",
        user_agent="pytest",
    )
    # делаем revoked
    q = await session.execute(
        select(RefreshToken).where(RefreshToken.jti == payload["jti"])
    )
    db_rt = q.scalar_one()
    db_rt.revoked = True
    await session.commit()

    res = await client.post("/api/v1/auth/refresh", json={"refresh_token": token})
    assert res.status_code == 401
    assert res.json()["detail"] == "Refresh token revoked"


async def test_refresh_user_inactive(
    client: AsyncClient, session: AsyncSession, user_factory
):
    user = await user_factory(session, "refresh2-inactive@example.com")
    user.is_active = False
    await session.commit()

    payload = create_refresh_payload(subject=user.id, device="dev3")
    token = encode_token(payload)

    await create_refresh_record(
        session,
        user_id=user.id,
        jti=payload["jti"],
        exp_ts=payload["exp"],
        device_id="dev3",
        user_agent="pytest",
    )

    res = await client.post("/api/v1/auth/refresh", json={"refresh_token": token})
    assert res.status_code == 401
    assert res.json()["detail"] == "User not found or inactive"


async def test_refresh_success(
    client: AsyncClient, session: AsyncSession, user_factory
):
    user = await user_factory(session, "refresh2-ok@example.com")
    payload = create_refresh_payload(subject=user.id, device="dev4")
    token = encode_token(payload)

    await create_refresh_record(
        session,
        user_id=user.id,
        jti=payload["jti"],
        exp_ts=payload["exp"],
        device_id="dev4",
        user_agent="pytest",
    )

    res = await client.post("/api/v1/auth/refresh", json={"refresh_token": token})
    assert res.status_code == 200
    body = res.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["device_id"] == "dev4"


async def test_register_success(client: AsyncClient, session: AsyncSession):
    res = await client.post(
        "/api/v1/auth/register",
        json={"email": "new2@example.com", "password": "pwd1234"},
    )
    assert res.status_code == 201
    body = res.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["device_id"] is not None

    q = await session.execute(select(User).where(User.email == "new2@example.com"))
    assert q.scalar_one() is not None


async def test_register_duplicate_email(client: AsyncClient):
    # первый раз
    await client.post(
        "/api/v1/auth/register",
        json={"email": "dupe@example.com", "password": "pwd1234"},
    )
    # второй раз
    res = await client.post(
        "/api/v1/auth/register",
        json={"email": "dupe@example.com", "password": "pwd1234"},
    )
    assert res.status_code == 409
    assert res.json()["detail"] == "Email already registered"

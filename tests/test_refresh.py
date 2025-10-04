import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.models import RefreshToken
from adapters.security import create_access_token, create_refresh_payload, encode_token
from app.main import app
from services.tokens import create_refresh_record

pytestmark = pytest.mark.anyio


@pytest.fixture
async def client():
    # используем ASGITransport вместо app=...
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def test_refresh_invalid_token(client: AsyncClient):
    res = await client.post("/api/v1/auth/refresh", json={"refresh_token": "notajwt"})
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid refresh token"


async def test_refresh_wrong_type_token(
    client: AsyncClient, session: AsyncSession, user_factory
):
    user = await user_factory(session, "wrongtype@example.com")
    # access-токен вместо refresh
    bad = create_access_token(subject=str(user.id), role=user.role, device="dev1")
    res = await client.post("/api/v1/auth/refresh", json={"refresh_token": bad})
    assert res.status_code == 400
    assert res.json()["detail"] == "Not a refresh token"


async def test_refresh_revoked_token(
    client: AsyncClient, session: AsyncSession, user_factory
):
    user = await user_factory(session, "revoked@example.com")
    payload = create_refresh_payload(subject=user.id, device="dev2")
    token = encode_token(payload)

    # сохраняем refresh как отозванный
    await create_refresh_record(
        session,
        user_id=user.id,
        jti=payload["jti"],
        exp_ts=payload["exp"],
        device_id="dev2",
        user_agent="pytest",
    )
    q = await session.execute(
        select(RefreshToken).where(RefreshToken.jti == payload["jti"])
    )
    db_rt = q.scalar_one()
    db_rt.revoked = True
    await session.commit()

    res = await client.post("/api/v1/auth/refresh", json={"refresh_token": token})
    assert res.status_code == 401
    assert res.json()["detail"] == "Refresh token revoked"

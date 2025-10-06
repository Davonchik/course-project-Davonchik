import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from adapters.models import RefreshToken, RevokedToken
from adapters.security import (
    create_access_token,
    create_refresh_payload,
    decode_token,
    encode_token,
)
from app.routers.auth import LogoutIn, logout
from services.tokens import create_refresh_record

pytestmark = pytest.mark.anyio


def _mk_request_with_headers(headers: dict[str, str]) -> Request:
    """Минимальный Starlette Request для вызова ручки напрямую."""
    asgi_headers = [(k.encode().lower(), v.encode()) for k, v in headers.items()]
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/auth/logout",
        "headers": asgi_headers,
    }
    return Request(scope)


async def test_logout_blacklists_access_and_refresh_and_revokes_device(
    session: AsyncSession,
    user_factory,
):
    user = await user_factory(session, "logout1@example.com")
    device_id = "dev-abc"

    # создаём access + refresh
    access = create_access_token(subject=str(user.id), role=user.role, device=device_id)
    rc = create_refresh_payload(subject=str(user.id), device=device_id)
    refresh = encode_token(rc)

    # кладём refresh в БД (как будто логин/регистрация)
    await create_refresh_record(
        session,
        user_id=user.id,
        jti=rc["jti"],
        exp_ts=rc["exp"],
        device_id=device_id,
        user_agent="pytest",
    )

    # Request с Authorization и state.user
    req = _mk_request_with_headers({"authorization": f"Bearer {access}"})
    req.state.user = {"id": user.id, "claims": {"role": "user"}}

    await logout(
        req, LogoutIn(device_id=device_id, refresh_token=refresh), session=session
    )

    # refresh для девайса отозван
    q1 = await session.execute(
        select(RefreshToken).where(RefreshToken.jti == rc["jti"])
    )
    assert q1.scalar_one().revoked is True

    # access в блэклисте
    ac_claims = decode_token(access)
    q2 = await session.execute(
        select(RevokedToken).where(
            RevokedToken.jti == ac_claims["jti"],
            RevokedToken.token_type == "access",
        )
    )
    assert q2.scalar_one_or_none() is not None

    # refresh тоже в блэклисте
    q3 = await session.execute(
        select(RevokedToken).where(
            RevokedToken.jti == rc["jti"],
            RevokedToken.token_type == "refresh",
        )
    )
    assert q3.scalar_one_or_none() is not None


async def test_logout_without_auth_header_only_revokes_refreshes_for_device(
    session: AsyncSession,
    user_factory,
):
    user = await user_factory(session, "logout2@example.com")
    device_id = "dev-noauth"

    rc = create_refresh_payload(subject=str(user.id), device=device_id)
    refresh = encode_token(rc)

    await create_refresh_record(
        session,
        user_id=user.id,
        jti=rc["jti"],
        exp_ts=rc["exp"],
        device_id=device_id,
        user_agent="pytest",
    )

    req = _mk_request_with_headers({})
    req.state.user = {"id": user.id, "claims": {"role": "user"}}

    await logout(
        req, LogoutIn(device_id=device_id, refresh_token=refresh), session=session
    )

    # refresh отозван
    q1 = await session.execute(
        select(RefreshToken).where(RefreshToken.jti == rc["jti"])
    )
    assert q1.scalar_one().revoked is True

    # access в блэклист не добавлен
    q2 = await session.execute(
        select(RevokedToken).where(RevokedToken.token_type == "access")
    )
    assert q2.scalar_one_or_none() is None


async def test_logout_with_invalid_access_token_is_ignored(
    session: AsyncSession, user_factory
):
    """Проверяем, что если access битый — код не падает (ветка except)."""
    user = await user_factory(session, "logout3@example.com")
    device_id = "dev-bad"

    # некорректный access
    bad_access = "not-a-jwt"

    req = _mk_request_with_headers({"authorization": f"Bearer {bad_access}"})
    req.state.user = {"id": user.id, "claims": {"role": "user"}}

    res = await logout(req, LogoutIn(device_id=device_id), session=session)
    assert res is None  # тихо завершилось


async def test_logout_with_invalid_refresh_token_is_ignored(
    session: AsyncSession, user_factory
):
    """Проверяем, что если refresh битый — код не падает (ветка except)."""
    user = await user_factory(session, "logout4@example.com")
    device_id = "dev-badrefresh"

    bad_refresh = "not-a-jwt"
    req = _mk_request_with_headers({})
    req.state.user = {"id": user.id, "claims": {"role": "user"}}

    res = await logout(
        req, LogoutIn(device_id=device_id, refresh_token=bad_refresh), session=session
    )
    assert res is None


async def test_logout_without_user_in_state_returns_gracefully(session: AsyncSession):
    """Если middleware не установила state.user → функция просто возвращает None."""
    req = _mk_request_with_headers({})
    res = await logout(req, LogoutIn(device_id="whatever"), session=session)
    assert res is None

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from services.tokens import (
    blacklist,
    create_refresh_record,
    is_jti_blacklisted,
    is_refresh_revoked,
    revoke_refresh_by_jti,
    revoke_refresh_for_device,
)

pytestmark = pytest.mark.anyio


def _ts(minutes: int) -> int:
    return int((datetime.now(timezone.utc) + timedelta(minutes=minutes)).timestamp())


async def test_refresh_lifecycle_by_jti(session: AsyncSession):
    jti = "jti-1"
    await create_refresh_record(
        session,
        user_id=1,
        jti=jti,
        exp_ts=_ts(30),
        device_id="devA",
        user_agent="UA",
    )
    assert (await is_refresh_revoked(session, jti)) is False
    await revoke_refresh_by_jti(session, jti)
    assert (await is_refresh_revoked(session, jti)) is True


async def test_refresh_revoke_for_device(session: AsyncSession):
    await create_refresh_record(
        session, user_id=1, jti="jti-a", exp_ts=_ts(30), device_id="X", user_agent=None
    )
    await create_refresh_record(
        session, user_id=1, jti="jti-b", exp_ts=_ts(30), device_id="X", user_agent=None
    )
    await create_refresh_record(
        session, user_id=1, jti="jti-c", exp_ts=_ts(30), device_id="Y", user_agent=None
    )

    # до отзыва
    assert (await is_refresh_revoked(session, "jti-a")) is False
    assert (await is_refresh_revoked(session, "jti-b")) is False
    assert (await is_refresh_revoked(session, "jti-c")) is False

    await revoke_refresh_for_device(session, user_id=1, device_id="X")

    # после отзыва только device X
    assert (await is_refresh_revoked(session, "jti-a")) is True
    assert (await is_refresh_revoked(session, "jti-b")) is True
    assert (await is_refresh_revoked(session, "jti-c")) is False


async def test_blacklist_access_and_check(session: AsyncSession):
    jti = "acc-jti-1"
    await blacklist(
        session,
        token_type="access",
        jti=jti,
        user_id=1,
        exp_ts=_ts(5),
    )
    assert await is_jti_blacklisted(session, jti) is True

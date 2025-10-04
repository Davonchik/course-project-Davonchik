from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.models import RefreshToken, RevokedToken


def _dt(ts: int) -> datetime:
    return datetime.fromtimestamp(ts, tz=timezone.utc)


async def create_refresh_record(
    session: AsyncSession,
    *,
    user_id: int,
    jti: str,
    exp_ts: int,
    device_id: str,
    user_agent: Optional[str],
) -> None:
    session.add(
        RefreshToken(
            user_id=user_id,
            jti=jti,
            device_id=device_id,
            user_agent=user_agent,
            expires_at=_dt(exp_ts),
        )
    )
    await session.commit()


async def revoke_refresh_by_jti(session: AsyncSession, jti: str) -> None:
    await session.execute(
        update(RefreshToken)
        .where(RefreshToken.jti == jti, RefreshToken.revoked.is_(False))
        .values(revoked=True)
    )
    await session.commit()


async def revoke_refresh_for_device(
    session: AsyncSession, user_id: int, device_id: str
) -> None:
    await session.execute(
        update(RefreshToken)
        .where(
            RefreshToken.user_id == user_id,
            RefreshToken.device_id == device_id,
            RefreshToken.revoked.is_(False),
        )
        .values(revoked=True)
    )
    await session.commit()


async def is_refresh_revoked(session: AsyncSession, jti: str) -> bool:
    q = await session.execute(select(RefreshToken).where(RefreshToken.jti == jti))
    r = q.scalar_one_or_none()
    return (r is None) or bool(r.revoked)


async def blacklist(
    session: AsyncSession,
    *,
    token_type: str,  # "access" | "refresh"
    jti: str,
    user_id: int,
    exp_ts: int,
) -> None:
    session.add(
        RevokedToken(
            user_id=user_id,
            jti=jti,
            token_type=token_type,
            expires_at=_dt(exp_ts),
        )
    )
    await session.commit()


async def is_jti_blacklisted(session: AsyncSession, jti: str) -> bool:
    q = await session.execute(select(RevokedToken).where(RevokedToken.jti == jti))
    return q.scalar_one_or_none() is not None

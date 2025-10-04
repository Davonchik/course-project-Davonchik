from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.models import User


async def list_users(
    session: AsyncSession,
    limit: int,
    offset: int,
    q: Optional[str] = None,
) -> Sequence[User]:
    stmt = select(User).order_by(User.id.asc()).limit(limit).offset(offset)
    if q:
        # простой ILIKE фильтр по email
        stmt = (
            select(User)
            .where(User.email.ilike(f"%{q}%"))
            .order_by(User.id.asc())
            .limit(limit)
            .offset(offset)
        )

    res = await session.execute(stmt)
    return res.scalars().all()

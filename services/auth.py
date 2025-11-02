from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.models import User
from adapters.security import hash_password, verify_password


async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
    res = await session.execute(select(User).where(User.email == email))
    return res.scalars().first()


async def register_user(
    session: AsyncSession, email: str, password: str, role: str = "user"
) -> User:
    existing = await get_user_by_email(session, email)
    if existing:
        raise ValueError("EMAIL_TAKEN")

    user = User(
        email=email, hashed_password=hash_password(password), role=role, is_active=True
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def authenticate_user(
    session: AsyncSession, email: str, password: str
) -> Optional[User]:
    user = await get_user_by_email(session, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        return None
    return user


async def list_users(
    session: AsyncSession, limit: int, offset: int, q: Optional[str] = None
) -> Sequence[User]:
    stmt = select(User).order_by(User.id.asc()).limit(limit).offset(offset)
    if q:
        stmt = (
            select(User)
            .where(User.email.ilike(f"%{q}%"))
            .order_by(User.id.asc())
            .limit(limit)
            .offset(offset)
        )

    res = await session.execute(stmt)
    return res.scalars().all()

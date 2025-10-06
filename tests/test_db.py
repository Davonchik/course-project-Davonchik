import pytest

from adapters import db


@pytest.mark.asyncio
async def test_get_db_session(engine):
    db.async_session_factory = db.async_sessionmaker(
        bind=engine,
        class_=db.AsyncSession,
        expire_on_commit=False,
    )

    async for session in db.get_db_session():
        assert session.is_active

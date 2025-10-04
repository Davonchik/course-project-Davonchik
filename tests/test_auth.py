import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from services.auth import (
    authenticate_user,
    get_user_by_email,
    list_users,
    register_user,
)

pytestmark = pytest.mark.anyio


async def test_register_user_ok(session: AsyncSession):
    user = await register_user(session, "a@example.com", "secret123")
    assert user.id > 0
    assert user.email == "a@example.com"
    assert user.role == "user"
    assert user.is_active is True


async def test_register_user_unique_email(session: AsyncSession):
    await register_user(session, "dupe@example.com", "secret123")
    with pytest.raises(ValueError) as e:
        await register_user(session, "dupe@example.com", "anothersecret")
    assert str(e.value) == "EMAIL_TAKEN"


async def test_authenticate_user_success(session: AsyncSession):
    await register_user(session, "ok@example.com", "pwd1234")
    user = await authenticate_user(session, "ok@example.com", "pwd1234")
    assert user is not None
    assert user.email == "ok@example.com"


async def test_authenticate_user_wrong_password(session: AsyncSession):
    await register_user(session, "wrong@example.com", "pwd1234")
    user = await authenticate_user(session, "wrong@example.com", "nope")
    assert user is None


async def test_authenticate_user_inactive(session: AsyncSession):
    u = await register_user(session, "inactive@example.com", "pwd1234")
    u.is_active = False
    await session.commit()
    got = await authenticate_user(session, "inactive@example.com", "pwd1234")
    assert got is None


async def test_get_user_by_email(session: AsyncSession):
    saved = await register_user(session, "findme@example.com", "pwd1234")
    got = await get_user_by_email(session, "findme@example.com")
    assert got and got.id == saved.id


async def test_authenticate_user_no_such_user(session: AsyncSession):
    user = await authenticate_user(session, "noone@example.com", "anypass")
    assert user is None


async def test_list_users_with_q_filters_case_insensitive(session: AsyncSession):
    await register_user(session, "alice@example.com", "pwd")
    await register_user(session, "bob@example.com", "pwd")
    await register_user(session, "carol@example.com", "pwd")

    res = await list_users(session, limit=100, offset=0, q="BO")
    emails = [u.email for u in res]
    assert emails == ["bob@example.com"]  # ожидаем только bob

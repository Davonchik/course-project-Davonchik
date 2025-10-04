import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from services.admin import list_users
from services.auth import register_user

pytestmark = pytest.mark.anyio


async def test_admin_list_users_basic(session: AsyncSession):
    await register_user(session, "aa@example.com", "secret123")
    await register_user(session, "bb@example.com", "secret123")
    users = await list_users(session, limit=10, offset=0, q=None)
    emails = [u.email for u in users]
    assert set(emails) >= {"aa@example.com", "bb@example.com"}


async def test_admin_list_users_search_by_email(session: AsyncSession):
    await register_user(session, "john@example.com", "secret123")
    await register_user(session, "jane@example.com", "secret123")
    await register_user(session, "mark@sample.com", "secret123")

    got = await list_users(session, limit=50, offset=0, q="examp")
    emails = {u.email for u in got}
    # должны вернуться только адреса содержащие "examp"
    assert "john@example.com" in emails
    assert "jane@example.com" in emails
    assert "mark@sample.com" not in emails

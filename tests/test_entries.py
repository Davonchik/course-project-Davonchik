import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from domain.schemas import EntryCreate, EntryKind, EntryStatus, EntryUpdate
from services.entries import (
    create_entry,
    delete_entry,
    get_entry_any,
    get_entry_for_owner,
    list_entries_admin,
    list_entries_user,
    update_entry,
)

pytestmark = pytest.mark.anyio


async def test_create_entry_casts_link_to_str(session: AsyncSession, user_factory):
    u = await user_factory(session, "e1@example.com")
    payload = EntryCreate(
        title="Algo",
        kind=EntryKind.article,
        link="https://example.com/x",
        status=EntryStatus.planned,
    )
    e = await create_entry(session, u.id, payload)
    assert e.id > 0
    assert e.title == "Algo"
    assert e.link == "https://example.com/x"


async def test_list_entries_user_returns_only_own(
    session: AsyncSession, user_factory, entry_factory
):
    u1 = await user_factory(session, "u1@example.com")
    u2 = await user_factory(session, "u2@example.com")

    await entry_factory(session, owner_id=u1.id, title="A1")
    await entry_factory(session, owner_id=u1.id, title="A2")
    await entry_factory(session, owner_id=u2.id, title="B1")

    items_u1 = await list_entries_user(session, u1.id, None, 100, 0)
    titles = {e.title for e in items_u1}
    assert titles == {"A1", "A2"}


async def test_admin_list_filters_by_owner(
    session: AsyncSession, user_factory, entry_factory
):
    u1 = await user_factory(session, "entries-a-1@example.com")
    u2 = await user_factory(session, "entries-b-1@example.com")
    await entry_factory(session, owner_id=u1.id, title="A1")
    await entry_factory(session, owner_id=u2.id, title="B1")

    all_items = await list_entries_admin(
        session, status=None, limit=100, offset=0, owner_id=None
    )
    assert {e.title for e in all_items} == {"A1", "B1"}

    only_u1 = await list_entries_admin(
        session, status=None, limit=100, offset=0, owner_id=u1.id
    )
    assert {e.title for e in only_u1} == {"A1"}


async def test_get_entry_owner_only(session: AsyncSession, user_factory, entry_factory):
    u1 = await user_factory(session, "o1@example.com")
    u2 = await user_factory(session, "o2@example.com")
    e1 = await entry_factory(session, owner_id=u1.id, title="Mine")
    await entry_factory(session, owner_id=u2.id, title="NotMine")

    ok = await get_entry_for_owner(session, u1.id, e1.id)
    deny = await get_entry_for_owner(session, u1.id, e1.id + 1)
    assert ok is not None
    assert deny is None


async def test_update_entry(session: AsyncSession, user_factory, entry_factory):
    u = await user_factory(session, "upd@example.com")
    e = await entry_factory(session, owner_id=u.id, title="Old", status="planned")

    patch = EntryUpdate(title="New", status=EntryStatus.in_progress)
    e2 = await update_entry(session, e, patch)
    assert e2.title == "New"
    assert e2.status == EntryStatus.in_progress


async def test_delete_entry(session: AsyncSession, user_factory, entry_factory):
    u = await user_factory(session, "del@example.com")
    e = await entry_factory(session, owner_id=u.id, title="X")
    await delete_entry(session, e)
    gone = await get_entry_any(session, e.id)
    assert gone is None


async def test_list_entries_user_with_status(session, user_factory, entry_factory):
    u = await user_factory(session, "status@example.com")
    await entry_factory(session, owner_id=u.id, title="T1", status="planned")
    await entry_factory(session, owner_id=u.id, title="T2", status="in_progress")

    items = await list_entries_user(session, u.id, status="planned", limit=10, offset=0)
    assert {e.status for e in items} == {"planned"}


async def test_update_entry_casts_link(session, user_factory, entry_factory):
    u = await user_factory(session, "link@example.com")
    e = await entry_factory(session, owner_id=u.id, title="T", link=None)

    patch = EntryUpdate(link="https://example.com/test")
    e2 = await update_entry(session, e, patch)
    assert isinstance(e2.link, str)
    assert e2.link.startswith("https://")


async def test_list_entries_admin_with_status(session: AsyncSession, user_factory):
    u = await user_factory(session, "adminstatus@example.com")

    await create_entry(
        session,
        u.id,
        EntryCreate(
            title="Planned", kind=EntryKind.article, status=EntryStatus.planned
        ),
    )
    await create_entry(
        session,
        u.id,
        EntryCreate(
            title="InProgress", kind=EntryKind.article, status=EntryStatus.in_progress
        ),
    )

    all_items = await list_entries_admin(session, status=None, limit=10, offset=0)
    titles_all = {e.title for e in all_items}
    assert {"Planned", "InProgress"} == titles_all

    planned_only = await list_entries_admin(
        session, status=EntryStatus.planned, limit=10, offset=0
    )
    titles_planned = {e.title for e in planned_only}
    assert titles_planned == {"Planned"}

    progress_only = await list_entries_admin(
        session, status=EntryStatus.in_progress, limit=10, offset=0
    )
    titles_progress = {e.title for e in progress_only}
    assert titles_progress == {"InProgress"}

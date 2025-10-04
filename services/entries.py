from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.models import Entry
from domain.schemas import EntryCreate, EntryStatus, EntryUpdate


async def create_entry(
    session: AsyncSession, owner_id: int, data: EntryCreate
) -> Entry:
    payload = data.model_dump()
    if payload.get("link") is not None:
        payload["link"] = str(payload["link"])
    obj = Entry(**payload, owner_id=owner_id)
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj


async def list_entries_user(
    session: AsyncSession,
    owner_id: int,
    status: Optional[EntryStatus],
    limit: int,
    offset: int,
) -> Sequence[Entry]:
    stmt = select(Entry).where(Entry.owner_id == owner_id)
    if status:
        stmt = stmt.where(Entry.status == status)
    stmt = stmt.order_by(Entry.id.desc()).limit(limit).offset(offset)
    res = await session.execute(stmt)
    return res.scalars().all()


async def list_entries_admin(
    session: AsyncSession,
    status: Optional[EntryStatus],
    limit: int,
    offset: int,
    owner_id: Optional[int] = None,
) -> Sequence[Entry]:
    stmt = select(Entry)
    if owner_id is not None:
        stmt = stmt.where(Entry.owner_id == owner_id)
    if status:
        stmt = stmt.where(Entry.status == status)
    stmt = stmt.order_by(Entry.id.desc()).limit(limit).offset(offset)
    res = await session.execute(stmt)
    return res.scalars().all()


async def get_entry_for_owner(
    session: AsyncSession, owner_id: int, entry_id: int
) -> Optional[Entry]:
    res = await session.execute(
        select(Entry).where(Entry.id == entry_id, Entry.owner_id == owner_id)
    )
    return res.scalars().first()


async def get_entry_any(session: AsyncSession, entry_id: int) -> Optional[Entry]:
    res = await session.execute(select(Entry).where(Entry.id == entry_id))
    return res.scalars().first()


async def update_entry(
    session: AsyncSession, entry: Entry, patch: EntryUpdate
) -> Entry:
    payload = patch.model_dump(exclude_unset=True)
    if payload.get("link") is not None:
        payload["link"] = str(payload["link"])
    for k, v in payload.items():
        setattr(entry, k, v)
    await session.commit()
    await session.refresh(entry)
    return entry


async def delete_entry(session: AsyncSession, entry: Entry) -> None:
    await session.delete(entry)
    await session.commit()

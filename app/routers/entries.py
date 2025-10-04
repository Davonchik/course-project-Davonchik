from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_session, oauth2_scheme
from domain.schemas import EntryCreate, EntryStatus, EntryUpdate
from services.entries import (
    create_entry,
    delete_entry,
    get_entry_any,
    get_entry_for_owner,
    list_entries_admin,
    list_entries_user,
    update_entry,
)

router = APIRouter(prefix="/api/v1/entries", tags=["entries"])


@router.post("", status_code=201)
async def create_entry_ep(
    req: Request,
    payload: EntryCreate,
    session: AsyncSession = Depends(get_session),
    _=Depends(oauth2_scheme),
):
    return await create_entry(session, req.state.user["id"], payload)


@router.get("")
async def list_entries_ep(
    req: Request,
    entry_status: Optional[EntryStatus] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    owner_id: Optional[int] = Query(None, description="Admin only: filter by owner_id"),
    session: AsyncSession = Depends(get_session),
    _=Depends(oauth2_scheme),
):
    print(req.state.user)
    if req.state.user["claims"]["role"] == "admin":
        items = await list_entries_admin(session, entry_status, limit, offset, owner_id)
    else:
        if owner_id is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can filter by owner_id",
            )
        items = await list_entries_user(
            session, req.state.user["id"], entry_status, limit, offset
        )
    return {"items": items, "limit": limit, "offset": offset, "count": len(items)}


@router.get("/{entry_id}")
async def get_entry_ep(
    req: Request,
    entry_id: int,
    session: AsyncSession = Depends(get_session),
    _=Depends(oauth2_scheme),
):
    if req.state.user["claims"]["role"] == "admin":
        item = await get_entry_any(session, entry_id)
    else:
        item = await get_entry_for_owner(session, req.state.user["id"], entry_id)

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found"
        )
    return item


@router.patch("/{entry_id}")
async def update_entry_ep(
    req: Request,
    entry_id: int,
    patch: EntryUpdate,
    session: AsyncSession = Depends(get_session),
    _=Depends(oauth2_scheme),
):
    if req.state.user["claims"]["role"] == "admin":
        item = await get_entry_any(session, entry_id)
    else:
        item = await get_entry_for_owner(session, req.state.user["id"], entry_id)

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found"
        )
    return await update_entry(session, item, patch)


@router.delete("/{entry_id}", status_code=204)
async def delete_entry_ep(
    req: Request,
    entry_id: int,
    session: AsyncSession = Depends(get_session),
    _=Depends(oauth2_scheme),
):
    if req.state.user["claims"]["role"] == "admin":
        item = await get_entry_any(session, entry_id)
    else:
        item = await get_entry_for_owner(session, req.state.user["id"], entry_id)

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found"
        )
    await delete_entry(session, item)
    return None

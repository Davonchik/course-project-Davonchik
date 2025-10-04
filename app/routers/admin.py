from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_session, oauth2_scheme
from domain.schemas import UserListItem
from services.admin import list_users

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.get("", response_model=list[UserListItem])
async def list_users_ep(
    req: Request,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    q: Optional[str] = Query(
        None, description="Search by email (substring, case-insensitive)"
    ),
    session: AsyncSession = Depends(get_session),
    _=Depends(oauth2_scheme),
) -> list[UserListItem]:
    if req.state.user["claims"]["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")

    users = await list_users(session, limit=limit, offset=offset, q=q)
    return users

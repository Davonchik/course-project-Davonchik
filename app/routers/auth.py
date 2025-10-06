from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.models import User
from adapters.security import (
    create_access_token,
    create_refresh_payload,
    decode_token,
    encode_token,
)
from app.deps import get_session, oauth2_scheme
from services.auth import authenticate_user, register_user
from services.tokens import (
    blacklist,
    create_refresh_record,
    is_refresh_revoked,
    revoke_refresh_by_jti,
    revoke_refresh_for_device,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    device_id: Optional[str] = None


class LoginIn(BaseModel):
    email: EmailStr
    password: str
    device_id: Optional[str] = None


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    device_id: str


class RefreshIn(BaseModel):
    refresh_token: str


class LogoutIn(BaseModel):
    device_id: str
    refresh_token: Optional[str] = None


def _device_id_or_new(device_id: Optional[str]) -> str:
    return device_id if device_id else uuid4().hex


@router.post("/refresh", response_model=TokenOut)
async def refresh_token(
    payload: RefreshIn,
    session: AsyncSession = Depends(get_session),
    user_agent: str | None = Header(default=None, alias="User-Agent"),
):
    try:
        claims = decode_token(payload.refresh_token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    if claims.get("type") != "refresh":
        raise HTTPException(status_code=400, detail="Not a refresh token")

    # проверка, что он не отозван/неподделан
    if await is_refresh_revoked(session, claims["jti"]):
        raise HTTPException(status_code=401, detail="Refresh token revoked")

    user_id = int(claims["sub"])
    device_id = claims.get("device")

    # гасим текущий refresh (ротация)
    await revoke_refresh_by_jti(session, claims["jti"])

    res = await session.execute(select(User).where(User.id == user_id))
    user = res.scalars().first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    access = create_access_token(subject=str(user.id), role=user.role, device=device_id)
    rc2 = create_refresh_payload(subject=str(user.id), device=device_id)
    new_refresh = encode_token(rc2)

    await create_refresh_record(
        session,
        user_id=user.id,
        jti=rc2["jti"],
        exp_ts=rc2["exp"],
        device_id=device_id,
        user_agent=user_agent,
    )

    return TokenOut(access_token=access, refresh_token=new_refresh, device_id=device_id)


@router.post("/register", response_model=TokenOut, status_code=201)
async def register(
    payload: RegisterIn,
    session: AsyncSession = Depends(get_session),
    user_agent: str | None = Header(default=None, alias="User-Agent"),
):
    try:
        user = await register_user(session, payload.email, payload.password)
    except ValueError as e:
        if str(e) == "EMAIL_TAKEN":
            raise HTTPException(status_code=409, detail="Email already registered")
        raise

    device_id = _device_id_or_new(payload.device_id)
    access = create_access_token(subject=str(user.id), role=user.role, device=device_id)
    rc = create_refresh_payload(subject=str(user.id), device=device_id)
    refresh = encode_token(rc)

    await create_refresh_record(
        session,
        user_id=user.id,
        jti=rc["jti"],
        exp_ts=rc["exp"],
        device_id=device_id,
        user_agent=user_agent,
    )

    return TokenOut(access_token=access, refresh_token=refresh, device_id=device_id)


@router.post("/login", response_model=TokenOut)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
    user_agent: str | None = Header(default=None, alias="User-Agent"),
    x_device_id: Optional[str] = Header(default=None, alias="X-Device-Id"),
):
    user = await authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    device_id = _device_id_or_new(x_device_id)
    access = create_access_token(subject=str(user.id), role=user.role, device=device_id)
    rc = create_refresh_payload(subject=str(user.id), device=device_id)
    refresh = encode_token(rc)

    await create_refresh_record(
        session,
        user_id=user.id,
        jti=rc["jti"],
        exp_ts=rc["exp"],
        device_id=device_id,
        user_agent=user_agent,
    )

    return TokenOut(access_token=access, refresh_token=refresh, device_id=device_id)


@router.get("/me")
async def me(
    req: Request,
    _=Depends(oauth2_scheme),
):
    return {"id": req.state.user["id"], "role": req.state.user["claims"]["role"]}


@router.post("/logout", status_code=204)
async def logout(
    req: Request,
    payload: LogoutIn,
    session: AsyncSession = Depends(get_session),
):
    # 1) положим текущий access в блэклист (если он от этого же device)
    auth = req.headers.get("Authorization")
    if auth and " " in auth:
        token = auth.split(" ", 1)[1].strip()
        try:
            ac = decode_token(token)
            if ac.get("type") == "access" and ac.get("device") == payload.device_id:
                await blacklist(
                    session,
                    token_type="access",
                    jti=ac["jti"],
                    user_id=int(ac["sub"]),
                    exp_ts=ac["exp"],
                )
        except Exception:
            pass

    # 2) отзываем ВСЕ refresh для этого девайса
    user_claims = getattr(req.state, "user", None)
    if not user_claims:
        # если мидлвара не сработала на этот роут — просто тихо завершим
        return None

    user_id = int(req.state.user["id"])
    await revoke_refresh_for_device(
        session, user_id=user_id, device_id=payload.device_id
    )

    if payload.refresh_token:
        try:
            rc = decode_token(payload.refresh_token)
            if (
                rc.get("type") == "refresh"
                and int(rc["sub"]) == user_id
                and rc.get("device") == payload.device_id
            ):
                await blacklist(
                    session,
                    token_type="refresh",
                    jti=rc["jti"],
                    user_id=user_id,
                    exp_ts=rc["exp"],
                )
        except Exception:
            pass

    return None

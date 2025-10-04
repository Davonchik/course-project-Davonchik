import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

pytestmark = pytest.mark.anyio


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def test_login_invalid_credentials(client: AsyncClient):
    # юзер есть, но пароль неправильный
    await client.post(
        "/api/v1/auth/register",
        json={"email": "badlogin@example.com", "password": "secret123"},
    )
    res = await client.post(
        "/api/v1/auth/login",
        data={"username": "badlogin@example.com", "password": "wrongpwd"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid credentials"


async def test_me_success(client: AsyncClient):
    # сначала зарегистрируем и залогинимся, чтобы получить токен
    await client.post(
        "/api/v1/auth/register", json={"email": "me@example.com", "password": "pwd1234"}
    )
    login = await client.post(
        "/api/v1/auth/login",
        data={"username": "me@example.com", "password": "pwd1234"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    access = login.json()["access_token"]

    res = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {access}"}
    )
    assert res.status_code == 200
    body = res.json()
    assert "id" in body
    assert "role" in body

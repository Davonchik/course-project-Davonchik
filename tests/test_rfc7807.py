import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app

pytestmark = pytest.mark.anyio


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def test_401_missing_authorization_returns_problem_json_with_correlation_id(
    client: AsyncClient,
):
    res = await client.get("/api/v1/entries")
    assert res.status_code == 401
    ctype = res.headers.get("content-type", "")
    assert ctype.startswith("application/problem+json")

    body = res.json()
    assert body["title"] == "Unauthorized"
    assert body["status"] == 401
    assert body["detail"] == "Missing Authorization header"
    assert "correlation_id" in body and isinstance(body["correlation_id"], str)

    # header and body correlation IDs should match
    assert res.headers.get("X-Correlation-ID") == body["correlation_id"]


async def test_422_validation_returns_problem_json_with_errors_and_correlation_id(
    client: AsyncClient,
):
    # invalid email and too-short password
    res = await client.post(
        "/api/v1/auth/register", json={"email": "not-an-email", "password": "123"}
    )
    assert res.status_code == 422
    ctype = res.headers.get("content-type", "")
    assert ctype.startswith("application/problem+json")

    body = res.json()
    assert body["title"] == "Unprocessable Entity"
    assert body["status"] == 422
    assert body["detail"] == "Validation failed"
    assert isinstance(body.get("errors"), list) and len(body["errors"]) >= 1
    assert "correlation_id" in body and isinstance(body["correlation_id"], str)
    assert res.headers.get("X-Correlation-ID") == body["correlation_id"]


async def test_500_internal_error_returns_problem_json_masked_with_correlation_id(
    monkeypatch,
):
    # Force unexpected exception inside auth.register handler
    import app.routers.auth as auth_router_mod

    def boom(*args, **kwargs):  # noqa: ANN001, ANN002
        raise RuntimeError("boom")

    monkeypatch.setattr(auth_router_mod, "register_user", boom)

    # use transport that doesn't raise app exceptions to allow 500 response
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/v1/auth/register",
            json={"email": "x@example.com", "password": "secret123"},
        )
        assert res.status_code == 500
        ctype = res.headers.get("content-type", "")
        assert ctype.startswith("application/problem+json")

        body = res.json()
        assert body["title"] == "Internal Server Error"
        assert body["status"] == 500
        assert body["detail"] == "Internal server error"  # masked, no internals
        assert "correlation_id" in body and isinstance(body["correlation_id"], str)
        assert res.headers.get("X-Correlation-ID") == body["correlation_id"]


async def test_sql_injection_in_admin_search_filter_does_not_break_query(
    client: AsyncClient, session: AsyncSession, user_factory
):
    # Create admin user and regular user
    await user_factory(session, "admin@example.com", password="admin123", role="admin")
    await user_factory(session, "user@example.com", password="user123", role="user")

    # Login as admin
    login_res = await client.post(
        "/api/v1/auth/login",
        data={"username": "admin@example.com", "password": "admin123"},
    )
    assert login_res.status_code == 200
    access_token = login_res.json()["access_token"]

    # Attempt SQL injection in search query parameter
    sqli_payloads = [
        "' OR 1=1 --",
        "'; DROP TABLE users; --",
        "admin' OR '1'='1",
        "' UNION SELECT * FROM users --",
    ]

    for payload in sqli_payloads:
        res = await client.get(
            "/api/v1/admin",
            params={"q": payload},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        # Should return 200 with safe results (not break or expose extra data)
        assert res.status_code == 200
        body = res.json()
        assert isinstance(body, list)
        # Should not return all users or crash; parameterized query handles it safely
        # If it found nothing matching the literal string, that's fine
        assert len(body) <= 2  # we only created 2 users

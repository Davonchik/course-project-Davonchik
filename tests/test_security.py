from adapters import security


def test_access_token_roundtrip():
    token = security.create_access_token(subject=1, role="user", device="dev")
    decoded = security.decode_token(token)
    assert decoded["sub"] == "1"
    assert decoded["role"] == "user"
    assert decoded["type"] == "access"


def test_refresh_token_payload():
    payload = security.create_refresh_payload(subject=1, device="dev")
    assert payload["type"] == "refresh"
    assert "jti" in payload

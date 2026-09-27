import pytest
from apps.api.app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)

def test_password_hashing():
    plain = "SuperSecret123!"
    hashed = get_password_hash(plain)
    assert hashed != plain
    assert verify_password(plain, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

def test_jwt_access_token_creation_and_decode():
    sub = "user-12345"
    workspace_id = "ws-98765"
    role = "admin"
    token = create_access_token(subject=sub, workspace_id=workspace_id, role=role)
    
    payload = decode_token(token)
    assert payload["sub"] == sub
    assert payload["workspace_id"] == workspace_id
    assert payload["role"] == role
    assert payload["type"] == "access"

def test_jwt_refresh_token_creation_and_decode():
    sub = "user-12345"
    token = create_refresh_token(subject=sub)
    payload = decode_token(token)
    assert payload["sub"] == sub
    assert payload["type"] == "refresh"

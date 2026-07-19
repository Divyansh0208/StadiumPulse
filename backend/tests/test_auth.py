"""Unit tests for password hashing and JWT token creation."""
from backend.orchestrator.app.auth import hash_password, verify_password, create_token
from backend.shared.config import get_settings
import jwt


def test_hash_and_verify_roundtrip():
    hashed = hash_password("correct-horse-battery-staple")
    assert verify_password("correct-horse-battery-staple", hashed)


def test_wrong_password_fails_verify():
    hashed = hash_password("correct-horse-battery-staple")
    assert not verify_password("wrong-password", hashed)


def test_hash_is_not_plaintext():
    hashed = hash_password("mypassword")
    assert hashed != "mypassword"
    assert hashed.startswith("$2b$")  # bcrypt prefix


def test_token_roundtrip():
    settings = get_settings()
    token = create_token("alice")
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    assert payload["sub"] == "alice"
    assert "exp" in payload

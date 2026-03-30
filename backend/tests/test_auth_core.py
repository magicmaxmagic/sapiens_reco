from app.core.auth import (
    create_access_token,
    decode_access_token,
    try_extract_auth_context,
    validate_admin_password_policy,
    validate_admin_credentials,
)


def test_create_and_decode_access_token_roundtrip():
    token, expires_in = create_access_token(subject="admin")

    assert isinstance(token, str)
    assert expires_in > 0

    payload = decode_access_token(token)
    assert payload["sub"] == "admin"
    assert payload["role"] == "admin"
    assert "exp" in payload
    assert "iat" in payload


def test_try_extract_auth_context_with_invalid_token_returns_none():
    context = try_extract_auth_context("Bearer not-a-valid-token")
    assert context is None


def test_validate_admin_credentials_with_test_defaults():
    assert validate_admin_credentials("admin", "TestAdmin#2026Secure") is True
    assert validate_admin_credentials("admin", "wrong") is False


def test_validate_admin_password_policy_accepts_complex_password():
    is_valid, violations = validate_admin_password_policy(
        "Complex#Pass2026",
        min_length=12,
    )

    assert is_valid is True
    assert violations == []


def test_validate_admin_password_policy_rejects_weak_password():
    is_valid, violations = validate_admin_password_policy(
        "weakpass",
        min_length=12,
    )

    assert is_valid is False
    assert "minimum_length<12" in violations
    assert "missing_uppercase" in violations
    assert "missing_digit" in violations
    assert "missing_special_char" in violations

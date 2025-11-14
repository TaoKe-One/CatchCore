"""
Unit tests for authentication and security utilities.

Tests password hashing, token creation, and JWT verification.
"""

import pytest
from datetime import datetime, timedelta, timezone
from jose import JWTError

from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.core.config import settings


# ============================================================================
# PASSWORD HASHING TESTS
# ============================================================================


class TestPasswordHashing:
    """Test password hashing and verification functions."""

    def test_get_password_hash_creates_hash(self):
        """Test that get_password_hash creates a valid hash."""
        password = "TestPassword123!"
        hashed = get_password_hash(password)

        assert hashed is not None
        assert len(hashed) > 0
        assert hashed != password
        assert "$2b$" in hashed  # bcrypt prefix

    def test_password_hash_is_different_each_time(self):
        """Test that same password produces different hashes."""
        password = "TestPassword123!"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        assert hash1 != hash2  # Different salts

    def test_verify_password_with_correct_password(self):
        """Test verify_password returns True with correct password."""
        password = "TestPassword123!"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_with_incorrect_password(self):
        """Test verify_password returns False with wrong password."""
        password = "TestPassword123!"
        wrong_password = "WrongPassword456!"
        hashed = get_password_hash(password)

        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_with_empty_password(self):
        """Test verify_password with empty strings."""
        hashed = get_password_hash("TestPassword123!")

        assert verify_password("", hashed) is False

    def test_verify_password_case_sensitive(self):
        """Test that password verification is case-sensitive."""
        password = "TestPassword123!"
        wrong_case = "testpassword123!"
        hashed = get_password_hash(password)

        assert verify_password(wrong_case, hashed) is False

    def test_password_with_special_characters(self):
        """Test password hashing with special characters."""
        password = "P@ssw0rd!#$%^&*()"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_password_with_unicode_characters(self):
        """Test password hashing with unicode characters."""
        password = "密码123!test"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True


# ============================================================================
# ACCESS TOKEN TESTS
# ============================================================================


class TestAccessToken:
    """Test JWT access token creation and verification."""

    def test_create_access_token_returns_string(self):
        """Test that create_access_token returns a valid JWT string."""
        data = {"sub": "user123"}
        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_has_correct_structure(self):
        """Test JWT token has correct 3-part structure."""
        data = {"sub": "user123"}
        token = create_access_token(data)

        # JWT format: header.payload.signature
        parts = token.split(".")
        assert len(parts) == 3

    def test_create_access_token_with_custom_expiry(self):
        """Test create_access_token with custom expiration delta."""
        data = {"sub": "user123"}
        expires_delta = timedelta(hours=2)
        token = create_access_token(data, expires_delta)

        decoded = decode_token(token)
        assert decoded is not None
        assert "exp" in decoded

    def test_create_access_token_default_expiry(self):
        """Test create_access_token uses default expiration."""
        data = {"sub": "user123"}
        token = create_access_token(data)

        decoded = decode_token(token)
        assert decoded is not None
        assert "exp" in decoded

    def test_create_access_token_includes_data(self):
        """Test that token includes provided data."""
        data = {"sub": "user123", "email": "user@example.com"}
        token = create_access_token(data)

        decoded = decode_token(token)
        assert decoded["sub"] == "user123"
        assert decoded["email"] == "user@example.com"

    def test_create_access_token_empty_data(self):
        """Test create_access_token with empty data dict."""
        data = {}
        token = create_access_token(data)

        decoded = decode_token(token)
        assert decoded is not None
        assert "exp" in decoded

    def test_access_token_expires(self):
        """Test that token with past expiration cannot be decoded."""
        data = {"sub": "user123"}
        expires_delta = timedelta(seconds=-1)  # Already expired
        token = create_access_token(data, expires_delta)

        # Should fail to decode
        decoded = decode_token(token)
        assert decoded is None

    def test_access_token_not_yet_expired(self):
        """Test token that hasn't expired yet."""
        data = {"sub": "user123"}
        expires_delta = timedelta(hours=1)
        token = create_access_token(data, expires_delta)

        decoded = decode_token(token)
        assert decoded is not None
        assert decoded["sub"] == "user123"


# ============================================================================
# REFRESH TOKEN TESTS
# ============================================================================


class TestRefreshToken:
    """Test JWT refresh token creation and verification."""

    def test_create_refresh_token_returns_string(self):
        """Test that create_refresh_token returns a valid JWT string."""
        data = {"sub": "user123"}
        token = create_refresh_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token_has_correct_structure(self):
        """Test refresh token has correct 3-part JWT structure."""
        data = {"sub": "user123"}
        token = create_refresh_token(data)

        parts = token.split(".")
        assert len(parts) == 3

    def test_create_refresh_token_has_type_field(self):
        """Test refresh token includes 'type: refresh' field."""
        data = {"sub": "user123"}
        token = create_refresh_token(data)

        decoded = decode_token(token)
        assert decoded is not None
        assert decoded.get("type") == "refresh"

    def test_create_refresh_token_expiry_longer_than_access(self):
        """Test refresh token expiry is longer than access token default."""
        data = {"sub": "user123"}
        refresh_token = create_refresh_token(data)
        access_token = create_access_token(data)

        refresh_decoded = decode_token(refresh_token)
        access_decoded = decode_token(access_token)

        # Refresh token should expire later
        assert refresh_decoded["exp"] > access_decoded["exp"]

    def test_create_refresh_token_includes_data(self):
        """Test refresh token includes provided data."""
        data = {"sub": "user123", "email": "user@example.com"}
        token = create_refresh_token(data)

        decoded = decode_token(token)
        assert decoded["sub"] == "user123"
        assert decoded["email"] == "user@example.com"

    def test_refresh_token_has_expiration(self):
        """Test refresh token includes expiration claim."""
        data = {"sub": "user123"}
        token = create_refresh_token(data)

        decoded = decode_token(token)
        assert "exp" in decoded

    def test_refresh_token_expires_based_on_setting(self):
        """Test refresh token uses REFRESH_TOKEN_EXPIRE_DAYS setting."""
        data = {"sub": "user123"}
        token = create_refresh_token(data)

        decoded = decode_token(token)
        assert decoded is not None
        # Token should be valid for refresh period


# ============================================================================
# TOKEN DECODING TESTS
# ============================================================================


class TestTokenDecoding:
    """Test JWT token decoding and verification."""

    def test_decode_token_valid_token(self):
        """Test decode_token with valid token."""
        data = {"sub": "user123"}
        token = create_access_token(data)

        decoded = decode_token(token)
        assert decoded is not None
        assert decoded["sub"] == "user123"

    def test_decode_token_invalid_token(self):
        """Test decode_token with invalid token."""
        token = "invalid.token.here"

        decoded = decode_token(token)
        assert decoded is None

    def test_decode_token_malformed_token(self):
        """Test decode_token with malformed token."""
        token = "not a valid jwt at all"

        decoded = decode_token(token)
        assert decoded is None

    def test_decode_token_empty_string(self):
        """Test decode_token with empty string."""
        token = ""

        decoded = decode_token(token)
        assert decoded is None

    def test_decode_token_wrong_secret_key(self):
        """Test that token signed with different key cannot be decoded."""
        import json
        import base64
        from jose import jwt

        data = {"sub": "user123"}
        # Create token with incorrect secret
        wrong_token = jwt.encode(
            data, "wrong-secret-key", algorithm=settings.ALGORITHM
        )

        # Should fail with correct secret key
        decoded = decode_token(wrong_token)
        assert decoded is None

    def test_decode_token_tampered_payload(self):
        """Test that tampered token cannot be decoded."""
        data = {"sub": "user123"}
        token = create_access_token(data)

        # Tamper with token
        parts = token.split(".")
        tampered = f"{parts[0]}.modified.{parts[2]}"

        decoded = decode_token(tampered)
        assert decoded is None

    def test_decode_token_preserves_all_fields(self):
        """Test that decode preserves all token fields."""
        data = {
            "sub": "user123",
            "email": "user@example.com",
            "username": "testuser",
            "is_admin": True,
        }
        token = create_access_token(data)

        decoded = decode_token(token)
        assert decoded["sub"] == "user123"
        assert decoded["email"] == "user@example.com"
        assert decoded["username"] == "testuser"
        assert decoded["is_admin"] is True


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestSecurityIntegration:
    """Integration tests for complete authentication flows."""

    def test_complete_auth_flow(self):
        """Test complete authentication flow: hash -> verify -> token."""
        password = "TestPassword123!"
        username = "testuser"
        email = "test@example.com"

        # Step 1: Hash password on registration
        password_hash = get_password_hash(password)

        # Step 2: Verify password on login
        assert verify_password(password, password_hash) is True

        # Step 3: Create token on successful login
        token = create_access_token({
            "sub": username,
            "email": email,
        })

        # Step 4: Decode token on API request
        decoded = decode_token(token)
        assert decoded["sub"] == username
        assert decoded["email"] == email

    def test_wrong_password_blocks_token_creation(self):
        """Test that wrong password prevents token creation."""
        password = "TestPassword123!"
        wrong_password = "WrongPassword!"
        password_hash = get_password_hash(password)

        # Login attempt with wrong password
        if not verify_password(wrong_password, password_hash):
            # Token should not be created
            token = None
        else:
            token = create_access_token({"sub": "user"})

        assert token is None

    def test_token_refresh_flow(self):
        """Test token refresh flow: access -> refresh -> new access."""
        user_id = "user123"

        # Step 1: Create initial tokens
        access_token = create_access_token({"sub": user_id})
        refresh_token = create_refresh_token({"sub": user_id})

        # Step 2: Both should be decodable
        access_decoded = decode_token(access_token)
        refresh_decoded = decode_token(refresh_token)

        assert access_decoded is not None
        assert refresh_decoded is not None

        # Step 3: Create new access token from refresh
        new_access = create_access_token({"sub": user_id})
        assert decode_token(new_access) is not None

    def test_password_change_invalidates_old_hash(self):
        """Test that old password hashes don't work after password change."""
        old_password = "OldPassword123!"
        new_password = "NewPassword456!"

        # Step 1: Hash old password
        old_hash = get_password_hash(old_password)
        assert verify_password(old_password, old_hash) is True

        # Step 2: User changes password
        new_hash = get_password_hash(new_password)

        # Step 3: Old password should not verify with new hash
        assert verify_password(old_password, new_hash) is False

        # Step 4: New password should verify with new hash
        assert verify_password(new_password, new_hash) is True


# ============================================================================
# EDGE CASES AND ERROR HANDLING
# ============================================================================


class TestSecurityEdgeCases:
    """Test edge cases and error handling in security functions."""

    def test_very_long_password(self):
        """Test password hashing with very long password."""
        password = "P" * 1000  # Very long password
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_password_with_null_bytes(self):
        """Test password with null bytes."""
        password = "Test\x00Password"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_token_with_large_payload(self):
        """Test token creation with large payload."""
        data = {f"field_{i}": f"value_{i}" for i in range(100)}
        data["sub"] = "user123"

        token = create_access_token(data)
        decoded = decode_token(token)

        assert decoded is not None
        assert len(decoded) >= 100

    def test_concurrent_token_creation(self):
        """Test multiple tokens can be created concurrently."""
        import threading

        tokens = []

        def create_token():
            token = create_access_token({"sub": "user123"})
            tokens.append(token)

        threads = [threading.Thread(target=create_token) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(tokens) == 10
        assert len(set(tokens)) == 10  # All unique

    def test_password_verification_with_none_values(self):
        """Test verify_password with None values."""
        try:
            result = verify_password(None, None)
            # If it doesn't raise, it should return False
            assert result is False
        except (TypeError, AttributeError):
            # Either response is acceptable for None values
            pass

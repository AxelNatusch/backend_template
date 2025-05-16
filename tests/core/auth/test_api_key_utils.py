"""
Tests for API key utilities.
"""

import base64
import re
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from uuid import UUID

import pytest
from fastapi import HTTPException

from src.core.auth.api_key_utils import (
    _create_api_key_with_metadata,
    _generate_api_key,
    _hash_api_key,
    _is_api_key_expired,
    _validate_api_key,
    _verify_api_key,
)
from src.core.config.settings import settings


@pytest.fixture
def api_key_data():
    """Fixture to generate a test API key with hash."""
    api_key, hashed_key = _generate_api_key()
    return {"api_key": api_key, "hashed_key": hashed_key}


class TestGenerateApiKey:
    """Tests for _generate_api_key function."""

    def test_returns_tuple(self):
        """Test that _generate_api_key returns a tuple of (api_key, hashed_key)."""
        result = _generate_api_key()

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], str)  # api_key
        assert isinstance(result[1], str)  # hashed_key

    def test_api_key_format(self):
        """Test that the generated API key has the correct format."""
        api_key, _ = _generate_api_key()

        # Check format - should be {prefix}_{base64_string}
        assert api_key.startswith(f"{settings.API_KEY_PREFIX}_")

        # Verify the part after prefix is valid base64-url
        key_parts = api_key.split("_", 1)
        assert len(key_parts) == 2

        # The pattern for URL-safe base64 without padding
        b64_pattern = r"^[A-Za-z0-9\-_]+$"
        assert re.match(b64_pattern, key_parts[1])

        # Try to decode it to confirm it's valid base64
        try:
            # Add padding if needed
            padding_needed = len(key_parts[1]) % 4
            if padding_needed:
                key_parts[1] += "=" * (4 - padding_needed)
            base64.urlsafe_b64decode(key_parts[1])
        except Exception as e:
            pytest.fail(f"API key contains invalid base64: {e}")

    def test_different_keys_each_time(self):
        """Test that each generated API key is unique."""
        api_key1, _ = _generate_api_key()
        api_key2, _ = _generate_api_key()
        api_key3, _ = _generate_api_key()

        assert api_key1 != api_key2
        assert api_key1 != api_key3
        assert api_key2 != api_key3

    def test_custom_prefix(self):
        """Test that a custom prefix can be used."""
        custom_prefix = "custom"
        api_key, _ = _generate_api_key(prefix=custom_prefix)

        assert api_key.startswith(f"{custom_prefix}_")

    def test_hashed_key_differs_from_raw_key(self):
        """Test that the hashed key is different from the raw key."""
        api_key, hashed_key = _generate_api_key()

        assert api_key != hashed_key
        # The hashed key should be a SHA-256 hex digest (64 characters)
        assert len(hashed_key) == 64
        assert all(c in "0123456789abcdef" for c in hashed_key)


class TestHashApiKey:
    """Tests for _hash_api_key function."""

    def test_consistent_hashing(self):
        """Test that the same API key always produces the same hash."""
        test_key = "test_12345abcdef"

        hash1 = _hash_api_key(test_key)
        hash2 = _hash_api_key(test_key)

        assert hash1 == hash2

    def test_different_keys_different_hashes(self):
        """Test that different API keys produce different hashes."""
        key1 = "test_key1"
        key2 = "test_key2"

        hash1 = _hash_api_key(key1)
        hash2 = _hash_api_key(key2)

        assert hash1 != hash2

    def test_hash_format(self):
        """Test that the hash has the expected format (SHA-256 hex digest)."""
        test_key = "test_api_key"
        hashed = _hash_api_key(test_key)

        # SHA-256 produces a 64-character hex string
        assert len(hashed) == 64
        assert all(c in "0123456789abcdef" for c in hashed)


class TestCreateApiKeyWithMetadata:
    """Tests for _create_api_key_with_metadata function."""

    def test_metadata_structure(self):
        """Test the structure of the generated API key metadata."""
        user_id = 123
        key_name = "Test API Key"

        result = _create_api_key_with_metadata(user_id, name=key_name)

        # Check required fields
        assert "id" in result
        assert "key" in result
        assert "key_hash" in result
        assert "user_id" in result
        assert "name" in result
        assert "created_at" in result
        assert "expires_at" in result
        assert "last_used_at" in result

        # Check values
        assert result["user_id"] == user_id
        assert result["name"] == key_name
        assert result["key"].startswith(f"{settings.API_KEY_PREFIX}_")
        assert result["last_used_at"] is None

        # Check ID format (should be a UUID)
        try:
            UUID(result["id"])
        except ValueError:
            pytest.fail("ID is not a valid UUID")

        # Created at should be a datetime
        assert isinstance(result["created_at"], datetime)

    def test_expiration_none_by_default(self):
        """Test that the API key has no expiration by default."""
        result = _create_api_key_with_metadata(123)

        assert result["expires_at"] is None

    def test_custom_expiration(self):
        """Test that a custom expiration time can be set."""
        expires_delta = timedelta(days=30)
        expected_expiry = datetime.now(timezone.utc) + expires_delta

        result = _create_api_key_with_metadata(123, expires_delta=expires_delta)

        assert result["expires_at"] is not None
        assert isinstance(result["expires_at"], datetime)

        # Check expiry is within a few seconds of expected
        time_diff = abs((result["expires_at"] - expected_expiry).total_seconds())
        assert time_diff < 2  # Should be less than 2 seconds difference

    def test_integer_type_user_id(self):
        """Test that user_id is properly handled as an integer."""
        user_id = 42

        result = _create_api_key_with_metadata(user_id)

        assert result["user_id"] == user_id
        assert isinstance(result["user_id"], int)


class TestVerifyApiKey:
    """Tests for _verify_api_key function."""

    def test_verify_valid_key(self, api_key_data):
        """Test that a valid API key verifies correctly."""
        api_key = api_key_data["api_key"]
        hashed_key = api_key_data["hashed_key"]

        result = _verify_api_key(api_key, hashed_key)

        assert result is True

    def test_verify_invalid_key(self, api_key_data):
        """Test that an invalid API key fails verification."""
        api_key = api_key_data["api_key"] + "invalid"
        hashed_key = api_key_data["hashed_key"]

        result = _verify_api_key(api_key, hashed_key)

        assert result is False

    def test_verify_with_wrong_hash(self, api_key_data):
        """Test verification with wrong hash fails."""
        api_key = api_key_data["api_key"]
        wrong_hash = "a" * 64  # Fake hash

        result = _verify_api_key(api_key, wrong_hash)

        assert result is False

    def test_verify_empty_strings(self):
        """Test verification with empty strings."""
        result = _verify_api_key("", "")

        assert result is False


class TestIsApiKeyExpired:
    """Tests for _is_api_key_expired function."""

    def test_expired_key(self):
        """Test that an expired key is detected correctly."""
        expired_time = datetime.now(timezone.utc) - timedelta(minutes=5)

        result = _is_api_key_expired(expired_time)

        assert result is True

    def test_valid_key(self):
        """Test that a non-expired key is detected correctly."""
        future_time = datetime.now(timezone.utc) + timedelta(days=1)

        result = _is_api_key_expired(future_time)

        assert result is False

    def test_none_expiry(self):
        """Test that None expiry is treated as non-expired."""
        result = _is_api_key_expired(None)

        assert result is False


class TestValidateApiKey:
    """Tests for _validate_api_key function."""

    def test_validate_valid_key(self, api_key_data):
        """Test validation of a valid API key."""
        api_key = api_key_data["api_key"]
        hashed_key = api_key_data["hashed_key"]

        result = _validate_api_key(api_key, hashed_key)

        assert result is True

    def test_validate_invalid_key(self, api_key_data):
        """Test validation of an invalid API key raises HTTPException."""
        api_key = api_key_data["api_key"] + "invalid"
        hashed_key = api_key_data["hashed_key"]

        with pytest.raises(HTTPException) as exc_info:
            _validate_api_key(api_key, hashed_key)

        assert exc_info.value.status_code == 401
        assert "Invalid API key" in exc_info.value.detail

    def test_validate_expired_key(self, api_key_data):
        """Test validation of an expired API key raises HTTPException."""
        api_key = api_key_data["api_key"]
        hashed_key = api_key_data["hashed_key"]
        expired_time = datetime.now(timezone.utc) - timedelta(minutes=5)

        with pytest.raises(HTTPException) as exc_info:
            _validate_api_key(api_key, hashed_key, expired_time)

        assert exc_info.value.status_code == 401
        assert "API key expired" in exc_info.value.detail

    def test_validate_future_expiry(self, api_key_data):
        """Test validation of a key with future expiry."""
        api_key = api_key_data["api_key"]
        hashed_key = api_key_data["hashed_key"]
        future_time = datetime.now(timezone.utc) + timedelta(days=1)

        result = _validate_api_key(api_key, hashed_key, future_time)

        assert result is True

    def test_validate_none_expiry(self, api_key_data):
        """Test validation of a key with None expiry."""
        api_key = api_key_data["api_key"]
        hashed_key = api_key_data["hashed_key"]

        result = _validate_api_key(api_key, hashed_key, None)

        assert result is True


# Integration tests for API key functions


def test_generate_and_verify_flow():
    """Test the full flow: generate key, hash it, and verify it."""
    # Generate key
    api_key, hashed_key = _generate_api_key()

    # Verify key
    is_valid = _verify_api_key(api_key, hashed_key)

    assert is_valid is True


def test_metadata_and_validate_flow():
    """Test creating a key with metadata and validating it."""
    # Create key with metadata
    metadata = _create_api_key_with_metadata(123)
    api_key = metadata["key"]
    hashed_key = metadata["key_hash"]

    # Validate key
    is_valid = _validate_api_key(api_key, hashed_key)

    assert is_valid is True


def test_expired_key_flow():
    """Test the full flow with an expired key."""
    # Use a mocked datetime to create a key that's already expired
    with patch("src.core.auth.api_key_utils.datetime") as mock_datetime:
        past_time = datetime.now(timezone.utc) - timedelta(hours=24)
        mock_datetime.now.return_value = past_time

        # Create key with short expiration
        metadata = _create_api_key_with_metadata(123, expires_delta=timedelta(minutes=30))

    # Now validate the key (should be expired)
    api_key = metadata["key"]
    hashed_key = metadata["key_hash"]
    expires_at = metadata["expires_at"]

    # Verify key is actually expired
    assert _is_api_key_expired(expires_at) is True

    # Validation should raise an exception
    with pytest.raises(HTTPException) as exc_info:
        _validate_api_key(api_key, hashed_key, expires_at)

    assert exc_info.value.status_code == 401
    assert "API key expired" in exc_info.value.detail

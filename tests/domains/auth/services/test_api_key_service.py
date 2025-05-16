import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from fastapi import HTTPException

from src.domains.auth.models.api_key import APIKey
from src.domains.auth.services.api_key_service import APIKeyService
from src.core.auth.api_key_utils import _hash_api_key, _is_api_key_expired


@pytest.fixture
def api_key_service(db_session):
    """Return an APIKeyService instance with a test database session."""
    return APIKeyService(db_session)


@pytest.fixture
def test_api_key_in_db(db_session):
    """Create and return a test API key in the database."""
    # Create an API key that's already in the database
    api_key = APIKey(
        key_hash=_hash_api_key("test_api_key_12345"),
        user_id=1,
        name="Test API Key",
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(api_key)
    db_session.commit()
    db_session.refresh(api_key)
    return api_key


@pytest.fixture
def expired_api_key_in_db(db_session):
    """Create and return an expired API key in the database."""
    api_key = APIKey(
        key_hash=_hash_api_key("expired_api_key_67890"),
        user_id=1,
        name="Expired API Key",
        expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        is_active=True,
        created_at=datetime.now(timezone.utc) - timedelta(days=31),
        updated_at=datetime.now(timezone.utc) - timedelta(days=31),
    )
    db_session.add(api_key)
    db_session.commit()
    db_session.refresh(api_key)
    return api_key


@pytest.fixture
def revoked_api_key_in_db(db_session):
    """Create and return a revoked (inactive) API key in the database."""
    api_key = APIKey(
        key_hash=_hash_api_key("revoked_api_key_54321"),
        user_id=1,
        name="Revoked API Key",
        expires_at=None,
        is_active=False,
        created_at=datetime.now(timezone.utc) - timedelta(days=15),
        updated_at=datetime.now(timezone.utc) - timedelta(days=5),
    )
    db_session.add(api_key)
    db_session.commit()
    db_session.refresh(api_key)
    return api_key


@pytest.fixture
def raw_test_api_key():
    """Return a raw API key string for testing."""
    return "test_api_key_12345"


class TestAPIKeyService:
    """Tests for the APIKeyService class."""

    @patch("src.domains.auth.services.api_key_service._generate_api_key")
    def test_create_api_key(self, mock_generate_api_key, api_key_service):
        """Test creating a new API key."""
        # Mock the _generate_api_key function to return a known value
        mock_generate_api_key.return_value = (
            "test_api_key_12345",
            "hashed_key_value",
        )

        # Call the service method
        result = api_key_service.create_api_key(user_id=1, name="Test Key", expires_in_days=30)

        # Check the result contains expected values
        assert result.key == "test_api_key_12345"
        assert result.name == "Test Key"
        assert result.user_id == 1
        assert result.id is not None
        assert result.created_at is not None
        assert result.expires_at is not None

        # Verify expires_at is about 30 days in the future (if it exists)
        if result.expires_at:
            # Make sure both datetimes have timezone info for comparison
            expires_at = result.expires_at
            if hasattr(expires_at, "tzinfo") and expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)

            now = datetime.now(timezone.utc)
            delta = expires_at - now
            assert 29 <= delta.days <= 30

    def test_get_user_api_keys(
        self,
        api_key_service,
        test_api_key_in_db,
        revoked_api_key_in_db,
        expired_api_key_in_db,
    ):
        """Test retrieving all active API keys for a user."""
        # Create another active key for a different user
        other_user_key = APIKey(
            key_hash=_hash_api_key("other_user_key"),
            user_id=2,
            name="Other User Key",
            is_active=True,
        )
        api_key_service.session.add(other_user_key)
        api_key_service.session.commit()

        # Get user 1's API keys
        keys = api_key_service.get_user_api_keys(1)

        # Should find all active keys for user 1 (including expired ones)
        assert len(keys) == 2  # Both test_api_key_in_db and expired_api_key_in_db should be returned

        # Verify the keys belong to user 1 and are active
        assert all(key.is_active for key in keys)

        # Check that the correct keys are included
        key_ids = [key.id for key in keys]
        assert test_api_key_in_db.id in key_ids
        assert expired_api_key_in_db.id in key_ids  # Expired key should be returned as it's still active
        assert revoked_api_key_in_db.id not in key_ids

        # Check that the other user's key is not included
        assert other_user_key.id not in key_ids

    def test_get_user_api_keys_filter_expired(self, api_key_service, test_api_key_in_db, expired_api_key_in_db):
        """Test filtering expired API keys if needed by application logic."""
        # This test demonstrates how to filter expired keys at the application level
        # Get user 1's API keys
        keys = api_key_service.get_user_api_keys(1)

        # Filter out expired keys manually (simulating what application code might do)
        unexpired_keys = [key for key in keys if not (key.expires_at and _is_api_key_expired(key.expires_at))]

        # Should only have the non-expired key
        assert len(unexpired_keys) == 1
        assert unexpired_keys[0].id == test_api_key_in_db.id

    def test_validate_api_key_valid(self, api_key_service, test_api_key_in_db):
        """Test validating a valid API key."""
        # Use the raw key that corresponds to the hashed key in the fixture
        raw_key = "test_api_key_12345"

        # Validate the key
        result = api_key_service.validate_api_key(raw_key)

        # Check the returned API key
        assert result.id == test_api_key_in_db.id
        assert result.user_id == test_api_key_in_db.user_id
        assert result.key_hash == test_api_key_in_db.key_hash

        # Verify last_used_at was updated
        assert result.last_used_at is not None

    def test_validate_api_key_invalid(self, api_key_service):
        """Test validating an invalid API key."""
        with pytest.raises(HTTPException) as excinfo:
            api_key_service.validate_api_key("invalid_key")

        assert excinfo.value.status_code == 401
        assert "Invalid API key" in excinfo.value.detail

    def test_validate_api_key_expired(self, api_key_service, expired_api_key_in_db):
        """Test validating an expired API key."""
        # Use the raw key that corresponds to the expired key in the fixture
        raw_key = "expired_api_key_67890"

        with pytest.raises(HTTPException) as excinfo:
            api_key_service.validate_api_key(raw_key)

        assert excinfo.value.status_code == 401
        assert "API key has expired" in excinfo.value.detail

    def test_validate_api_key_revoked(self, api_key_service, revoked_api_key_in_db):
        """Test validating a revoked API key."""
        # Use the raw key that corresponds to the revoked key in the fixture
        raw_key = "revoked_api_key_54321"

        with pytest.raises(HTTPException) as excinfo:
            api_key_service.validate_api_key(raw_key)

        assert excinfo.value.status_code == 401
        assert "API key has been revoked" in excinfo.value.detail

    def test_revoke_api_key(self, api_key_service, test_api_key_in_db, raw_test_api_key):
        """Test revoking a valid API key."""
        # Initially the key should be active
        assert test_api_key_in_db.is_active is True

        # Revoke the key
        result = api_key_service.revoke_api_key(raw_test_api_key, test_api_key_in_db.user_id)

        # Check the result
        assert result is True

        # Verify the key is now inactive
        api_key_service.session.refresh(test_api_key_in_db)
        assert test_api_key_in_db.is_active is False

    def test_revoke_api_key_not_found(self, api_key_service):
        """Test revoking a non-existent API key."""
        with pytest.raises(HTTPException) as excinfo:
            api_key_service.revoke_api_key("nonexistent_key", 1)

        assert excinfo.value.status_code == 404
        assert "API key not found" in excinfo.value.detail

    def test_revoke_api_key_unauthorized(self, api_key_service, test_api_key_in_db, raw_test_api_key):
        """Test revoking an API key with the wrong user ID."""
        wrong_user_id = test_api_key_in_db.user_id + 1

        with pytest.raises(HTTPException) as excinfo:
            api_key_service.revoke_api_key(raw_test_api_key, wrong_user_id)

        assert excinfo.value.status_code == 403
        assert "Not authorized to revoke this API key" in excinfo.value.detail

    def test_revoke_api_key_by_id(self, api_key_service, test_api_key_in_db):
        """Test revoking a valid API key by ID."""
        # Initially the key should be active
        assert test_api_key_in_db.is_active is True

        # Revoke the key
        result = api_key_service.revoke_api_key_by_id(test_api_key_in_db.id, test_api_key_in_db.user_id)

        # Check the result
        assert result is True

        # Verify the key is now inactive
        api_key_service.session.refresh(test_api_key_in_db)
        assert test_api_key_in_db.is_active is False

    def test_delete_api_key_by_id(self, api_key_service, test_api_key_in_db):
        """Test deleting an API key."""
        # Verify the key exists initially
        api_key_id = test_api_key_in_db.id
        assert api_key_service.repository.get_by_id(api_key_id) is not None

        # Delete the key
        result = api_key_service.delete_api_key_by_id(api_key_id, test_api_key_in_db.user_id)

        # Check the result
        assert result is True

        # Verify the key was deleted
        assert api_key_service.repository.get_by_id(api_key_id) is None

    def test_delete_api_key_by_id_not_found(self, api_key_service):
        """Test deleting a non-existent API key."""
        with pytest.raises(HTTPException) as excinfo:
            api_key_service.delete_api_key_by_id(999, 1)

        assert excinfo.value.status_code == 404
        assert "API key not found" in excinfo.value.detail

    def test_delete_api_key_by_id_unauthorized(self, api_key_service, test_api_key_in_db):
        """Test deleting an API key with the wrong user ID."""
        wrong_user_id = test_api_key_in_db.user_id + 1

        with pytest.raises(HTTPException) as excinfo:
            api_key_service.delete_api_key_by_id(test_api_key_in_db.id, wrong_user_id)

        assert excinfo.value.status_code == 403
        assert "Not authorized to delete this API key" in excinfo.value.detail

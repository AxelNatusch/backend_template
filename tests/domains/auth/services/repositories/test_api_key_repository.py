import pytest
from datetime import datetime, timedelta, timezone

from src.domains.auth.models.api_key import APIKey
from src.domains.auth.services.repositories.api_key_repository import (
    APIKeyRepository,
)


@pytest.fixture
def api_key_repository(db_session):
    """Return an APIKeyRepository instance with a test database session."""
    return APIKeyRepository(db_session)


@pytest.fixture
def sample_api_key_data():
    """Return sample API key data for testing."""
    return {
        "key_hash": "test_hash_12345",
        "user_id": 1,
        "name": "Test API Key",
        "expires_at": datetime.now(timezone.utc) + timedelta(days=30),
    }


@pytest.fixture
def create_test_api_key(db_session):
    """Create and return a test API key in the database."""
    api_key = APIKey(
        key_hash="test_hash_12345",
        user_id=1,
        name="Test API Key",
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        is_active=True,
    )
    db_session.add(api_key)
    db_session.commit()
    db_session.refresh(api_key)
    return api_key


@pytest.fixture
def create_test_api_keys_for_user(db_session):
    """Create multiple API keys for testing get_user_api_keys."""
    user_id = 1
    keys = [
        APIKey(
            key_hash="active_hash_1",
            user_id=user_id,
            name="Active Key 1",
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            is_active=True,
        ),
        APIKey(
            key_hash="active_hash_2",
            user_id=user_id,
            name="Active Key 2",
            is_active=True,  # No expiration
        ),
        APIKey(
            key_hash="inactive_hash",
            user_id=user_id,
            name="Inactive Key",
            is_active=False,
        ),
        APIKey(
            key_hash="other_user_hash",
            user_id=2,
            name="Other User Key",
            is_active=True,
        ),
    ]
    db_session.add_all(keys)
    db_session.commit()
    # Refresh keys to get IDs etc.
    refreshed_keys = []
    for key in keys:
        db_session.refresh(key)
        refreshed_keys.append(key)
    return refreshed_keys


class TestAPIKeyRepository:
    """Tests for the APIKeyRepository class."""

    def test_create_api_key(self, api_key_repository, sample_api_key_data):
        """Test creating a new API key."""
        api_key = api_key_repository.create(sample_api_key_data)

        assert api_key.id is not None
        assert api_key.key_hash == sample_api_key_data["key_hash"]
        assert api_key.user_id == sample_api_key_data["user_id"]
        assert api_key.name == sample_api_key_data["name"]

        # Convert both dates to the same format for comparison (remove timezone info)
        expected_date = sample_api_key_data["expires_at"].replace(tzinfo=None)
        actual_date = api_key.expires_at
        if hasattr(actual_date, "tzinfo") and actual_date.tzinfo is not None:
            actual_date = actual_date.replace(tzinfo=None)

        assert actual_date == expected_date
        assert api_key.is_active is True

    def test_get_by_key_hash(self, api_key_repository, create_test_api_key):
        """Test retrieving an API key by its hash."""
        api_key = api_key_repository.get_by_key_hash(create_test_api_key.key_hash)

        assert api_key is not None
        assert api_key.id == create_test_api_key.id
        assert api_key.key_hash == create_test_api_key.key_hash

    def test_get_by_key_hash_not_found(self, api_key_repository):
        """Test retrieving a non-existent API key by hash."""
        api_key = api_key_repository.get_by_key_hash("nonexistent_hash")

        assert api_key is None

    def test_get_by_id(self, api_key_repository, create_test_api_key):
        """Test retrieving an API key by its ID."""
        api_key = api_key_repository.get_by_id(create_test_api_key.id)

        assert api_key is not None
        assert api_key.id == create_test_api_key.id
        assert api_key.key_hash == create_test_api_key.key_hash

    def test_get_by_id_not_found(self, api_key_repository):
        """Test retrieving a non-existent API key by ID."""
        api_key = api_key_repository.get_by_id(999)

        assert api_key is None

    def test_get_user_api_keys(self, api_key_repository, create_test_api_keys_for_user):
        """Test retrieving all API keys for a user."""
        target_user_id = 1
        # Get all active keys for user ID 1
        user_keys = api_key_repository.get_user_api_keys(target_user_id)

        # Expecting the 2 active keys for user 1
        assert len(user_keys) == 2
        assert all(key.user_id == target_user_id for key in user_keys)
        assert all(key.is_active for key in user_keys)

        # Check the key hashes are correct
        key_hashes = {key.key_hash for key in user_keys}
        assert key_hashes == {"active_hash_1", "active_hash_2"}

        # Verify inactive and other user keys are not present
        assert "inactive_hash" not in key_hashes
        assert "other_user_hash" not in key_hashes

    def test_update_last_used(self, api_key_repository, create_test_api_key):
        """Test updating the last_used_at timestamp for an API key."""
        # Initially, last_used_at should be None
        assert create_test_api_key.last_used_at is None

        # Update last used timestamp
        api_key_repository.update_last_used(create_test_api_key.id)

        # Fetch the updated key
        updated_key = api_key_repository.get_by_id(create_test_api_key.id)

        # Check the timestamp was updated
        assert updated_key.last_used_at is not None
        # Don't compare timestamps directly as they might be the same in fast test runs

    def test_revoke(self, api_key_repository, create_test_api_key):
        """Test revoking (deactivating) an API key."""
        # Initially, the key should be active
        assert create_test_api_key.is_active is True

        # Revoke the key
        result = api_key_repository.revoke(create_test_api_key.id)

        # Check the result and the updated key
        assert result is True

        revoked_key = api_key_repository.get_by_id(create_test_api_key.id)
        assert revoked_key.is_active is False
        # Don't compare timestamps directly as they might be the same in fast test runs

    def test_revoke_nonexistent_key(self, api_key_repository):
        """Test revoking a non-existent API key."""
        result = api_key_repository.revoke(999)

        assert result is False

    def test_delete(self, api_key_repository, create_test_api_key):
        """Test deleting an API key."""
        # Verify the key exists initially
        assert api_key_repository.get_by_id(create_test_api_key.id) is not None

        # Delete the key
        result = api_key_repository.delete(create_test_api_key.id)

        # Check the result and that the key was deleted
        assert result is True
        assert api_key_repository.get_by_id(create_test_api_key.id) is None

    def test_delete_nonexistent_key(self, api_key_repository):
        """Test deleting a non-existent API key."""
        result = api_key_repository.delete(999)

        assert result is False

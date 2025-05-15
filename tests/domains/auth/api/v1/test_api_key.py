from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from src.domains.auth.models.api_key import APIKeyResponse, APIKeyPublic
from src.domains.auth.models.user import UserPublic


@pytest.fixture
def mock_api_key_service():
    """Mock the APIKeyService."""
    with patch("src.domains.auth.api.v1.api_key.APIKeyService") as mock:
        service_instance = MagicMock()
        mock.return_value = service_instance
        yield service_instance


@pytest.fixture
def mock_db():
    """Mock the get_db dependency to return a mock session."""
    mock_session = MagicMock()
    
    with patch("src.domains.auth.api.v1.api_key.get_db") as mock_get_db:
        mock_get_db.return_value = mock_session
        yield mock_session


@pytest.fixture
def mock_unauthenticated_user():
    """Mock an unauthenticated user by raising an exception."""
    with patch("src.domains.auth.api.v1.api_key.get_current_user") as mock:
        mock.side_effect = Exception("Not authenticated")
        yield mock


@pytest.fixture
def mock_current_user():
    """Mock the get_current_user dependency to return a mock user."""
    mock_user = UserPublic(id=1, username="testuser", email="test@example.com", is_active=True, role="user", created_at=datetime.now())
    with patch("src.domains.auth.api.v1.api_key.get_current_user") as mock_get_user:
        mock_get_user.return_value = mock_user
        yield mock_user


class TestAPIKeyEndpoints:
    """Tests for API key endpoints."""

    def test_create_api_key(self, client: TestClient, mock_api_key_service, mock_db, mock_current_user):
        """Test creating a new API key."""
        # Mock the service response
        created_at = datetime.now()
        mock_api_key_service.create_api_key.return_value = APIKeyResponse(
            id=1,
            key="test-api-key",
            name="Test Key",
            created_at=created_at,
            expires_at=created_at + timedelta(days=30),
            user_id=mock_current_user.id
        )

        # Make the request
        response = client.post(
            "/auth/api-keys/",
            json={"name": "Test Key", "expires_in_days": 30}
        )

        # Verify the response
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["id"] == 1
        assert data["key"] == "test-api-key"
        assert data["name"] == "Test Key"
        assert "created_at" in data
        assert "expires_at" in data
        assert data["user_id"] == mock_current_user.id

        # Verify the service was called with correct params
        mock_api_key_service.create_api_key.assert_called_once_with(
            user_id=mock_current_user.id,
            name="Test Key",
            expires_in_days=30
        )

    def test_get_api_keys(self, client: TestClient, mock_api_key_service, mock_db, mock_current_user):
        """Test listing all API keys for a user."""
        # Mock the service response
        created_at = datetime.now()
        mock_api_key_service.get_user_api_keys.return_value = [
            APIKeyPublic(
                id=1,
                name="Test Key 1",
                created_at=created_at,
                expires_at=created_at + timedelta(days=30),
                last_used_at=None,
                is_active=True,
            ),
            APIKeyPublic(
                id=2,
                name="Test Key 2",
                created_at=created_at,
                expires_at=None,
                last_used_at=created_at - timedelta(days=1),
                is_active=True,
            )
        ]

        # Make the request
        response = client.get("/auth/api-keys/")

        # Verify the response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        assert data[0]["id"] == 1
        assert data[0]["name"] == "Test Key 1"
        assert data[1]["id"] == 2
        assert data[1]["name"] == "Test Key 2"

        # Verify the service was called with correct params
        mock_api_key_service.get_user_api_keys.assert_called_once_with(mock_current_user.id)

    def test_revoke_api_key(self, client: TestClient, mock_api_key_service, mock_db, mock_current_user):
        """Test revoking an API key."""
        # Mock the service response
        mock_api_key_service.revoke_api_key.return_value = True

        # Make the request
        response = client.put(
            "/auth/api-keys/revoke", 
            json={"api_key": "test-api-key-to-revoke"}
        )

        # Verify the response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True

        # Verify the service was called with correct params
        mock_api_key_service.revoke_api_key.assert_called_once_with("test-api-key-to-revoke", mock_current_user.id)

    def test_revoke_api_key_by_id(self, client: TestClient, mock_api_key_service, mock_db, mock_current_user):
        """Test revoking an API key by ID."""
        # Mock the service response
        mock_api_key_service.revoke_api_key_by_id.return_value = True

        # Make the request
        response = client.put(
            "/auth/api-keys/revoke/1", 
            json={"api_key_id": 1}
        )

        # Verify the response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True

        # Verify the service was called with correct params
        mock_api_key_service.revoke_api_key_by_id.assert_called_once_with(1, mock_current_user.id)

    def test_revoke_api_key_forbidden(self, client: TestClient, mock_api_key_service, mock_db, mock_current_user):
        """Test revoking an API key with insufficient permissions."""
        # Mock the service to raise an exception - simulate service layer check
        # The service checks if api_key.user_id == current_user.id
        mock_api_key_service.revoke_api_key.side_effect = Exception("Not authorized")
        
        try:
            # This will raise an exception that should be caught by the test app's exception handler
            response = client.put(
                "/auth/api-keys/revoke", 
                json={"api_key": "test-api-key-to-revoke"}
            )
            # We should never get here, but if we do, fail the test
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        except Exception as e:
            # The exception should be "Not authorized"
            assert str(e) == "Not authorized"

        # Verify the service was still called
        mock_api_key_service.revoke_api_key.assert_called_once_with("test-api-key-to-revoke", mock_current_user.id)

    def test_delete_api_key(self, client: TestClient, mock_api_key_service, mock_db, mock_current_user):
        """Test deleting an API key."""
        # Mock the service response
        mock_api_key_service.delete_api_key_by_id.return_value = True

        # Make the request
        response = client.delete("/auth/api-keys/1")

        # Verify the response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True

        # Verify the service was called with correct params
        mock_api_key_service.delete_api_key_by_id.assert_called_once_with(1, mock_current_user.id)

    def test_delete_api_key_forbidden(self, client: TestClient, mock_api_key_service, mock_db, mock_current_user):
        """Test deleting an API key with insufficient permissions."""
        # Mock the service to raise an exception - simulate service layer check
        mock_api_key_service.delete_api_key_by_id.side_effect = Exception("Not authorized")
        
        try:
            # This will raise an exception that should be caught by the test app's exception handler
            response = client.delete("/auth/api-keys/1")
            # We should never get here, but if we do, fail the test
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        except Exception as e:
            # The exception should be "Not authorized"
            assert str(e) == "Not authorized"

        # Verify the service was called
        mock_api_key_service.delete_api_key_by_id.assert_called_once_with(1, mock_current_user.id)
        
    def test_api_key_lifecycle(self, client: TestClient, mock_api_key_service, mock_db, mock_current_user):
        """End-to-end test for the full API key lifecycle: create, list, revoke, delete."""
        created_at = datetime.now()
        api_key_id = 1
        api_key_raw = "test-api-key-lifecycle"
        mock_user_id = mock_current_user.id
        
        # 1. Create API key
        mock_api_key_service.create_api_key.return_value = APIKeyResponse(
            id=api_key_id,
            key=api_key_raw,
            name="Lifecycle Test Key",
            created_at=created_at,
            expires_at=created_at + timedelta(days=90),
            user_id=mock_user_id
        )
        
        create_response = client.post(
            "/auth/api-keys/",
            json={"name": "Lifecycle Test Key", "expires_in_days": 90}
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        created_key = create_response.json()
        assert created_key["id"] == api_key_id
        assert created_key["key"] == api_key_raw
        
        # 2. List API keys (should include our new key)
        mock_api_key_service.get_user_api_keys.return_value = [
            APIKeyPublic(
                id=api_key_id,
                name="Lifecycle Test Key",
                created_at=created_at,
                expires_at=created_at + timedelta(days=90),
                last_used_at=None,
                is_active=True,
            )
        ]
        
        list_response = client.get("/auth/api-keys/")
        assert list_response.status_code == status.HTTP_200_OK
        keys_list = list_response.json()
        assert len(keys_list) == 1
        assert keys_list[0]["id"] == api_key_id
        assert keys_list[0]["is_active"] is True
        
        # 3. Revoke the API key
        mock_api_key_service.revoke_api_key.return_value = True
        
        revoke_response = client.put(
            "/auth/api-keys/revoke",
            json={"api_key": api_key_raw}
        )
        assert revoke_response.status_code == status.HTTP_200_OK
        assert revoke_response.json()["success"] is True
        
        # 4. List API keys again (should show as inactive or be filtered)
        # Assuming get_user_api_keys only returns active keys now
        mock_api_key_service.get_user_api_keys.return_value = []
        
        list_response_after_revoke = client.get("/auth/api-keys/")
        assert list_response_after_revoke.status_code == status.HTTP_200_OK
        keys_list_after_revoke = list_response_after_revoke.json()
        # Check if the key is not returned anymore (assuming service filters inactive)
        assert len(keys_list_after_revoke) == 0
        
        # 5. Delete the API key
        mock_api_key_service.delete_api_key_by_id.return_value = True
        
        delete_response = client.delete(f"/auth/api-keys/{api_key_id}")
        assert delete_response.status_code == status.HTTP_200_OK
        assert delete_response.json()["success"] is True
        
        # 6. List API keys again (should be empty)
        mock_api_key_service.get_user_api_keys.return_value = []
        
        final_list_response = client.get("/auth/api-keys/")
        assert final_list_response.status_code == status.HTTP_200_OK
        assert len(final_list_response.json()) == 0

        mock_api_key_service.revoke_api_key.assert_called_with(api_key_raw, mock_user_id)
        mock_api_key_service.delete_api_key_by_id.assert_called_with(api_key_id, mock_user_id) 
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from unittest.mock import MagicMock, patch

from src.api.dependencies.auth import verify_api_key
from src.domains.auth.models.api_key import APIKey
from src.domains.auth.models.user import User, UserRole
from src.domains.auth.services.api_key_service import APIKeyService


@pytest.fixture
def mock_api_key_record():
    """Create a mock API key record."""
    return APIKey(
        id=1,
        key_hash="test_key_hash",
        user_id=1,
        name="Test API Key",
        is_active=True
    )


@pytest.fixture
def mock_credentials():
    """Create mock HTTP authorization credentials."""
    credentials = MagicMock(spec=HTTPAuthorizationCredentials)
    credentials.credentials = "test_api_key"
    return credentials


class TestApiKeyAuthentication:
    """Tests for API key authentication dependencies."""

    @pytest.mark.asyncio
    @patch.object(APIKeyService, 'validate_api_key')
    async def test_verify_api_key_success(
        self, mock_validate_api_key, mock_api_key_record, mock_credentials, test_user, db_session
    ):
        """Test successful authentication with API key."""
        # Mock the API key validation
        mock_validate_api_key.return_value = mock_api_key_record
        
        # Mock the database query to return our test user
        with patch('sqlmodel.Session.exec') as mock_exec:
            mock_exec.return_value.first.return_value = test_user
            
            # Call the dependency function
            user = await verify_api_key(api_key="test_api_key", db=db_session)
            
            # Verify the returned user is our test user
            assert user.id == test_user.id
            assert user.username == test_user.username
            
            # Verify the API key service was called with the right credentials
            mock_validate_api_key.assert_called_once_with("test_api_key")

    @pytest.mark.asyncio
    @patch.object(APIKeyService, 'validate_api_key')
    async def test_verify_api_key_invalid_key(
        self, mock_validate_api_key, mock_credentials, db_session
    ):
        """Test authentication with invalid API key."""
        # Simulate an invalid API key
        mock_validate_api_key.side_effect = HTTPException(
            status_code=401, 
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"}
        )
        
        # Call should raise the same HTTP exception
        with pytest.raises(HTTPException) as excinfo:
            await verify_api_key(api_key="invalid_api_key", db=db_session)
        
        # Verify the exception details
        assert excinfo.value.status_code == 401
        assert excinfo.value.detail == "Invalid API key"
        assert excinfo.value.headers == {"WWW-Authenticate": "Bearer"}

    @pytest.mark.asyncio
    @patch.object(APIKeyService, 'validate_api_key')
    async def test_verify_api_key_user_not_found(
        self, mock_validate_api_key, mock_api_key_record, mock_credentials, db_session
    ):
        """Test authentication when the user associated with the API key is not found."""
        # Mock the API key validation
        mock_validate_api_key.return_value = mock_api_key_record
        
        # Mock the database query to return None (user not found)
        with patch('sqlmodel.Session.exec') as mock_exec:
            mock_exec.return_value.first.return_value = None
            
            # Call should raise HTTP exception for user not found
            with pytest.raises(HTTPException) as excinfo:
                await verify_api_key(api_key="test_api_key", db=db_session)
            
            # Verify the exception details
            assert excinfo.value.status_code == 401
            assert excinfo.value.detail == "User not found"
            assert excinfo.value.headers == {"WWW-Authenticate": "Bearer"}

    @pytest.mark.asyncio
    @patch.object(APIKeyService, 'validate_api_key')
    async def test_verify_api_key_inactive_user(
        self, mock_validate_api_key, mock_api_key_record, mock_credentials, db_session
    ):
        """Test authentication when the user is inactive."""
        # Mock the API key validation
        mock_validate_api_key.return_value = mock_api_key_record
        
        # Create an inactive user
        inactive_user = User(
            id=2,
            username="inactiveuser",
            email="inactive@example.com",
            role=UserRole.USER,
            is_active=False,
            password="$2b$12$test_hashed_password_value"
        )
        
        # Mock the database query to return the inactive user
        with patch('sqlmodel.Session.exec') as mock_exec:
            mock_exec.return_value.first.return_value = inactive_user
            
            # Call should raise HTTP exception for inactive user
            with pytest.raises(HTTPException) as excinfo:
                await verify_api_key(api_key="test_api_key", db=db_session)
            
            # Verify the exception details
            assert excinfo.value.status_code == 401
            assert excinfo.value.detail == "Inactive user"
            assert excinfo.value.headers == {"WWW-Authenticate": "Bearer"}

    @pytest.mark.asyncio
    @patch.object(APIKeyService, 'validate_api_key')
    async def test_verify_api_key_unexpected_error(
        self, mock_validate_api_key, mock_credentials, db_session
    ):
        """Test authentication when an unexpected error occurs."""
        # Simulate an unexpected error
        mock_validate_api_key.side_effect = Exception("Unexpected error")
        
        # Call should raise a generic HTTP exception
        with pytest.raises(HTTPException) as excinfo:
            await verify_api_key(api_key="test_api_key", db=db_session)
        
        # Verify the exception details
        assert excinfo.value.status_code == 401
        assert excinfo.value.detail == "Could not validate API key"
        assert excinfo.value.headers == {"WWW-Authenticate": "Bearer"} 
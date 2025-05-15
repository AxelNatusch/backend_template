import pytest
from fastapi import FastAPI, Depends, APIRouter, status
from fastapi.testclient import TestClient

from src.api.dependencies.auth import verify_api_key
from src.core.db.session import get_db
from src.domains.auth.models.user import User
from src.domains.auth.services.api_key_service import APIKeyService


# Create a test router with an endpoint protected by API key authentication
router = APIRouter()

@router.get("/protected-by-api-key")
def protected_endpoint(current_user: User = Depends(verify_api_key)):
    return {"message": "You accessed this with an API key!", "user_id": current_user.id}


@pytest.fixture
def api_key_app(db_session, test_user):
    """Create a test app with API key authentication."""
    # Create a test app
    app = FastAPI()
    
    # Override the get_db dependency for this app
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Add our test router
    app.include_router(router)
    
    return app


@pytest.fixture
def api_key_client(api_key_app, monkeypatch):
    """Create a test client with API key authentication."""
    return TestClient(api_key_app)


class TestApiKeyIntegration:
    """Integration tests for API key authentication."""
    
    def test_endpoint_with_valid_api_key(self, api_key_client, test_user, monkeypatch):
        """Test accessing an endpoint with a valid API key."""
        # Mock the APIKeyService.validate_api_key method
        def mock_validate_api_key(*args, **kwargs):
            from src.domains.auth.models.api_key import APIKey
            return APIKey(
                id=1,
                key_hash="test_key_hash",
                user_id=test_user.id,
                name="Test API Key",
                is_active=True
            )
        
        # Apply the mock
        monkeypatch.setattr(
            APIKeyService, 
            "validate_api_key", 
            mock_validate_api_key
        )
        
        # Mock the SQLModel.exec method to return our test user
        def mock_exec(*args, **kwargs):
            class MockResult:
                def first(self):
                    return test_user
            return MockResult()
        
        # Apply the mock
        monkeypatch.setattr(
            "sqlmodel.Session.exec", 
            mock_exec
        )
        
        # Make the request with a test API key
        response = api_key_client.get(
            "/protected-by-api-key",
            headers={"api-key": "test_api_key"}
        )
        
        # Verify the response
        assert response.status_code == 200
        assert response.json() == {
            "message": "You accessed this with an API key!",
            "user_id": test_user.id
        }
    
    def test_endpoint_with_invalid_api_key(self, api_key_client, monkeypatch):
        """Test accessing an endpoint with an invalid API key."""
        # Mock the APIKeyService.validate_api_key method to raise an exception
        def mock_validate_api_key(*args, **kwargs):
            from fastapi import HTTPException
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Apply the mock
        monkeypatch.setattr(
            APIKeyService, 
            "validate_api_key", 
            mock_validate_api_key
        )
        
        # Make the request with an invalid API key
        response = api_key_client.get(
            "/protected-by-api-key",
            headers={"api-key": "invalid_api_key"}
        )
        
        # Verify the response
        assert response.status_code == 401
        assert response.json() == {"detail": "Invalid API key"}
    
    def test_endpoint_without_api_key(self, api_key_client):
        """Test accessing an endpoint without an API key."""
        # Make the request without an API key
        response = api_key_client.get("/protected-by-api-key")
        
        # Verify the response - should get a 422 Unprocessable Entity
        assert response.status_code == 422
        assert "detail" in response.json() 
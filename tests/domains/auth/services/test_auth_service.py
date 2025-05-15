"""
Tests for AuthService.
"""

import pytest
from fastapi import HTTPException

from src.domains.auth.models.user import UserCreate
from src.domains.auth.services.auth_service import AuthService
from src.domains.auth.services.repositories.user_repository import UserRepository


@pytest.fixture
def auth_service(db_session):
    """Create an AuthService instance for testing."""
    return AuthService(db_session)


@pytest.fixture
def user_repository(db_session):
    """Create a UserRepository instance for testing."""
    return UserRepository(db_session)


@pytest.fixture
def test_user(user_repository):
    """Create a test user for auth tests."""
    user_data = UserCreate(
        username="testuser",
        email="test@example.com",
        password="Password123!",
    )
    return user_repository.create(user_data)


def test_register_success(auth_service):
    """Test successful user registration."""
    user_data = UserCreate(
        username="newuser",
        email="new@example.com",
        password="Password123!",
    )

    result = auth_service.register(user_data)

    # Check user data
    assert result.username == "newuser"
    assert result.email == "new@example.com"
    assert result.is_active is True
    
    # Check it's a UserPublic model
    assert hasattr(result, "id")
    assert hasattr(result, "created_at")
    assert hasattr(result, "role")


def test_register_duplicate_email(auth_service, test_user):
    """Test registration with duplicate email."""
    user_data = UserCreate(
        username="anotheruser",
        email="test@example.com",  # Same as test_user
        password="Password123!",
    )

    with pytest.raises(HTTPException) as excinfo:
        auth_service.register(user_data)

    assert excinfo.value.status_code == 400
    assert "Email already registered" in excinfo.value.detail


def test_login_success(auth_service, test_user):
    """Test successful login."""
    result = auth_service.login("testuser", "Password123!")

    # Check user data
    assert result.user.username == "testuser"
    assert result.user.email == "test@example.com"

    # Check tokens
    assert result.access_token is not None
    assert result.refresh_token is not None


def test_login_invalid_email(auth_service):
    """Test login with invalid email."""
    with pytest.raises(HTTPException) as excinfo:
        auth_service.login("nonexistent@example.com", "Password123!")

    assert excinfo.value.status_code == 401
    assert "Invalid credentials" in excinfo.value.detail


def test_login_invalid_password(auth_service, test_user):
    """Test login with invalid password."""
    with pytest.raises(HTTPException) as excinfo:
        auth_service.login("test@example.com", "WrongPassword123!")

    assert excinfo.value.status_code == 401
    assert "Invalid credentials" in excinfo.value.detail

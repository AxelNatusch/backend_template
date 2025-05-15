"""
Tests for User model.
"""

import pytest
from pydantic import ValidationError

from src.domains.auth.models.user import UserCreate, UserRole, UserUpdate


def test_user_create_validation():
    """Test UserCreate validation rules."""
    # Valid user
    valid_user = UserCreate(
        username="testuser",
        email="test@example.com",
        password="Password123!",
    )
    assert valid_user.username == "testuser"
    assert valid_user.email == "test@example.com"
    assert valid_user.password == "Password123!"

    # Empty username
    with pytest.raises(ValidationError):
        UserCreate(
            username="",
            email="test@example.com",
            password="Password123!",
        )


def test_user_update_validation():
    """Test UserUpdate validation rules."""
    # Valid update with all fields
    valid_update = UserUpdate(
        username="updateduser",
        email="updated@example.com",
        password="NewPassword123!",
        is_active=False,
        role=UserRole.ADMIN,
    )
    assert valid_update.username == "updateduser"
    assert valid_update.email == "updated@example.com"
    assert valid_update.password == "NewPassword123!"
    assert valid_update.is_active is False
    assert valid_update.role == UserRole.ADMIN

    # Valid update with partial fields
    partial_update = UserUpdate(username="newname")
    assert partial_update.username == "newname"
    assert partial_update.email is None
    assert partial_update.password is None
    assert partial_update.is_active is None
    assert partial_update.role is None

    # Invalid email
    with pytest.raises(ValidationError):
        UserUpdate(email="not-an-email")

    # Invalid role
    with pytest.raises(ValidationError):
        UserUpdate(role="superuser")  # Not in UserRole enum

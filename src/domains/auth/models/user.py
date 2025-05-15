"""
User domain models and schemas.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import (
    BaseModel,
    Field as PydanticField,
    EmailStr,
    field_validator,
)
from sqlmodel import Field, SQLModel


class UserRole(str, Enum):
    """User role enumeration."""

    USER = "user"
    ADMIN = "admin"


def current_time():
    """Get current time in UTC."""
    return datetime.now(timezone.utc)


class User(SQLModel, table=True):
    """
    User database model.
    """

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field()
    email: str = Field(unique=True, index=True)
    password: str = Field(nullable=False)
    is_active: bool = Field(default=True)
    role: UserRole = Field(default=UserRole.USER)
    created_at: datetime = Field(default_factory=current_time)
    updated_at: datetime = Field(default_factory=current_time)

    def update(self, user_data: dict):
        """Update user fields."""
        for key, value in user_data.items():
            if key != "id" and hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = current_time()


class UserBase(BaseModel):
    """
    Base model with common user fields and validators.
    """

    username: str = PydanticField(..., description="Username for display purposes")
    email: EmailStr = PydanticField(..., description="Email address for login")
    role: UserRole = PydanticField(default=UserRole.USER, description="User role")

    @field_validator("username")
    @classmethod
    def username_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Username must not be empty")
        return v


class UserCreate(UserBase):
    """
    Schema for creating a new user.
    """

    password: str = PydanticField(..., description="User password (will be hashed)")

    @field_validator("password")
    @classmethod
    def password_valid(cls, v):
        if len(v) < 3:
            raise ValueError("Password must be at least 3 characters long")
        # Check for mix of uppercase, lowercase, and numbers
        # has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        # has_digit = any(c.isdigit() for c in v)
        # has_special = any(not c.isalnum() for c in v)

        if not (has_lower):
            raise ValueError("Password must include uppercase, lowercase, and numbers")

        # if not has_special:
        #     raise ValueError("Password must include at least one special character")

        return v


class UserUpdate(BaseModel):
    """
    Schema for updating an existing user.
    """

    username: Optional[str] = PydanticField(
        None, description="Username for display purposes"
    )
    email: Optional[EmailStr] = PydanticField(
        None, description="Email address for login"
    )
    password: Optional[str] = PydanticField(
        None, description="User password (will be hashed)"
    )
    is_active: Optional[bool] = PydanticField(
        None, description="Whether the user is active"
    )
    role: Optional[UserRole] = PydanticField(None, description="User role")


class UserPublic(UserBase):
    """
    Schema for returning user data.
    """

    id: int = PydanticField(..., description="User ID")
    is_active: bool = PydanticField(..., description="Whether the user is active")
    created_at: datetime = PydanticField(
        ..., description="Timestamp of account creation"
    )

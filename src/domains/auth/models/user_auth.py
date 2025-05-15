"""
Authentication schemas for token handling and responses.
"""

from typing import Optional

from pydantic import BaseModel, EmailStr

from src.domains.auth.models.user import UserRole, UserPublic


class Token(BaseModel):
    """JWT access token model."""

    access_token: str
    refresh_token: Optional[str] = None


class TokenPayload(BaseModel):
    """JWT token payload."""

    sub: str  # User ID
    exp: int  # Expiration timestamp
    username: str
    email: str
    role: UserRole


class LoginRequest(BaseModel):
    """Login request body."""

    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    """Refresh token request body."""

    refresh_token: str


class LoginResponse(BaseModel):
    """Login response body."""

    user: UserPublic
    access_token: str
    refresh_token: Optional[str] = None

"""
JWT token utilities for authentication.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt
from fastapi import HTTPException, status

from src.core.config.settings import settings
from src.domains.auth.models.user import UserRole


def create_access_token(
    user_id: int,
    username: str,
    email: str,
    role: UserRole,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Generate a new JWT access token.

    Args:
        user_id: User identifier
        username: User's display name
        email: User's email
        role: User's role
        expires_delta: Optional expiration override

    Returns:
        JWT token string
    """
    expires = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta
        else timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    to_encode = {
        "sub": str(user_id),
        "exp": expires.timestamp(),
        "username": username,
        "email": email,
        "role": role,
    }

    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(
    user_id: int, expires_delta: Optional[timedelta] = None
) -> str:
    """
    Generate a new refresh token.

    Args:
        user_id: User identifier
        expires_delta: Optional expiration override

    Returns:
        JWT refresh token string
    """
    # Default to 7 days for refresh tokens
    expires = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    )

    to_encode = {
        "sub": str(user_id),
        "exp": expires.timestamp(),
        "token_type": "refresh",
    }

    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode a JWT token without verification.

    Args:
        token: JWT token to decode

    Returns:
        Decoded token payload
    """
    try:
        return jwt.decode(token, options={"verify_signature": False})
    except jwt.PyJWTError:
        return {}


def verify_token(token: str) -> Dict[str, Any]:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token to verify

    Returns:
        Decoded and verified token payload

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

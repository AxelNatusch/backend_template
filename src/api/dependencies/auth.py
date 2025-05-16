"""
Authentication dependencies for FastAPI.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, Security, status, Header
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
    OAuth2PasswordBearer,
)
from sqlmodel import Session, select

from src.core.auth.jwt import verify_token
from src.core.db import get_db
from src.domains.auth.models.user import User, UserRole
from src.domains.auth.services.api_key_service import APIKeyService

# Use OAuth2PasswordBearer for consistency with FastAPI docs
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/login", auto_error=False)

# HTTPBearer for JWT token
security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Security(security)],
    db: Session = Depends(get_db),
) -> User:
    """
    Get current authenticated user based on JWT token.

    Args:
        credentials: HTTP Bearer token
        db: Database session

    Returns:
        Current authenticated user

    Raises:
        HTTPException: If token is invalid or user not found
    """
    try:
        payload = verify_token(credentials.credentials)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.exec(select(User).where(User.id == user_id)).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def verify_api_key(
    api_key: Annotated[str, Header(...)],
    db: Session = Depends(get_db),
) -> User:
    """
    Get current authenticated user based on API key.

    Args:
        api_key: API key from header
        db: Database session

    Returns:
        Current authenticated user

    Raises:
        HTTPException: If API key is invalid or user not found
    """
    api_key_service = APIKeyService(db)

    try:
        # Validate the API key and get the associated API key record
        api_key_record = api_key_service.validate_api_key(api_key)

        # Get the user associated with the API key
        user = db.exec(select(User).where(User.id == api_key_record.user_id)).first()

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive user",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user

    except HTTPException:
        # Re-raise HTTPExceptions from the validate_api_key method
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate API key",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_admin_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Get current user and verify they have admin role.

    Args:
        current_user: Current authenticated user

    Returns:
        Current authenticated user if admin

    Raises:
        HTTPException: If user is not an admin
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user

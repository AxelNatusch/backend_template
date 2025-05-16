"""
Authentication API endpoints.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, status, HTTPException, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

from src.api.dependencies.auth import (
    get_current_admin_user,
    get_current_user,
    verify_api_key,
)
from src.core.db import get_db
from src.domains.auth.models.user import User, UserCreate, UserPublic
from src.domains.auth.models.user_auth import (
    LoginResponse,
    Token,
    RefreshTokenRequest,
)
from src.domains.auth.services.auth_service import AuthService

router = APIRouter(tags=["auth"])
logger = logging.getLogger(__name__)


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: Annotated[UserCreate, Query(...)],
    current_user: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Register a new user."""
    auth_service = AuthService(db)
    try:
        return auth_service.register(user_data)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception(f"Unexpected error during user registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during registration.",
        )


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
):
    """Authenticate user and return access/refresh tokens."""
    auth_service = AuthService(db)
    login_response = auth_service.login(form_data.username, form_data.password)
    if not login_response:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return login_response


@router.post("/refresh", response_model=Token)
async def refresh_access_token(
    request_data: Annotated[RefreshTokenRequest, Query(...)],
    db: Session = Depends(get_db),
):
    """Refresh access token using a refresh token."""
    auth_service = AuthService(db)
    return await auth_service.refresh_token(request_data.refresh_token)


@router.get("/me", response_model=UserPublic)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get current authenticated user's details."""
    return current_user


@router.get("/me-api-key", response_model=UserPublic)
async def read_users_me_api_key(
    current_user: Annotated[User, Depends(verify_api_key)],
):
    """Get current authenticated user's details using API key."""
    return current_user

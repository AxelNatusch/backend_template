"""
Authentication service for login/register operations.
"""

from fastapi import HTTPException, status
from sqlmodel import Session

from src.core.auth.jwt import (
    create_access_token,
    create_refresh_token,
    verify_token,
)
from src.core.auth.password import verify_password
from src.domains.auth.models.user import UserCreate, UserPublic
from src.domains.auth.models.user_auth import LoginResponse, Token
from src.domains.auth.services.user_service import UserService

import logging

logger = logging.getLogger(__name__)


class AuthService:
    """
    Service for authentication operations.
    """

    def __init__(self, session: Session):
        self.session = session
        self.user_service = UserService(session)

    def register(self, user_data: UserCreate) -> UserPublic:
        """
        Register a new user.

        Args:
            user_data: User registration data

        Returns:
            User data
        """
        logger.info(f"Attempting to register user with username: {user_data.username} and email: {user_data.email}")
        # Create user
        user = self.user_service.create_user(user_data)
        logger.info(f"Successfully created user with ID: {user.id}, Username: {user.username}")

        user_public = UserPublic(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            created_at=user.created_at,
            is_active=user.is_active,
        )
        return user_public

    def login(self, username: str, password: str) -> LoginResponse:
        """
        Authenticate a user.

        Args:
            username: User username
            password: User password

        Returns:
            User data with access token

        Raises:
            HTTPException: If credentials are invalid
        """
        logger.info(f"Login attempt for username: {username}")
        # Get user by email
        user = self.user_service.get_user_by_username(username)
        if not user:
            logger.warning(f"Login failed: User not found for username: {username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verify password
        if not verify_password(password, user.password):
            logger.warning(f"Login failed: Invalid password for username: {username} (User ID: {user.id})")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Generate tokens
        logger.info(f"Login successful for username: {username} (User ID: {user.id}). Generating tokens.")
        access_token = create_access_token(
            user_id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
        )

        refresh_token = create_refresh_token(user_id=user.id)

        # Return login response
        logger.info(f"Tokens generated successfully for user ID: {user.id}")
        return LoginResponse(
            user=UserPublic(
                id=user.id,
                username=user.username,
                email=user.email,
                role=user.role,
                created_at=user.created_at,
                is_active=user.is_active,
            ),
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def refresh_token(self, refresh_token_str: str) -> Token:
        """
        Verify a refresh token and issue new access and refresh tokens.

        Args:
            refresh_token_str: The refresh token string.

        Returns:
            A Token object containing the new access and refresh tokens.

        Raises:
            HTTPException: If the refresh token is invalid, expired,
                           malformed, or the user is not found/inactive.
        """
        logger.info("Attempting to refresh token.")
        try:
            payload = verify_token(refresh_token_str)
            logger.debug(f"Refresh token payload verified: {payload}")

            # Verify token type
            token_type = payload.get("token_type")
            if token_type != "refresh":
                logger.warning(f"Refresh token failed: Invalid token type '{token_type}'. Expected 'refresh'.")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            user_id = payload.get("sub")
            if not user_id:
                logger.warning("Refresh token failed: 'sub' (user ID) not found in token payload.")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            logger.info(f"Fetching user with ID: {user_id} for token refresh.")
            user = self.user_service.get_user(user_id)

            if not user:
                logger.warning(f"Refresh token failed: User not found for ID: {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            if not user.is_active:
                logger.warning(f"Refresh token failed: User ID {user_id} is inactive.")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Inactive user",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Issue new tokens (implementing rotation)
            logger.info(f"Issuing new tokens for user ID: {user_id}")
            new_access_token = create_access_token(
                user_id=user.id,
                username=user.username,
                email=user.email,
                role=user.role,
            )
            new_refresh_token = create_refresh_token(user_id=user.id)

            logger.info(f"Token refresh successful for user ID: {user.id}")
            return Token(
                access_token=new_access_token,
                refresh_token=new_refresh_token,
                token_type="bearer",
            )

        except HTTPException as http_exc:
            logger.warning(
                f"HTTPException during token refresh: {http_exc.detail} (Status Code: {http_exc.status_code})"
            )
            raise http_exc
        except Exception as e:
            logger.exception(f"Unexpected error during token refresh: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )

"""
User service for business logic related to users.
"""

from typing import Optional

from fastapi import HTTPException, status
from sqlmodel import Session

from src.domains.auth.models.user import User, UserCreate, UserUpdate
from src.domains.auth.services.repositories.user_repository import UserRepository

import logging

logger = logging.getLogger(__name__)

class UserService:
    """
    Service for user-related business logic.
    """

    def __init__(self, session: Session):
        self.repository = UserRepository(session)

    def create_user(self, user_data: UserCreate) -> User:
        """
        Create a new user.
        Raises HTTPException if email already exists.

        Args:
            user_data: User creation data

        Returns:
            Created user

        Raises:
            HTTPException: If email already registered
        """
        logger.info(f"Attempting to create user with email: {user_data.email} and username: {user_data.username}")
        # Check if email already exists
        existing_user_email = self.repository.get_by_email(user_data.email)
        if existing_user_email:
            logger.warning(f"Failed to create user. Email {user_data.email} already registered.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        existing_user_username = self.repository.get_by_username(user_data.username)
        if existing_user_username:
            logger.warning(f"Failed to create user. Username {user_data.username} already registered.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered",
            )
        # Create user
        created_user = self.repository.create(user_data)
        logger.info(f"Successfully created user with ID: {created_user.id}")
        return created_user

    def get_user(self, user_id: int) -> User:
        """
        Get a user by ID.
        Raises HTTPException if user not found.

        Args:
            user_id: User ID

        Returns:
            User

        Raises:
            HTTPException: If user not found
        """
        logger.info(f"Attempting to retrieve user with ID: {user_id}")
        user = self.repository.get_by_id(user_id)
        if not user:
            logger.warning(f"User with ID {user_id} not found.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found",
            )
        logger.info(f"Successfully retrieved user with ID: {user_id}")
        return user

    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get a user by email.

        Args:
            email: User email

        Returns:
            User if found, None otherwise
        """
        logger.info(f"Attempting to retrieve user by email: {email}")
        user = self.repository.get_by_email(email)
        if user:
            logger.info(f"Found user with email: {email}, ID: {user.id}")
        else:
            logger.info(f"No user found with email: {email}")
        return user


    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Get a user by username.
        """
        logger.info(f"Attempting to retrieve user by username: {username}")
        user = self.repository.get_by_username(username)
        if user:
            logger.info(f"Found user with username: {username}, ID: {user.id}")
        else:
            logger.info(f"No user found with username: {username}")
        return user

    def update_user(self, user_id: int, user_data: UserUpdate) -> User:
        """
        Update a user.
        Raises HTTPException if user not found or email conflicts.

        Args:
            user_id: User ID
            user_data: User update data

        Returns:
            Updated user

        Raises:
            HTTPException: If user not found or email already registered by another user
        """
        logger.info(f"Attempting to update user with ID: {user_id}")
        # If email is being updated, check if it already exists for another user
        if user_data.email:
            logger.info(f"Checking if email {user_data.email} is already registered for another user.")
            existing_user = self.repository.get_by_email(user_data.email)
            if existing_user and existing_user.id != user_id:
                logger.warning(f"Failed to update user {user_id}. Email {user_data.email} already registered by user {existing_user.id}.")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered",
                )

        # Update user
        updated_user = self.repository.update(user_id, user_data)
        if not updated_user:
            logger.warning(f"Failed to update user. User with ID {user_id} not found.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found",
            )

        logger.info(f"Successfully updated user with ID: {user_id}")
        return updated_user

    def delete_user(self, user_id: int) -> None:
        """
        Delete a user.
        Raises HTTPException if user not found.

        Args:
            user_id: User ID

        Raises:
            HTTPException: If user not found
        """
        logger.info(f"Attempting to delete user with ID: {user_id}")
        result = self.repository.delete(user_id)
        if not result:
            logger.warning(f"Failed to delete user. User with ID {user_id} not found.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found",
            )
        logger.info(f"Successfully deleted user with ID: {user_id}")

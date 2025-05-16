from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import HTTPException, status
from sqlmodel import Session

from src.core.auth.api_key_utils import (
    _generate_api_key,
    _hash_api_key,
    _is_api_key_expired,
)
from src.domains.auth.models.api_key import APIKey, APIKeyPublic, APIKeyResponse
from src.domains.auth.services.repositories.api_key_repository import (
    APIKeyRepository,
)

import logging

logger = logging.getLogger(__name__)


class APIKeyService:
    """Service for managing API keys."""

    def __init__(self, session: Session):
        self.session = session
        self.repository = APIKeyRepository(session)

    def create_api_key(
        self,
        user_id: int,
        name: str = "API Key",
        expires_in_days: Optional[int] = None,
    ) -> APIKeyResponse:
        """
        Create a new API key for a user.

        Args:
            user_id: ID of the user creating the key
            name: Name/description of the key
            expires_in_days: Optional expiration time in days

        Returns:
            Dictionary with key data including the raw key (to be shown only once)
        """
        logger.info(f"Attempting to create API key for user ID: {user_id} with name: '{name}'")
        # Set expiration if provided
        expires_at = None
        if expires_in_days is not None and expires_in_days > 0:
            expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)
            logger.info(f"API key will expire on: {expires_at}")
        else:
            logger.info("API key will not expire.")

        # Generate the API key and hash
        api_key, key_hash = _generate_api_key()

        # Create API key data
        api_key_data = {
            "key_hash": key_hash,
            "user_id": user_id,
            "name": name,
            "expires_at": expires_at,
        }

        # Save to database
        db_api_key = self.repository.create(api_key_data)
        logger.info(f"Successfully created API key with ID: {db_api_key.id} for user ID: {user_id}")

        # Return response with the actual key (this is the only time it will be visible)
        return APIKeyResponse(
            id=db_api_key.id,
            key=api_key,
            name=db_api_key.name,
            created_at=db_api_key.created_at,
            expires_at=db_api_key.expires_at,
            user_id=db_api_key.user_id,
        )

    def get_user_api_keys(self, user_id: int) -> List[APIKeyPublic]:
        """
        Get all active API keys for a user.

        Args:
            user_id: ID of the user

        Returns:
            List of API key data (without the actual keys)
        """
        logger.info(f"Retrieving API keys for user ID: {user_id}")
        api_keys = self.repository.get_user_api_keys(user_id)

        public_keys = [
            APIKeyPublic(
                id=key.id,
                name=key.name,
                created_at=key.created_at,
                expires_at=key.expires_at,
                last_used_at=key.last_used_at,
                is_active=key.is_active,
            )
            for key in api_keys
        ]
        logger.info(f"Found {len(public_keys)} active API keys for user ID: {user_id}")
        return public_keys

    def validate_api_key(self, api_key: str) -> APIKey:
        """
        Validate an API key and return the associated API key object.

        Args:
            api_key: The API key to validate

        Returns:
            The API key object if valid

        Raises:
            HTTPException: If key is invalid, expired, or inactive
        """
        logger.debug("Attempting to validate API key.")  # Avoid logging the key itself
        # Hash the provided key
        key_hash = _hash_api_key(api_key)

        # Find the key in the database
        db_api_key = self.repository.get_by_key_hash(key_hash)

        if not db_api_key:
            logger.warning("API key validation failed: Key hash not found.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if key is active
        if not db_api_key.is_active:
            logger.warning(f"API key validation failed: Key ID {db_api_key.id} is inactive (revoked).")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if key has expired
        if db_api_key.expires_at and _is_api_key_expired(db_api_key.expires_at):
            logger.warning(f"API key validation failed: Key ID {db_api_key.id} has expired.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Update last used timestamp
        self.repository.update_last_used(db_api_key.id)
        logger.info(f"Successfully validated API key ID: {db_api_key.id} for user ID: {db_api_key.user_id}")

        return db_api_key

    def revoke_api_key(self, api_key: str, user_id: int) -> bool:
        """
        Revoke (deactivate) an API key.

        Args:
            api_key: The raw API key string to revoke
            user_id: ID of the user (for authorization)

        Returns:
            True if key was revoked, False otherwise

        Raises:
            HTTPException: If key not found or user not authorized
        """
        logger.info(f"User ID: {user_id} attempting to revoke API key: {api_key[:5]}...")
        hashed_key = _hash_api_key(api_key)
        db_api_key = self.repository.get_by_key_hash(hashed_key)

        if not db_api_key:
            logger.warning("Revocation failed: API key not found.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

        if db_api_key.user_id != user_id:
            logger.warning(
                f"Revocation failed: User ID {user_id} not authorized to revoke API key "
                f"owned by user ID {db_api_key.user_id}."
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to revoke this API key",
            )

        revoked = self.repository.revoke(db_api_key.id)
        if revoked:
            logger.info(f"Successfully revoked API key: {api_key[:5]}... by user ID: {user_id}")
        else:
            # This case might indicate the key was already inactive or another issue occurred at the DB level
            logger.warning(
                f"Attempt to revoke API key: {api_key[:5]}... by user ID: {user_id} "
                f"returned false from repository (might be already inactive)."
            )
        return revoked

    def revoke_api_key_by_id(self, api_key_id: int, user_id: int) -> bool:
        """
        Revoke (deactivate) an API key by its ID.
        """
        logger.info(f"User ID: {user_id} attempting to revoke API key ID: {api_key_id}")
        api_key = self.repository.get_by_id(api_key_id)

        if not api_key:
            logger.warning(f"Revocation failed: API key ID {api_key_id} not found.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

        if api_key.user_id != user_id:
            logger.warning(
                f"Revocation failed: User ID {user_id} not authorized to revoke API key ID {api_key_id} "
                f"owned by user ID {api_key.user_id}."
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to revoke this API key",
            )

        revoked = self.repository.revoke(api_key_id)
        if revoked:
            logger.info(f"Successfully revoked API key ID: {api_key_id} by user ID: {user_id}")
        else:
            logger.warning(
                f"Attempt to revoke API key ID: {api_key_id} by user ID: {user_id} "
                f"returned false from repository (might be already inactive)."
            )
        return revoked

    def delete_api_key_by_id(self, api_key_id: int, user_id: int) -> bool:
        """
        Permanently delete an API key.

        Args:
            api_key_id: ID of the API key to delete
            user_id: ID of the user (for authorization)

        Returns:
            True if key was deleted, False otherwise

        Raises:
            HTTPException: If key not found or user not authorized
        """
        logger.info(f"User ID: {user_id} attempting to delete API key ID: {api_key_id}")
        api_key = self.repository.get_by_id(api_key_id)

        if not api_key:
            logger.warning(f"Deletion failed: API key ID {api_key_id} not found.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

        if api_key.user_id != user_id:
            logger.warning(
                f"Deletion failed: User ID {user_id} not authorized to delete "
                f"API key ID {api_key_id} owned by user ID {api_key.user_id}."
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this API key",
            )

        deleted = self.repository.delete(api_key_id)
        if deleted:
            logger.info(f"Successfully deleted API key ID: {api_key_id} by user ID: {user_id}")
        else:
            # This case might indicate the key was already deleted or another issue occurred at the DB level
            logger.warning(
                f"Attempt to delete API key ID: {api_key_id} by user ID: {user_id} returned"
                f"false from repository (might be already deleted)."
            )

        return deleted

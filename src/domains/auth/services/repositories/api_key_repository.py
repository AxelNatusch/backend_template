from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, select

from src.domains.auth.models.api_key import APIKey
from src.core.exceptions.base import DatabaseError


class APIKeyRepository:
    """Repository for API key database operations."""

    def __init__(self, session: Session):
        self.session = session

    def create(self, api_key_data: dict) -> APIKey:
        """Create a new API key in the database."""
        try:
            api_key = APIKey(
                key_hash=api_key_data["key_hash"],
                user_id=api_key_data["user_id"],
                name=api_key_data["name"],
                expires_at=api_key_data.get("expires_at"),
                is_active=True,
            )
            self.session.add(api_key)
            self.session.commit()
            self.session.refresh(api_key)
            return api_key
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError(f"Failed to create API key: {str(e)}")

    def get_by_key_hash(self, key_hash: str) -> Optional[APIKey]:
        """Get API key by its hash value."""
        try:
            statement = select(APIKey).where(APIKey.key_hash == key_hash)
            result = self.session.exec(statement).first()
            return result
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to retrieve API key: {str(e)}")

    def get_by_id(self, api_key_id: int) -> Optional[APIKey]:
        """Get API key by its ID."""
        try:
            statement = select(APIKey).where(APIKey.id == api_key_id)
            result = self.session.exec(statement).first()
            return result
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to retrieve API key: {str(e)}")

    def get_user_api_keys(self, user_id: int) -> List[APIKey]:
        """Get all API keys for a user."""
        try:
            statement = select(APIKey).where(APIKey.user_id == user_id, APIKey.is_active)
            result = self.session.exec(statement).all()
            return result
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to retrieve user API keys: {str(e)}")

    def update_last_used(self, api_key_id: int) -> None:
        """Update the last used timestamp for an API key."""
        try:
            api_key = self.get_by_id(api_key_id)
            if api_key:
                # Update timestamps with timezone-aware datetimes
                now = datetime.now(timezone.utc)
                api_key.last_used_at = now
                api_key.updated_at = now
                self.session.add(api_key)
                self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError(f"Failed to update API key usage: {str(e)}")

    def revoke(self, api_key_id: int) -> bool:
        """Revoke (deactivate) an API key."""
        try:
            api_key = self.get_by_id(api_key_id)
            if api_key:
                # Update activity and timestamp with timezone-aware datetime
                api_key.is_active = False
                api_key.updated_at = datetime.now(timezone.utc)
                self.session.add(api_key)
                self.session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError(f"Failed to revoke API key: {str(e)}")

    def delete(self, api_key_id: int) -> bool:
        """Delete an API key from the database."""
        try:
            api_key = self.get_by_id(api_key_id)
            if api_key:
                self.session.delete(api_key)
                self.session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError(f"Failed to delete API key: {str(e)}")

"""
User repository for database operations.
"""

from typing import Optional
from uuid import UUID

from sqlmodel import Session, select

from src.core.auth.password import get_password_hash
from src.domains.auth.models.user import User, UserCreate, UserUpdate


class UserRepository:
    """
    Repository for user database operations.
    """

    def __init__(self, session: Session):
        self.session = session

    def create(self, user_data: UserCreate) -> User:
        """
        Create a new user.

        Args:
            user_data: User creation data

        Returns:
            Created user
        """
        # Hash the password
        hashed_password = get_password_hash(user_data.password)

        # Create user with hashed password
        user = User(
            username=user_data.username,
            email=user_data.email,
            password=hashed_password,
            role=user_data.role,
        )

        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)

        return user

    def get_by_id(self, user_id: int) -> Optional[User]:
        """
        Get a user by ID.

        Args:
            user_id: User ID

        Returns:
            User if found, None otherwise
        """
        return self.session.get(User, user_id)

    def get_by_email(self, email: str) -> Optional[User]:
        """
        Get a user by email.

        Args:
            email: User email

        Returns:
            User if found, None otherwise
        """
        return self.session.exec(select(User).where(User.email == email)).first()

    def get_by_username(self, username: str) -> Optional[User]:
        """
        Get a user by username.
        """
        return self.session.exec(select(User).where(User.username == username)).first()

    def update(self, user_id: UUID, user_data: UserUpdate) -> Optional[User]:
        """
        Update a user.

        Args:
            user_id: User ID
            user_data: User update data

        Returns:
            Updated user if found, None otherwise
        """
        user = self.session.get(User, user_id)
        if not user:
            return None

        # Convert to dict for update
        data_dict = user_data.model_dump(exclude_unset=True)

        # Hash password if provided
        if "password" in data_dict:
            data_dict["password"] = get_password_hash(data_dict["password"])

        # Update user
        user.update(data_dict)

        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)

        return user

    def delete(self, user_id: UUID) -> bool:
        """
        Delete a user.

        Args:
            user_id: User ID

        Returns:
            True if deleted, False if not found
        """
        user = self.session.get(User, user_id)
        if not user:
            return False

        self.session.delete(user)
        self.session.commit()

        return True

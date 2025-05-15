import os
from typing import Generator
import logging

from sqlmodel import Session, create_engine, select

from src.core.config.settings import settings
from src.domains.auth.models.user import User, UserCreate, UserRole
from src.domains.auth.services.user_service import UserService


logger = logging.getLogger(__name__)

def get_engine():
    """
    Creates and returns a database engine.
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise Exception("DATABASE_URL environment variable is not set")

    return create_engine(
        database_url,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800,
    )


def ensure_admin_user_exists() -> None:
    """
    Ensures an admin user exists in the database.
    Creates one with default credentials if none exists.
    """
    engine = get_engine()
    with Session(engine) as session:
        # Check if any admin user exists
        admin_exists = session.exec(
            select(User).where(User.role == UserRole.ADMIN)
        ).first()
        
        if not admin_exists:
            # Create admin user using settings
            admin_email = settings.ADMIN_EMAIL
            admin_password = settings.ADMIN_PASSWORD
            admin_username = settings.ADMIN_USERNAME
            
            if not admin_email or not admin_password or not admin_username:
                raise Exception("ADMIN_EMAIL, ADMIN_PASSWORD, and ADMIN_USERNAME must be set in the environment variables")
                return
                
            # Create admin user
            admin_user = UserCreate(
                username=admin_username,
                email=admin_email,
                password=admin_password,
                role=UserRole.ADMIN,
            )
            
            user_service = UserService(session)
            user_service.create_user(admin_user)
            logger.info(f"Admin user created with email: {admin_email}")


def init_db(create_tables: bool = True) -> None:
    """
    Initializes the database and ensures an admin user exists.

    Args:
        create_tables: If True, creates all tables. (DEVELOPMENT ONLY)
    """
    if create_tables:
        # For initial setup or development environments
        # SQLModel.metadata.drop_all(engine)

        # create all tables if they don't exist
        # SQLModel.metadata.create_all(engine)
        pass
        
    # Ensure an admin user exists
    ensure_admin_user_exists()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI endpoints that need a database session.
    Yields a session and ensures it's closed properly after use.
    """
    engine = get_engine()
    with Session(engine) as session:
        try:
            yield session
        finally:
            session.close()

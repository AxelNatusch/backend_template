import pytest
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
import logging

from src.domains.auth.api.v1.api_key import router as api_key_router
from src.api.dependencies.auth import get_current_user, get_db
from src.domains.auth.models.user import User, UserRole


# Disable logging for tests by default
logging.disable(logging.CRITICAL)


@pytest.fixture(scope="function")
def enable_logging():
    """Temporarily enable logging for tests that need it."""
    # Enable all logging
    logging.disable(logging.NOTSET)
    yield
    # Disable logging again after the test
    logging.disable(logging.CRITICAL)


@pytest.fixture(scope="function")
def db_session():
    """Create an isolated in-memory database session for testing."""
    # Create in-memory database for testing
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # Create tables for our models
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    # Clean up the database after the test
    SQLModel.metadata.drop_all(engine)
    engine.dispose()  # Close the connection pool


@pytest.fixture
def test_user(db_session):
    """Create a real test user in the database."""
    # Create a real user in the test database
    user = User(
        username="testuser",
        email="test@example.com",
        role=UserRole.USER,
        is_active=True,
        # Use the password field, not hashed_password
        password="$2b$12$test_hashed_password_value",
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


@pytest.fixture
def client(test_user, db_session):
    """Return a TestClient instance for testing API endpoints."""
    # Create a test app to ensure routes are registered correctly for tests
    test_app = FastAPI()

    # Add exception handler for the test app
    @test_app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": str(exc)},
        )

    # Create dependency override functions
    async def override_get_current_user():
        return test_user

    async def override_get_db():
        yield db_session

    # Setup dependency overrides BEFORE including the router
    # This ensures that the router's endpoints use our overridden dependencies
    test_app.dependency_overrides[get_current_user] = override_get_current_user
    test_app.dependency_overrides[get_db] = override_get_db

    # Mount the API key router
    test_app.include_router(
        api_key_router,
        prefix="/auth/api-keys",  # Use hyphen in path as expected in tests
    )

    # Return a test client with our configured test app
    yield TestClient(test_app)

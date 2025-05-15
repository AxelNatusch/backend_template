"""
Main router for the users domain.
"""

from fastapi import APIRouter

from src.domains.auth.api.v1.auth import router as auth_router
from src.domains.auth.api.v1.api_key import router as api_key_router

# Create the main router for the users domain
router = APIRouter(prefix="/auth")

# Include the auth router
router.include_router(auth_router)
# Include the API key router
router.include_router(api_key_router, prefix="/api_keys")

"""
API router registration module.
This module collects and registers all domain routers.
"""

from fastapi import APIRouter

from src.core.config.settings import settings
from src.domains.auth.api.router import router as auth_router

# Create main API router
api_router = APIRouter(prefix=settings.API_V1_STR)

# Include domain routers
api_router.include_router(auth_router)

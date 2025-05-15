from src.domains.auth.api.v1.auth import router as auth_router
from src.domains.auth.api.v1.api_key import router as api_key_router

__all__ = ["auth_router", "api_key_router"]

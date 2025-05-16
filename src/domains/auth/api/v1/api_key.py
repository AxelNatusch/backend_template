"""
API Key management endpoints.
"""

from fastapi import APIRouter, Depends, status, Path, Body
from sqlmodel import Session
from typing import Dict, List, Annotated
from pydantic import BaseModel

from src.api.dependencies.auth import get_current_user
from src.core.db import get_db
from src.domains.auth.models.user import User
from src.domains.auth.models.api_key import (
    APIKeyCreate,
    APIKeyPublic,
    APIKeyResponse,
)
from src.domains.auth.services.api_key_service import APIKeyService

router = APIRouter(tags=["api_keys"])


class RevokeApiKeyRequest(BaseModel):
    api_key: str


class RevokeApiKeyByIdRequest(BaseModel):
    api_key_id: int


@router.post("/", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
def create_api_key(
    api_key_data: Annotated[APIKeyCreate, Body(...)],
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> APIKeyResponse:
    """
    Create a new API key for the authenticated user.
    """
    api_key_service = APIKeyService(session)
    return api_key_service.create_api_key(
        user_id=current_user.id,
        name=api_key_data.name,
        expires_in_days=api_key_data.expires_in_days,
    )


@router.get("/", response_model=List[APIKeyPublic], status_code=status.HTTP_200_OK)
def get_api_keys(
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> List[Dict]:
    """
    Get all API keys for the authenticated user.
    """
    api_key_service = APIKeyService(session)
    return api_key_service.get_user_api_keys(current_user.id)


@router.put("/revoke", status_code=status.HTTP_200_OK)
def revoke_api_key(
    request: Annotated[RevokeApiKeyRequest, Body(...)],
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Dict:
    """
    Revoke an API key.
    """
    api_key_service = APIKeyService(session)
    revoked = api_key_service.revoke_api_key(request.api_key, current_user.id)
    return {"success": revoked}


@router.put("/revoke/{api_key_id}", status_code=status.HTTP_200_OK)
def revoke_api_key_by_id(
    api_key_id: Annotated[int, Path(...)],
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Dict:
    """
    Revoke an API key by its ID.
    """
    api_key_service = APIKeyService(session)
    revoked = api_key_service.revoke_api_key_by_id(api_key_id, current_user.id)
    return {"success": revoked}


@router.delete("/{api_key_id}", status_code=status.HTTP_200_OK)
def delete_api_key(
    api_key_id: Annotated[int, Path(...)],
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Dict:
    """
    Delete an API key permanently.
    """
    api_key_service = APIKeyService(session)
    deleted = api_key_service.delete_api_key_by_id(api_key_id, current_user.id)
    return {"success": deleted}

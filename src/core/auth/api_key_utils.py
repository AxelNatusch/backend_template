"""
API key utilities for authentication.
"""

import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Tuple
from uuid import uuid4

from fastapi import HTTPException, status

from src.core.config.settings import settings


def _generate_api_key(prefix: str = settings.API_KEY_PREFIX) -> Tuple[str, str]:
    """
    Generate a secure API key with a prefix.
    
    Args:
        prefix: Short prefix to identify the API key
        
    Returns:
        Tuple of (API key, hashed key for storage)
    """
    # Generate a secure random token
    token_bytes = secrets.token_bytes(32)
    
    # Create a readable key with the prefix
    token_b64 = base64.urlsafe_b64encode(token_bytes).decode().rstrip("=")
    api_key = f"{prefix}_{token_b64}"
    
    # Hash the key for storage
    hashed_key = _hash_api_key(api_key)
    
    return api_key, hashed_key


def _hash_api_key(api_key: str) -> str:
    """
    Hash an API key for secure storage.
    
    Args:
        api_key: The API key to hash
        
    Returns:
        Hashed API key (never store raw keys in your database)
    """
    # Use a constant-time comparison hash for security
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    return key_hash


def _create_api_key_with_metadata(
    user_id: int, 
    name: str = "API Key",
    expires_delta: Optional[timedelta] = None
) -> Dict:
    """
    Create an API key with associated metadata.
    
    Args:
        user_id: ID of the user that owns this key
        name: Name/description of the key
        expires_delta: Optional expiration time
        
    Returns:
        Dictionary with key data including the raw key (to be shown only once)
    """
    # Generate key and hash
    api_key, hashed_key = _generate_api_key()
    
    # Create expiration timestamp if provided
    expires_at = None
    if expires_delta:
        expires_at = datetime.now(timezone.utc) + expires_delta
    
    # Create key metadata
    key_data = {
        "id": str(uuid4()),
        "key": api_key, 
        "key_hash": hashed_key, 
        "user_id": user_id,
        "name": name,
        "created_at": datetime.now(timezone.utc),
        "expires_at": expires_at,
        "last_used_at": None,
    }
    
    return key_data


def _verify_api_key(api_key: str, stored_key_hash: str) -> bool:
    """
    Verify an API key against a stored hash.
    
    Args:
        api_key: The API key to verify
        stored_key_hash: The stored hash to check against
        
    Returns:
        True if the key is valid, False otherwise
    """
    # Hash the provided key
    provided_key_hash = _hash_api_key(api_key)
    
    # Compare hashes in constant time to prevent timing attacks
    return hmac.compare_digest(provided_key_hash, stored_key_hash)


def _is_api_key_expired(expires_at: Optional[datetime]) -> bool:
    """
    Check if an API key has expired.
    
    Args:
        expires_at: Expiration datetime or None if no expiration
        
    Returns:
        True if expired, False if still valid or no expiration
    """
    if expires_at is None:
        return False
    
    # Ensure we're comparing datetimes with the same timezone awareness
    now = datetime.now(timezone.utc)
    
    # Convert expires_at to timezone-aware if it's naive
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    
    return now > expires_at



def _validate_api_key(api_key: str, stored_key_hash: str, expires_at: Optional[datetime] = None) -> bool:
    """
    Validate an API key against a stored hash and check expiration.
    
    Args:
        api_key: The API key to validate
        stored_key_hash: The stored hash to check against
        expires_at: Optional expiration datetime
        
    Returns:
        True if key is valid and not expired
    
    Raises:
        HTTPException: If key is invalid or expired
    """
    # First verify the key
    if not _verify_api_key(api_key, stored_key_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Then check expiration
    if expires_at and _is_api_key_expired(expires_at):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return True

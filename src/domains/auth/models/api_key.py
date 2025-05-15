from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field as PydanticField
from sqlmodel import Field, SQLModel


class APIKey(SQLModel, table=True):
    """
    Table to store API keys.
    """
    id: int | None = Field(default=None, primary_key=True)
    key_hash: str = Field(index=True, unique=True)
    user_id: int = Field(foreign_key="user.id")
    name: str = Field(default=None)
    expires_at: Optional[datetime] = Field(default=None)
    is_active: bool = Field(default=True)
    last_used_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class APIKeyCreate(BaseModel):
    """
    Schema for creating a new API key.
    """
    name: str = PydanticField(..., description="Name or description of the API key")
    expires_in_days: Optional[int] = PydanticField(None, description="Number of days until the key expires")


class APIKeyPublic(BaseModel):
    """
    Schema for returning API key data (without the actual key).
    """
    id: int = PydanticField(..., description="API key ID")
    name: str = PydanticField(..., description="Name or description of the API key")
    created_at: datetime = PydanticField(..., description="Timestamp of API key creation")
    expires_at: Optional[datetime] = PydanticField(None, description="Timestamp when the key expires")
    last_used_at: Optional[datetime] = PydanticField(None, description="Timestamp of last key usage")
    is_active: bool = PydanticField(..., description="Whether the key is active")


class APIKeyResponse(BaseModel):
    """
    Schema for returning a newly created API key (including the actual key).
    """
    id: int = PydanticField(..., description="API key ID")
    key: str = PydanticField(..., description="The API key (shown only once)")
    name: str = PydanticField(..., description="Name or description of the API key")
    created_at: datetime = PydanticField(..., description="Timestamp of API key creation")
    expires_at: Optional[datetime] = PydanticField(None, description="Timestamp when the key expires")
    user_id: int = PydanticField(..., description="User ID associated with this key")


"""Asset schemas."""

from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional, List


class ServiceResponse(BaseModel):
    """Service response schema."""

    id: int
    port: int
    protocol: Optional[str] = None
    service_name: Optional[str] = None
    version: Optional[str] = None
    state: str
    discovered_at: datetime

    class Config:
        from_attributes = True


class AssetCreate(BaseModel):
    """Asset creation schema."""

    ip: str
    hostname: Optional[str] = None
    department: Optional[str] = None
    environment: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("ip")
    @classmethod
    def validate_ip(cls, v: str) -> str:
        """Validate IP address format."""
        # Simple validation - can be enhanced
        parts = v.split(".")
        if len(parts) == 4:
            try:
                for part in parts:
                    num = int(part)
                    if num < 0 or num > 255:
                        raise ValueError("Invalid IP address")
                return v
            except (ValueError, AttributeError):
                raise ValueError("Invalid IP address format")
        # Allow CIDR notation
        if "/" in v:
            return v
        raise ValueError("Invalid IP address")


class AssetUpdate(BaseModel):
    """Asset update schema."""

    hostname: Optional[str] = None
    status: Optional[str] = None
    department: Optional[str] = None
    environment: Optional[str] = None
    notes: Optional[str] = None


class AssetResponse(BaseModel):
    """Asset response schema."""

    id: int
    ip: str
    hostname: Optional[str] = None
    os: Optional[str] = None
    status: str
    department: Optional[str] = None
    environment: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    services: List[ServiceResponse] = []

    class Config:
        from_attributes = True


class AssetBatchImportRequest(BaseModel):
    """Asset batch import request."""

    assets: List[AssetCreate]
    group_id: Optional[int] = None  # Optional group to add imported assets


class AssetFilterRequest(BaseModel):
    """Asset filter request."""

    ip: Optional[str] = None
    hostname: Optional[str] = None
    status: Optional[str] = None
    department: Optional[str] = None
    environment: Optional[str] = None
    page: int = 1
    page_size: int = 20

    @field_validator("page", "page_size")
    @classmethod
    def validate_pagination(cls, v: int) -> int:
        """Validate pagination parameters."""
        if v < 1:
            raise ValueError("Must be >= 1")
        return v

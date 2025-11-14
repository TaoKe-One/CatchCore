"""Node schemas for API requests and responses."""

from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel, Field


class NodeCreate(BaseModel):
    """Schema for creating a new node."""

    name: str = Field(..., min_length=1, max_length=255, description="Unique node name")
    host: str = Field(..., description="Node host IP address")
    port: int = Field(default=8000, ge=1, le=65535, description="Node port")
    node_type: str = Field(default="scanner", description="Node type: scanner, worker, coordinator")
    max_concurrent_tasks: int = Field(default=5, ge=1, le=100, description="Maximum concurrent tasks")
    api_version: Optional[str] = Field(default=None, description="API version")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "name": "scanner-node-01",
                "host": "192.168.1.100",
                "port": 8001,
                "node_type": "scanner",
                "max_concurrent_tasks": 5,
                "api_version": "0.1.0",
            }
        }


class NodeUpdate(BaseModel):
    """Schema for updating node configuration."""

    max_concurrent_tasks: Optional[int] = Field(None, ge=1, le=100)
    status: Optional[str] = Field(None, description="Node status: online, offline, maintenance")
    api_version: Optional[str] = Field(None)

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "max_concurrent_tasks": 8,
                "status": "maintenance",
            }
        }


class NodeResponse(BaseModel):
    """Schema for node response."""

    id: int
    name: str
    host: str
    port: int
    status: str
    node_type: str
    cpu_usage: float = Field(default=0.0, description="CPU usage percentage")
    memory_usage: float = Field(default=0.0, description="Memory usage percentage")
    disk_usage: float = Field(default=0.0, description="Disk usage percentage")
    max_concurrent_tasks: int
    current_tasks: int = Field(default=0, description="Current running tasks")
    api_version: Optional[str]
    last_heartbeat: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True

        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "scanner-node-01",
                "host": "192.168.1.100",
                "port": 8001,
                "status": "online",
                "node_type": "scanner",
                "cpu_usage": 45.5,
                "memory_usage": 62.3,
                "disk_usage": 38.9,
                "max_concurrent_tasks": 5,
                "current_tasks": 3,
                "api_version": "0.1.0",
                "last_heartbeat": "2025-11-14T10:30:00Z",
                "created_at": "2025-11-14T09:00:00Z",
                "updated_at": "2025-11-14T10:30:00Z",
            }
        }


class NodeHealthResponse(BaseModel):
    """Schema for node health check response."""

    id: int
    name: str
    status: str
    last_heartbeat: Optional[datetime]
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    current_tasks: int
    is_healthy: bool = Field(description="True if node is healthy and responsive")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "scanner-node-01",
                "status": "online",
                "last_heartbeat": "2025-11-14T10:30:00Z",
                "cpu_usage": 45.5,
                "memory_usage": 62.3,
                "disk_usage": 38.9,
                "current_tasks": 3,
                "is_healthy": True,
            }
        }


class NodeListResponse(BaseModel):
    """Schema for node list response."""

    total: int
    skip: int
    limit: int
    nodes: List[NodeResponse]

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "total": 3,
                "skip": 0,
                "limit": 100,
                "nodes": [
                    {
                        "id": 1,
                        "name": "scanner-node-01",
                        "host": "192.168.1.100",
                        "port": 8001,
                        "status": "online",
                        "node_type": "scanner",
                        "cpu_usage": 45.5,
                        "memory_usage": 62.3,
                        "disk_usage": 38.9,
                        "max_concurrent_tasks": 5,
                        "current_tasks": 3,
                        "api_version": "0.1.0",
                        "last_heartbeat": "2025-11-14T10:30:00Z",
                        "created_at": "2025-11-14T09:00:00Z",
                        "updated_at": "2025-11-14T10:30:00Z",
                    },
                ],
            }
        }

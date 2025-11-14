"""Task schemas."""

from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional, List, Dict, Any


class TaskCreate(BaseModel):
    """Task creation schema."""

    name: str
    task_type: str  # port_scan, service_identify, fingerprint, poc_detection, etc.
    target_range: str  # IP, IP segment, or domain
    description: Optional[str] = None
    priority: Optional[int] = 5  # 1-10
    configs: Optional[Dict[str, str]] = None  # Additional configurations

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: int) -> int:
        """Validate priority."""
        if v < 1 or v > 10:
            raise ValueError("Priority must be between 1 and 10")
        return v


class TaskResponse(BaseModel):
    """Task response schema."""

    id: int
    name: str
    task_type: str
    target_range: str
    status: str
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    priority: int
    description: Optional[str] = None

    class Config:
        from_attributes = True


class TaskProgressUpdate(BaseModel):
    """Task progress update schema."""

    status: str
    progress: int  # 0-100
    current_step: Optional[str] = None
    message: Optional[str] = None


class TaskResultResponse(BaseModel):
    """Task result response schema."""

    id: int
    task_id: int
    result_type: str
    result_data: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True

"""POC related schemas."""

from typing import Optional, List
from pydantic import BaseModel, Field


class POCTagBase(BaseModel):
    """Base POC tag schema."""

    tag: str


class POCTagCreate(POCTagBase):
    """Create POC tag schema."""

    pass


class POCTagResponse(POCTagBase):
    """POC tag response schema."""

    id: int
    poc_id: int

    class Config:
        """Pydantic config."""

        from_attributes = True


class POCBase(BaseModel):
    """Base POC schema."""

    name: str = Field(..., min_length=1, max_length=255)
    cve_id: Optional[str] = None
    cvss_score: Optional[str] = None
    severity: Optional[str] = Field(None, pattern="^(critical|high|medium|low|info)$")
    poc_type: str = Field(..., min_length=1)
    description: Optional[str] = None
    content: str = Field(..., min_length=1)
    source: Optional[str] = None
    author: Optional[str] = None
    reference_link: Optional[str] = None
    affected_product: Optional[str] = None
    affected_version: Optional[str] = None
    is_active: int = Field(default=1, ge=0, le=1)


class POCCreate(POCBase):
    """Create POC schema."""

    tags: Optional[List[str]] = None


class POCUpdate(BaseModel):
    """Update POC schema."""

    name: Optional[str] = None
    cve_id: Optional[str] = None
    cvss_score: Optional[str] = None
    severity: Optional[str] = None
    poc_type: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    source: Optional[str] = None
    author: Optional[str] = None
    reference_link: Optional[str] = None
    affected_product: Optional[str] = None
    affected_version: Optional[str] = None
    is_active: Optional[int] = None
    tags: Optional[List[str]] = None


class POCResponse(POCBase):
    """POC response schema."""

    id: int
    created_at: str
    updated_at: str
    tags: List[POCTagResponse] = []

    class Config:
        """Pydantic config."""

        from_attributes = True


class POCSearchRequest(BaseModel):
    """POC search request schema."""

    keyword: Optional[str] = None
    cve_id: Optional[str] = None
    severity: Optional[str] = None
    poc_type: Optional[str] = None
    source: Optional[str] = None
    tag: Optional[str] = None
    is_active: Optional[int] = None


class POCExecutionRequest(BaseModel):
    """POC execution request schema."""

    poc_id: int
    target: str = Field(..., min_length=1)
    port: Optional[int] = Field(None, ge=1, le=65535)
    options: Optional[dict] = None


class POCExecutionResult(BaseModel):
    """POC execution result schema."""

    poc_id: int
    target: str
    port: Optional[int]
    vulnerable: bool
    output: str
    error: Optional[str] = None
    execution_time: float


class POCBulkImportRequest(BaseModel):
    """POC bulk import request schema."""

    source: str = Field(..., description="Source: nuclei, afrog, custom, etc.")
    pocs: List[POCCreate]


class POCStatisticsResponse(BaseModel):
    """POC statistics response schema."""

    total_pocs: int
    by_severity: dict
    by_type: dict
    by_source: dict
    by_tag: dict
    total_cves: int

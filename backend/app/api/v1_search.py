"""Advanced search and filtering API routes."""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.services.search_service import SearchService
from app.schemas.vulnerability import VulnerabilityResponse
from app.schemas.asset import AssetResponse
from app.schemas.task import TaskResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/vulnerabilities", response_model=dict)
async def search_vulnerabilities(
    q: Optional[str] = Query(None, description="Advanced search query"),
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    cve_id: Optional[str] = Query(None),
    asset_id: Optional[int] = Query(None),
    date_from: Optional[str] = Query(None, description="ISO format date"),
    date_to: Optional[str] = Query(None, description="ISO format date"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Advanced search for vulnerabilities."""
    filters = {}

    if severity:
        filters["severity"] = severity

    if status:
        filters["status"] = status

    if cve_id:
        filters["cve_id"] = cve_id

    if asset_id:
        filters["asset_id"] = asset_id

    if date_from:
        filters["date_from"] = date_from

    if date_to:
        filters["date_to"] = date_to

    try:
        vulnerabilities, total = await SearchService.search_vulnerabilities(
            db,
            query=q or "",
            filters=filters,
            page=page,
            page_size=page_size,
        )

        return {
            "code": 0,
            "message": "success",
            "data": {
                "items": [
                    {
                        "id": v.id,
                        "cve_id": v.cve_id,
                        "severity": v.severity,
                        "status": v.status,
                        "description": v.description,
                        "discovered_at": v.discovered_at.isoformat() if v.discovered_at else None,
                    }
                    for v in vulnerabilities
                ],
                "total": total,
                "page": page,
                "page_size": page_size,
            },
        }

    except Exception as e:
        logger.error(f"Error searching vulnerabilities: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed",
        )


@router.get("/assets", response_model=dict)
async def search_assets(
    q: Optional[str] = Query(None, description="Advanced search query"),
    status: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    environment: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Advanced search for assets."""
    filters = {}

    if status:
        filters["status"] = status

    if department:
        filters["department"] = department

    if environment:
        filters["environment"] = environment

    try:
        assets, total = await SearchService.search_assets(
            db,
            query=q or "",
            filters=filters,
            page=page,
            page_size=page_size,
        )

        return {
            "code": 0,
            "message": "success",
            "data": {
                "items": [
                    {
                        "id": a.id,
                        "ip_address": a.ip_address,
                        "hostname": a.hostname,
                        "status": a.status,
                        "department": a.department,
                        "environment": a.environment,
                    }
                    for a in assets
                ],
                "total": total,
                "page": page,
                "page_size": page_size,
            },
        }

    except Exception as e:
        logger.error(f"Error searching assets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed",
        )


@router.get("/tasks", response_model=dict)
async def search_tasks(
    q: Optional[str] = Query(None, description="Advanced search query"),
    status: Optional[str] = Query(None),
    task_type: Optional[str] = Query(None),
    priority: Optional[int] = Query(None, ge=1, le=10),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Advanced search for tasks."""
    filters = {}

    if status:
        filters["status"] = status

    if task_type:
        filters["task_type"] = task_type

    if priority:
        filters["priority"] = priority

    try:
        tasks, total = await SearchService.search_tasks(
            db,
            query=q or "",
            filters=filters,
            page=page,
            page_size=page_size,
        )

        return {
            "code": 0,
            "message": "success",
            "data": {
                "items": [
                    {
                        "id": t.id,
                        "name": t.name,
                        "task_type": t.task_type,
                        "status": t.status,
                        "progress": t.progress,
                        "priority": t.priority,
                        "created_at": t.created_at.isoformat() if t.created_at else None,
                    }
                    for t in tasks
                ],
                "total": total,
                "page": page,
                "page_size": page_size,
            },
        }

    except Exception as e:
        logger.error(f"Error searching tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed",
        )


@router.get("/suggestions", response_model=dict)
async def get_search_suggestions(
    type: str = Query("vulnerability", regex="^(vulnerability|asset|task)$"),
    current_user: User = Depends(get_current_user),
):
    """Get search syntax suggestions and examples."""
    suggestions = SearchService.get_search_suggestions(type)

    return {
        "code": 0,
        "message": "success",
        "data": suggestions,
    }


@router.get("/syntax", response_model=dict)
async def get_search_syntax(
    current_user: User = Depends(get_current_user),
):
    """Get detailed search syntax documentation."""
    syntax_doc = {
        "title": "Advanced Search Syntax",
        "description": "CatchCore supports advanced search syntax for filtering data",
        "basic_syntax": {
            "description": "Basic search format",
            "examples": [
                {"format": "field=value", "description": "Exact match", "example": "severity=critical"},
                {"format": "field:operator:value", "description": "Operator-based search", "example": "cve:like:CVE-2021"},
            ],
        },
        "operators": {
            "comparison": [
                {"symbol": "=", "name": "Equals", "example": "severity=high"},
                {"symbol": "!=", "name": "Not equals", "example": "status!=fixed"},
                {"symbol": ">", "name": "Greater than", "example": "cvss_score>7.0"},
                {"symbol": "<", "name": "Less than", "example": "cvss_score<5.0"},
                {"symbol": ">=", "name": "Greater or equal", "example": "priority>=8"},
                {"symbol": "<=", "name": "Less or equal", "example": "priority<=5"},
            ],
            "string": [
                {"symbol": "like", "name": "Contains", "example": "name:like:Apache"},
                {"symbol": "in", "name": "In list", "example": "severity:in:critical,high"},
            ],
        },
        "logical_operators": [
            {"operator": "AND", "description": "Both conditions must be true", "example": "severity=critical AND status=open"},
            {"operator": "OR", "description": "At least one condition must be true", "example": "severity=critical OR severity=high"},
        ],
        "vulnerability_fields": [
            {"name": "cve", "type": "string", "description": "CVE identifier"},
            {"name": "severity", "type": "enum", "values": ["critical", "high", "medium", "low", "info"]},
            {"name": "status", "type": "enum", "values": ["open", "fixed", "verified", "false_positive"]},
            {"name": "ip", "type": "ip", "description": "IP address"},
        ],
        "asset_fields": [
            {"name": "ip", "type": "ip", "description": "IP address"},
            {"name": "hostname", "type": "string", "description": "Host name"},
            {"name": "status", "type": "enum", "values": ["active", "inactive", "archived"]},
            {"name": "department", "type": "string", "description": "Department name"},
        ],
        "task_fields": [
            {"name": "name", "type": "string", "description": "Task name"},
            {"name": "status", "type": "enum", "values": ["pending", "running", "completed", "failed"]},
            {"name": "type", "type": "string", "description": "Task type"},
        ],
        "examples": [
            {
                "category": "Vulnerability Search",
                "queries": [
                    "severity=critical AND status=open",
                    "cve:like:CVE-2021",
                    "severity:in:critical,high",
                    "ip=192.168.1.1",
                ],
            },
            {
                "category": "Asset Search",
                "queries": [
                    "ip=192.168.1.0/24",
                    "hostname:like:server",
                    "department=IT AND status=active",
                ],
            },
            {
                "category": "Task Search",
                "queries": [
                    "status=completed",
                    "type=port_scan AND priority>=8",
                    "name:like:DMZ",
                ],
            },
        ],
    }

    return {
        "code": 0,
        "message": "success",
        "data": syntax_doc,
    }

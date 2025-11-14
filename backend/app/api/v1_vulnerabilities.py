"""Vulnerability management API routes."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.models import Vulnerability, VulnerabilityHistory, User
from app.schemas.vulnerability import (
    VulnerabilityResponse,
    VulnerabilityUpdateRequest,
    VulnerabilityFilterRequest,
)
from app.api.deps import get_current_user

router = APIRouter(prefix="/vulnerabilities", tags=["vulnerabilities"])


@router.get("", response_model=dict)
async def list_vulnerabilities(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    asset_id: Optional[int] = Query(None),
    cve_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get paginated list of vulnerabilities with filters."""
    query = select(Vulnerability)

    # Apply filters
    filters = []
    if severity:
        filters.append(Vulnerability.severity == severity)
    if status:
        filters.append(Vulnerability.status == status)
    if asset_id:
        filters.append(Vulnerability.asset_id == asset_id)
    if cve_id:
        filters.append(Vulnerability.cve_id.ilike(f"%{cve_id}%"))

    if filters:
        query = query.where(or_(*filters))

    # Get total count
    count_query = select(func.count(Vulnerability.id))
    if filters:
        count_query = count_query.where(or_(*filters))
    count_result = await db.execute(count_query)
    total = count_result.scalar()

    # Apply pagination and ordering
    query = query.order_by(Vulnerability.discovered_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size)

    result = await db.execute(query)
    vulnerabilities = result.scalars().all()

    return {
        "code": 0,
        "message": "success",
        "data": {
            "items": [VulnerabilityResponse.from_orm(vuln) for vuln in vulnerabilities],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


@router.get("/{vulnerability_id}", response_model=dict)
async def get_vulnerability(
    vulnerability_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get vulnerability details by ID."""
    result = await db.execute(
        select(Vulnerability).where(Vulnerability.id == vulnerability_id)
    )
    vuln = result.scalar_one_or_none()

    if not vuln:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vulnerability not found",
        )

    return {
        "code": 0,
        "message": "success",
        "data": VulnerabilityResponse.from_orm(vuln),
    }


@router.put("/{vulnerability_id}", response_model=dict)
async def update_vulnerability(
    vulnerability_id: int,
    update_req: VulnerabilityUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update vulnerability status and remediation info."""
    result = await db.execute(
        select(Vulnerability).where(Vulnerability.id == vulnerability_id)
    )
    db_vuln = result.scalar_one_or_none()

    if not db_vuln:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vulnerability not found",
        )

    old_status = db_vuln.status

    # Update fields
    if update_req.status:
        db_vuln.status = update_req.status
    if update_req.remediation:
        db_vuln.remediation = update_req.remediation

    # Record history
    if update_req.status and update_req.status != old_status:
        history = VulnerabilityHistory(
            vulnerability_id=vulnerability_id,
            old_status=old_status,
            new_status=update_req.status,
            operator_id=current_user.id,
            notes=update_req.notes,
        )
        db.add(history)

    db.add(db_vuln)
    await db.commit()
    await db.refresh(db_vuln)

    return {
        "code": 0,
        "message": "success",
        "data": VulnerabilityResponse.from_orm(db_vuln),
    }


@router.delete("/{vulnerability_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vulnerability(
    vulnerability_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a vulnerability."""
    result = await db.execute(
        select(Vulnerability).where(Vulnerability.id == vulnerability_id)
    )
    db_vuln = result.scalar_one_or_none()

    if not db_vuln:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vulnerability not found",
        )

    await db.delete(db_vuln)
    await db.commit()

    return None


@router.get("/{vulnerability_id}/history", response_model=dict)
async def get_vulnerability_history(
    vulnerability_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get vulnerability status change history."""
    # Check if vulnerability exists
    result = await db.execute(
        select(Vulnerability).where(Vulnerability.id == vulnerability_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vulnerability not found",
        )

    # Get total count
    count_result = await db.execute(
        select(func.count(VulnerabilityHistory.id)).where(
            VulnerabilityHistory.vulnerability_id == vulnerability_id
        )
    )
    total = count_result.scalar()

    # Get history
    history_result = await db.execute(
        select(VulnerabilityHistory)
        .where(VulnerabilityHistory.vulnerability_id == vulnerability_id)
        .order_by(VulnerabilityHistory.timestamp.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    history = history_result.scalars().all()

    return {
        "code": 0,
        "message": "success",
        "data": {
            "vulnerability_id": vulnerability_id,
            "history": history,
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


@router.get("/stats/summary", response_model=dict)
async def get_vulnerability_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get vulnerability statistics summary."""
    # Total count
    total_result = await db.execute(
        select(func.count(Vulnerability.id))
    )
    total = total_result.scalar()

    # Count by severity
    severity_result = await db.execute(
        select(Vulnerability.severity, func.count(Vulnerability.id)).group_by(
            Vulnerability.severity
        )
    )
    severity_stats = dict(severity_result.all())

    # Count by status
    status_result = await db.execute(
        select(Vulnerability.status, func.count(Vulnerability.id)).group_by(
            Vulnerability.status
        )
    )
    status_stats = dict(status_result.all())

    return {
        "code": 0,
        "message": "success",
        "data": {
            "total": total,
            "by_severity": severity_stats,
            "by_status": status_stats,
        },
    }

"""Asset management API routes."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import List, Optional
import ipaddress

from app.core.database import get_db
from app.models import Asset, Service
from app.schemas.asset import (
    AssetCreate,
    AssetUpdate,
    AssetResponse,
    AssetBatchImportRequest,
)
from app.api.deps import get_current_user

router = APIRouter(prefix="/assets", tags=["assets"])


def parse_ip_range(ip_str: str) -> List[str]:
    """Parse IP address or CIDR notation and return list of IPs."""
    try:
        # Try to parse as CIDR notation
        if "/" in ip_str:
            network = ipaddress.ip_network(ip_str, strict=False)
            return [str(ip) for ip in network.hosts()]
        else:
            # Single IP
            ipaddress.ip_address(ip_str)
            return [ip_str]
    except ValueError:
        raise ValueError(f"Invalid IP or CIDR notation: {ip_str}")


@router.post("", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
async def create_asset(
    asset_in: AssetCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new asset."""
    # Check if asset already exists
    result = await db.execute(select(Asset).where(Asset.ip == asset_in.ip))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Asset with IP {asset_in.ip} already exists",
        )

    db_asset = Asset(**asset_in.dict())
    db.add(db_asset)
    await db.commit()
    await db.refresh(db_asset)

    return db_asset


@router.get("", response_model=dict)
async def list_assets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    ip: Optional[str] = Query(None),
    hostname: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    environment: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get paginated list of assets with filters."""
    query = select(Asset)

    # Apply filters
    filters = []
    if ip:
        filters.append(Asset.ip.ilike(f"%{ip}%"))
    if hostname:
        filters.append(Asset.hostname.ilike(f"%{hostname}%"))
    if status:
        filters.append(Asset.status == status)
    if department:
        filters.append(Asset.department == department)
    if environment:
        filters.append(Asset.environment == environment)

    if filters:
        query = query.where(or_(*filters))

    # Get total count
    count_result = await db.execute(select(func.count(Asset.id)).select_from(Asset).where(or_(*filters) if filters else True))
    total = count_result.scalar()

    # Apply pagination
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    assets = result.scalars().all()

    return {
        "code": 0,
        "message": "success",
        "data": {
            "items": [AssetResponse.from_orm(asset) for asset in assets],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get asset details by ID."""
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()

    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found",
        )

    return asset


@router.put("/{asset_id}", response_model=AssetResponse)
async def update_asset(
    asset_id: int,
    asset_in: AssetUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update asset information."""
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    db_asset = result.scalar_one_or_none()

    if not db_asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found",
        )

    # Update fields
    update_data = asset_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_asset, field, value)

    db.add(db_asset)
    await db.commit()
    await db.refresh(db_asset)

    return db_asset


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset(
    asset_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete an asset."""
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    db_asset = result.scalar_one_or_none()

    if not db_asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found",
        )

    await db.delete(db_asset)
    await db.commit()

    return None


@router.post("/batch-import", response_model=dict, status_code=status.HTTP_201_CREATED)
async def batch_import_assets(
    import_req: AssetBatchImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Batch import assets from list."""
    imported_count = 0
    skipped_count = 0
    errors = []

    for asset_in in import_req.assets:
        try:
            # Check if asset already exists
            result = await db.execute(select(Asset).where(Asset.ip == asset_in.ip))
            if result.scalar_one_or_none():
                skipped_count += 1
                continue

            # Parse IP range if CIDR notation
            ips = parse_ip_range(asset_in.ip)
            for ip in ips:
                db_asset = Asset(
                    ip=ip,
                    hostname=asset_in.hostname,
                    department=asset_in.department,
                    environment=asset_in.environment,
                    notes=asset_in.notes,
                )
                db.add(db_asset)
                imported_count += 1

        except ValueError as e:
            errors.append(f"Invalid IP {asset_in.ip}: {str(e)}")
            skipped_count += 1

    await db.commit()

    return {
        "code": 0,
        "message": "success",
        "data": {
            "imported": imported_count,
            "skipped": skipped_count,
            "errors": errors,
        },
    }


@router.get("/{asset_id}/services", response_model=dict)
async def get_asset_services(
    asset_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get services discovered on an asset."""
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()

    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found",
        )

    # Get services
    service_result = await db.execute(
        select(Service).where(Service.asset_id == asset_id)
    )
    services = service_result.scalars().all()

    return {
        "code": 0,
        "message": "success",
        "data": {
            "asset_id": asset_id,
            "services": services,
        },
    }

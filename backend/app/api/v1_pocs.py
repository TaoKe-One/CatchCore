"""POC management API routes."""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from typing import Optional, List
from datetime import datetime

from app.core.database import get_db
from app.models.poc import POC, POCTag
from app.models.user import User
from app.schemas.poc import (
    POCCreate,
    POCUpdate,
    POCResponse,
    POCSearchRequest,
    POCExecutionRequest,
    POCExecutionResult,
    POCBulkImportRequest,
    POCStatisticsResponse,
)
from app.api.deps import get_current_user
from app.services.poc_service import POCService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pocs", tags=["pocs"])


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_poc(
    poc_in: POCCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new POC."""
    # Validate POC content
    if not POCService.validate_poc_content(poc_in.content, poc_in.poc_type):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid POC content format",
        )

    # Create POC
    db_poc = POC(
        name=poc_in.name,
        cve_id=poc_in.cve_id,
        cvss_score=poc_in.cvss_score,
        severity=poc_in.severity,
        poc_type=poc_in.poc_type,
        description=poc_in.description,
        content=poc_in.content,
        source=poc_in.source,
        author=poc_in.author,
        reference_link=poc_in.reference_link,
        affected_product=poc_in.affected_product,
        affected_version=poc_in.affected_version,
        is_active=poc_in.is_active,
    )

    db.add(db_poc)
    await db.flush()

    # Add tags if provided
    if poc_in.tags:
        for tag_name in poc_in.tags:
            tag = POCTag(poc_id=db_poc.id, tag=tag_name)
            db.add(tag)

    await db.commit()
    await db.refresh(db_poc)

    return {
        "code": 0,
        "message": "POC created successfully",
        "data": POCResponse.from_orm(db_poc),
    }


@router.get("", response_model=dict)
async def list_pocs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = Query(None),
    cve_id: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    poc_type: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    is_active: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get paginated list of POCs with filters."""
    query = select(POC)

    # Apply filters
    filters = []

    if keyword:
        filters.append(
            or_(
                POC.name.ilike(f"%{keyword}%"),
                POC.description.ilike(f"%{keyword}%"),
                POC.cve_id.ilike(f"%{keyword}%"),
            )
        )

    if cve_id:
        filters.append(POC.cve_id == cve_id)

    if severity:
        filters.append(POC.severity == severity)

    if poc_type:
        filters.append(POC.poc_type == poc_type)

    if source:
        filters.append(POC.source == source)

    if is_active is not None:
        filters.append(POC.is_active == is_active)

    if filters:
        query = query.where(or_(*filters) if len(filters) > 1 else filters[0])

    # If tag filter is provided, join with POCTag
    if tag:
        query = query.join(POCTag).where(POCTag.tag == tag)

    # Get total count
    count_query = select(func.count(POC.id))
    if filters:
        count_query = count_query.where(or_(*filters) if len(filters) > 1 else filters[0])
    if tag:
        count_query = count_query.join(POCTag).where(POCTag.tag == tag)

    count_result = await db.execute(count_query)
    total = count_result.scalar()

    # Apply pagination and ordering
    query = query.order_by(POC.created_at.desc()).offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    pocs = result.unique().scalars().all()

    return {
        "code": 0,
        "message": "success",
        "data": {
            "items": [POCResponse.from_orm(poc) for poc in pocs],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


@router.get("/{poc_id}", response_model=dict)
async def get_poc(
    poc_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get POC details by ID."""
    result = await db.execute(select(POC).where(POC.id == poc_id))
    poc = result.scalar_one_or_none()

    if not poc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="POC not found",
        )

    return {
        "code": 0,
        "message": "success",
        "data": POCResponse.from_orm(poc),
    }


@router.put("/{poc_id}", response_model=dict)
async def update_poc(
    poc_id: int,
    poc_in: POCUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update POC information."""
    result = await db.execute(select(POC).where(POC.id == poc_id))
    db_poc = result.scalar_one_or_none()

    if not db_poc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="POC not found",
        )

    # Update fields
    update_data = poc_in.dict(exclude_unset=True, exclude={"tags"})
    for field, value in update_data.items():
        if value is not None:
            setattr(db_poc, field, value)

    # Update tags if provided
    if poc_in.tags is not None:
        # Remove old tags
        await db.execute(
            select(POCTag).where(POCTag.poc_id == poc_id).delete()
        )

        # Add new tags
        for tag_name in poc_in.tags:
            tag = POCTag(poc_id=poc_id, tag=tag_name)
            db.add(tag)

    db_poc.updated_at = datetime.utcnow()
    db.add(db_poc)
    await db.commit()
    await db.refresh(db_poc)

    return {
        "code": 0,
        "message": "POC updated successfully",
        "data": POCResponse.from_orm(db_poc),
    }


@router.delete("/{poc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_poc(
    poc_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a POC."""
    result = await db.execute(select(POC).where(POC.id == poc_id))
    db_poc = result.scalar_one_or_none()

    if not db_poc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="POC not found",
        )

    await db.delete(db_poc)
    await db.commit()

    return None


@router.post("/{poc_id}/execute", response_model=dict)
async def execute_poc(
    poc_id: int,
    execution_in: POCExecutionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Execute a POC against a target."""
    result = await db.execute(select(POC).where(POC.id == poc_id))
    db_poc = result.scalar_one_or_none()

    if not db_poc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="POC not found",
        )

    if db_poc.is_active == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="POC is not active",
        )

    try:
        # Execute POC
        exec_result = await POCService.execute_poc(
            target=execution_in.target,
            port=execution_in.port,
            poc_content=db_poc.content,
            poc_type=db_poc.poc_type,
            options=execution_in.options,
        )

        return {
            "code": 0,
            "message": "POC executed successfully",
            "data": POCExecutionResult(
                poc_id=poc_id,
                target=execution_in.target,
                port=execution_in.port,
                vulnerable=exec_result["vulnerable"],
                output=exec_result["output"],
                error=exec_result["error"],
                execution_time=exec_result["execution_time"],
            ),
        }

    except Exception as e:
        logger.error(f"Error executing POC {poc_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute POC",
        )


@router.post("/bulk-import", response_model=dict, status_code=status.HTTP_201_CREATED)
async def bulk_import_pocs(
    import_in: POCBulkImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Bulk import POCs from various sources."""
    imported = 0
    failed = 0
    errors = []

    for poc_in in import_in.pocs:
        try:
            # Validate content
            if not POCService.validate_poc_content(poc_in.content, poc_in.poc_type):
                failed += 1
                errors.append(f"Invalid content for POC: {poc_in.name}")
                continue

            # Create POC
            db_poc = POC(
                name=poc_in.name,
                cve_id=poc_in.cve_id,
                cvss_score=poc_in.cvss_score,
                severity=poc_in.severity,
                poc_type=poc_in.poc_type,
                description=poc_in.description,
                content=poc_in.content,
                source=import_in.source,
                author=poc_in.author,
                reference_link=poc_in.reference_link,
                affected_product=poc_in.affected_product,
                affected_version=poc_in.affected_version,
                is_active=poc_in.is_active,
            )

            db.add(db_poc)
            await db.flush()

            # Add tags
            if poc_in.tags:
                for tag_name in poc_in.tags:
                    tag = POCTag(poc_id=db_poc.id, tag=tag_name)
                    db.add(tag)

            imported += 1

        except Exception as e:
            failed += 1
            errors.append(f"Error importing {poc_in.name}: {str(e)}")
            logger.error(f"Error importing POC: {e}")

    await db.commit()

    return {
        "code": 0,
        "message": "Bulk import completed",
        "data": {
            "imported": imported,
            "failed": failed,
            "errors": errors,
        },
    }


@router.get("/statistics", response_model=dict)
async def get_poc_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get POC statistics."""
    result = await db.execute(select(POC))
    pocs = result.scalars().all()

    # Convert to dict for statistics calculation
    poc_dicts = [
        {
            "name": poc.name,
            "severity": poc.severity,
            "poc_type": poc.poc_type,
            "source": poc.source,
            "cve_id": poc.cve_id,
            "tags": [{"tag": tag.tag} for tag in poc.tags],
        }
        for poc in pocs
    ]

    stats = POCService.get_poc_statistics(poc_dicts)

    return {
        "code": 0,
        "message": "success",
        "data": stats,
    }


@router.post("/upload", response_model=dict, status_code=status.HTTP_201_CREATED)
async def upload_poc(
    file: UploadFile = File(...),
    poc_type: str = Query("nuclei"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload and import POC from file."""
    try:
        content = await file.read()
        content_str = content.decode('utf-8')

        # Validate content
        if not POCService.validate_poc_content(content_str, poc_type):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid POC file format",
            )

        # Parse metadata
        metadata = POCService.parse_poc_metadata(content_str, poc_type)

        # Create POC
        db_poc = POC(
            name=metadata.get("name") or file.filename or "Imported POC",
            description=metadata.get("description"),
            severity=metadata.get("severity"),
            poc_type=poc_type,
            content=content_str,
            source="uploaded",
            cve_id=metadata.get("cve_ids")[0] if metadata.get("cve_ids") else None,
        )

        db.add(db_poc)
        await db.flush()

        # Add CVE tags if available
        if metadata.get("cve_ids"):
            for cve_id in metadata["cve_ids"]:
                tag = POCTag(poc_id=db_poc.id, tag=f"cve:{cve_id}")
                db.add(tag)

        await db.commit()
        await db.refresh(db_poc)

        return {
            "code": 0,
            "message": "POC uploaded successfully",
            "data": POCResponse.from_orm(db_poc),
        }

    except Exception as e:
        logger.error(f"Error uploading POC: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload POC",
        )


@router.post("/{poc_id}/clone", response_model=dict, status_code=status.HTTP_201_CREATED)
async def clone_poc(
    poc_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Clone an existing POC."""
    result = await db.execute(select(POC).where(POC.id == poc_id))
    original_poc = result.scalar_one_or_none()

    if not original_poc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="POC not found",
        )

    # Create cloned POC
    cloned_poc = POC(
        name=f"{original_poc.name} (Copy)",
        cve_id=original_poc.cve_id,
        cvss_score=original_poc.cvss_score,
        severity=original_poc.severity,
        poc_type=original_poc.poc_type,
        description=original_poc.description,
        content=original_poc.content,
        source=original_poc.source,
        author=original_poc.author,
        reference_link=original_poc.reference_link,
        affected_product=original_poc.affected_product,
        affected_version=original_poc.affected_version,
        is_active=original_poc.is_active,
    )

    db.add(cloned_poc)
    await db.flush()

    # Clone tags
    for tag in original_poc.tags:
        cloned_tag = POCTag(poc_id=cloned_poc.id, tag=tag.tag)
        db.add(cloned_tag)

    await db.commit()
    await db.refresh(cloned_poc)

    return {
        "code": 0,
        "message": "POC cloned successfully",
        "data": POCResponse.from_orm(cloned_poc),
    }

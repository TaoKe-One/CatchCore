"""Task management API routes."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import Optional
from datetime import datetime
import logging

from app.core.database import get_db
from app.models import Task, TaskConfig, TaskLog, User
from app.models.task import TaskStatusEnum, TaskTypeEnum
from app.schemas.task import TaskCreate, TaskResponse, TaskProgressUpdate
from app.api.deps import get_current_user
from app.celery_app import celery_app
from app.services.scan_service import port_scan_task, service_identify_task, fingerprint_task, full_scan_task

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_in: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new scanning task."""
    # Validate task type
    try:
        TaskTypeEnum(task_in.task_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid task type: {task_in.task_type}",
        )

    # Create task
    db_task = Task(
        name=task_in.name,
        task_type=task_in.task_type,
        target_range=task_in.target_range,
        description=task_in.description,
        priority=task_in.priority or 5,
        created_by=current_user.id,
    )

    db.add(db_task)
    await db.flush()

    # Add task configurations
    if task_in.configs:
        for key, value in task_in.configs.items():
            config = TaskConfig(task_id=db_task.id, config_key=key, config_value=value)
            db.add(config)

    await db.commit()
    await db.refresh(db_task)

    return {
        "code": 0,
        "message": "success",
        "data": TaskResponse.from_orm(db_task),
    }


@router.get("", response_model=dict)
async def list_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    task_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get paginated list of tasks with filters."""
    query = select(Task)

    # Apply filters
    filters = []
    if status:
        filters.append(Task.status == status)
    if task_type:
        filters.append(Task.task_type == task_type)

    if filters:
        query = query.where(or_(*filters))

    # Get total count
    count_query = select(func.count(Task.id))
    if filters:
        count_query = count_query.where(or_(*filters))
    count_result = await db.execute(count_query)
    total = count_result.scalar()

    # Apply pagination and ordering
    query = query.order_by(Task.created_at.desc()).offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    tasks = result.scalars().all()

    return {
        "code": 0,
        "message": "success",
        "data": {
            "items": [TaskResponse.from_orm(task) for task in tasks],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


@router.get("/{task_id}", response_model=dict)
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get task details by ID."""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    return {
        "code": 0,
        "message": "success",
        "data": TaskResponse.from_orm(task),
    }


@router.put("/{task_id}", response_model=dict)
async def update_task(
    task_id: int,
    task_in: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update task information."""
    result = await db.execute(select(Task).where(Task.id == task_id))
    db_task = result.scalar_one_or_none()

    if not db_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # Update fields
    db_task.name = task_in.name
    db_task.task_type = task_in.task_type
    db_task.target_range = task_in.target_range
    db_task.description = task_in.description
    if task_in.priority:
        db_task.priority = task_in.priority

    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)

    return {
        "code": 0,
        "message": "success",
        "data": TaskResponse.from_orm(db_task),
    }


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a task."""
    result = await db.execute(select(Task).where(Task.id == task_id))
    db_task = result.scalar_one_or_none()

    if not db_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    await db.delete(db_task)
    await db.commit()

    return None


@router.post("/{task_id}/start", response_model=dict)
async def start_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Start a scanning task (submits to Celery for async execution)."""
    result = await db.execute(select(Task).where(Task.id == task_id))
    db_task = result.scalar_one_or_none()

    if not db_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    if db_task.status != TaskStatusEnum.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Task cannot be started from {db_task.status} status",
        )

    # Update task status
    db_task.status = TaskStatusEnum.RUNNING
    db_task.started_at = datetime.utcnow()
    db_task.progress = 0

    # Add log entry
    log_entry = TaskLog(
        task_id=task_id,
        level="INFO",
        message="Task started - queued for execution",
    )
    db.add(log_entry)
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)

    # Submit to Celery based on task type
    try:
        celery_task = None

        if db_task.task_type == TaskTypeEnum.PORT_SCAN:
            celery_task = port_scan_task.delay(task_id, db_task.target_range)
            logger.info(f"Submitted port_scan task {task_id} to Celery: {celery_task.id}")

        elif db_task.task_type == TaskTypeEnum.SERVICE_IDENTIFY:
            celery_task = service_identify_task.delay(task_id, db_task.id, [])
            logger.info(f"Submitted service_identify task {task_id} to Celery: {celery_task.id}")

        elif db_task.task_type == TaskTypeEnum.FINGERPRINT:
            celery_task = fingerprint_task.delay(task_id, db_task.id, {})
            logger.info(f"Submitted fingerprint task {task_id} to Celery: {celery_task.id}")

        else:
            # Full scan or custom task type
            celery_task = full_scan_task.delay(task_id, db_task.target_range, str(db_task.task_type))
            logger.info(f"Submitted full_scan task {task_id} to Celery: {celery_task.id}")

        # Store Celery task ID
        if celery_task:
            config = TaskConfig(task_id=task_id, config_key="celery_task_id", config_value=celery_task.id)
            db.add(config)
            await db.commit()

    except Exception as e:
        logger.error(f"Failed to submit task {task_id} to Celery: {e}")
        # Update task status to failed
        db_task.status = TaskStatusEnum.FAILED
        error_log = TaskLog(
            task_id=task_id,
            level="ERROR",
            message=f"Failed to submit task to job queue: {str(e)}",
        )
        db.add(error_log)
        db.add(db_task)
        await db.commit()
        await db.refresh(db_task)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit task for execution",
        )

    return {
        "code": 0,
        "message": "Task submitted successfully",
        "data": TaskResponse.from_orm(db_task),
    }


@router.post("/{task_id}/pause", response_model=dict)
async def pause_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Pause a running task."""
    result = await db.execute(select(Task).where(Task.id == task_id))
    db_task = result.scalar_one_or_none()

    if not db_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    if db_task.status != TaskStatusEnum.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only running tasks can be paused",
        )

    db_task.status = TaskStatusEnum.PAUSED

    log_entry = TaskLog(
        task_id=task_id,
        level="INFO",
        message="Task paused",
    )
    db.add(log_entry)
    db.add(db_task)
    await db.commit()

    return {
        "code": 0,
        "message": "success",
        "data": TaskResponse.from_orm(db_task),
    }


@router.post("/{task_id}/resume", response_model=dict)
async def resume_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Resume a paused task."""
    result = await db.execute(select(Task).where(Task.id == task_id))
    db_task = result.scalar_one_or_none()

    if not db_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    if db_task.status != TaskStatusEnum.PAUSED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only paused tasks can be resumed",
        )

    db_task.status = TaskStatusEnum.RUNNING

    log_entry = TaskLog(
        task_id=task_id,
        level="INFO",
        message="Task resumed",
    )
    db.add(log_entry)
    db.add(db_task)
    await db.commit()

    return {
        "code": 0,
        "message": "success",
        "data": TaskResponse.from_orm(db_task),
    }


@router.post("/{task_id}/cancel", response_model=dict)
async def cancel_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cancel a task."""
    result = await db.execute(select(Task).where(Task.id == task_id))
    db_task = result.scalar_one_or_none()

    if not db_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    if db_task.status in [TaskStatusEnum.COMPLETED, TaskStatusEnum.CANCELLED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Task cannot be cancelled from {db_task.status} status",
        )

    db_task.status = TaskStatusEnum.CANCELLED
    db_task.finished_at = datetime.utcnow()

    log_entry = TaskLog(
        task_id=task_id,
        level="INFO",
        message="Task cancelled",
    )
    db.add(log_entry)
    db.add(db_task)
    await db.commit()

    return {
        "code": 0,
        "message": "success",
        "data": TaskResponse.from_orm(db_task),
    }


@router.get("/{task_id}/logs", response_model=dict)
async def get_task_logs(
    task_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get task execution logs."""
    result = await db.execute(select(Task).where(Task.id == task_id))
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # Get total count
    count_result = await db.execute(
        select(func.count(TaskLog.id)).where(TaskLog.task_id == task_id)
    )
    total = count_result.scalar()

    # Get logs
    log_result = await db.execute(
        select(TaskLog)
        .where(TaskLog.task_id == task_id)
        .order_by(TaskLog.timestamp.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    logs = log_result.scalars().all()

    return {
        "code": 0,
        "message": "success",
        "data": {
            "task_id": task_id,
            "logs": logs,
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }

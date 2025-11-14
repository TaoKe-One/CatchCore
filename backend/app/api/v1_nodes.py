"""Node management API routes."""

import logging
from typing import List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.node import Node
from app.models.user import User
from app.schemas.node import (
    NodeCreate,
    NodeUpdate,
    NodeResponse,
    NodeHealthResponse,
    NodeListResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/nodes", tags=["nodes"])


@router.post("/register", response_model=NodeResponse, status_code=status.HTTP_201_CREATED)
async def register_node(
    node_data: NodeCreate,
    db: AsyncSession = Depends(get_db),
) -> NodeResponse:
    """Register a new scanning node."""
    try:
        # Check if node already exists
        result = await db.execute(select(Node).where(Node.name == node_data.name))
        existing_node = result.scalar_one_or_none()

        if existing_node:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Node with name '{node_data.name}' already exists",
            )

        # Create new node
        new_node = Node(
            name=node_data.name,
            host=node_data.host,
            port=node_data.port,
            node_type=node_data.node_type,
            status="offline",  # Will be "online" after first heartbeat
            max_concurrent_tasks=node_data.max_concurrent_tasks,
            api_version=node_data.api_version,
        )

        db.add(new_node)
        await db.commit()
        await db.refresh(new_node)

        logger.info(f"Node registered: {new_node.name} ({new_node.host}:{new_node.port})")

        return NodeResponse.from_orm(new_node)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error registering node: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register node",
        )


@router.get("", response_model=NodeListResponse)
async def list_nodes(
    status_filter: Optional[str] = None,
    node_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NodeListResponse:
    """List all nodes with optional filtering."""
    try:
        # Build query
        query = select(Node)

        if status_filter:
            query = query.where(Node.status == status_filter)

        if node_type:
            query = query.where(Node.node_type == node_type)

        # Get total count
        count_result = await db.execute(select(Node))
        total = len(count_result.fetchall())

        # Get paginated results
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        nodes = result.scalars().all()

        return NodeListResponse(
            total=total,
            skip=skip,
            limit=limit,
            nodes=[NodeResponse.from_orm(node) for node in nodes],
        )

    except Exception as e:
        logger.error(f"Error listing nodes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list nodes",
        )


@router.get("/{node_id}", response_model=NodeResponse)
async def get_node(
    node_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NodeResponse:
    """Get node details by ID."""
    try:
        result = await db.execute(select(Node).where(Node.id == node_id))
        node = result.scalar_one_or_none()

        if not node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Node with ID {node_id} not found",
            )

        return NodeResponse.from_orm(node)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting node: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get node",
        )


@router.get("/{node_id}/health", response_model=NodeHealthResponse)
async def check_node_health(
    node_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NodeHealthResponse:
    """Check node health status."""
    try:
        result = await db.execute(select(Node).where(Node.id == node_id))
        node = result.scalar_one_or_none()

        if not node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Node with ID {node_id} not found",
            )

        # Determine if node is healthy
        is_healthy = False
        if node.status == "online":
            # Check if last heartbeat is recent (within 120 seconds)
            if node.last_heartbeat:
                time_since_heartbeat = datetime.utcnow() - node.last_heartbeat
                is_healthy = time_since_heartbeat <= timedelta(seconds=120)
            else:
                is_healthy = False

        return NodeHealthResponse(
            id=node.id,
            name=node.name,
            status=node.status,
            last_heartbeat=node.last_heartbeat,
            cpu_usage=node.cpu_usage,
            memory_usage=node.memory_usage,
            disk_usage=node.disk_usage,
            current_tasks=node.current_tasks,
            is_healthy=is_healthy,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking node health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check node health",
        )


@router.put("/{node_id}", response_model=NodeResponse)
async def update_node(
    node_id: int,
    node_data: NodeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NodeResponse:
    """Update node configuration."""
    try:
        result = await db.execute(select(Node).where(Node.id == node_id))
        node = result.scalar_one_or_none()

        if not node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Node with ID {node_id} not found",
            )

        # Update fields if provided
        if node_data.max_concurrent_tasks is not None:
            node.max_concurrent_tasks = node_data.max_concurrent_tasks
        if node_data.status is not None:
            node.status = node_data.status
        if node_data.api_version is not None:
            node.api_version = node_data.api_version

        node.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(node)

        logger.info(f"Node updated: {node.name}")

        return NodeResponse.from_orm(node)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating node: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update node",
        )


@router.post("/{node_id}/heartbeat")
async def node_heartbeat(
    node_id: int,
    heartbeat_data: dict,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update node heartbeat and resource metrics."""
    try:
        result = await db.execute(select(Node).where(Node.id == node_id))
        node = result.scalar_one_or_none()

        if not node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Node with ID {node_id} not found",
            )

        # Update node metrics
        node.status = heartbeat_data.get("status", "online")
        node.cpu_usage = heartbeat_data.get("cpu_usage", 0.0)
        node.memory_usage = heartbeat_data.get("memory_usage", 0.0)
        node.disk_usage = heartbeat_data.get("disk_usage", 0.0)
        node.current_tasks = heartbeat_data.get("current_tasks", 0)
        node.last_heartbeat = datetime.utcnow()
        node.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(node)

        return {
            "status": "ok",
            "node_id": node.id,
            "message": "Heartbeat received",
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error processing heartbeat: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process heartbeat",
        )


@router.delete("/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_node(
    node_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a node."""
    try:
        result = await db.execute(select(Node).where(Node.id == node_id))
        node = result.scalar_one_or_none()

        if not node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Node with ID {node_id} not found",
            )

        # Check if node has active tasks
        if node.current_tasks > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Node has {node.current_tasks} active tasks. Cannot delete.",
            )

        await db.delete(node)
        await db.commit()

        logger.info(f"Node deleted: {node.name}")

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting node: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete node",
        )


@router.get("/stats/summary")
async def get_nodes_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Get summary statistics of all nodes."""
    try:
        # Get all nodes
        result = await db.execute(select(Node))
        nodes = result.scalars().all()

        total_nodes = len(nodes)
        online_nodes = sum(1 for n in nodes if n.status == "online")
        offline_nodes = sum(1 for n in nodes if n.status == "offline")
        maintenance_nodes = sum(1 for n in nodes if n.status == "maintenance")

        total_capacity = sum(n.max_concurrent_tasks for n in nodes)
        current_tasks = sum(n.current_tasks for n in nodes)
        available_capacity = total_capacity - current_tasks

        avg_cpu = sum(n.cpu_usage for n in nodes) / total_nodes if total_nodes > 0 else 0
        avg_memory = sum(n.memory_usage for n in nodes) / total_nodes if total_nodes > 0 else 0
        avg_disk = sum(n.disk_usage for n in nodes) / total_nodes if total_nodes > 0 else 0

        return {
            "total_nodes": total_nodes,
            "online_nodes": online_nodes,
            "offline_nodes": offline_nodes,
            "maintenance_nodes": maintenance_nodes,
            "total_capacity": total_capacity,
            "current_tasks": current_tasks,
            "available_capacity": available_capacity,
            "capacity_usage_percent": (current_tasks / total_capacity * 100) if total_capacity > 0 else 0,
            "average_metrics": {
                "cpu_usage": round(avg_cpu, 2),
                "memory_usage": round(avg_memory, 2),
                "disk_usage": round(avg_disk, 2),
            },
            "nodes_by_type": {
                "scanner": sum(1 for n in nodes if n.node_type == "scanner"),
                "worker": sum(1 for n in nodes if n.node_type == "worker"),
                "coordinator": sum(1 for n in nodes if n.node_type == "coordinator"),
            },
        }

    except Exception as e:
        logger.error(f"Error getting nodes summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get nodes summary",
        )

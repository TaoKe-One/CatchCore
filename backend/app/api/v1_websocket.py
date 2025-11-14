"""WebSocket endpoints for real-time task updates."""

import logging
import json
import asyncio
from typing import Set, Dict, Any
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.task import Task, TaskLog
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])

# Track active connections per task
active_connections: Dict[int, Set[WebSocket]] = {}


class ConnectionManager:
    """Manages WebSocket connections and broadcasting."""

    def __init__(self):
        """Initialize connection manager."""
        self.active_connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, task_id: int, websocket: WebSocket):
        """
        Accept and register a new WebSocket connection.

        Args:
            task_id: Task ID for the connection
            websocket: WebSocket connection object
        """
        await websocket.accept()

        if task_id not in self.active_connections:
            self.active_connections[task_id] = set()

        self.active_connections[task_id].add(websocket)
        logger.info(f"Client connected to task {task_id}. Active: {len(self.active_connections[task_id])}")

    def disconnect(self, task_id: int, websocket: WebSocket):
        """
        Unregister and disconnect a WebSocket connection.

        Args:
            task_id: Task ID
            websocket: WebSocket connection object
        """
        if task_id in self.active_connections:
            self.active_connections[task_id].discard(websocket)
            if not self.active_connections[task_id]:
                del self.active_connections[task_id]
            logger.info(f"Client disconnected from task {task_id}")

    async def broadcast(self, task_id: int, message: Dict[str, Any]):
        """
        Broadcast message to all connections for a task.

        Args:
            task_id: Task ID
            message: Message dictionary to send
        """
        if task_id not in self.active_connections:
            return

        disconnected = set()
        for connection in self.active_connections[task_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Error sending message to connection: {e}")
                disconnected.add(connection)

        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(task_id, connection)

    async def send_personal(self, websocket: WebSocket, message: Dict[str, Any]):
        """
        Send message to a specific connection.

        Args:
            websocket: WebSocket connection
            message: Message dictionary to send
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.warning(f"Error sending personal message: {e}")

    def get_connection_count(self, task_id: int) -> int:
        """Get number of active connections for a task."""
        return len(self.active_connections.get(task_id, set()))


manager = ConnectionManager()


async def get_task_logs(task_id: int, db: AsyncSession, limit: int = 50) -> list:
    """
    Get recent task logs.

    Args:
        task_id: Task ID
        db: Database session
        limit: Maximum number of logs to return

    Returns:
        List of log dictionaries
    """
    try:
        result = await db.execute(
            select(TaskLog)
            .where(TaskLog.task_id == task_id)
            .order_by(TaskLog.timestamp.desc())
            .limit(limit)
        )
        logs = result.scalars().all()
        return [
            {
                "timestamp": log.timestamp.isoformat(),
                "level": log.level,
                "message": log.message,
            }
            for log in reversed(logs)  # Reverse to get chronological order
        ]
    except Exception as e:
        logger.error(f"Error fetching task logs: {e}")
        return []


async def get_task_status(task_id: int, db: AsyncSession) -> Dict[str, Any]:
    """
    Get current task status.

    Args:
        task_id: Task ID
        db: Database session

    Returns:
        Task status dictionary
    """
    try:
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()

        if not task:
            return {"error": "Task not found"}

        return {
            "task_id": task.id,
            "name": task.name,
            "status": task.status,
            "progress": task.progress,
            "current_step": task.current_step,
            "total_steps": task.total_steps,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        }
    except Exception as e:
        logger.error(f"Error fetching task status: {e}")
        return {"error": str(e)}


@router.websocket("/task/{task_id}")
async def websocket_task_endpoint(
    websocket: WebSocket,
    task_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    WebSocket endpoint for real-time task updates.

    Clients can connect to `/api/v1/ws/task/{task_id}` to receive:
    - Task progress updates
    - Task logs in real-time
    - Task completion notifications
    - Error messages

    Message types:
    - "status": Current task status
    - "progress": Progress update (0-100%)
    - "log": Task execution log
    - "result": Task result data
    - "error": Error message
    - "complete": Task completion notification
    """
    await manager.connect(task_id, websocket)

    try:
        # Send initial status
        status = await get_task_status(task_id, db)
        await manager.send_personal(
            websocket,
            {
                "type": "status",
                "timestamp": datetime.utcnow().isoformat(),
                "data": status,
            },
        )

        # Send recent logs
        logs = await get_task_logs(task_id, db, limit=50)
        await manager.send_personal(
            websocket,
            {
                "type": "logs",
                "timestamp": datetime.utcnow().isoformat(),
                "data": logs,
            },
        )

        # Listen for client messages and send updates
        while True:
            # Receive message from client (keep connection alive)
            data = await websocket.receive_text()

            if data == "ping":
                # Health check
                await manager.send_personal(
                    websocket,
                    {
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )
            elif data == "status":
                # Client requests status update
                status = await get_task_status(task_id, db)
                await manager.send_personal(
                    websocket,
                    {
                        "type": "status",
                        "timestamp": datetime.utcnow().isoformat(),
                        "data": status,
                    },
                )
            elif data == "logs":
                # Client requests recent logs
                logs = await get_task_logs(task_id, db)
                await manager.send_personal(
                    websocket,
                    {
                        "type": "logs",
                        "timestamp": datetime.utcnow().isoformat(),
                        "data": logs,
                    },
                )
            else:
                # Try to parse as JSON command
                try:
                    command = json.loads(data)
                    # Handle custom commands here
                    logger.debug(f"Received command: {command}")
                except json.JSONDecodeError:
                    logger.warning(f"Invalid message format: {data}")

    except WebSocketDisconnect:
        manager.disconnect(task_id, websocket)
        logger.info(f"WebSocket disconnected for task {task_id}")

    except Exception as e:
        logger.error(f"WebSocket error for task {task_id}: {e}")
        manager.disconnect(task_id, websocket)


async def push_task_update(
    task_id: int,
    message_type: str,
    data: Any,
    db: AsyncSession = None,
):
    """
    Push an update to all clients connected to a task.

    Args:
        task_id: Task ID
        message_type: Type of message (status, progress, log, result, error, complete)
        data: Data to send
        db: Optional database session
    """
    message = {
        "type": message_type,
        "timestamp": datetime.utcnow().isoformat(),
        "data": data,
    }

    await manager.broadcast(task_id, message)
    logger.debug(f"Pushed {message_type} update to task {task_id}")


async def push_task_log(
    task_id: int,
    level: str,
    message: str,
    db: AsyncSession = None,
):
    """
    Push a log message to all clients connected to a task.

    Args:
        task_id: Task ID
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        message: Log message
        db: Optional database session
    """
    log_data = {
        "level": level,
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
    }

    await push_task_update(task_id, "log", log_data, db)


async def push_task_progress(
    task_id: int,
    progress: int,
    step: str = None,
    db: AsyncSession = None,
):
    """
    Push a progress update to all clients connected to a task.

    Args:
        task_id: Task ID
        progress: Progress percentage (0-100)
        step: Current step description
        db: Optional database session
    """
    progress_data = {
        "progress": min(max(progress, 0), 100),
        "step": step,
    }

    await push_task_update(task_id, "progress", progress_data, db)


async def push_task_result(
    task_id: int,
    results: Any,
    db: AsyncSession = None,
):
    """
    Push task results to all clients.

    Args:
        task_id: Task ID
        results: Result data
        db: Optional database session
    """
    await push_task_update(task_id, "result", results, db)


async def push_task_error(
    task_id: int,
    error: str,
    db: AsyncSession = None,
):
    """
    Push an error message to all clients.

    Args:
        task_id: Task ID
        error: Error message
        db: Optional database session
    """
    await push_task_update(task_id, "error", {"error": error}, db)


async def push_task_completion(
    task_id: int,
    status: str = "completed",
    db: AsyncSession = None,
):
    """
    Push task completion notification to all clients.

    Args:
        task_id: Task ID
        status: Final task status (completed, failed, cancelled)
        db: Optional database session
    """
    await push_task_update(
        task_id,
        "complete",
        {"status": status, "timestamp": datetime.utcnow().isoformat()},
        db,
    )

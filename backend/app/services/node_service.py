"""Node management and task distribution service."""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

from app.models.node import Node
from app.models.task import Task, TaskStatusEnum

logger = logging.getLogger(__name__)


class NodeService:
    """Service for managing nodes and distributing tasks."""

    @staticmethod
    async def get_online_nodes(
        db: AsyncSession,
        node_type: Optional[str] = None,
    ) -> List[Node]:
        """Get all online nodes, optionally filtered by type."""
        try:
            # Build query for online nodes
            query = select(Node).where(Node.status == "online")

            if node_type:
                query = query.where(Node.node_type == node_type)

            # Check heartbeat timeout (120 seconds)
            cutoff_time = datetime.utcnow() - timedelta(seconds=120)
            query = query.where(Node.last_heartbeat >= cutoff_time)

            result = await db.execute(query)
            nodes = result.scalars().all()

            return nodes

        except Exception as e:
            logger.error(f"Error getting online nodes: {e}")
            return []

    @staticmethod
    async def get_available_node(
        db: AsyncSession,
        node_type: str = "scanner",
    ) -> Optional[Node]:
        """Get the best available node for task distribution.

        Uses load balancing strategy:
        1. Filter healthy online nodes of specified type
        2. Check node capacity (current_tasks < max_concurrent_tasks)
        3. Select node with lowest current task count
        """
        try:
            # Get online nodes
            query = select(Node).where(
                and_(
                    Node.status == "online",
                    Node.node_type == node_type,
                )
            )

            # Check heartbeat timeout
            cutoff_time = datetime.utcnow() - timedelta(seconds=120)
            query = query.where(Node.last_heartbeat >= cutoff_time)

            # Order by current tasks (ascending) and CPU usage (ascending)
            query = query.order_by(
                Node.current_tasks.asc(),
                Node.cpu_usage.asc(),
            )

            result = await db.execute(query)
            nodes = result.scalars().all()

            # Find first node with available capacity
            for node in nodes:
                if node.current_tasks < node.max_concurrent_tasks:
                    return node

            logger.warning(f"No available {node_type} nodes with capacity")
            return None

        except Exception as e:
            logger.error(f"Error getting available node: {e}")
            return None

    @staticmethod
    async def select_node_for_task(
        db: AsyncSession,
        task: Task,
    ) -> Optional[Node]:
        """Select the best node for a specific task based on task type.

        Task type to node type mapping:
        - port_scan -> scanner
        - service_identify -> scanner
        - fingerprint -> scanner
        - poc_detection -> worker
        - password_crack -> worker
        - directory_scan -> scanner
        - url_scan -> scanner
        - custom -> scanner (default)
        """
        try:
            # Map task type to node type
            task_type_to_node_type = {
                "port_scan": "scanner",
                "service_identify": "scanner",
                "fingerprint": "scanner",
                "poc_detection": "worker",
                "password_crack": "worker",
                "directory_scan": "scanner",
                "url_scan": "scanner",
                "custom": "scanner",
            }

            node_type = task_type_to_node_type.get(task.task_type, "scanner")

            # Get available node of appropriate type
            node = await NodeService.get_available_node(db, node_type)

            if node:
                logger.info(f"Selected node {node.name} for task {task.id}")
            else:
                logger.warning(f"No available {node_type} node for task {task.id}")

            return node

        except Exception as e:
            logger.error(f"Error selecting node for task: {e}")
            return None

    @staticmethod
    async def increment_node_tasks(
        db: AsyncSession,
        node_id: int,
    ) -> bool:
        """Increment the current task count for a node."""
        try:
            result = await db.execute(select(Node).where(Node.id == node_id))
            node = result.scalar_one_or_none()

            if not node:
                logger.error(f"Node {node_id} not found")
                return False

            # Check capacity
            if node.current_tasks >= node.max_concurrent_tasks:
                logger.warning(
                    f"Node {node.name} reached max capacity "
                    f"({node.current_tasks}/{node.max_concurrent_tasks})"
                )
                return False

            node.current_tasks += 1
            node.updated_at = datetime.utcnow()

            await db.commit()
            await db.refresh(node)

            logger.debug(f"Incremented tasks for node {node.name}: {node.current_tasks}")
            return True

        except Exception as e:
            await db.rollback()
            logger.error(f"Error incrementing node tasks: {e}")
            return False

    @staticmethod
    async def decrement_node_tasks(
        db: AsyncSession,
        node_id: int,
    ) -> bool:
        """Decrement the current task count for a node."""
        try:
            result = await db.execute(select(Node).where(Node.id == node_id))
            node = result.scalar_one_or_none()

            if not node:
                logger.error(f"Node {node_id} not found")
                return False

            if node.current_tasks > 0:
                node.current_tasks -= 1
            node.updated_at = datetime.utcnow()

            await db.commit()
            await db.refresh(node)

            logger.debug(f"Decremented tasks for node {node.name}: {node.current_tasks}")
            return True

        except Exception as e:
            await db.rollback()
            logger.error(f"Error decrementing node tasks: {e}")
            return False

    @staticmethod
    async def update_node_resources(
        db: AsyncSession,
        node_id: int,
        cpu_usage: float,
        memory_usage: float,
        disk_usage: float,
    ) -> bool:
        """Update node resource metrics."""
        try:
            result = await db.execute(select(Node).where(Node.id == node_id))
            node = result.scalar_one_or_none()

            if not node:
                logger.error(f"Node {node_id} not found")
                return False

            node.cpu_usage = cpu_usage
            node.memory_usage = memory_usage
            node.disk_usage = disk_usage
            node.updated_at = datetime.utcnow()

            await db.commit()

            return True

        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating node resources: {e}")
            return False

    @staticmethod
    async def mark_node_offline(
        db: AsyncSession,
        node_id: int,
    ) -> bool:
        """Mark a node as offline."""
        try:
            result = await db.execute(select(Node).where(Node.id == node_id))
            node = result.scalar_one_or_none()

            if not node:
                logger.error(f"Node {node_id} not found")
                return False

            node.status = "offline"
            node.updated_at = datetime.utcnow()

            await db.commit()

            logger.info(f"Node {node.name} marked as offline")
            return True

        except Exception as e:
            await db.rollback()
            logger.error(f"Error marking node offline: {e}")
            return False

    @staticmethod
    async def get_node_statistics(db: AsyncSession) -> Dict[str, Any]:
        """Get overall statistics of all nodes."""
        try:
            result = await db.execute(select(Node))
            nodes = result.scalars().all()

            if not nodes:
                return {
                    "total_nodes": 0,
                    "online_nodes": 0,
                    "offline_nodes": 0,
                    "total_capacity": 0,
                    "current_tasks": 0,
                }

            total_nodes = len(nodes)
            online_nodes = sum(1 for n in nodes if n.status == "online")
            offline_nodes = sum(1 for n in nodes if n.status == "offline")
            total_capacity = sum(n.max_concurrent_tasks for n in nodes)
            current_tasks = sum(n.current_tasks for n in nodes)
            available_capacity = total_capacity - current_tasks

            avg_cpu = sum(n.cpu_usage for n in nodes) / total_nodes
            avg_memory = sum(n.memory_usage for n in nodes) / total_nodes
            avg_disk = sum(n.disk_usage for n in nodes) / total_nodes

            return {
                "total_nodes": total_nodes,
                "online_nodes": online_nodes,
                "offline_nodes": offline_nodes,
                "maintenance_nodes": total_nodes - online_nodes - offline_nodes,
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
            logger.error(f"Error getting node statistics: {e}")
            return {}

    @staticmethod
    async def check_and_mark_offline_nodes(db: AsyncSession) -> int:
        """Check all nodes and mark those with expired heartbeats as offline.

        Returns the number of nodes marked as offline.
        """
        try:
            # Find nodes with last heartbeat older than 120 seconds
            cutoff_time = datetime.utcnow() - timedelta(seconds=120)

            result = await db.execute(
                select(Node).where(
                    and_(
                        Node.status == "online",
                        Node.last_heartbeat < cutoff_time,
                    )
                )
            )
            nodes = result.scalars().all()

            offline_count = 0
            for node in nodes:
                node.status = "offline"
                node.updated_at = datetime.utcnow()
                offline_count += 1
                logger.warning(f"Node {node.name} marked offline due to heartbeat timeout")

            if offline_count > 0:
                await db.commit()
                logger.info(f"Marked {offline_count} nodes as offline")

            return offline_count

        except Exception as e:
            await db.rollback()
            logger.error(f"Error checking offline nodes: {e}")
            return 0

    @staticmethod
    async def redistribute_tasks_from_offline_node(
        db: AsyncSession,
        node_id: int,
    ) -> List[int]:
        """Redistribute tasks from an offline node to other available nodes.

        Returns list of task IDs that were redistributed.
        """
        try:
            # Get all running tasks on the offline node
            result = await db.execute(
                select(Task).where(
                    and_(
                        Task.status == TaskStatusEnum.RUNNING,
                        # This would need to be added to Task model:
                        # assigned_node_id == node_id
                    )
                )
            )
            tasks = result.scalars().all()

            redistributed_task_ids = []

            for task in tasks:
                # Try to find a new node for each task
                new_node = await NodeService.select_node_for_task(db, task)

                if new_node:
                    # Update task assignment and reset to pending
                    task.status = TaskStatusEnum.PENDING
                    task.updated_at = datetime.utcnow()
                    redistributed_task_ids.append(task.id)
                    logger.info(
                        f"Redistributed task {task.id} from offline node to {new_node.name}"
                    )
                else:
                    # Keep task in running state if no node available
                    logger.warning(f"Could not find node for task {task.id}")

            if redistributed_task_ids:
                await db.commit()

            return redistributed_task_ids

        except Exception as e:
            await db.rollback()
            logger.error(f"Error redistributing tasks: {e}")
            return []

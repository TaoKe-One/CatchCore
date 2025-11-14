"""Scan service for managing scan tasks."""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.celery_app import celery_app
from app.core.database import get_db
from app.models.task import Task, TaskLog, TaskStatusEnum
from app.services.port_scan_service import PortScanService
from app.services.service_identify_service import ServiceIdentifyService
from app.services.fingerprint_service import FingerprintService

logger = logging.getLogger(__name__)


class ScanService:
    """Service for managing and executing scans."""

    @staticmethod
    async def get_task_progress(task_id: int, db: AsyncSession) -> Dict[str, Any]:
        """Get current task progress."""
        try:
            result = await db.execute(select(Task).where(Task.id == task_id))
            task = result.scalar_one_or_none()
            if not task:
                return {"error": "Task not found"}

            return {
                "task_id": task.id,
                "status": task.status,
                "progress": task.progress,
                "current_step": task.current_step,
                "total_steps": task.total_steps,
                "started_at": task.started_at,
                "updated_at": task.updated_at,
            }
        except Exception as e:
            logger.error(f"Error getting task progress: {e}")
            return {"error": str(e)}

    @staticmethod
    async def add_task_log(
        task_id: int,
        level: str,
        message: str,
        db: AsyncSession,
    ) -> None:
        """Add a log entry for a task."""
        try:
            log = TaskLog(
                task_id=task_id,
                level=level,
                message=message,
                timestamp=datetime.utcnow(),
            )
            db.add(log)
            await db.commit()
        except Exception as e:
            logger.error(f"Error adding task log: {e}")

    @staticmethod
    async def update_task_status(
        task_id: int,
        status: TaskStatusEnum,
        progress: int = None,
        db: AsyncSession = None,
    ) -> None:
        """Update task status in database."""
        if db is None:
            async for session in get_db():
                db = session
                break

        try:
            result = await db.execute(select(Task).where(Task.id == task_id))
            task = result.scalar_one_or_none()
            if task:
                task.status = status
                if progress is not None:
                    task.progress = min(progress, 100)
                task.updated_at = datetime.utcnow()

                if status == TaskStatusEnum.RUNNING:
                    task.started_at = datetime.utcnow()
                elif status in [TaskStatusEnum.COMPLETED, TaskStatusEnum.FAILED, TaskStatusEnum.CANCELLED]:
                    task.completed_at = datetime.utcnow()

                await db.commit()
        except Exception as e:
            logger.error(f"Error updating task status: {e}")


@celery_app.task(bind=True, name="app.services.scan_service.port_scan_task")
def port_scan_task(self, task_id: int, target: str, options: dict = None):
    """Async port scan task.

    Args:
        task_id: Database task ID
        target: Target IP or CIDR range
        options: Scan options (ports, timing, etc.)

    Returns:
        dict: Scan results
    """
    if options is None:
        options = {}

    logger.info(f"Starting port scan for task {task_id}, target {target}")

    try:
        # Update task status to running
        # (In async context, would use: await ScanService.update_task_status(...))

        self.update_state(
            state="PROGRESS",
            meta={
                "current": 0,
                "total": 100,
                "status": "Initializing port scan...",
            },
        )

        # Execute nmap scan
        logger.info(f"Executing nmap scan on {target}")
        results = PortScanService.scan_with_nmap(target, options)

        if not results:
            logger.warning(f"No results from port scan for {target}")
            return {
                "task_id": task_id,
                "status": "completed",
                "results_count": 0,
                "error": "No open ports found",
            }

        self.update_state(
            state="PROGRESS",
            meta={
                "current": 50,
                "total": 100,
                "status": f"Found {len(results)} open ports, analyzing...",
            },
        )

        logger.info(f"Port scan completed: {len(results)} ports found")

        return {
            "task_id": task_id,
            "status": "completed",
            "results_count": len(results),
            "results": results,
        }

    except Exception as e:
        logger.error(f"Error in port scan task {task_id}: {e}", exc_info=True)
        self.update_state(
            state="FAILURE",
            meta={"error": str(e)},
        )
        return {
            "task_id": task_id,
            "status": "failed",
            "error": str(e),
        }


@celery_app.task(bind=True, name="app.services.scan_service.service_identify_task")
def service_identify_task(self, task_id: int, asset_id: int, ports: List[int]):
    """Async service identification task.

    Args:
        task_id: Database task ID
        asset_id: Asset ID to scan
        ports: List of ports to identify services on

    Returns:
        dict: Service identification results
    """
    logger.info(f"Starting service identification for task {task_id}, asset {asset_id}")

    try:
        self.update_state(
            state="PROGRESS",
            meta={
                "current": 0,
                "total": 100,
                "status": f"Identifying services on {len(ports)} ports...",
            },
        )

        # Perform service identification
        services = ServiceIdentifyService.identify_services(asset_id, ports)

        self.update_state(
            state="PROGRESS",
            meta={
                "current": 75,
                "total": 100,
                "status": f"Identified {len(services)} services...",
            },
        )

        logger.info(f"Service identification completed: {len(services)} services found")

        return {
            "task_id": task_id,
            "status": "completed",
            "services_count": len(services),
            "services": services,
        }

    except Exception as e:
        logger.error(f"Error in service identify task {task_id}: {e}", exc_info=True)
        self.update_state(
            state="FAILURE",
            meta={"error": str(e)},
        )
        return {
            "task_id": task_id,
            "status": "failed",
            "error": str(e),
        }


@celery_app.task(bind=True, name="app.services.scan_service.fingerprint_task")
def fingerprint_task(self, task_id: int, asset_id: int, service_data: dict):
    """Async fingerprint matching task.

    Args:
        task_id: Database task ID
        asset_id: Asset ID
        service_data: Service information for fingerprinting

    Returns:
        dict: Fingerprint matching results
    """
    logger.info(f"Starting fingerprint matching for task {task_id}, asset {asset_id}")

    try:
        self.update_state(
            state="PROGRESS",
            meta={
                "current": 0,
                "total": 100,
                "status": "Loading fingerprint database...",
            },
        )

        # Perform fingerprint matching
        matches = FingerprintService.match_fingerprints(asset_id, service_data)

        self.update_state(
            state="PROGRESS",
            meta={
                "current": 100,
                "total": 100,
                "status": f"Matched {len(matches)} fingerprints",
            },
        )

        logger.info(f"Fingerprint matching completed: {len(matches)} matches found")

        return {
            "task_id": task_id,
            "status": "completed",
            "matches_count": len(matches),
            "matches": matches,
        }

    except Exception as e:
        logger.error(f"Error in fingerprint task {task_id}: {e}", exc_info=True)
        self.update_state(
            state="FAILURE",
            meta={"error": str(e)},
        )
        return {
            "task_id": task_id,
            "status": "failed",
            "error": str(e),
        }


@celery_app.task(bind=True, name="app.services.scan_service.full_scan_task")
def full_scan_task(self, task_id: int, target: str, scan_type: str, options: dict = None):
    """Async full scan orchestration task.

    Coordinates port scanning, service identification, and fingerprint matching.

    Args:
        task_id: Database task ID
        target: Target IP or CIDR range
        scan_type: Type of scan (port_scan, service_identify, fingerprint, full)
        options: Scan options

    Returns:
        dict: Full scan results
    """
    if options is None:
        options = {}

    logger.info(f"Starting {scan_type} scan for task {task_id}, target {target}")

    try:
        # Step 1: Port scanning (0-33%)
        self.update_state(
            state="PROGRESS",
            meta={
                "current": 5,
                "total": 100,
                "status": "Step 1/3: Port scanning...",
            },
        )

        port_results = PortScanService.scan_with_nmap(target, options)
        if not port_results:
            logger.warning(f"No open ports found on {target}")
            return {
                "task_id": task_id,
                "status": "completed",
                "error": "No open ports found",
            }

        self.update_state(
            state="PROGRESS",
            meta={
                "current": 33,
                "total": 100,
                "status": f"Step 2/3: Service identification ({len(port_results)} ports)...",
            },
        )

        # Step 2: Service identification (33-66%)
        services = ServiceIdentifyService.identify_services_from_ports(port_results)

        self.update_state(
            state="PROGRESS",
            meta={
                "current": 66,
                "total": 100,
                "status": f"Step 3/3: Fingerprint matching ({len(services)} services)...",
            },
        )

        # Step 3: Fingerprint matching (66-99%)
        matches = FingerprintService.match_fingerprints_batch(services)

        self.update_state(
            state="PROGRESS",
            meta={
                "current": 99,
                "total": 100,
                "status": "Finalizing results...",
            },
        )

        logger.info(
            f"Full scan completed: {len(port_results)} ports, "
            f"{len(services)} services, {len(matches)} fingerprints"
        )

        return {
            "task_id": task_id,
            "status": "completed",
            "ports_found": len(port_results),
            "services_identified": len(services),
            "fingerprints_matched": len(matches),
            "results": {
                "ports": port_results,
                "services": services,
                "fingerprints": matches,
            },
        }

    except Exception as e:
        logger.error(f"Error in full scan task {task_id}: {e}", exc_info=True)
        self.update_state(
            state="FAILURE",
            meta={"error": str(e)},
        )
        return {
            "task_id": task_id,
            "status": "failed",
            "error": str(e),
        }

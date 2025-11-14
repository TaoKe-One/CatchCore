"""Service for processing and storing tool scan results."""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.task import Task, TaskResult
from app.models.vulnerability import Vulnerability
from app.models.asset import Asset
from app.services.tool_integration import ToolIntegration

logger = logging.getLogger(__name__)


class ToolResultService:
    """Service for handling tool scan results and database storage."""

    @staticmethod
    async def process_and_store_result(
        db: AsyncSession,
        task_id: int,
        tool_name: str,
        scan_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Process tool scan result and store in database.

        Args:
            db: Database session
            task_id: Task ID
            tool_name: Tool name (afrog, dddd, fscan, nuclei, dirsearch)
            scan_result: Tool execution result from tool_integration service

        Returns:
            Processing result with statistics
        """

        try:
            # Get task
            stmt = select(Task).where(Task.id == task_id)
            result = await db.execute(stmt)
            task = result.scalars().first()

            if not task:
                raise ValueError(f"Task {task_id} not found")

            # Store raw result
            task_result = TaskResult(
                task_id=task_id,
                result_type=f"tool_{tool_name}",
                result_data=scan_result,
                created_at=datetime.utcnow()
            )
            db.add(task_result)
            await db.flush()

            # Parse and extract findings
            findings_count = 0
            vulnerabilities_count = 0
            ports_count = 0
            directories_count = 0

            if scan_result.get("status") == "success":
                if tool_name == "fscan":
                    findings_count = await ToolResultService._process_fscan_results(
                        db, task, scan_result
                    )
                    ports_count = findings_count

                elif tool_name == "nuclei":
                    findings_count = await ToolResultService._process_nuclei_results(
                        db, task, scan_result
                    )
                    vulnerabilities_count = findings_count

                elif tool_name == "afrog":
                    findings_count = await ToolResultService._process_afrog_results(
                        db, task, scan_result
                    )
                    vulnerabilities_count = findings_count

                elif tool_name == "dddd":
                    findings_count = await ToolResultService._process_dddd_results(
                        db, task, scan_result
                    )
                    vulnerabilities_count = findings_count

                elif tool_name == "dirsearch":
                    findings_count = await ToolResultService._process_dirsearch_results(
                        db, task, scan_result
                    )
                    directories_count = findings_count

            await db.commit()

            logger.info(
                f"Tool result stored for task {task_id}: {tool_name}, "
                f"findings: {findings_count}"
            )

            return {
                "status": "success",
                "task_id": task_id,
                "tool": tool_name,
                "findings": findings_count,
                "vulnerabilities": vulnerabilities_count,
                "ports": ports_count,
                "directories": directories_count,
                "task_result_id": task_result.id,
            }

        except Exception as e:
            logger.error(f"Error processing tool result: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def _process_fscan_results(
        db: AsyncSession,
        task: Task,
        result: Dict[str, Any],
    ) -> int:
        """Process FScan port scan results."""
        ports_found = 0
        target = result.get("target", "")

        try:
            # Get or create asset for target
            asset = await ToolResultService._get_or_create_asset(db, target)

            # Process each port finding
            results = result.get("results", [])
            for port_info in results:
                ports_found += 1

                # Store port information as task result metadata
                port_data = {
                    "ip": port_info.get("ip"),
                    "port": port_info.get("port"),
                    "service": port_info.get("service"),
                    "version": port_info.get("version"),
                    "tool": "fscan",
                    "timestamp": datetime.utcnow().isoformat(),
                }

                # Create vulnerability record for service detection
                vuln = Vulnerability(
                    asset_id=asset.id,
                    title=f"Port {port_info.get('port')}/{port_info.get('service', 'unknown')}",
                    description=f"Service detected: {port_info.get('service')} {port_info.get('version', '')}",
                    severity="info",
                    status="open",
                    discovered_at=datetime.utcnow(),
                )
                db.add(vuln)

            return ports_found

        except Exception as e:
            logger.warning(f"Error processing FScan results: {e}")
            return ports_found

    @staticmethod
    async def _process_nuclei_results(
        db: AsyncSession,
        task: Task,
        result: Dict[str, Any],
    ) -> int:
        """Process Nuclei vulnerability scan results."""
        vulns_found = 0
        target = result.get("target", "")

        try:
            # Get or create asset
            asset = await ToolResultService._get_or_create_asset(db, target)

            # Process each vulnerability
            results = result.get("results", [])
            for vuln_info in results:
                vuln_found = False

                # Extract severity from nuclei result
                severity_map = {
                    "critical": "critical",
                    "high": "high",
                    "medium": "medium",
                    "low": "low",
                    "info": "info",
                }
                severity = severity_map.get(
                    str(vuln_info.get("severity", "")).lower(),
                    "medium"
                )

                # Create vulnerability record
                vuln = Vulnerability(
                    asset_id=asset.id,
                    title=vuln_info.get("name", "Unknown Vulnerability"),
                    description=f"Detected by Nuclei\nMatched URL: {vuln_info.get('matched_at', 'N/A')}",
                    cve_id=vuln_info.get("id"),
                    severity=severity,
                    status="open",
                    discovered_at=datetime.utcnow(),
                )
                db.add(vuln)
                vulns_found += 1
                vuln_found = True

            return vulns_found

        except Exception as e:
            logger.warning(f"Error processing Nuclei results: {e}")
            return vulns_found

    @staticmethod
    async def _process_afrog_results(
        db: AsyncSession,
        task: Task,
        result: Dict[str, Any],
    ) -> int:
        """Process Afrog vulnerability scan results."""
        vulns_found = 0
        target = result.get("target", "")

        try:
            asset = await ToolResultService._get_or_create_asset(db, target)

            results = result.get("results", [])
            for vuln_info in results:
                severity = vuln_info.get("severity", "medium").lower()

                vuln = Vulnerability(
                    asset_id=asset.id,
                    title=vuln_info.get("vulnerability", "Unknown Vulnerability"),
                    description=f"Detected by Afrog\nTarget: {vuln_info.get('target', 'N/A')}",
                    severity=severity,
                    status="open",
                    discovered_at=datetime.utcnow(),
                )
                db.add(vuln)
                vulns_found += 1

            return vulns_found

        except Exception as e:
            logger.warning(f"Error processing Afrog results: {e}")
            return vulns_found

    @staticmethod
    async def _process_dddd_results(
        db: AsyncSession,
        task: Task,
        result: Dict[str, Any],
    ) -> int:
        """Process DDDD vulnerability scan results."""
        vulns_found = 0
        target = result.get("target", "")

        try:
            asset = await ToolResultService._get_or_create_asset(db, target)

            results = result.get("results", [])
            for vuln_info in results:
                severity = vuln_info.get("severity", "medium").lower()

                vuln = Vulnerability(
                    asset_id=asset.id,
                    title=vuln_info.get("name", "Unknown Vulnerability"),
                    description=f"Detected by DDDD\nDetails: {vuln_info.get('description', 'N/A')}",
                    severity=severity,
                    status="open",
                    discovered_at=datetime.utcnow(),
                )
                db.add(vuln)
                vulns_found += 1

            return vulns_found

        except Exception as e:
            logger.warning(f"Error processing DDDD results: {e}")
            return vulns_found

    @staticmethod
    async def _process_dirsearch_results(
        db: AsyncSession,
        task: Task,
        result: Dict[str, Any],
    ) -> int:
        """Process DirSearch directory enumeration results."""
        dirs_found = 0
        target = result.get("target", "")

        try:
            asset = await ToolResultService._get_or_create_asset(db, target)

            results = result.get("results", [])
            for dir_info in results:
                dirs_found += 1

                # Store directory as low-severity finding
                vuln = Vulnerability(
                    asset_id=asset.id,
                    title=f"Directory Discovered: {dir_info.get('path', 'unknown')}",
                    description=f"HTTP Status: {dir_info.get('status', 'unknown')}\nPath: {dir_info.get('path', 'unknown')}",
                    severity="info",
                    status="open",
                    discovered_at=datetime.utcnow(),
                )
                db.add(vuln)

            return dirs_found

        except Exception as e:
            logger.warning(f"Error processing DirSearch results: {e}")
            return dirs_found

    @staticmethod
    async def _get_or_create_asset(db: AsyncSession, target: str) -> Asset:
        """
        Get or create asset from target address.

        Args:
            db: Database session
            target: Target IP, domain, or URL

        Returns:
            Asset object
        """
        # Extract IP or hostname from target
        ip_address = target.split("://")[-1].split("/")[0].split(":")[0]

        # Check if asset exists
        stmt = select(Asset).where(Asset.ip_address == ip_address)
        result = await db.execute(stmt)
        asset = result.scalars().first()

        if asset:
            return asset

        # Create new asset
        asset = Asset(
            ip_address=ip_address,
            hostname=target,
            status="active",
            created_at=datetime.utcnow(),
        )
        db.add(asset)
        await db.flush()

        return asset

    @staticmethod
    async def get_tool_results(
        db: AsyncSession,
        task_id: int,
        tool_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get tool results for a task.

        Args:
            db: Database session
            task_id: Task ID
            tool_name: Optional tool name filter

        Returns:
            List of tool results
        """
        query = select(TaskResult).where(TaskResult.task_id == task_id)

        if tool_name:
            query = query.where(
                TaskResult.result_type == f"tool_{tool_name}"
            )

        result = await db.execute(query)
        task_results = result.scalars().all()

        return [
            {
                "id": tr.id,
                "task_id": tr.task_id,
                "tool": tr.result_type.replace("tool_", ""),
                "data": tr.result_data,
                "created_at": tr.created_at.isoformat() if tr.created_at else None,
            }
            for tr in task_results
        ]

    @staticmethod
    async def get_task_statistics(
        db: AsyncSession,
        task_id: int,
    ) -> Dict[str, Any]:
        """
        Get statistics for a task including all findings.

        Args:
            db: Database session
            task_id: Task ID

        Returns:
            Statistics dictionary
        """
        try:
            # Get task
            stmt = select(Task).where(Task.id == task_id)
            result = await db.execute(stmt)
            task = result.scalars().first()

            if not task:
                return {}

            # Get vulnerabilities from this task's assets
            vuln_stmt = select(Vulnerability).where(
                Vulnerability.asset_id.in_(
                    select(Asset.id).where(Asset.id.in_([]))
                )
            )

            # Count tool results
            tool_results = await ToolResultService.get_tool_results(db, task_id)

            # Count vulnerabilities by severity
            severity_counts = {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
                "info": 0,
            }

            port_count = 0
            vuln_count = 0
            dir_count = 0

            for tool_result in tool_results:
                tool_name = tool_result["tool"]
                data = tool_result["data"]

                if tool_name == "fscan":
                    port_count += data.get("ports_found", 0)
                elif tool_name == "nuclei":
                    vuln_count += data.get("vulnerabilities_found", 0)
                elif tool_name == "afrog":
                    vuln_count += data.get("vulnerabilities_found", 0)
                elif tool_name == "dddd":
                    vuln_count += data.get("vulnerabilities_found", 0)
                elif tool_name == "dirsearch":
                    dir_count += data.get("directories_found", 0)

            return {
                "task_id": task_id,
                "task_name": task.name,
                "task_status": task.status,
                "tools_executed": [tr["tool"] for tr in tool_results],
                "tools_count": len(tool_results),
                "total_ports": port_count,
                "total_vulnerabilities": vuln_count,
                "total_directories": dir_count,
                "total_findings": port_count + vuln_count + dir_count,
                "severity_distribution": severity_counts,
            }

        except Exception as e:
            logger.error(f"Error getting task statistics: {e}")
            return {}

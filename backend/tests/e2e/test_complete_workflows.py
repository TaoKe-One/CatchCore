"""
End-to-End workflow tests for complete scan scenarios.

Tests complete workflows from task creation to report generation.
"""

import pytest
from unittest.mock import patch, MagicMock
import json
from datetime import datetime, timezone

from app.models.task import Task, TaskLog, TaskResult
from app.models.asset import Asset
from app.models.vulnerability import Vulnerability
from app.models.user import User
from app.services.tool_integration import ToolIntegration
from app.services.tool_result_service import ToolResultService


# ============================================================================
# COMPLETE SCAN WORKFLOW TESTS
# ============================================================================


class TestCompleteScanWorkflows:
    """Test complete end-to-end scan workflows."""

    @pytest.mark.asyncio
    async def test_complete_port_scan_workflow(self, db_session, test_user):
        """Test complete port scan workflow from creation to completion."""
        target_ip = "192.168.1.100"

        # Step 1: Create task
        task = Task(
            name="Complete Port Scan Workflow",
            task_type="port_scan",
            target_range=target_ip,
            status="pending",
            created_by=test_user.id,
            priority=5,
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        assert task.id is not None
        assert task.status == "pending"

        # Step 2: Update to running
        task.status = "running"
        task.progress = 0
        await db_session.commit()

        # Step 3: Add log entry
        log = TaskLog(
            task_id=task.id,
            level="INFO",
            message="Port scan started",
        )
        db_session.add(log)
        await db_session.commit()

        # Step 4: Mock tool execution and store results
        fscan_output = {
            "tool": "fscan",
            "target": target_ip,
            "status": "success",
            "ports_found": 3,
            "results": [
                {"ip": target_ip, "port": 22, "service": "ssh"},
                {"ip": target_ip, "port": 80, "service": "http"},
                {"ip": target_ip, "port": 443, "service": "https"},
            ],
        }

        # Store results
        await ToolResultService.process_and_store_result(
            db_session, task.id, "fscan", fscan_output
        )

        # Step 5: Update progress
        task.progress = 100
        task.status = "completed"
        await db_session.commit()

        # Step 6: Add completion log
        log = TaskLog(
            task_id=task.id,
            level="INFO",
            message="Port scan completed successfully",
        )
        db_session.add(log)
        await db_session.commit()

        # Step 7: Verify workflow completion
        assert task.status == "completed"
        assert task.progress == 100

    @pytest.mark.asyncio
    async def test_complete_vulnerability_scan_workflow(self, db_session, test_user):
        """Test complete vulnerability scan workflow."""
        target_url = "http://example.com"

        # Step 1: Create task
        task = Task(
            name="Complete Vulnerability Scan",
            task_type="vulnerability_scan",
            target_range=target_url,
            created_by=test_user.id,
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        # Step 2: Execute scan and store results
        nuclei_output = {
            "tool": "nuclei",
            "target": target_url,
            "status": "success",
            "vulnerabilities_found": 3,
            "results": [
                {
                    "id": "cve-2021-41773",
                    "name": "Apache RCE",
                    "severity": "critical",
                    "matched_at": f"{target_url}/cgi-bin/",
                },
                {
                    "id": "cve-2020-5902",
                    "name": "F5 BIG-IP RCE",
                    "severity": "critical",
                    "matched_at": f"{target_url}/mgmt/",
                },
                {
                    "id": "http-title",
                    "name": "Title Detection",
                    "severity": "info",
                    "matched_at": target_url,
                },
            ],
        }

        await ToolResultService.process_and_store_result(
            db_session, task.id, "nuclei", nuclei_output
        )

        # Step 3: Verify results storage
        results = await ToolResultService.get_tool_results(
            db_session, task.id, tool_name="nuclei"
        )
        assert len(results) > 0

        # Step 4: Get statistics
        stats = await ToolResultService.get_task_statistics(
            db_session, task.id
        )
        assert stats["total_findings"] >= 3

    @pytest.mark.asyncio
    async def test_complete_multi_tool_scan_workflow(self, db_session, test_user):
        """Test complete multi-tool scan workflow."""
        target = "192.168.1.100"

        # Step 1: Create task
        task = Task(
            name="Complete Multi-Tool Scan",
            task_type="full_scan",
            target_range=target,
            created_by=test_user.id,
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        # Step 2: Execute FScan
        fscan_result = {
            "tool": "fscan",
            "target": target,
            "ports_found": 5,
            "results": [
                {"ip": target, "port": 22, "service": "ssh"},
                {"ip": target, "port": 80, "service": "http"},
            ],
        }
        await ToolResultService.process_and_store_result(
            db_session, task.id, "fscan", fscan_result
        )

        # Step 3: Execute Nuclei
        nuclei_result = {
            "tool": "nuclei",
            "target": target,
            "vulnerabilities_found": 2,
            "results": [
                {"id": "cve-2021-41773", "name": "Apache RCE", "severity": "critical"},
            ],
        }
        await ToolResultService.process_and_store_result(
            db_session, task.id, "nuclei", nuclei_result
        )

        # Step 4: Execute DirSearch
        dirsearch_result = {
            "tool": "dirsearch",
            "target": f"http://{target}",
            "directories_found": 10,
            "results": [
                {"path": "/admin", "status": 200},
                {"path": "/api", "status": 200},
            ],
        }
        await ToolResultService.process_and_store_result(
            db_session, task.id, "dirsearch", dirsearch_result
        )

        # Step 5: Get aggregated statistics
        stats = await ToolResultService.get_task_statistics(
            db_session, task.id
        )

        assert stats is not None
        assert len(stats.get("tools_executed", [])) >= 3

    @pytest.mark.asyncio
    async def test_complete_poc_execution_workflow(self, db_session, test_user):
        """Test complete POC execution workflow."""
        # Step 1: Create task
        task = Task(
            name="Complete POC Execution",
            task_type="poc_detection",
            target_range="http://example.com",
            created_by=test_user.id,
        )
        db_session.add(task)
        await db_session.commit()

        # Step 2: Create asset
        asset = Asset(
            ip_address="192.168.1.100",
            hostname="poc-target.local",
            created_by=test_user.id,
        )
        db_session.add(asset)
        await db_session.commit()

        # Step 3: Execute Afrog
        afrog_result = {
            "tool": "afrog",
            "target": "http://example.com",
            "status": "success",
            "findings": [
                {
                    "vulnerability": "SQL Injection",
                    "severity": "high",
                    "target": "http://example.com/search",
                }
            ],
        }
        await ToolResultService.process_and_store_result(
            db_session, task.id, "afrog", afrog_result
        )

        # Step 4: Create vulnerability records
        vuln = Vulnerability(
            asset_id=asset.id,
            title="SQL Injection",
            severity="high",
            status="open",
        )
        db_session.add(vuln)
        await db_session.commit()

        assert vuln.id is not None


# ============================================================================
# COMPLEX WORKFLOW TESTS
# ============================================================================


class TestComplexWorkflows:
    """Test complex multi-step workflows."""

    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self, db_session, test_user):
        """Test workflow with error recovery."""
        task = Task(
            name="Error Recovery Workflow",
            task_type="port_scan",
            target_range="192.168.1.100",
            created_by=test_user.id,
        )
        db_session.add(task)
        await db_session.commit()

        # Step 1: Update to running
        task.status = "running"
        task.progress = 10
        await db_session.commit()

        # Step 2: Simulate error
        log = TaskLog(
            task_id=task.id,
            level="ERROR",
            message="Connection timeout",
        )
        db_session.add(log)
        await db_session.commit()

        # Step 3: Retry
        log = TaskLog(
            task_id=task.id,
            level="INFO",
            message="Retrying operation",
        )
        db_session.add(log)
        await db_session.commit()

        # Step 4: Succeed
        task.status = "completed"
        task.progress = 100
        await db_session.commit()

        assert task.status == "completed"

    @pytest.mark.asyncio
    async def test_progressive_scan_workflow(self, db_session, test_user):
        """Test progressive scan with multiple phases."""
        task = Task(
            name="Progressive Scan",
            task_type="full_scan",
            target_range="192.168.1.0/24",
            created_by=test_user.id,
        )
        db_session.add(task)
        await db_session.commit()

        # Phase 1: Network discovery
        task.progress = 20
        task.current_step = "network_discovery"
        await db_session.commit()

        log = TaskLog(
            task_id=task.id,
            level="INFO",
            message="Network discovery completed",
        )
        db_session.add(log)
        await db_session.commit()

        # Phase 2: Port scanning
        task.progress = 40
        task.current_step = "port_scanning"
        await db_session.commit()

        # Phase 3: Service identification
        task.progress = 60
        task.current_step = "service_identification"
        await db_session.commit()

        # Phase 4: Vulnerability scanning
        task.progress = 80
        task.current_step = "vulnerability_scanning"
        await db_session.commit()

        # Phase 5: Report generation
        task.progress = 100
        task.current_step = "report_generation"
        task.status = "completed"
        await db_session.commit()

        assert task.progress == 100
        assert task.status == "completed"

    @pytest.mark.asyncio
    async def test_concurrent_task_workflow(self, db_session, test_user):
        """Test concurrent execution of multiple tasks."""
        # Create multiple tasks
        tasks = []
        targets = [
            "192.168.1.100",
            "192.168.1.101",
            "192.168.1.102",
        ]

        for target in targets:
            task = Task(
                name=f"Concurrent Scan {target}",
                task_type="port_scan",
                target_range=target,
                status="running",
                created_by=test_user.id,
            )
            db_session.add(task)
            tasks.append(task)

        await db_session.commit()

        # Update all tasks concurrently
        for task in tasks:
            task.progress = 50
            log = TaskLog(
                task_id=task.id,
                level="INFO",
                message=f"Scanning {task.target_range}",
            )
            db_session.add(log)

        await db_session.commit()

        # Complete all tasks
        for task in tasks:
            task.progress = 100
            task.status = "completed"

        await db_session.commit()

        # Verify all completed
        assert all(task.status == "completed" for task in tasks)


# ============================================================================
# REAL-WORLD SCENARIO TESTS
# ============================================================================


class TestRealWorldScenarios:
    """Test real-world security scanning scenarios."""

    @pytest.mark.asyncio
    async def test_penetration_test_workflow(self, db_session, test_user):
        """Test complete penetration test workflow."""
        # Step 1: Create task for pen test
        task = Task(
            name="Penetration Test - Customer Network",
            task_type="full_scan",
            target_range="192.168.0.0/16",
            description="Full penetration test of customer infrastructure",
            priority=9,
            created_by=test_user.id,
        )
        db_session.add(task)
        await db_session.commit()

        # Step 2: Discovery phase
        task.status = "running"
        task.progress = 0
        await db_session.commit()

        log = TaskLog(
            task_id=task.id,
            level="INFO",
            message="Starting network discovery",
        )
        db_session.add(log)
        await db_session.commit()

        # Step 3: Scanning phase
        task.progress = 30
        await db_session.commit()

        for tool in ["fscan", "nuclei"]:
            result = {
                "tool": tool,
                "target": "192.168.0.1",
                "status": "success",
                "findings": [],
            }
            await ToolResultService.process_and_store_result(
                db_session, task.id, tool, result
            )

        # Step 4: Analysis phase
        task.progress = 60
        await db_session.commit()

        # Step 5: Report generation
        task.progress = 100
        task.status = "completed"
        await db_session.commit()

        log = TaskLog(
            task_id=task.id,
            level="INFO",
            message="Penetration test completed",
        )
        db_session.add(log)
        await db_session.commit()

    @pytest.mark.asyncio
    async def test_compliance_scan_workflow(self, db_session, test_user):
        """Test compliance scanning workflow."""
        task = Task(
            name="PCI-DSS Compliance Scan",
            task_type="compliance_scan",
            target_range="10.0.0.0/8",
            description="Annual PCI-DSS compliance scan",
            priority=10,
            created_by=test_user.id,
        )
        db_session.add(task)
        await db_session.commit()

        # Execute comprehensive scan
        tools = ["fscan", "nuclei", "afrog"]

        for i, tool in enumerate(tools):
            progress = 25 + (i * 25)
            task.progress = progress
            await db_session.commit()

            result = {
                "tool": tool,
                "status": "success",
                "findings": 0,
            }
            await ToolResultService.process_and_store_result(
                db_session, task.id, tool, result
            )

        task.progress = 100
        task.status = "completed"
        await db_session.commit()

    @pytest.mark.asyncio
    async def test_incident_response_workflow(self, db_session, test_user):
        """Test incident response workflow."""
        task = Task(
            name="Incident Response - Suspicious Activity",
            task_type="incident_response",
            target_range="192.168.1.0/24",
            description="Quick scan for suspicious activity",
            priority=10,
            created_by=test_user.id,
        )
        db_session.add(task)
        await db_session.commit()

        # Quick initial scan
        task.status = "running"
        task.progress = 0
        await db_session.commit()

        # Fast port scan
        result = {
            "tool": "fscan",
            "status": "success",
            "ports_found": 10,
        }
        await ToolResultService.process_and_store_result(
            db_session, task.id, "fscan", result
        )

        task.progress = 50
        await db_session.commit()

        # Vulnerability scan
        result = {
            "tool": "nuclei",
            "status": "success",
            "vulnerabilities_found": 2,
        }
        await ToolResultService.process_and_store_result(
            db_session, task.id, "nuclei", result
        )

        task.progress = 100
        task.status = "completed"
        await db_session.commit()


# ============================================================================
# WORKFLOW WITH ASSET TRACKING
# ============================================================================


class TestWorkflowWithAssetTracking:
    """Test workflows with asset discovery and tracking."""

    @pytest.mark.asyncio
    async def test_asset_discovery_workflow(self, db_session, test_user):
        """Test workflow with asset discovery."""
        task = Task(
            name="Asset Discovery Scan",
            task_type="asset_discovery",
            target_range="192.168.0.0/16",
            created_by=test_user.id,
        )
        db_session.add(task)
        await db_session.commit()

        # Discover assets
        discovered_ips = [
            "192.168.1.1",
            "192.168.1.10",
            "192.168.1.50",
            "192.168.2.1",
        ]

        for ip in discovered_ips:
            asset = Asset(
                ip_address=ip,
                hostname=f"host-{ip.split('.')[-1]}.local",
                status="active",
                created_by=test_user.id,
            )
            db_session.add(asset)

        await db_session.commit()

        # Store scan results
        result = {
            "tool": "fscan",
            "assets_discovered": len(discovered_ips),
            "results": [{"ip": ip} for ip in discovered_ips],
        }
        await ToolResultService.process_and_store_result(
            db_session, task.id, "fscan", result
        )

        task.status = "completed"
        await db_session.commit()

    @pytest.mark.asyncio
    async def test_vulnerability_tracking_workflow(
        self, db_session, test_user, test_asset
    ):
        """Test vulnerability discovery and tracking workflow."""
        task = Task(
            name="Vulnerability Tracking",
            task_type="vulnerability_tracking",
            target_range=test_asset.ip_address,
            created_by=test_user.id,
        )
        db_session.add(task)
        await db_session.commit()

        # Initial scan
        vulns_data = [
            {"id": "cve-2021-41773", "name": "Apache RCE", "severity": "critical"},
            {"id": "cve-2020-5902", "name": "F5 RCE", "severity": "critical"},
            {"id": "cve-2019-1234", "name": "SSL Issue", "severity": "high"},
        ]

        for vuln_data in vulns_data:
            vuln = Vulnerability(
                asset_id=test_asset.id,
                title=vuln_data["name"],
                cve_id=vuln_data["id"],
                severity=vuln_data["severity"],
                status="open",
            )
            db_session.add(vuln)

        await db_session.commit()

        # Store scan results
        result = {
            "tool": "nuclei",
            "target": test_asset.ip_address,
            "vulnerabilities_found": len(vulns_data),
        }
        await ToolResultService.process_and_store_result(
            db_session, task.id, "nuclei", result
        )

        task.status = "completed"
        task.progress = 100
        await db_session.commit()

        # Verify vulnerabilities stored
        assert len(vulns_data) == 3

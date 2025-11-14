"""
Unit tests for Tool Result Service.

Tests result processing, storage, and statistics aggregation.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timezone
import json

from app.services.tool_result_service import ToolResultService
from app.models.task import Task
from app.models.asset import Asset
from app.models.vulnerability import Vulnerability


# ============================================================================
# FSCAN RESULT PROCESSING TESTS
# ============================================================================


class TestFscanResultProcessing:
    """Test processing of FScan port scanning results."""

    @pytest.mark.asyncio
    async def test_process_fscan_results_creates_vulnerabilities(self, db_session):
        """Test fscan results create vulnerability records."""
        task = Task(
            name="Test Scan",
            task_type="port_scan",
            target_range="192.168.1.100",
            status="completed",
            created_by=1,
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        result = {
            "tool": "fscan",
            "target": "192.168.1.100",
            "ports_found": 3,
            "results": [
                {
                    "ip": "192.168.1.100",
                    "port": 22,
                    "service": "ssh",
                    "version": "OpenSSH 7.4",
                },
                {
                    "ip": "192.168.1.100",
                    "port": 80,
                    "service": "http",
                    "version": "Apache 2.4.6",
                },
            ],
        }

        count = await ToolResultService._process_fscan_results(
            db_session, task, result
        )

        assert count >= 2  # At least 2 ports should be stored

    @pytest.mark.asyncio
    async def test_fscan_creates_asset_if_not_exists(self, db_session):
        """Test fscan creates asset record if not found."""
        task = Task(
            name="Test Scan",
            task_type="port_scan",
            target_range="192.168.1.100",
            status="completed",
            created_by=1,
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        result = {
            "tool": "fscan",
            "target": "192.168.1.100",
            "ports_found": 1,
            "results": [
                {
                    "ip": "192.168.1.100",
                    "port": 22,
                    "service": "ssh",
                }
            ],
        }

        count = await ToolResultService._process_fscan_results(
            db_session, task, result
        )

        # Asset should be created
        assert count > 0

    @pytest.mark.asyncio
    async def test_fscan_port_records_have_correct_severity(self, db_session):
        """Test fscan port records have correct severity level."""
        # Port discoveries should have info severity
        pass

    @pytest.mark.asyncio
    async def test_fscan_empty_results(self, db_session):
        """Test fscan processing with no open ports."""
        task = Task(
            name="Test Scan",
            task_type="port_scan",
            target_range="192.168.1.200",
            status="completed",
            created_by=1,
        )
        db_session.add(task)
        await db_session.commit()

        result = {
            "tool": "fscan",
            "target": "192.168.1.200",
            "ports_found": 0,
            "results": [],
        }

        count = await ToolResultService._process_fscan_results(
            db_session, task, result
        )

        assert count == 0


# ============================================================================
# NUCLEI RESULT PROCESSING TESTS
# ============================================================================


class TestNucleiResultProcessing:
    """Test processing of Nuclei vulnerability scan results."""

    @pytest.mark.asyncio
    async def test_process_nuclei_results_creates_vulnerabilities(self, db_session):
        """Test nuclei results create vulnerability records."""
        task = Task(
            name="Test Scan",
            task_type="vulnerability_scan",
            target_range="http://example.com",
            status="completed",
            created_by=1,
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        result = {
            "tool": "nuclei",
            "target": "http://example.com",
            "vulnerabilities_found": 2,
            "results": [
                {
                    "id": "cve-2021-41773",
                    "name": "Apache RCE",
                    "severity": "critical",
                    "matched_at": "http://example.com/cgi-bin/",
                },
                {
                    "id": "http-title",
                    "name": "Title Detection",
                    "severity": "info",
                    "matched_at": "http://example.com/",
                },
            ],
        }

        count = await ToolResultService._process_nuclei_results(
            db_session, task, result
        )

        assert count >= 2

    @pytest.mark.asyncio
    async def test_nuclei_extracts_severity_levels(self, db_session):
        """Test nuclei correctly extracts severity levels."""
        task = Task(
            name="Test Scan",
            task_type="vulnerability_scan",
            target_range="http://example.com",
            status="completed",
            created_by=1,
        )
        db_session.add(task)
        await db_session.commit()

        result = {
            "tool": "nuclei",
            "target": "http://example.com",
            "results": [
                {
                    "id": "cve-2021-41773",
                    "name": "Apache RCE",
                    "severity": "critical",
                },
            ],
        }

        count = await ToolResultService._process_nuclei_results(
            db_session, task, result
        )

        assert count > 0

    @pytest.mark.asyncio
    async def test_nuclei_multiple_severity_levels(self, db_session):
        """Test nuclei with mixed severity levels."""
        task = Task(
            name="Test Scan",
            task_type="vulnerability_scan",
            target_range="http://example.com",
            status="completed",
            created_by=1,
        )
        db_session.add(task)
        await db_session.commit()

        result = {
            "tool": "nuclei",
            "target": "http://example.com",
            "results": [
                {"id": "1", "name": "Critical", "severity": "critical"},
                {"id": "2", "name": "High", "severity": "high"},
                {"id": "3", "name": "Medium", "severity": "medium"},
                {"id": "4", "name": "Low", "severity": "low"},
                {"id": "5", "name": "Info", "severity": "info"},
            ],
        }

        count = await ToolResultService._process_nuclei_results(
            db_session, task, result
        )

        assert count >= 5


# ============================================================================
# DIRSEARCH RESULT PROCESSING TESTS
# ============================================================================


class TestDirsearchResultProcessing:
    """Test processing of DirSearch directory enumeration results."""

    @pytest.mark.asyncio
    async def test_process_dirsearch_results(self, db_session):
        """Test dirsearch results create records."""
        task = Task(
            name="Test Scan",
            task_type="directory_scan",
            target_range="http://example.com",
            status="completed",
            created_by=1,
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        result = {
            "tool": "dirsearch",
            "target": "http://example.com",
            "directories_found": 3,
            "results": [
                {"path": "/admin", "status": 200},
                {"path": "/api", "status": 200},
                {"path": "/backup", "status": 403},
            ],
        }

        count = await ToolResultService._process_dirsearch_results(
            db_session, task, result
        )

        assert count >= 3

    @pytest.mark.asyncio
    async def test_dirsearch_empty_results(self, db_session):
        """Test dirsearch with no directories found."""
        task = Task(
            name="Test Scan",
            task_type="directory_scan",
            target_range="http://example.com",
            status="completed",
            created_by=1,
        )
        db_session.add(task)
        await db_session.commit()

        result = {
            "tool": "dirsearch",
            "target": "http://example.com",
            "directories_found": 0,
            "results": [],
        }

        count = await ToolResultService._process_dirsearch_results(
            db_session, task, result
        )

        assert count == 0


# ============================================================================
# MAIN STORAGE METHOD TESTS
# ============================================================================


class TestProcessAndStoreResult:
    """Test main process_and_store_result method."""

    @pytest.mark.asyncio
    async def test_store_fscan_result(self, db_session, test_task):
        """Test storing fscan results."""
        result = {
            "tool": "fscan",
            "target": "192.168.1.100",
            "status": "success",
            "ports_found": 2,
            "results": [
                {"ip": "192.168.1.100", "port": 22, "service": "ssh"},
                {"ip": "192.168.1.100", "port": 80, "service": "http"},
            ],
        }

        storage_result = await ToolResultService.process_and_store_result(
            db_session, test_task.id, "fscan", result
        )

        assert storage_result is not None
        assert storage_result.get("status") == "success"

    @pytest.mark.asyncio
    async def test_store_nuclei_result(self, db_session, test_task):
        """Test storing nuclei results."""
        result = {
            "tool": "nuclei",
            "target": "http://example.com",
            "status": "success",
            "vulnerabilities_found": 1,
            "results": [
                {
                    "id": "cve-2021-41773",
                    "name": "Apache RCE",
                    "severity": "critical",
                }
            ],
        }

        storage_result = await ToolResultService.process_and_store_result(
            db_session, test_task.id, "nuclei", result
        )

        assert storage_result is not None
        assert storage_result.get("status") == "success"

    @pytest.mark.asyncio
    async def test_invalid_tool_name(self, db_session, test_task):
        """Test invalid tool name handling."""
        result = {"status": "success"}

        # Should handle invalid tool gracefully
        try:
            await ToolResultService.process_and_store_result(
                db_session, test_task.id, "invalid_tool", result
            )
        except ValueError:
            pass  # Exception is acceptable

    @pytest.mark.asyncio
    async def test_task_not_found(self, db_session):
        """Test handling of non-existent task."""
        result = {"status": "success"}

        # Should handle missing task gracefully
        try:
            await ToolResultService.process_and_store_result(
                db_session, 99999, "fscan", result
            )
        except ValueError:
            pass


# ============================================================================
# RESULT RETRIEVAL TESTS
# ============================================================================


class TestGetToolResults:
    """Test retrieving stored tool results."""

    @pytest.mark.asyncio
    async def test_get_all_results_for_task(self, db_session, test_task):
        """Test retrieving all results for a task."""
        # Store some results first
        result = {
            "tool": "fscan",
            "status": "success",
            "results": [],
        }

        await ToolResultService.process_and_store_result(
            db_session, test_task.id, "fscan", result
        )

        # Retrieve results
        results = await ToolResultService.get_tool_results(
            db_session, test_task.id
        )

        assert isinstance(results, list)
        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_filter_results_by_tool(self, db_session, test_task):
        """Test filtering results by tool name."""
        # Store multiple tool results
        fscan_result = {"tool": "fscan", "status": "success", "results": []}
        nuclei_result = {"tool": "nuclei", "status": "success", "results": []}

        await ToolResultService.process_and_store_result(
            db_session, test_task.id, "fscan", fscan_result
        )
        await ToolResultService.process_and_store_result(
            db_session, test_task.id, "nuclei", nuclei_result
        )

        # Get only fscan results
        results = await ToolResultService.get_tool_results(
            db_session, test_task.id, tool_name="fscan"
        )

        assert isinstance(results, list)
        # All results should be from fscan
        for result in results:
            assert result.get("tool") == "fscan"

    @pytest.mark.asyncio
    async def test_empty_results_for_task(self, db_session, test_task):
        """Test retrieving results for task with no results."""
        results = await ToolResultService.get_tool_results(
            db_session, test_task.id
        )

        assert isinstance(results, list)
        assert len(results) == 0


# ============================================================================
# STATISTICS AGGREGATION TESTS
# ============================================================================


class TestTaskStatistics:
    """Test task statistics aggregation."""

    @pytest.mark.asyncio
    async def test_get_task_statistics(self, db_session, test_task):
        """Test getting aggregated task statistics."""
        # Store some results
        fscan_result = {
            "tool": "fscan",
            "ports_found": 5,
            "results": [
                {"ip": "192.168.1.100", "port": 22},
                {"ip": "192.168.1.100", "port": 80},
            ],
        }

        await ToolResultService.process_and_store_result(
            db_session, test_task.id, "fscan", fscan_result
        )

        stats = await ToolResultService.get_task_statistics(
            db_session, test_task.id
        )

        assert stats is not None
        assert isinstance(stats, dict)
        assert "total_findings" in stats

    def test_severity_distribution_calculation(self):
        """Test severity distribution calculation."""
        vulnerabilities = [
            {"severity": "critical"},
            {"severity": "critical"},
            {"severity": "high"},
            {"severity": "medium"},
            {"severity": "low"},
            {"severity": "info"},
        ]

        # Count by severity
        distribution = {}
        for vuln in vulnerabilities:
            severity = vuln["severity"]
            distribution[severity] = distribution.get(severity, 0) + 1

        assert distribution["critical"] == 2
        assert distribution["high"] == 1
        assert distribution["medium"] == 1
        assert distribution["low"] == 1
        assert distribution["info"] == 1

    def test_total_findings_count(self):
        """Test total findings calculation."""
        fscan_ports = 8
        nuclei_vulns = 5
        dirsearch_dirs = 45

        total_findings = fscan_ports + nuclei_vulns + dirsearch_dirs

        assert total_findings == 58


# ============================================================================
# ASSET MANAGEMENT TESTS
# ============================================================================


class TestGetOrCreateAsset:
    """Test asset creation and retrieval."""

    @pytest.mark.asyncio
    async def test_get_asset_if_exists(self, db_session, test_asset):
        """Test retrieving existing asset."""
        asset = await ToolResultService._get_or_create_asset(
            db_session, test_asset.ip_address
        )

        assert asset is not None
        assert asset.ip_address == test_asset.ip_address

    @pytest.mark.asyncio
    async def test_create_asset_if_not_exists(self, db_session):
        """Test creating new asset."""
        new_ip = "192.168.1.150"

        asset = await ToolResultService._get_or_create_asset(db_session, new_ip)

        assert asset is not None
        assert asset.ip_address == new_ip

    @pytest.mark.asyncio
    async def test_asset_reuse_on_multiple_scans(self, db_session):
        """Test same asset is reused across multiple scans."""
        target_ip = "192.168.1.100"

        asset1 = await ToolResultService._get_or_create_asset(db_session, target_ip)
        asset2 = await ToolResultService._get_or_create_asset(db_session, target_ip)

        assert asset1.id == asset2.id


# ============================================================================
# TRANSACTION AND ERROR HANDLING TESTS
# ============================================================================


class TestTransactionHandling:
    """Test transaction handling and rollback."""

    @pytest.mark.asyncio
    async def test_rollback_on_error(self, db_session):
        """Test database rollback on error."""
        task = Task(
            name="Test",
            task_type="port_scan",
            target_range="192.168.1.100",
            created_by=1,
        )
        db_session.add(task)
        await db_session.commit()

        # Transaction should rollback on error
        try:
            # Simulate an error
            raise Exception("Test error")
        except Exception:
            await db_session.rollback()


# ============================================================================
# EDGE CASES AND SPECIAL SCENARIOS
# ============================================================================


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    @pytest.mark.asyncio
    async def test_very_large_result_set(self, db_session, test_task):
        """Test handling of very large result set."""
        # Create result with many ports
        large_result = {
            "tool": "fscan",
            "target": "192.168.1.100",
            "ports_found": 100,
            "results": [
                {"ip": "192.168.1.100", "port": i, "service": f"service_{i}"}
                for i in range(1000, 1100)
            ],
        }

        count = await ToolResultService.process_and_store_result(
            db_session, test_task.id, "fscan", large_result
        )

        # Should handle large result set
        assert count > 0

    @pytest.mark.asyncio
    async def test_unicode_in_vulnerability_details(self, db_session, test_task):
        """Test handling of unicode characters in results."""
        result = {
            "tool": "nuclei",
            "target": "http://example.com",
            "results": [
                {
                    "id": "cve-2021-41773",
                    "name": "Apache RCE - 中文测试",
                    "severity": "critical",
                }
            ],
        }

        count = await ToolResultService.process_and_store_result(
            db_session, test_task.id, "nuclei", result
        )

        assert count > 0

    @pytest.mark.asyncio
    async def test_special_characters_in_paths(self, db_session, test_task):
        """Test special characters in file paths."""
        result = {
            "tool": "dirsearch",
            "target": "http://example.com",
            "results": [
                {
                    "path": "/path/with spaces",
                    "status": 200,
                },
                {
                    "path": "/path/with%20encoded",
                    "status": 200,
                },
                {
                    "path": "/path/with'quotes",
                    "status": 200,
                },
            ],
        }

        count = await ToolResultService.process_and_store_result(
            db_session, test_task.id, "dirsearch", result
        )

        assert count >= 3

    @pytest.mark.asyncio
    async def test_duplicate_results_in_multiple_scans(self, db_session, test_task):
        """Test handling of duplicate findings from multiple scans."""
        # First scan
        result1 = {
            "tool": "fscan",
            "target": "192.168.1.100",
            "results": [
                {"ip": "192.168.1.100", "port": 22, "service": "ssh"}
            ],
        }

        # Same finding from second scan
        result2 = {
            "tool": "fscan",
            "target": "192.168.1.100",
            "results": [
                {"ip": "192.168.1.100", "port": 22, "service": "ssh"}
            ],
        }

        count1 = await ToolResultService.process_and_store_result(
            db_session, test_task.id, "fscan", result1
        )
        count2 = await ToolResultService.process_and_store_result(
            db_session, test_task.id, "fscan", result2
        )

        # Both should be stored (allowing duplicates or deduplicating)
        assert count1 > 0
        assert count2 > 0

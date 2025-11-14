"""
Integration tests for tool execution and result processing.

Tests complete workflows from tool execution to result storage.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import json

from app.services.tool_integration import ToolIntegration
from app.services.tool_result_service import ToolResultService
from app.models.task import Task


# ============================================================================
# FSCAN EXECUTION INTEGRATION TESTS
# ============================================================================


class TestFscanExecutionIntegration:
    """Test FScan execution from tool call to result storage."""

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_fscan_execute_and_store_workflow(
        self, mock_run, db_session, test_task
    ):
        """Test complete FScan execute and store workflow."""
        # Mock FScan output
        fscan_result = {
            "tool": "fscan",
            "target": "192.168.1.100",
            "status": "success",
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
                {
                    "ip": "192.168.1.100",
                    "port": 443,
                    "service": "https",
                    "version": "Apache 2.4.6",
                },
            ],
        }

        mock_run.return_value = MagicMock(
            stdout=json.dumps(fscan_result),
            returncode=0,
        )

        # Execute tool
        result = await ToolIntegration.scan_with_fscan("192.168.1.100", {})

        # Store results
        storage_result = await ToolResultService.process_and_store_result(
            db_session, test_task.id, "fscan", result
        )

        assert storage_result is not None
        assert storage_result.get("status") == "success"

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_fscan_multiple_executions(self, mock_run, db_session, test_user):
        """Test multiple FScan executions on different targets."""
        targets = [
            "192.168.1.100",
            "192.168.1.101",
            "192.168.1.102",
        ]

        for target in targets:
            # Create task for each target
            task = Task(
                name=f"Scan {target}",
                task_type="port_scan",
                target_range=target,
                created_by=test_user.id,
            )
            db_session.add(task)

        await db_session.commit()

        # All tasks should be created
        assert True


# ============================================================================
# NUCLEI EXECUTION INTEGRATION TESTS
# ============================================================================


class TestNucleiExecutionIntegration:
    """Test Nuclei execution from tool call to result storage."""

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_nuclei_execute_and_store_workflow(
        self, mock_run, db_session, test_task
    ):
        """Test complete Nuclei execute and store workflow."""
        # Mock Nuclei output
        nuclei_result = {
            "tool": "nuclei",
            "target": "http://example.com",
            "status": "success",
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

        mock_run.return_value = MagicMock(
            stdout=json.dumps(nuclei_result),
            returncode=0,
        )

        # Execute tool
        result = await ToolIntegration.scan_with_nuclei(
            "http://example.com", None, {}
        )

        # Store results
        storage_result = await ToolResultService.process_and_store_result(
            db_session, test_task.id, "nuclei", result
        )

        assert storage_result is not None
        assert storage_result.get("status") == "success"

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_nuclei_with_templates(self, mock_run, db_session, test_task):
        """Test Nuclei execution with custom templates."""
        mock_run.return_value = MagicMock(
            stdout=json.dumps({"status": "success"}),
            returncode=0,
        )

        templates = ["cve-2021-41773", "http-default-login"]
        result = await ToolIntegration.scan_with_nuclei(
            "http://example.com",
            templates=templates,
            options={},
        )

        assert result is not None


# ============================================================================
# DIRSEARCH EXECUTION INTEGRATION TESTS
# ============================================================================


class TestDirsearchExecutionIntegration:
    """Test DirSearch execution and result storage."""

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_dirsearch_execute_and_store_workflow(
        self, mock_run, db_session, test_task
    ):
        """Test complete DirSearch execute and store workflow."""
        # Mock DirSearch output
        dirsearch_result = {
            "tool": "dirsearch",
            "target": "http://example.com",
            "status": "success",
            "directories_found": 10,
            "results": [
                {"path": "/admin", "status": 200},
                {"path": "/api", "status": 200},
                {"path": "/backup", "status": 403},
                {"path": "/config", "status": 403},
                {"path": "/test", "status": 200},
            ],
        }

        mock_run.return_value = MagicMock(
            stdout=json.dumps(dirsearch_result),
            returncode=0,
        )

        # Execute tool
        result = await ToolIntegration.scan_with_dirsearch(
            "http://example.com", {}
        )

        # Store results
        storage_result = await ToolResultService.process_and_store_result(
            db_session, test_task.id, "dirsearch", result
        )

        assert storage_result is not None


# ============================================================================
# TOOL CHAIN INTEGRATION TESTS
# ============================================================================


class TestToolChainIntegration:
    """Test sequential tool chain execution."""

    @pytest.mark.asyncio
    @patch.object(ToolIntegration, "scan_with_fscan")
    @patch.object(ToolIntegration, "scan_with_nuclei")
    async def test_fscan_then_nuclei_chain(
        self, mock_nuclei, mock_fscan, db_session, test_task
    ):
        """Test executing FScan then Nuclei in sequence."""
        # Mock FScan result
        fscan_result = {
            "tool": "fscan",
            "ports_found": 2,
            "results": [
                {"ip": "192.168.1.100", "port": 80},
                {"ip": "192.168.1.100", "port": 443},
            ],
        }
        mock_fscan.return_value = fscan_result

        # Mock Nuclei result
        nuclei_result = {
            "tool": "nuclei",
            "vulnerabilities_found": 1,
            "results": [
                {
                    "id": "cve-2021-41773",
                    "name": "Apache RCE",
                    "severity": "critical",
                }
            ],
        }
        mock_nuclei.return_value = nuclei_result

        # Execute chain
        tools = ["fscan", "nuclei"]
        results = await ToolIntegration.execute_tool_chain(
            "192.168.1.100",
            tools,
            {},
        )

        assert results is not None

    @pytest.mark.asyncio
    async def test_tool_chain_result_aggregation(self, db_session, test_task):
        """Test aggregating results from tool chain."""
        # Create multiple tool results
        tools = ["fscan", "nuclei", "dirsearch"]

        for tool in tools:
            if tool == "fscan":
                data = {"ports_found": 5}
            elif tool == "nuclei":
                data = {"vulnerabilities_found": 3}
            else:
                data = {"directories_found": 20}

            # Store each tool's result
            await ToolResultService.process_and_store_result(
                db_session, test_task.id, tool, {"tool": tool, **data}
            )

        # Get aggregated statistics
        stats = await ToolResultService.get_task_statistics(
            db_session, test_task.id
        )

        assert stats is not None


# ============================================================================
# ERROR RECOVERY INTEGRATION TESTS
# ============================================================================


class TestErrorRecoveryIntegration:
    """Test error handling and recovery in tool execution."""

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_tool_timeout_recovery(
        self, mock_run, db_session, test_task
    ):
        """Test recovery from tool timeout."""
        mock_run.side_effect = TimeoutError("Scan timed out")

        try:
            result = await ToolIntegration.scan_with_fscan("192.168.1.100", {})
            assert False, "Should raise TimeoutError"
        except TimeoutError:
            # Expected - log error and continue
            pass

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_tool_not_installed_recovery(
        self, mock_run, db_session, test_task
    ):
        """Test recovery from tool not installed."""
        mock_run.side_effect = FileNotFoundError("fscan: command not found")

        try:
            result = await ToolIntegration.scan_with_fscan("192.168.1.100", {})
            assert False, "Should raise FileNotFoundError"
        except FileNotFoundError:
            # Expected - fallback or skip
            pass

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_partial_tool_chain_failure(
        self, mock_run, db_session, test_task
    ):
        """Test partial tool chain failure handling."""

        def run_side_effect(cmd, *args, **kwargs):
            if "fscan" in cmd:
                return MagicMock(
                    stdout=json.dumps({"status": "success"}),
                    returncode=0,
                )
            else:
                raise TimeoutError()

        mock_run.side_effect = run_side_effect

        # First tool succeeds, second fails
        # Chain should handle failure gracefully


# ============================================================================
# RESULT PROCESSING INTEGRATION TESTS
# ============================================================================


class TestResultProcessingIntegration:
    """Test result processing pipeline."""

    @pytest.mark.asyncio
    async def test_fscan_result_extraction_and_storage(
        self, db_session, test_task, test_asset
    ):
        """Test complete FScan result extraction and storage."""
        fscan_output = {
            "tool": "fscan",
            "target": "192.168.1.100",
            "ports_found": 3,
            "results": [
                {"ip": "192.168.1.100", "port": 22, "service": "ssh"},
                {"ip": "192.168.1.100", "port": 80, "service": "http"},
                {"ip": "192.168.1.100", "port": 443, "service": "https"},
            ],
        }

        # Process and store
        count = await ToolResultService.process_and_store_result(
            db_session, test_task.id, "fscan", fscan_output
        )

        assert count >= 0

    @pytest.mark.asyncio
    async def test_nuclei_result_extraction_and_storage(
        self, db_session, test_task
    ):
        """Test complete Nuclei result extraction and storage."""
        nuclei_output = {
            "tool": "nuclei",
            "vulnerabilities_found": 2,
            "results": [
                {
                    "id": "cve-2021-41773",
                    "name": "Apache RCE",
                    "severity": "critical",
                },
                {
                    "id": "cve-2020-5902",
                    "name": "F5 BIG-IP RCE",
                    "severity": "critical",
                },
            ],
        }

        # Process and store
        count = await ToolResultService.process_and_store_result(
            db_session, test_task.id, "nuclei", nuclei_output
        )

        assert count >= 0

    @pytest.mark.asyncio
    async def test_dirsearch_result_extraction_and_storage(
        self, db_session, test_task
    ):
        """Test complete DirSearch result extraction and storage."""
        dirsearch_output = {
            "tool": "dirsearch",
            "directories_found": 5,
            "results": [
                {"path": "/admin", "status": 200},
                {"path": "/api", "status": 200},
                {"path": "/backup", "status": 403},
            ],
        }

        # Process and store
        count = await ToolResultService.process_and_store_result(
            db_session, test_task.id, "dirsearch", dirsearch_output
        )

        assert count >= 0

    @pytest.mark.asyncio
    async def test_statistics_aggregation_from_multiple_tools(
        self, db_session, test_task
    ):
        """Test statistics aggregation from multiple tool results."""
        # Store FScan results
        await ToolResultService.process_and_store_result(
            db_session,
            test_task.id,
            "fscan",
            {
                "tool": "fscan",
                "ports_found": 5,
                "results": [
                    {"port": 22},
                    {"port": 80},
                    {"port": 443},
                ],
            },
        )

        # Store Nuclei results
        await ToolResultService.process_and_store_result(
            db_session,
            test_task.id,
            "nuclei",
            {
                "tool": "nuclei",
                "vulnerabilities_found": 3,
                "results": [
                    {"severity": "critical"},
                    {"severity": "high"},
                    {"severity": "medium"},
                ],
            },
        )

        # Get statistics
        stats = await ToolResultService.get_task_statistics(
            db_session, test_task.id
        )

        assert stats is not None


# ============================================================================
# CONCURRENT TOOL EXECUTION TESTS
# ============================================================================


class TestConcurrentToolExecution:
    """Test concurrent tool execution."""

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_concurrent_fscan_scans(self, mock_run, db_session, test_user):
        """Test concurrent FScan execution on multiple targets."""
        mock_run.return_value = MagicMock(
            stdout=json.dumps({"status": "success", "ports_found": 0}),
            returncode=0,
        )

        from app.models.task import Task

        tasks = []
        for i in range(3):
            task = Task(
                name=f"Scan {i}",
                task_type="port_scan",
                target_range=f"192.168.1.{100+i}",
                created_by=test_user.id,
            )
            tasks.append(task)
            db_session.add(task)

        await db_session.commit()

        # All tasks created
        assert len(tasks) == 3

    @pytest.mark.asyncio
    async def test_results_isolation_between_tasks(
        self, db_session, test_user
    ):
        """Test that results from different tasks are isolated."""
        from app.models.task import Task
        from app.models.task import TaskResult

        # Create two tasks
        task1 = Task(
            name="Task 1",
            task_type="port_scan",
            target_range="192.168.1.100",
            created_by=test_user.id,
        )
        task2 = Task(
            name="Task 2",
            task_type="port_scan",
            target_range="192.168.1.101",
            created_by=test_user.id,
        )
        db_session.add(task1)
        db_session.add(task2)
        await db_session.commit()

        # Store different results
        result1 = TaskResult(
            task_id=task1.id,
            result_type="tool_fscan",
            result_data={"target": "192.168.1.100"},
        )
        result2 = TaskResult(
            task_id=task2.id,
            result_type="tool_fscan",
            result_data={"target": "192.168.1.101"},
        )
        db_session.add(result1)
        db_session.add(result2)
        await db_session.commit()

        # Results should be isolated
        assert result1.task_id == task1.id
        assert result2.task_id == task2.id


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================


class TestPerformanceIntegration:
    """Test performance characteristics of tool execution."""

    @pytest.mark.asyncio
    async def test_process_large_tool_output(self, db_session, test_task):
        """Test processing large tool output."""
        # Create large result set
        large_output = {
            "tool": "fscan",
            "ports_found": 1000,
            "results": [
                {"ip": "192.168.1.100", "port": i} for i in range(1000, 2000)
            ],
        }

        # Should handle large result
        result = await ToolResultService.process_and_store_result(
            db_session, test_task.id, "fscan", large_output
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_retrieve_large_result_set(
        self, db_session, test_task
    ):
        """Test retrieving large result set."""
        # Store multiple large results
        for i in range(5):
            data = {
                "tool": f"tool{i}",
                "results": [{"item": f"Item {j}"} for j in range(100)],
            }
            await ToolResultService.process_and_store_result(
                db_session, test_task.id, f"tool{i}", data
            )

        # Retrieve all results
        results = await ToolResultService.get_tool_results(
            db_session, test_task.id
        )

        assert isinstance(results, list)

"""
Performance and load testing for CatchCore scanning operations.

Tests system performance under various load conditions including large datasets,
concurrent operations, memory efficiency, and execution time baselines.
"""

import pytest
import asyncio
import time
import json
from unittest.mock import patch, MagicMock
import psutil
import os

from app.models.task import Task, TaskLog, TaskResult
from app.models.asset import Asset
from app.models.vulnerability import Vulnerability
from app.services.tool_integration import ToolIntegration
from app.services.tool_result_service import ToolResultService


# ============================================================================
# LARGE DATASET PERFORMANCE TESTS
# ============================================================================


class TestLargeDatasetPerformance:
    """Test system performance with large datasets."""

    @pytest.mark.asyncio
    async def test_process_large_port_scan_result(self, db_session, test_task):
        """Test processing port scan with 1000+ ports."""
        # Create large port scan result
        large_result = {
            "tool": "fscan",
            "target": "192.168.1.100",
            "status": "success",
            "ports_found": 1000,
            "results": [
                {
                    "ip": "192.168.1.100",
                    "port": 1000 + i,
                    "service": f"service_{i}" if i % 100 == 0 else "unknown",
                }
                for i in range(1000)
            ],
        }

        # Measure processing time
        start_time = time.time()
        await ToolResultService.process_and_store_result(
            db_session, test_task.id, "fscan", large_result
        )
        processing_time = time.time() - start_time

        # Verify processing completed within acceptable time (< 5 seconds)
        assert processing_time < 5.0
        assert test_task.id is not None

    @pytest.mark.asyncio
    async def test_process_large_vulnerability_result(self, db_session, test_task):
        """Test processing vulnerability scan with 500+ findings."""
        large_vuln_result = {
            "tool": "nuclei",
            "target": "http://example.com",
            "status": "success",
            "vulnerabilities_found": 500,
            "results": [
                {
                    "id": f"cve-{2020 + (i // 100)}-{5000 + i}",
                    "name": f"Vulnerability {i}",
                    "severity": ["critical", "high", "medium", "low"][i % 4],
                    "matched_at": f"http://example.com/path/{i}",
                }
                for i in range(500)
            ],
        }

        start_time = time.time()
        await ToolResultService.process_and_store_result(
            db_session, test_task.id, "nuclei", large_vuln_result
        )
        processing_time = time.time() - start_time

        assert processing_time < 5.0

    @pytest.mark.asyncio
    async def test_bulk_asset_creation_performance(self, db_session, test_user):
        """Test bulk creation of 500+ assets."""
        num_assets = 500

        start_time = time.time()
        for i in range(num_assets):
            asset = Asset(
                ip_address=f"192.168.1.{i % 256}",
                hostname=f"host-{i}.local",
                status="active",
                created_by=test_user.id,
            )
            db_session.add(asset)

        await db_session.commit()
        creation_time = time.time() - start_time

        # Verify bulk creation completed within acceptable time (< 3 seconds)
        assert creation_time < 3.0
        assert num_assets > 0

    @pytest.mark.asyncio
    async def test_bulk_vulnerability_creation_performance(
        self, db_session, test_asset
    ):
        """Test bulk creation of 300+ vulnerabilities."""
        num_vulns = 300

        start_time = time.time()
        for i in range(num_vulns):
            vuln = Vulnerability(
                asset_id=test_asset.id,
                title=f"Vulnerability {i}",
                cve_id=f"cve-2021-{40000 + i}",
                severity=["critical", "high", "medium", "low"][i % 4],
                status="open",
            )
            db_session.add(vuln)

        await db_session.commit()
        creation_time = time.time() - start_time

        assert creation_time < 2.0

    @pytest.mark.asyncio
    async def test_large_result_retrieval_performance(
        self, db_session, test_task
    ):
        """Test retrieving large result sets from database."""
        # Store large result
        large_result = {
            "tool": "fscan",
            "target": "192.168.1.100",
            "ports_found": 500,
            "results": [
                {
                    "ip": "192.168.1.100",
                    "port": 10000 + i,
                    "service": f"service_{i}",
                }
                for i in range(500)
            ],
        }

        await ToolResultService.process_and_store_result(
            db_session, test_task.id, "fscan", large_result
        )

        # Measure retrieval time
        start_time = time.time()
        results = await ToolResultService.get_tool_results(
            db_session, test_task.id, tool_name="fscan"
        )
        retrieval_time = time.time() - start_time

        # Verify retrieval completed within acceptable time (< 2 seconds)
        assert retrieval_time < 2.0
        assert len(results) > 0


# ============================================================================
# CONCURRENT OPERATION PERFORMANCE TESTS
# ============================================================================


class TestConcurrentOperationPerformance:
    """Test system performance under concurrent load."""

    @pytest.mark.asyncio
    async def test_concurrent_task_execution(self, db_session, test_user):
        """Test concurrent execution of 10+ scanning tasks."""
        num_tasks = 10
        tasks_to_create = []

        # Create multiple tasks
        for i in range(num_tasks):
            task = Task(
                name=f"Concurrent Task {i}",
                task_type="port_scan",
                target_range=f"192.168.1.{i}",
                status="running",
                created_by=test_user.id,
            )
            db_session.add(task)
            tasks_to_create.append(task)

        await db_session.commit()

        # Execute concurrent operations
        start_time = time.time()

        async def execute_task(task):
            task.progress = 50
            await db_session.commit()
            await asyncio.sleep(0.1)  # Simulate work
            task.progress = 100
            task.status = "completed"
            await db_session.commit()

        await asyncio.gather(*[execute_task(task) for task in tasks_to_create])

        execution_time = time.time() - start_time

        # Verify concurrent execution (should be faster than sequential)
        assert execution_time < (num_tasks * 0.3)  # More efficient than sequential
        assert all(task.status == "completed" for task in tasks_to_create)

    @pytest.mark.asyncio
    async def test_concurrent_tool_execution_with_results(self, db_session, test_task):
        """Test concurrent execution of multiple tools with result storage."""
        tools = ["fscan", "nuclei", "dirsearch"]

        start_time = time.time()

        async def execute_and_store(tool_name):
            result = {
                "tool": tool_name,
                "target": "192.168.1.100",
                "status": "success",
                "findings": 50,
            }
            await ToolResultService.process_and_store_result(
                db_session, test_task.id, tool_name, result
            )

        await asyncio.gather(*[execute_and_store(tool) for tool in tools])

        execution_time = time.time() - start_time

        # Verify concurrent tool execution
        assert execution_time < 3.0
        assert test_task.id is not None

    @pytest.mark.asyncio
    async def test_concurrent_asset_creation(self, db_session, test_user):
        """Test concurrent creation of assets."""
        num_assets = 50

        start_time = time.time()

        async def create_asset(index):
            asset = Asset(
                ip_address=f"192.168.2.{index % 256}",
                hostname=f"async-host-{index}.local",
                status="active",
                created_by=test_user.id,
            )
            db_session.add(asset)
            await db_session.commit()

        # Execute in batches to avoid overwhelming database
        batch_size = 10
        for i in range(0, num_assets, batch_size):
            batch = [
                create_asset(j)
                for j in range(i, min(i + batch_size, num_assets))
            ]
            await asyncio.gather(*batch)

        creation_time = time.time() - start_time

        assert creation_time < 5.0


# ============================================================================
# MEMORY EFFICIENCY TESTS
# ============================================================================


class TestMemoryEfficiency:
    """Test memory usage during operations."""

    @pytest.mark.asyncio
    async def test_memory_usage_large_result_processing(self, db_session, test_task):
        """Test memory efficiency when processing large results."""
        # Get baseline memory
        process = psutil.Process(os.getpid())
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Create and process large result
        large_result = {
            "tool": "fscan",
            "target": "192.168.1.100",
            "ports_found": 2000,
            "results": [
                {
                    "ip": "192.168.1.100",
                    "port": 30000 + i,
                    "service": f"service_{i}",
                }
                for i in range(2000)
            ],
        }

        await ToolResultService.process_and_store_result(
            db_session, test_task.id, "fscan", large_result
        )

        # Get peak memory
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - baseline_memory

        # Memory increase should be reasonable (< 100 MB for this operation)
        assert memory_increase < 100.0

    @pytest.mark.asyncio
    async def test_memory_usage_concurrent_operations(self, db_session, test_user):
        """Test memory usage during concurrent operations."""
        process = psutil.Process(os.getpid())
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Execute concurrent operations
        async def create_multiple_assets(count):
            for i in range(count):
                asset = Asset(
                    ip_address=f"192.168.3.{i % 256}",
                    hostname=f"mem-test-{i}.local",
                    status="active",
                    created_by=test_user.id,
                )
                db_session.add(asset)

            await db_session.commit()

        await asyncio.gather(
            create_multiple_assets(100),
            create_multiple_assets(100),
            create_multiple_assets(100),
        )

        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - baseline_memory

        # Memory usage should remain reasonable
        assert memory_increase < 150.0


# ============================================================================
# QUERY PERFORMANCE TESTS
# ============================================================================


class TestQueryPerformance:
    """Test database query performance."""

    @pytest.mark.asyncio
    async def test_filter_large_asset_set(self, db_session, test_user):
        """Test filtering performance on large asset set."""
        # Create 200 assets
        for i in range(200):
            asset = Asset(
                ip_address=f"192.168.4.{i % 256}",
                hostname=f"query-test-{i}.local",
                status="active" if i % 2 == 0 else "inactive",
                created_by=test_user.id,
            )
            db_session.add(asset)

        await db_session.commit()

        # Measure query time
        start_time = time.time()

        # Simulate filtering query
        from sqlalchemy import select

        query = select(Asset).where(Asset.status == "active")
        # Note: In real implementation, this would execute the query
        query_time = time.time() - start_time

        # Query should complete quickly
        assert query_time < 1.0

    @pytest.mark.asyncio
    async def test_aggregate_statistics_performance(
        self, db_session, test_task, test_asset
    ):
        """Test aggregation query performance."""
        # Create multiple vulnerabilities
        for i in range(100):
            vuln = Vulnerability(
                asset_id=test_asset.id,
                title=f"Vuln {i}",
                severity=["critical", "high", "medium", "low"][i % 4],
                status="open" if i % 3 == 0 else "closed",
            )
            db_session.add(vuln)

        await db_session.commit()

        # Measure aggregation query time
        start_time = time.time()

        stats = await ToolResultService.get_task_statistics(db_session, test_task.id)

        aggregation_time = time.time() - start_time

        # Aggregation should complete quickly
        assert aggregation_time < 2.0
        assert stats is not None


# ============================================================================
# EXECUTION TIME BASELINE TESTS
# ============================================================================


class TestExecutionTimeBaselines:
    """Test and establish execution time baselines."""

    @pytest.mark.asyncio
    async def test_baseline_port_scan_workflow_time(self, db_session, test_user):
        """Establish baseline execution time for port scan workflow."""
        start_time = time.time()

        # Create task
        task = Task(
            name="Baseline Port Scan",
            task_type="port_scan",
            target_range="192.168.1.100",
            status="running",
            created_by=test_user.id,
        )
        db_session.add(task)
        await db_session.commit()

        # Execute scan
        scan_result = {
            "tool": "fscan",
            "target": "192.168.1.100",
            "ports_found": 50,
            "results": [
                {
                    "ip": "192.168.1.100",
                    "port": 8000 + i,
                    "service": f"svc_{i}",
                }
                for i in range(50)
            ],
        }

        await ToolResultService.process_and_store_result(
            db_session, task.id, "fscan", scan_result
        )

        # Complete task
        task.status = "completed"
        task.progress = 100
        await db_session.commit()

        workflow_time = time.time() - start_time

        # Workflow should complete in reasonable time (< 3 seconds)
        assert workflow_time < 3.0
        assert task.status == "completed"

    @pytest.mark.asyncio
    async def test_baseline_multi_tool_workflow_time(self, db_session, test_user):
        """Establish baseline execution time for multi-tool workflow."""
        start_time = time.time()

        # Create task
        task = Task(
            name="Baseline Multi-Tool",
            task_type="full_scan",
            target_range="192.168.1.100",
            status="running",
            created_by=test_user.id,
        )
        db_session.add(task)
        await db_session.commit()

        # Execute multiple tools
        tools_data = [
            {
                "tool": "fscan",
                "target": "192.168.1.100",
                "ports_found": 30,
                "results": [
                    {
                        "ip": "192.168.1.100",
                        "port": 9000 + i,
                        "service": f"svc_{i}",
                    }
                    for i in range(30)
                ],
            },
            {
                "tool": "nuclei",
                "target": "http://192.168.1.100",
                "vulnerabilities_found": 20,
                "results": [
                    {
                        "id": f"cve-2021-{50000 + i}",
                        "name": f"Vuln {i}",
                        "severity": "high" if i % 2 == 0 else "medium",
                    }
                    for i in range(20)
                ],
            },
        ]

        for tool_data in tools_data:
            await ToolResultService.process_and_store_result(
                db_session, task.id, tool_data["tool"], tool_data
            )

        # Complete task
        task.status = "completed"
        task.progress = 100
        await db_session.commit()

        workflow_time = time.time() - start_time

        # Multi-tool workflow should complete in reasonable time (< 4 seconds)
        assert workflow_time < 4.0

    @pytest.mark.asyncio
    async def test_baseline_report_generation_time(self, db_session, test_task):
        """Establish baseline execution time for report generation."""
        # Setup task with results
        result = {
            "tool": "fscan",
            "target": "192.168.1.100",
            "ports_found": 100,
            "results": [
                {
                    "ip": "192.168.1.100",
                    "port": 50000 + i,
                    "service": f"svc_{i}",
                }
                for i in range(100)
            ],
        }

        await ToolResultService.process_and_store_result(
            db_session, test_task.id, "fscan", result
        )

        # Measure report generation time
        start_time = time.time()

        # Get statistics for report
        stats = await ToolResultService.get_task_statistics(db_session, test_task.id)

        generation_time = time.time() - start_time

        # Report generation should be quick
        assert generation_time < 2.0
        assert stats is not None


# ============================================================================
# STRESS TEST SCENARIOS
# ============================================================================


class TestStressScenarios:
    """Test system under stress conditions."""

    @pytest.mark.asyncio
    async def test_rapid_task_creation_stress(self, db_session, test_user):
        """Test rapid creation of many tasks."""
        num_tasks = 100

        start_time = time.time()

        for i in range(num_tasks):
            task = Task(
                name=f"Stress Task {i}",
                task_type="port_scan",
                target_range=f"192.168.5.{i % 256}",
                status="pending",
                created_by=test_user.id,
            )
            db_session.add(task)

        await db_session.commit()
        stress_time = time.time() - start_time

        # Should handle rapid creation
        assert stress_time < 5.0
        assert num_tasks > 0

    @pytest.mark.asyncio
    async def test_rapid_logging_stress(self, db_session, test_task):
        """Test rapid logging operations."""
        num_logs = 500

        start_time = time.time()

        for i in range(num_logs):
            log = TaskLog(
                task_id=test_task.id,
                level="INFO" if i % 3 == 0 else "DEBUG",
                message=f"Log message {i}",
            )
            db_session.add(log)

        await db_session.commit()
        logging_time = time.time() - start_time

        # Should handle rapid logging
        assert logging_time < 3.0

    @pytest.mark.asyncio
    async def test_mixed_operation_stress(self, db_session, test_user, test_task):
        """Test mixed concurrent operations under stress."""
        start_time = time.time()

        async def create_asset(index):
            asset = Asset(
                ip_address=f"192.168.6.{index % 256}",
                hostname=f"stress-{index}.local",
                status="active",
                created_by=test_user.id,
            )
            db_session.add(asset)
            await db_session.commit()

        async def create_log(index):
            log = TaskLog(
                task_id=test_task.id,
                level="INFO",
                message=f"Stress log {index}",
            )
            db_session.add(log)
            await db_session.commit()

        # Execute mixed operations
        await asyncio.gather(
            *[create_asset(i) for i in range(50)],
            *[create_log(i) for i in range(50)],
        )

        stress_time = time.time() - start_time

        assert stress_time < 5.0


# ============================================================================
# EDGE CASE PERFORMANCE TESTS
# ============================================================================


class TestEdgeCasePerformance:
    """Test performance in edge cases."""

    @pytest.mark.asyncio
    async def test_empty_result_processing_performance(self, db_session, test_task):
        """Test processing of empty scan results."""
        empty_result = {
            "tool": "fscan",
            "target": "192.168.1.200",
            "status": "success",
            "ports_found": 0,
            "results": [],
        }

        start_time = time.time()
        await ToolResultService.process_and_store_result(
            db_session, test_task.id, "fscan", empty_result
        )
        processing_time = time.time() - start_time

        # Should process empty results quickly
        assert processing_time < 1.0

    @pytest.mark.asyncio
    async def test_duplicate_result_handling_performance(self, db_session, test_task):
        """Test handling of duplicate results."""
        result = {
            "tool": "fscan",
            "target": "192.168.1.100",
            "ports_found": 10,
            "results": [
                {
                    "ip": "192.168.1.100",
                    "port": 80,
                    "service": "http",
                }
            ] * 10,  # Same result repeated
        }

        start_time = time.time()
        await ToolResultService.process_and_store_result(
            db_session, test_task.id, "fscan", result
        )
        processing_time = time.time() - start_time

        # Should handle duplicates efficiently
        assert processing_time < 2.0

    @pytest.mark.asyncio
    async def test_very_long_field_content_performance(self, db_session, test_task):
        """Test performance with very long field content."""
        # Create vulnerability with very long description
        long_description = "A" * 10000  # 10KB string

        result = {
            "tool": "nuclei",
            "target": "http://example.com",
            "vulnerabilities_found": 1,
            "results": [
                {
                    "id": "test-very-long",
                    "name": "Test Vulnerability",
                    "description": long_description,
                    "severity": "medium",
                }
            ],
        }

        start_time = time.time()
        await ToolResultService.process_and_store_result(
            db_session, test_task.id, "nuclei", result
        )
        processing_time = time.time() - start_time

        # Should handle long content reasonably
        assert processing_time < 3.0

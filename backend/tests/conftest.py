"""
Pytest configuration and shared fixtures for CatchCore tests.
"""

import pytest
import asyncio
from typing import Generator, AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from unittest.mock import Mock, AsyncMock, patch

# Import app models and dependencies
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.database import Base
from app.models.user import User
from app.models.asset import Asset
from app.models.task import Task, TaskConfig, TaskLog, TaskResult
from app.models.vulnerability import Vulnerability
from app.models.poc import POC
from app.core.config import settings


# ============================================================================
# DATABASE FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_db_engine():
    """Create test database engine (in-memory SQLite)."""
    # Use in-memory SQLite for tests
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def db_session(test_db_engine):
    """Provide a test database session."""
    async_session = async_sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
        # Rollback any pending transactions
        await session.rollback()


# ============================================================================
# MODEL FIXTURES
# ============================================================================

@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password_123",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_asset(db_session: AsyncSession, test_user: User) -> Asset:
    """Create a test asset."""
    asset = Asset(
        ip_address="192.168.1.100",
        hostname="test-server.local",
        status="active",
        department="IT",
        environment="production",
        created_by=test_user.id,
    )
    db_session.add(asset)
    await db_session.commit()
    await db_session.refresh(asset)
    return asset


@pytest.fixture
async def test_task(db_session: AsyncSession, test_user: User) -> Task:
    """Create a test task."""
    task = Task(
        name="Test Port Scan",
        task_type="port_scan",
        target_range="192.168.1.100",
        status="pending",
        created_by=test_user.id,
        priority=5,
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)
    return task


@pytest.fixture
async def test_vulnerability(db_session: AsyncSession, test_asset: Asset) -> Vulnerability:
    """Create a test vulnerability."""
    vuln = Vulnerability(
        asset_id=test_asset.id,
        title="SQL Injection",
        description="SQL Injection vulnerability in login form",
        cve_id="CVE-2024-1234",
        cvss_score=7.5,
        severity="high",
        status="open",
    )
    db_session.add(vuln)
    await db_session.commit()
    await db_session.refresh(vuln)
    return vuln


@pytest.fixture
async def test_poc(db_session: AsyncSession) -> POC:
    """Create a test POC."""
    poc = POC(
        name="Apache RCE PoC",
        cve_id="CVE-2021-41773",
        cvss_score="9.8",
        severity="critical",
        poc_type="nuclei",
        description="Remote Code Execution in Apache",
        content="id: apache-rce\ninfo:\n  name: Apache RCE",
        source="nuclei",
        is_active=True,
    )
    db_session.add(poc)
    await db_session.commit()
    await db_session.refresh(poc)
    return poc


# ============================================================================
# MOCK FIXTURES
# ============================================================================

@pytest.fixture
def mock_logger():
    """Provide a mock logger."""
    return Mock()


@pytest.fixture
def mock_subprocess():
    """Provide mock subprocess for tool testing."""
    with patch("subprocess.run") as mock_run:
        yield mock_run


@pytest.fixture
def mock_tool_result():
    """Provide mock tool execution result."""
    return {
        "tool": "fscan",
        "target": "192.168.1.100",
        "status": "success",
        "ports_found": 8,
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
                "version": "Apache/2.4.6",
            },
        ],
    }


@pytest.fixture
def mock_nuclei_result():
    """Provide mock Nuclei vulnerability result."""
    return {
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


# ============================================================================
# UTILITY FIXTURES
# ============================================================================

@pytest.fixture
def sample_task_data():
    """Provide sample task creation data."""
    return {
        "name": "Full Network Scan",
        "task_type": "port_scan",
        "target_range": "192.168.1.0/24",
        "description": "Comprehensive network assessment",
        "priority": 8,
    }


@pytest.fixture
def sample_asset_data():
    """Provide sample asset data."""
    return {
        "ip_address": "192.168.1.50",
        "hostname": "web-server.local",
        "status": "active",
        "department": "Web Team",
        "environment": "production",
    }


@pytest.fixture
def sample_poc_data():
    """Provide sample POC data."""
    return {
        "name": "OpenSSL Heartbleed",
        "cve_id": "CVE-2014-0160",
        "cvss_score": "7.5",
        "severity": "high",
        "poc_type": "nuclei",
        "description": "Heartbleed vulnerability in OpenSSL",
        "content": "id: openssl-heartbleed\ninfo:\n  name: OpenSSL Heartbleed",
        "source": "nuclei",
        "is_active": True,
    }


# ============================================================================
# PYTEST HOOKS
# ============================================================================

def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as an end-to-end test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


@pytest.fixture(autouse=True)
def reset_db_for_each_test(db_session):
    """Reset database state between tests."""
    yield
    # Cleanup happens automatically with rollback in db_session fixture

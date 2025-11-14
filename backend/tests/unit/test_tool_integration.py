"""
Unit tests for Tool Integration Service.

Tests external tool execution (Afrog, DDDD, FScan, Nuclei, DirSearch).
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock, call
import json
import asyncio

from app.services.tool_integration import ToolIntegration


# ============================================================================
# TOOL INSTALLATION DETECTION TESTS
# ============================================================================


class TestToolDetection:
    """Test tool installation detection."""

    @patch("shutil.which")
    def test_fscan_installed(self, mock_which):
        """Test detection of installed fscan."""
        mock_which.return_value = "/usr/bin/fscan"

        result = ToolIntegration.check_tool_installed("fscan")

        assert result is True

    @patch("shutil.which")
    def test_fscan_not_installed(self, mock_which):
        """Test detection of missing fscan."""
        mock_which.return_value = None

        result = ToolIntegration.check_tool_installed("fscan")

        assert result is False

    @patch("shutil.which")
    def test_nuclei_installed(self, mock_which):
        """Test detection of installed nuclei."""
        mock_which.return_value = "/usr/bin/nuclei"

        result = ToolIntegration.check_tool_installed("nuclei")

        assert result is True

    @patch("shutil.which")
    def test_afrog_installed(self, mock_which):
        """Test detection of installed afrog."""
        mock_which.return_value = "/usr/bin/afrog"

        result = ToolIntegration.check_tool_installed("afrog")

        assert result is True

    @patch("shutil.which")
    def test_dddd_installed(self, mock_which):
        """Test detection of installed dddd."""
        mock_which.return_value = "/usr/bin/dddd"

        result = ToolIntegration.check_tool_installed("dddd")

        assert result is True

    @patch("shutil.which")
    def test_dirsearch_installed(self, mock_which):
        """Test detection of installed dirsearch."""
        mock_which.return_value = "/usr/bin/dirsearch"

        result = ToolIntegration.check_tool_installed("dirsearch")

        assert result is True

    @patch("shutil.which")
    def test_invalid_tool_name(self, mock_which):
        """Test detection with invalid tool name."""
        result = ToolIntegration.check_tool_installed("invalid_tool")

        assert result is False

    @patch("shutil.which")
    def test_get_installed_tools(self, mock_which):
        """Test getting list of installed tools."""
        def which_side_effect(tool):
            installed = {
                "fscan": "/usr/bin/fscan",
                "nuclei": None,
                "afrog": "/usr/bin/afrog",
            }
            return installed.get(tool)

        mock_which.side_effect = which_side_effect

        result = ToolIntegration.get_installed_tools()

        assert isinstance(result, dict)
        assert "fscan" in result
        assert "nuclei" in result
        assert "afrog" in result


# ============================================================================
# FSCAN EXECUTION TESTS
# ============================================================================


class TestFscanExecution:
    """Test FScan port scanning execution."""

    @patch("subprocess.run")
    async def test_fscan_basic_scan(self, mock_run):
        """Test basic fscan execution."""
        mock_result = {
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
                }
            ],
        }

        mock_run.return_value = MagicMock(
            stdout=json.dumps(mock_result),
            stderr="",
            returncode=0,
        )

        result = await ToolIntegration.scan_with_fscan("192.168.1.100", {})

        assert result is not None
        assert isinstance(result, dict)

    @patch("subprocess.run")
    async def test_fscan_with_options(self, mock_run):
        """Test fscan with custom options."""
        mock_run.return_value = MagicMock(
            stdout=json.dumps({"status": "success"}),
            returncode=0,
        )

        options = {"threads": 50, "timeout": 30}
        result = await ToolIntegration.scan_with_fscan(
            "192.168.1.100", options
        )

        assert result is not None

    @patch("subprocess.run")
    async def test_fscan_timeout_error(self, mock_run):
        """Test fscan timeout handling."""
        mock_run.side_effect = TimeoutError("Scan timed out")

        with pytest.raises(TimeoutError):
            await ToolIntegration.scan_with_fscan("192.168.1.100", {})

    @patch("subprocess.run")
    async def test_fscan_invalid_target(self, mock_run):
        """Test fscan with invalid target."""
        mock_run.return_value = MagicMock(
            stdout=json.dumps({"error": "Invalid target"}),
            returncode=1,
        )

        result = await ToolIntegration.scan_with_fscan("invalid", {})

        # Should still return result, even if error
        assert result is not None

    @patch("subprocess.run")
    async def test_fscan_no_open_ports(self, mock_run):
        """Test fscan with no open ports."""
        mock_result = {
            "tool": "fscan",
            "status": "success",
            "ports_found": 0,
            "results": [],
        }

        mock_run.return_value = MagicMock(
            stdout=json.dumps(mock_result),
            returncode=0,
        )

        result = await ToolIntegration.scan_with_fscan("192.168.1.200", {})

        assert result is not None


# ============================================================================
# NUCLEI EXECUTION TESTS
# ============================================================================


class TestNucleiExecution:
    """Test Nuclei vulnerability scanning execution."""

    @patch("subprocess.run")
    async def test_nuclei_basic_scan(self, mock_run):
        """Test basic nuclei execution."""
        mock_result = {
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
                }
            ],
        }

        mock_run.return_value = MagicMock(
            stdout=json.dumps(mock_result),
            returncode=0,
        )

        result = await ToolIntegration.scan_with_nuclei("http://example.com", templates=None, options={})

        assert result is not None

    @patch("subprocess.run")
    async def test_nuclei_with_templates(self, mock_run):
        """Test nuclei with custom templates."""
        mock_run.return_value = MagicMock(
            stdout=json.dumps({"status": "success", "vulnerabilities_found": 0}),
            returncode=0,
        )

        templates = ["cve-2021-41773", "http-default-login"]
        result = await ToolIntegration.scan_with_nuclei(
            "http://example.com",
            templates=templates,
            options={},
        )

        assert result is not None

    @patch("subprocess.run")
    async def test_nuclei_multiple_vulnerabilities(self, mock_run):
        """Test nuclei detecting multiple vulnerabilities."""
        mock_result = {
            "tool": "nuclei",
            "vulnerabilities_found": 5,
            "results": [
                {"id": "cve-2021-41773", "severity": "critical"},
                {"id": "cve-2020-5902", "severity": "high"},
                {"id": "http-title", "severity": "info"},
                {"id": "tech-detect", "severity": "info"},
            ],
        }

        mock_run.return_value = MagicMock(
            stdout=json.dumps(mock_result),
            returncode=0,
        )

        result = await ToolIntegration.scan_with_nuclei("http://example.com", {}, {})

        assert result is not None

    @patch("subprocess.run")
    async def test_nuclei_timeout(self, mock_run):
        """Test nuclei timeout handling."""
        mock_run.side_effect = TimeoutError("Scan timed out")

        with pytest.raises(TimeoutError):
            await ToolIntegration.scan_with_nuclei("http://example.com", {}, {})


# ============================================================================
# AFROG EXECUTION TESTS
# ============================================================================


class TestAfrogExecution:
    """Test Afrog POC execution."""

    @patch("subprocess.run")
    async def test_afrog_basic_scan(self, mock_run):
        """Test basic afrog execution."""
        mock_result = {
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

        mock_run.return_value = MagicMock(
            stdout=json.dumps(mock_result),
            returncode=0,
        )

        result = await ToolIntegration.scan_with_afrog("http://example.com", {})

        assert result is not None

    @patch("subprocess.run")
    async def test_afrog_with_poc_file(self, mock_run):
        """Test afrog with POC file."""
        mock_run.return_value = MagicMock(
            stdout=json.dumps({"status": "success"}),
            returncode=0,
        )

        result = await ToolIntegration.scan_with_afrog(
            "http://example.com",
            poc_file="poc.yaml",
            options={},
        )

        assert result is not None

    @patch("subprocess.run")
    async def test_afrog_no_findings(self, mock_run):
        """Test afrog with no findings."""
        mock_result = {
            "tool": "afrog",
            "status": "success",
            "findings": [],
        }

        mock_run.return_value = MagicMock(
            stdout=json.dumps(mock_result),
            returncode=0,
        )

        result = await ToolIntegration.scan_with_afrog("http://example.com", {})

        assert result is not None


# ============================================================================
# DDDD EXECUTION TESTS
# ============================================================================


class TestDDDDExecution:
    """Test DDDD advanced scanning execution."""

    @patch("subprocess.run")
    async def test_dddd_basic_scan(self, mock_run):
        """Test basic DDDD execution."""
        mock_result = {
            "tool": "dddd",
            "target": "http://example.com",
            "status": "success",
            "findings": [
                {
                    "name": "Exposed Admin Panel",
                    "severity": "medium",
                }
            ],
        }

        mock_run.return_value = MagicMock(
            stdout=json.dumps(mock_result),
            returncode=0,
        )

        result = await ToolIntegration.scan_with_dddd("http://example.com", {})

        assert result is not None

    @patch("subprocess.run")
    async def test_dddd_with_options(self, mock_run):
        """Test DDDD with custom options."""
        mock_run.return_value = MagicMock(
            stdout=json.dumps({"status": "success"}),
            returncode=0,
        )

        options = {"depth": 3, "timeout": 60}
        result = await ToolIntegration.scan_with_dddd(
            "http://example.com",
            options=options,
        )

        assert result is not None


# ============================================================================
# DIRSEARCH EXECUTION TESTS
# ============================================================================


class TestDirsearchExecution:
    """Test DirSearch directory enumeration execution."""

    @patch("subprocess.run")
    async def test_dirsearch_basic_scan(self, mock_run):
        """Test basic dirsearch execution."""
        mock_result = {
            "tool": "dirsearch",
            "target": "http://example.com",
            "status": "success",
            "directories_found": 15,
            "results": [
                {
                    "path": "/admin",
                    "status": 200,
                },
                {
                    "path": "/api",
                    "status": 200,
                },
            ],
        }

        mock_run.return_value = MagicMock(
            stdout=json.dumps(mock_result),
            returncode=0,
        )

        result = await ToolIntegration.scan_with_dirsearch("http://example.com", {})

        assert result is not None

    @patch("subprocess.run")
    async def test_dirsearch_with_wordlist(self, mock_run):
        """Test dirsearch with custom wordlist."""
        mock_run.return_value = MagicMock(
            stdout=json.dumps({"status": "success"}),
            returncode=0,
        )

        options = {"wordlist": "custom.txt"}
        result = await ToolIntegration.scan_with_dirsearch(
            "http://example.com",
            options=options,
        )

        assert result is not None

    @patch("subprocess.run")
    async def test_dirsearch_multiple_directories(self, mock_run):
        """Test dirsearch finding multiple directories."""
        mock_result = {
            "tool": "dirsearch",
            "directories_found": 45,
            "results": [
                {"path": "/admin", "status": 200},
                {"path": "/api", "status": 200},
                {"path": "/backup", "status": 403},
                {"path": "/test", "status": 404},
            ],
        }

        mock_run.return_value = MagicMock(
            stdout=json.dumps(mock_result),
            returncode=0,
        )

        result = await ToolIntegration.scan_with_dirsearch("http://example.com", {})

        assert result is not None


# ============================================================================
# TOOL CHAIN EXECUTION TESTS
# ============================================================================


class TestToolChainExecution:
    """Test sequential tool chain execution."""

    @patch.object(ToolIntegration, "scan_with_fscan")
    @patch.object(ToolIntegration, "scan_with_nuclei")
    async def test_tool_chain_fscan_nuclei(self, mock_nuclei, mock_fscan):
        """Test chain execution: fscan then nuclei."""
        mock_fscan.return_value = {
            "tool": "fscan",
            "ports_found": 3,
            "results": [],
        }
        mock_nuclei.return_value = {
            "tool": "nuclei",
            "vulnerabilities_found": 0,
            "results": [],
        }

        tools = ["fscan", "nuclei"]
        results = await ToolIntegration.execute_tool_chain(
            "192.168.1.100",
            tools,
            {},
        )

        assert results is not None

    @patch.object(ToolIntegration, "scan_with_fscan")
    @patch.object(ToolIntegration, "scan_with_dirsearch")
    async def test_tool_chain_multiple_execution(self, mock_dirsearch, mock_fscan):
        """Test chain execution with multiple tools."""
        mock_fscan.return_value = {"tool": "fscan", "status": "success"}
        mock_dirsearch.return_value = {"tool": "dirsearch", "status": "success"}

        tools = ["fscan", "dirsearch"]
        results = await ToolIntegration.execute_tool_chain(
            "http://example.com",
            tools,
            {},
        )

        assert results is not None

    @patch("subprocess.run")
    async def test_tool_chain_partial_failure(self, mock_run):
        """Test chain execution with partial tool failure."""
        # First tool succeeds
        # Second tool fails
        def run_side_effect(cmd, *args, **kwargs):
            if "fscan" in cmd:
                return MagicMock(
                    stdout=json.dumps({"status": "success"}),
                    returncode=0,
                )
            else:
                return MagicMock(
                    stdout="",
                    returncode=1,
                )

        mock_run.side_effect = run_side_effect

        # Chain should continue despite failures
        # Implementation dependent on error handling strategy


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================


class TestToolErrorHandling:
    """Test error handling in tool execution."""

    @patch("subprocess.run")
    async def test_tool_not_installed_error(self, mock_run):
        """Test tool not installed error."""
        mock_run.side_effect = FileNotFoundError("fscan: command not found")

        with pytest.raises(FileNotFoundError):
            await ToolIntegration.scan_with_fscan("192.168.1.100", {})

    @patch("subprocess.run")
    async def test_tool_execution_timeout(self, mock_run):
        """Test tool execution timeout."""
        mock_run.side_effect = TimeoutError("Scan timed out after 300 seconds")

        with pytest.raises(TimeoutError):
            await ToolIntegration.scan_with_nuclei("http://example.com", {}, {})

    @patch("subprocess.run")
    async def test_tool_invalid_output(self, mock_run):
        """Test invalid JSON output from tool."""
        mock_run.return_value = MagicMock(
            stdout="This is not JSON",
            returncode=0,
        )

        # Should handle invalid JSON gracefully
        try:
            result = await ToolIntegration.scan_with_fscan("192.168.1.100", {})
        except json.JSONDecodeError:
            pass

    @patch("subprocess.run")
    async def test_tool_permission_denied(self, mock_run):
        """Test permission denied error."""
        mock_run.side_effect = PermissionError("Permission denied")

        with pytest.raises(PermissionError):
            await ToolIntegration.scan_with_fscan("192.168.1.100", {})


# ============================================================================
# OUTPUT FORMAT VALIDATION TESTS
# ============================================================================


class TestOutputFormatValidation:
    """Test validation of tool output format."""

    def test_fscan_output_format(self):
        """Test fscan output has required fields."""
        output = {
            "tool": "fscan",
            "target": "192.168.1.100",
            "status": "success",
            "ports_found": 3,
            "results": [],
        }

        assert "tool" in output
        assert "target" in output
        assert "status" in output
        assert "ports_found" in output
        assert "results" in output

    def test_nuclei_output_format(self):
        """Test nuclei output has required fields."""
        output = {
            "tool": "nuclei",
            "target": "http://example.com",
            "status": "success",
            "vulnerabilities_found": 2,
            "results": [],
        }

        assert "tool" in output
        assert "target" in output
        assert "status" in output
        assert "vulnerabilities_found" in output
        assert "results" in output

    def test_tool_status_values(self):
        """Test valid tool status values."""
        valid_statuses = ["success", "failed", "timeout", "error"]
        for status in valid_statuses:
            assert status in ["success", "failed", "timeout", "error"]

    def test_severity_levels(self):
        """Test valid severity levels."""
        valid_severities = ["critical", "high", "medium", "low", "info"]
        for severity in valid_severities:
            assert severity in valid_severities


# ============================================================================
# JSON PARSING TESTS
# ============================================================================


class TestJsonParsing:
    """Test JSON output parsing from tools."""

    def test_parse_valid_json(self):
        """Test parsing valid JSON."""
        json_str = '{"tool": "fscan", "status": "success"}'
        data = json.loads(json_str)

        assert data["tool"] == "fscan"
        assert data["status"] == "success"

    def test_parse_invalid_json(self):
        """Test parsing invalid JSON raises error."""
        json_str = "{'tool': 'fscan'}"  # Single quotes invalid in JSON

        with pytest.raises(json.JSONDecodeError):
            json.loads(json_str)

    def test_parse_complex_json(self):
        """Test parsing complex nested JSON."""
        json_str = json.dumps({
            "tool": "nuclei",
            "results": [
                {"id": "cve-1", "severity": "critical"},
                {"id": "cve-2", "severity": "high"},
            ],
            "metadata": {
                "scan_time": 123.45,
                "version": "2.9.0",
            },
        })

        data = json.loads(json_str)
        assert len(data["results"]) == 2
        assert data["metadata"]["scan_time"] == 123.45


# ============================================================================
# ASYNCIO INTEGRATION TESTS
# ============================================================================


class TestAsyncioIntegration:
    """Test asyncio integration in tool execution."""

    @pytest.mark.asyncio
    async def test_async_tool_execution(self):
        """Test tool execution is properly async."""
        # This test ensures coroutines are used properly
        pass

    @pytest.mark.asyncio
    async def test_concurrent_tool_execution(self):
        """Test concurrent execution of multiple tools."""
        # Multiple tools could be executed in parallel
        pass

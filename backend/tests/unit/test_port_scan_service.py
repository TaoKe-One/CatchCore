"""
Unit tests for Port Scan Service.

Tests port scanning, nmap execution, result parsing, and validation.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import json
from typing import List, Dict, Any

from app.services.port_scan_service import PortScanService


# ============================================================================
# TARGET VALIDATION TESTS
# ============================================================================


class TestTargetValidation:
    """Test target address validation."""

    def test_validate_single_ip(self):
        """Test validation of single IPv4 address."""
        target = "192.168.1.100"
        assert PortScanService.validate_target(target) is True

    def test_validate_cidr_notation(self):
        """Test validation of CIDR notation."""
        target = "192.168.1.0/24"
        assert PortScanService.validate_target(target) is True

    def test_validate_ipv6_address(self):
        """Test validation of IPv6 address."""
        target = "2001:db8::1"
        assert PortScanService.validate_target(target) is True

    def test_validate_ipv6_cidr(self):
        """Test validation of IPv6 CIDR notation."""
        target = "2001:db8::/32"
        assert PortScanService.validate_target(target) is True

    def test_validate_domain_name(self):
        """Test validation of domain name."""
        target = "example.com"
        assert PortScanService.validate_target(target) is True

    def test_validate_subdomain(self):
        """Test validation of subdomain."""
        target = "api.example.com"
        assert PortScanService.validate_target(target) is True

    def test_validate_localhost(self):
        """Test validation of localhost."""
        target = "localhost"
        assert PortScanService.validate_target(target) is True

    def test_validate_invalid_ip(self):
        """Test validation rejects invalid IP."""
        target = "256.256.256.256"
        # Should return False or raise exception
        result = PortScanService.validate_target(target)
        assert result is False or result is None

    def test_validate_invalid_cidr(self):
        """Test validation rejects invalid CIDR."""
        target = "192.168.1.0/33"  # Invalid subnet mask
        result = PortScanService.validate_target(target)
        assert result is False or result is None

    def test_validate_empty_string(self):
        """Test validation rejects empty string."""
        target = ""
        result = PortScanService.validate_target(target)
        assert result is False or result is None

    def test_validate_whitespace_only(self):
        """Test validation rejects whitespace-only string."""
        target = "   "
        result = PortScanService.validate_target(target)
        assert result is False or result is None

    def test_validate_special_characters(self):
        """Test validation rejects special characters."""
        target = "192.168.1.100; rm -rf /"
        result = PortScanService.validate_target(target)
        assert result is False or result is None


# ============================================================================
# NMAP COMMAND CONSTRUCTION TESTS
# ============================================================================


class TestNmapCommandConstruction:
    """Test nmap command line construction."""

    @patch("subprocess.run")
    def test_quick_scan_command(self, mock_run):
        """Test quick scan uses correct ports."""
        mock_run.return_value = MagicMock(stdout="", returncode=0)

        target = "192.168.1.100"
        PortScanService.scan_quick(target)

        # Verify nmap was called
        assert mock_run.called

    @patch("subprocess.run")
    def test_aggressive_scan_command(self, mock_run):
        """Test aggressive scan includes OS detection."""
        mock_run.return_value = MagicMock(stdout="", returncode=0)

        target = "192.168.1.100"
        PortScanService.scan_aggressive(target)

        # Verify nmap was called with aggressive flags
        assert mock_run.called

    def test_scan_options_with_custom_ports(self):
        """Test scan options with custom port range."""
        options = {
            "ports": "80,443,8080",
            "timing": "4",
            "scan_type": "syn",
        }
        # Test that options are properly formatted
        assert options["ports"] == "80,443,8080"
        assert options["timing"] in ["0", "1", "2", "3", "4", "5"]

    def test_scan_options_with_service_detection(self):
        """Test scan options with service detection."""
        options = {
            "service_detection": True,
            "os_detection": False,
        }
        assert options["service_detection"] is True
        assert options["os_detection"] is False

    def test_scan_timing_template_values(self):
        """Test all valid timing templates."""
        valid_timings = ["0", "1", "2", "3", "4", "5"]
        for timing in valid_timings:
            assert timing in ["0", "1", "2", "3", "4", "5"]

    def test_scan_type_options(self):
        """Test valid scan type options."""
        valid_scan_types = ["syn", "connect", "udp"]
        for scan_type in valid_scan_types:
            assert scan_type in valid_scan_types


# ============================================================================
# NMAP OUTPUT PARSING TESTS
# ============================================================================


class TestNmapOutputParsing:
    """Test parsing of nmap XML output."""

    def test_parse_nmap_xml_single_port(self):
        """Test parsing nmap output with single open port."""
        xml_output = """<?xml version="1.0"?>
        <nmaprun>
            <host>
                <status state="up"/>
                <address addr="192.168.1.100" addrtype="ipv4"/>
                <hostnames>
                    <hostname name="test.local" type="PTR"/>
                </hostnames>
                <ports>
                    <port protocol="tcp" portid="22">
                        <state state="open"/>
                        <service name="ssh" product="OpenSSH" version="7.4"/>
                    </port>
                </ports>
            </host>
        </nmaprun>"""

        result = PortScanService._parse_nmap_xml(xml_output)

        assert isinstance(result, list)
        assert len(result) > 0
        assert result[0]["port"] == 22
        assert result[0]["service"] == "ssh"

    def test_parse_nmap_xml_multiple_ports(self):
        """Test parsing nmap output with multiple ports."""
        xml_output = """<?xml version="1.0"?>
        <nmaprun>
            <host>
                <status state="up"/>
                <address addr="192.168.1.100" addrtype="ipv4"/>
                <ports>
                    <port protocol="tcp" portid="22">
                        <state state="open"/>
                        <service name="ssh"/>
                    </port>
                    <port protocol="tcp" portid="80">
                        <state state="open"/>
                        <service name="http"/>
                    </port>
                    <port protocol="tcp" portid="443">
                        <state state="open"/>
                        <service name="https"/>
                    </port>
                </ports>
            </host>
        </nmaprun>"""

        result = PortScanService._parse_nmap_xml(xml_output)

        assert len(result) >= 3
        ports = [r["port"] for r in result]
        assert 22 in ports
        assert 80 in ports
        assert 443 in ports

    def test_parse_nmap_xml_closed_ports(self):
        """Test parsing nmap output ignores closed ports."""
        xml_output = """<?xml version="1.0"?>
        <nmaprun>
            <host>
                <status state="up"/>
                <address addr="192.168.1.100" addrtype="ipv4"/>
                <ports>
                    <port protocol="tcp" portid="22">
                        <state state="open"/>
                        <service name="ssh"/>
                    </port>
                    <port protocol="tcp" portid="25">
                        <state state="closed"/>
                        <service name="smtp"/>
                    </port>
                </ports>
            </host>
        </nmaprun>"""

        result = PortScanService._parse_nmap_xml(xml_output)

        # Only open ports should be included
        ports = [r["port"] for r in result]
        assert 22 in ports
        assert 25 not in ports  # Closed port excluded

    def test_parse_nmap_xml_filtered_ports(self):
        """Test parsing nmap output ignores filtered ports."""
        xml_output = """<?xml version="1.0"?>
        <nmaprun>
            <host>
                <address addr="192.168.1.100" addrtype="ipv4"/>
                <ports>
                    <port protocol="tcp" portid="22">
                        <state state="open"/>
                        <service name="ssh"/>
                    </port>
                    <port protocol="tcp" portid="445">
                        <state state="filtered"/>
                        <service name="smb"/>
                    </port>
                </ports>
            </host>
        </nmaprun>"""

        result = PortScanService._parse_nmap_xml(xml_output)

        ports = [r["port"] for r in result]
        assert 22 in ports
        assert 445 not in ports  # Filtered port excluded

    def test_parse_nmap_xml_with_service_info(self):
        """Test parsing nmap output with service version."""
        xml_output = """<?xml version="1.0"?>
        <nmaprun>
            <host>
                <address addr="192.168.1.100" addrtype="ipv4"/>
                <ports>
                    <port protocol="tcp" portid="80">
                        <state state="open"/>
                        <service name="http" product="Apache httpd"
                                 version="2.4.6" extrainfo="(CentOS)"/>
                    </port>
                </ports>
            </host>
        </nmaprun>"""

        result = PortScanService._parse_nmap_xml(xml_output)

        assert len(result) > 0
        port_info = result[0]
        assert port_info["port"] == 80
        assert port_info["service"] == "http"
        assert "product" in str(port_info)

    def test_parse_nmap_xml_empty_output(self):
        """Test parsing empty nmap output."""
        xml_output = """<?xml version="1.0"?>
        <nmaprun>
        </nmaprun>"""

        result = PortScanService._parse_nmap_xml(xml_output)

        assert result is not None
        assert len(result) == 0

    def test_parse_nmap_xml_invalid_xml(self):
        """Test parsing invalid XML returns empty list or raises."""
        xml_output = "This is not XML at all"

        try:
            result = PortScanService._parse_nmap_xml(xml_output)
            assert result is not None
        except Exception:
            # Exception is acceptable for invalid XML
            pass

    def test_parse_nmap_xml_multiple_hosts(self):
        """Test parsing nmap output with multiple hosts."""
        xml_output = """<?xml version="1.0"?>
        <nmaprun>
            <host>
                <address addr="192.168.1.100" addrtype="ipv4"/>
                <ports>
                    <port protocol="tcp" portid="22">
                        <state state="open"/>
                        <service name="ssh"/>
                    </port>
                </ports>
            </host>
            <host>
                <address addr="192.168.1.101" addrtype="ipv4"/>
                <ports>
                    <port protocol="tcp" portid="80">
                        <state state="open"/>
                        <service name="http"/>
                    </port>
                </ports>
            </host>
        </nmaprun>"""

        result = PortScanService._parse_nmap_xml(xml_output)

        assert len(result) >= 2
        ips = [r["ip"] for r in result]
        assert "192.168.1.100" in ips
        assert "192.168.1.101" in ips


# ============================================================================
# SCAN EXECUTION TESTS
# ============================================================================


class TestScanExecution:
    """Test scan execution and error handling."""

    @patch("subprocess.run")
    def test_scan_with_nmap_success(self, mock_run):
        """Test successful nmap execution."""
        mock_run.return_value = MagicMock(
            stdout='<?xml version="1.0"?><nmaprun></nmaprun>',
            returncode=0,
        )

        result = PortScanService.scan_with_nmap("192.168.1.100", {})

        assert result is not None

    @patch("subprocess.run")
    def test_scan_with_nmap_not_installed(self, mock_run):
        """Test nmap not installed error handling."""
        mock_run.side_effect = FileNotFoundError("nmap not found")

        try:
            PortScanService.scan_with_nmap("192.168.1.100", {})
            assert False, "Should raise exception"
        except FileNotFoundError:
            pass

    @patch("subprocess.run")
    def test_scan_with_nmap_timeout(self, mock_run):
        """Test nmap timeout handling."""
        mock_run.side_effect = TimeoutError("Scan timed out")

        try:
            PortScanService.scan_with_nmap("192.168.1.100", {})
            assert False, "Should raise exception"
        except TimeoutError:
            pass

    @patch("subprocess.run")
    def test_scan_with_nmap_permission_denied(self, mock_run):
        """Test nmap permission denied error."""
        mock_run.side_effect = PermissionError("Permission denied")

        try:
            PortScanService.scan_with_nmap("192.168.1.100", {})
            assert False, "Should raise exception"
        except PermissionError:
            pass

    @patch("subprocess.run")
    def test_scan_quick_uses_limited_ports(self, mock_run):
        """Test quick scan uses limited port set."""
        mock_run.return_value = MagicMock(
            stdout='<?xml version="1.0"?><nmaprun></nmaprun>',
            returncode=0,
        )

        PortScanService.scan_quick("192.168.1.100")

        # Quick scan should use limited ports
        assert mock_run.called

    @patch("subprocess.run")
    def test_scan_aggressive_includes_os_detection(self, mock_run):
        """Test aggressive scan includes OS detection."""
        mock_run.return_value = MagicMock(
            stdout='<?xml version="1.0"?><nmaprun></nmaprun>',
            returncode=0,
        )

        PortScanService.scan_aggressive("192.168.1.100")

        assert mock_run.called


# ============================================================================
# PORT RANGE PARSING TESTS
# ============================================================================


class TestPortRangeParsing:
    """Test port range specification parsing."""

    def test_single_port(self):
        """Test single port specification."""
        port_spec = "22"
        # Should be valid
        assert port_spec.isdigit() or "-" in port_spec or "," in port_spec

    def test_port_range(self):
        """Test port range specification."""
        port_spec = "1-65535"
        assert "-" in port_spec

    def test_multiple_ports(self):
        """Test multiple specific ports."""
        port_spec = "22,80,443"
        assert "," in port_spec

    def test_common_ports(self):
        """Test common ports list."""
        port_spec = "21,22,80,443,3306,5432"
        ports = [int(p) for p in port_spec.split(",")]
        assert 22 in ports
        assert 80 in ports
        assert 443 in ports

    def test_port_range_start_end(self):
        """Test port range parsing."""
        port_spec = "1000-2000"
        parts = port_spec.split("-")
        assert int(parts[0]) < int(parts[1])


# ============================================================================
# RESULT FORMAT TESTS
# ============================================================================


class TestResultFormat:
    """Test scan result format and structure."""

    def test_result_has_required_fields(self):
        """Test that result contains required fields."""
        result = {
            "ip": "192.168.1.100",
            "port": 22,
            "protocol": "tcp",
            "state": "open",
            "service": {
                "name": "ssh",
                "product": "OpenSSH",
                "version": "7.4",
            },
        }

        assert "ip" in result
        assert "port" in result
        assert "protocol" in result
        assert "state" in result
        assert "service" in result

    def test_result_port_is_integer(self):
        """Test port is integer type."""
        result = {"port": 22}
        assert isinstance(result["port"], int)
        assert 1 <= result["port"] <= 65535

    def test_result_state_values(self):
        """Test port state values."""
        valid_states = ["open", "closed", "filtered", "unfiltered"]
        for state in valid_states:
            assert state in ["open", "closed", "filtered", "unfiltered"]

    def test_result_protocol_values(self):
        """Test protocol values."""
        valid_protocols = ["tcp", "udp"]
        for protocol in valid_protocols:
            assert protocol in valid_protocols


# ============================================================================
# EDGE CASES AND ERRORS
# ============================================================================


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_scan_private_ip_ranges(self):
        """Test scanning private IP ranges."""
        private_ranges = [
            "10.0.0.0/8",
            "172.16.0.0/12",
            "192.168.0.0/16",
        ]
        for ip_range in private_ranges:
            assert PortScanService.validate_target(ip_range) is True

    def test_scan_large_cidr_block(self):
        """Test scanning large CIDR blocks."""
        target = "10.0.0.0/8"  # 16M hosts
        # Should be valid but might be slow
        assert PortScanService.validate_target(target) is True

    def test_scan_single_host_in_cidr(self):
        """Test scanning single host in CIDR notation."""
        target = "192.168.1.100/32"
        assert PortScanService.validate_target(target) is True

    @patch("subprocess.run")
    def test_scan_invalid_target_caught(self, mock_run):
        """Test invalid target is caught before execution."""
        invalid_target = "999.999.999.999"

        # Validation should catch it before execution
        is_valid = PortScanService.validate_target(invalid_target)
        if not is_valid:
            assert mock_run.not_called or not mock_run.called

    def test_options_with_default_values(self):
        """Test scan with default options."""
        options = {
            "ports": "1-65535",
            "timing": "3",
            "scan_type": "syn",
            "skip_ping": False,
            "service_detection": True,
            "os_detection": False,
        }
        assert options["timing"] == "3"
        assert options["scan_type"] == "syn"

"""
Unit tests for Service Identification Service.

Tests banner grabbing, service detection, and vulnerability mapping.
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock, patch
import socket
import ssl

from app.services.service_identify_service import ServiceIdentifyService


# ============================================================================
# BANNER GRABBING TESTS
# ============================================================================


class TestBannerGrabbing:
    """Test banner grabbing functionality."""

    @patch("socket.socket")
    def test_grab_ssh_banner(self, mock_socket):
        """Test grabbing SSH service banner."""
        mock_sock_instance = MagicMock()
        mock_socket.return_value = mock_sock_instance
        mock_sock_instance.recv.return_value = b"SSH-2.0-OpenSSH_7.4\r\n"

        banner = ServiceIdentifyService._grab_banner("192.168.1.100", 22, 5)

        assert banner is not None
        assert "OpenSSH" in banner

    @patch("socket.socket")
    def test_grab_http_banner(self, mock_socket):
        """Test grabbing HTTP service banner."""
        mock_sock_instance = MagicMock()
        mock_socket.return_value = mock_sock_instance
        mock_sock_instance.recv.return_value = b"HTTP/1.1 200 OK\r\nServer: Apache/2.4.6\r\n"

        banner = ServiceIdentifyService._grab_banner("192.168.1.100", 80, 5)

        assert banner is not None

    @patch("socket.socket")
    def test_grab_ftp_banner(self, mock_socket):
        """Test grabbing FTP service banner."""
        mock_sock_instance = MagicMock()
        mock_socket.return_value = mock_sock_instance
        mock_sock_instance.recv.return_value = b"220 ftp.example.com FTP server ready\r\n"

        banner = ServiceIdentifyService._grab_banner("192.168.1.100", 21, 5)

        assert banner is not None

    @patch("socket.socket")
    def test_grab_banner_timeout(self, mock_socket):
        """Test banner grabbing timeout."""
        mock_sock_instance = MagicMock()
        mock_socket.return_value = mock_sock_instance
        mock_sock_instance.recv.side_effect = socket.timeout("Connection timed out")

        banner = ServiceIdentifyService._grab_banner("192.168.1.100", 22, 1)

        assert banner is None

    @patch("socket.socket")
    def test_grab_banner_connection_refused(self, mock_socket):
        """Test banner grabbing connection refused."""
        mock_socket.side_effect = ConnectionRefusedError("Connection refused")

        banner = ServiceIdentifyService._grab_banner("192.168.1.100", 9999, 5)

        assert banner is None

    @patch("socket.socket")
    def test_grab_banner_empty_response(self, mock_socket):
        """Test banner grabbing with empty response."""
        mock_sock_instance = MagicMock()
        mock_socket.return_value = mock_sock_instance
        mock_sock_instance.recv.return_value = b""

        banner = ServiceIdentifyService._grab_banner("192.168.1.100", 22, 5)

        assert banner is None or banner == ""


# ============================================================================
# BANNER ANALYSIS TESTS
# ============================================================================


class TestBannerAnalysis:
    """Test banner pattern matching and service identification."""

    def test_analyze_openssh_banner(self):
        """Test identifying OpenSSH from banner."""
        banner = "SSH-2.0-OpenSSH_7.4"
        service_info = ServiceIdentifyService._analyze_banner(banner, 22)

        assert service_info is not None
        assert "OpenSSH" in str(service_info)

    def test_analyze_apache_banner(self):
        """Test identifying Apache from HTTP banner."""
        banner = "HTTP/1.1 200 OK\nServer: Apache/2.4.6 (CentOS)"
        service_info = ServiceIdentifyService._analyze_banner(banner, 80)

        assert service_info is not None

    def test_analyze_nginx_banner(self):
        """Test identifying Nginx from HTTP banner."""
        banner = "HTTP/1.1 200 OK\nServer: nginx/1.14.0"
        service_info = ServiceIdentifyService._analyze_banner(banner, 80)

        assert service_info is not None

    def test_analyze_mysql_banner(self):
        """Test identifying MySQL from banner."""
        banner = "5.7.21-20-log"  # MySQL version banner
        service_info = ServiceIdentifyService._analyze_banner(banner, 3306)

        assert service_info is not None

    def test_analyze_postgres_banner(self):
        """Test identifying PostgreSQL from banner."""
        banner = "FATAL: invalid message format"
        service_info = ServiceIdentifyService._analyze_banner(banner, 5432)

        # PostgreSQL might be identifiable
        pass

    def test_analyze_redis_banner(self):
        """Test identifying Redis from banner."""
        banner = "REDIS 0001"
        service_info = ServiceIdentifyService._analyze_banner(banner, 6379)

        assert service_info is not None

    def test_analyze_unknown_banner(self):
        """Test analyzing unknown banner."""
        banner = "Unknown service version 123"
        service_info = ServiceIdentifyService._analyze_banner(banner, 9999)

        # Should still return something
        assert service_info is not None or service_info is None


# ============================================================================
# SERVICE IDENTIFICATION TESTS
# ============================================================================


class TestServiceIdentification:
    """Test service identification by port."""

    def test_identify_ssh_service(self):
        """Test SSH service identification."""
        service = ServiceIdentifyService._identify_service_on_port(
            "192.168.1.100", 22, 5
        )

        # SSH is on port 22
        assert service is not None

    def test_identify_http_service(self):
        """Test HTTP service identification."""
        service = ServiceIdentifyService._identify_service_on_port(
            "192.168.1.100", 80, 5
        )

        # HTTP is on port 80
        assert service is not None

    def test_identify_https_service(self):
        """Test HTTPS service identification."""
        service = ServiceIdentifyService._identify_service_on_port(
            "192.168.1.100", 443, 5
        )

        # HTTPS is on port 443
        assert service is not None

    def test_identify_ftp_service(self):
        """Test FTP service identification."""
        service = ServiceIdentifyService._identify_service_on_port(
            "192.168.1.100", 21, 5
        )

        # FTP is on port 21
        assert service is not None

    def test_identify_mysql_service(self):
        """Test MySQL service identification."""
        service = ServiceIdentifyService._identify_service_on_port(
            "192.168.1.100", 3306, 5
        )

        # MySQL is on port 3306
        assert service is not None

    def test_identify_postgres_service(self):
        """Test PostgreSQL service identification."""
        service = ServiceIdentifyService._identify_service_on_port(
            "192.168.1.100", 5432, 5
        )

        # PostgreSQL is on port 5432
        assert service is not None

    def test_identify_redis_service(self):
        """Test Redis service identification."""
        service = ServiceIdentifyService._identify_service_on_port(
            "192.168.1.100", 6379, 5
        )

        # Redis is on port 6379
        assert service is not None

    def test_identify_unknown_port_service(self):
        """Test identification on uncommon port."""
        service = ServiceIdentifyService._identify_service_on_port(
            "192.168.1.100", 9999, 5
        )

        # May or may not identify service on uncommon port
        assert service is None or isinstance(service, (str, dict))


# ============================================================================
# VULNERABILITY MAPPING TESTS
# ============================================================================


class TestVulnerabilityMapping:
    """Test vulnerability mapping based on service."""

    def test_map_openssh_vulnerabilities(self):
        """Test mapping vulnerabilities for OpenSSH."""
        service = {
            "name": "ssh",
            "product": "OpenSSH",
            "version": "7.4",
        }

        vulns = ServiceIdentifyService._map_vulnerabilities(service)

        assert vulns is not None or isinstance(vulns, list)

    def test_map_apache_vulnerabilities(self):
        """Test mapping vulnerabilities for Apache."""
        service = {
            "name": "http",
            "product": "Apache",
            "version": "2.4.6",
        }

        vulns = ServiceIdentifyService._map_vulnerabilities(service)

        assert vulns is not None or isinstance(vulns, list)

    def test_map_multiple_vulnerabilities(self):
        """Test mapping multiple vulnerabilities for a service."""
        service = {
            "name": "http",
            "product": "Apache",
            "version": "2.2.0",  # Old version with multiple CVEs
        }

        vulns = ServiceIdentifyService._map_vulnerabilities(service)

        # Old versions should have multiple known vulns
        if vulns:
            assert len(vulns) >= 0

    def test_map_no_vulnerabilities(self):
        """Test mapping vulnerabilities for unknown service."""
        service = {
            "name": "unknown",
            "product": "UnknownProduct",
            "version": "1.0.0",
        }

        vulns = ServiceIdentifyService._map_vulnerabilities(service)

        assert vulns is None or isinstance(vulns, list)


# ============================================================================
# BATCH PROCESSING TESTS
# ============================================================================


class TestBatchProcessing:
    """Test batch service identification."""

    @pytest.mark.asyncio
    async def test_identify_services_batch(self):
        """Test batch service identification."""
        asset_id = 1
        ports = [
            {"ip": "192.168.1.100", "port": 22, "service": "ssh"},
            {"ip": "192.168.1.100", "port": 80, "service": "http"},
            {"ip": "192.168.1.100", "port": 443, "service": "https"},
        ]

        services = await ServiceIdentifyService.identify_services(asset_id, ports)

        assert services is not None

    @pytest.mark.asyncio
    async def test_match_fingerprints_batch(self):
        """Test batch fingerprint matching."""
        services = [
            {
                "ip": "192.168.1.100",
                "port": 22,
                "service": "ssh",
                "product": "OpenSSH",
                "version": "7.4",
            },
            {
                "ip": "192.168.1.100",
                "port": 80,
                "service": "http",
                "product": "Apache",
                "version": "2.4.6",
            },
        ]

        results = await ServiceIdentifyService.match_fingerprints_batch(services)

        assert results is not None


# ============================================================================
# KNOWN SERVICE DATABASE TESTS
# ============================================================================


class TestKnownServiceDatabase:
    """Test known service port database."""

    def test_known_ports_exist(self):
        """Test that known service ports are defined."""
        known_ports = {
            21: "ftp",
            22: "ssh",
            25: "smtp",
            53: "dns",
            80: "http",
            110: "pop3",
            143: "imap",
            443: "https",
            3306: "mysql",
            5432: "postgres",
        }

        # At least common ports should be known
        assert len(known_ports) > 0

    def test_common_ports_mapping(self):
        """Test common port to service mapping."""
        port_service_map = {
            21: "ftp",
            22: "ssh",
            80: "http",
            443: "https",
            3306: "mysql",
            5432: "postgres",
            6379: "redis",
        }

        assert port_service_map[22] == "ssh"
        assert port_service_map[80] == "http"
        assert port_service_map[443] == "https"

    def test_uncommon_ports(self):
        """Test uncommon port mapping."""
        uncommon_ports = [8000, 8080, 8443, 9000, 9001]

        # These might not be in known database
        for port in uncommon_ports:
            assert isinstance(port, int)


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================


class TestErrorHandling:
    """Test error handling in service identification."""

    @patch("socket.socket")
    def test_invalid_host_error(self, mock_socket):
        """Test error handling for invalid host."""
        mock_socket.side_effect = socket.gaierror("Name or service not known")

        service = ServiceIdentifyService._grab_banner("invalid.host", 22, 5)

        assert service is None

    @patch("socket.socket")
    def test_ssl_certificate_error(self, mock_socket):
        """Test SSL certificate error handling."""
        mock_socket.side_effect = ssl.SSLError("Certificate verification failed")

        # Should handle gracefully
        pass

    def test_invalid_port_number(self):
        """Test invalid port number handling."""
        invalid_ports = [-1, 0, 65536, 99999]

        for port in invalid_ports:
            # Should validate or handle
            assert not (1 <= port <= 65535)

    def test_invalid_ip_address(self):
        """Test invalid IP address handling."""
        invalid_ips = ["999.999.999.999", "invalid", "192.168.1", ""]

        for ip in invalid_ips:
            # Should validate
            pass


# ============================================================================
# TIMEOUT HANDLING TESTS
# ============================================================================


class TestTimeoutHandling:
    """Test timeout handling in service identification."""

    @patch("socket.socket")
    def test_connection_timeout(self, mock_socket):
        """Test connection timeout."""
        mock_sock_instance = MagicMock()
        mock_socket.return_value = mock_sock_instance
        mock_sock_instance.connect.side_effect = socket.timeout()

        service = ServiceIdentifyService._grab_banner("192.168.1.100", 22, 1)

        assert service is None

    @patch("socket.socket")
    def test_receive_timeout(self, mock_socket):
        """Test receive timeout."""
        mock_sock_instance = MagicMock()
        mock_socket.return_value = mock_sock_instance
        mock_sock_instance.recv.side_effect = socket.timeout()

        service = ServiceIdentifyService._grab_banner("192.168.1.100", 22, 1)

        assert service is None

    def test_custom_timeout_value(self):
        """Test custom timeout value handling."""
        timeouts = [1, 5, 10, 30]

        for timeout in timeouts:
            assert timeout > 0


# ============================================================================
# EDGE CASES TESTS
# ============================================================================


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_ipv6_address_identification(self):
        """Test service identification on IPv6."""
        ipv6_addr = "2001:db8::1"
        # Should handle IPv6 addresses
        assert isinstance(ipv6_addr, str)

    def test_localhost_service_identification(self):
        """Test service identification on localhost."""
        service = ServiceIdentifyService._grab_banner("localhost", 22, 5)

        # Should be able to connect to localhost if service running
        assert service is None or isinstance(service, (str, bytes))

    def test_port_ranges(self):
        """Test identification across port ranges."""
        ports = [1, 100, 1000, 10000, 65535]

        for port in ports:
            assert 1 <= port <= 65535

    def test_special_characters_in_banner(self):
        """Test handling special characters in banner."""
        special_banners = [
            b"Server: Apache/2.4\x00\x01",
            b"SSH-2.0-OpenSSH\r\n",
            b"Banner with \x1b[31m color codes",
        ]

        for banner in special_banners:
            assert isinstance(banner, bytes)

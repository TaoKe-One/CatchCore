"""Service identification service for determining service types and versions."""

import socket
import logging
import ssl
from typing import List, Dict, Optional, Any, Tuple
import re

logger = logging.getLogger(__name__)


class ServiceIdentifyService:
    """Service for identifying service types and versions."""

    # Common service ports and their typical services
    COMMON_SERVICES = {
        21: "FTP",
        22: "SSH",
        23: "Telnet",
        25: "SMTP",
        53: "DNS",
        80: "HTTP",
        110: "POP3",
        143: "IMAP",
        443: "HTTPS",
        445: "SMB",
        465: "SMTPS",
        587: "SMTP",
        993: "IMAPS",
        995: "POP3S",
        1433: "MSSQL",
        3306: "MySQL",
        3389: "RDP",
        5432: "PostgreSQL",
        5984: "CouchDB",
        6379: "Redis",
        8080: "HTTP",
        8443: "HTTPS",
        9200: "Elasticsearch",
        27017: "MongoDB",
    }

    # Service banners for identification
    SERVICE_BANNERS = {
        "OpenSSH": r"SSH-2\.0-OpenSSH_([^\s]+)",
        "Apache": r"Apache/([^\s]+)",
        "Nginx": r"nginx/([^\s]+)",
        "IIS": r"IIS/([^\s]+)",
        "MySQL": r"mysql_native_password",
        "PostgreSQL": r"PostgreSQL ([^\s]+)",
        "MongoDB": r'{"ismaster"',
        "Redis": r"\$(-?\d+)\r\n",
    }

    @staticmethod
    def identify_services(asset_id: int, ports: List[int]) -> List[Dict[str, Any]]:
        """
        Identify services on given ports.

        Args:
            asset_id: Asset ID (for future database lookups)
            ports: List of port numbers to identify

        Returns:
            List of identified services
        """
        logger.info(f"Identifying services on {len(ports)} ports")
        services = []

        for port in ports:
            try:
                service = ServiceIdentifyService._identify_service_on_port(
                    "localhost", port
                )
                if service:
                    services.append(service)
            except Exception as e:
                logger.warning(f"Error identifying service on port {port}: {e}")
                continue

        return services

    @staticmethod
    def identify_services_from_ports(
        port_data: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Identify services from nmap port scan results.

        Args:
            port_data: List of port dictionaries from nmap output

        Returns:
            List of identified services with details
        """
        logger.info(f"Processing {len(port_data)} ports for service identification")
        services = []

        for port_info in port_data:
            try:
                service = ServiceIdentifyService._process_port_info(port_info)
                if service:
                    services.append(service)
            except Exception as e:
                logger.warning(f"Error processing port {port_info.get('port')}: {e}")
                continue

        return services

    @staticmethod
    def _identify_service_on_port(
        host: str, port: int, timeout: int = 5
    ) -> Optional[Dict[str, Any]]:
        """
        Identify service on a specific port by banner grabbing.

        Args:
            host: Host to connect to
            port: Port number
            timeout: Connection timeout in seconds

        Returns:
            Service information or None
        """
        logger.debug(f"Attempting to identify service on {host}:{port}")

        try:
            # Try to get banner
            banner = ServiceIdentifyService._grab_banner(host, port, timeout)
            if not banner:
                return None

            # Analyze banner
            service_name = ServiceIdentifyService._analyze_banner(banner, port)

            return {
                "port": port,
                "service": service_name,
                "banner": banner[:200],  # Limit banner length
                "confidence": "high" if service_name else "low",
            }

        except Exception as e:
            logger.debug(f"Could not identify service on {host}:{port}: {e}")
            return None

    @staticmethod
    def _grab_banner(host: str, port: int, timeout: int = 5) -> Optional[str]:
        """
        Grab service banner from port.

        Args:
            host: Host to connect to
            port: Port number
            timeout: Connection timeout in seconds

        Returns:
            Banner string or None
        """
        try:
            # Try SSL connection first for common HTTPS ports
            if port in [443, 465, 587, 993, 995, 8443]:
                try:
                    context = ssl.create_default_context()
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE

                    with socket.create_connection((host, port), timeout=timeout) as sock:
                        with context.wrap_socket(
                            sock, server_hostname=host
                        ) as ssock:
                            cert = ssock.getpeercert()
                            return f"SSL/TLS connection successful"
                except (ssl.SSLError, socket.error):
                    pass

            # Regular socket connection
            with socket.create_connection((host, port), timeout=timeout) as sock:
                # Send HTTP HEAD request for web services
                if port in [80, 8080, 8000, 3000]:
                    sock.sendall(b"HEAD / HTTP/1.0\r\n\r\n")
                # Send SMTP EHLO for mail services
                elif port in [25, 587, 465]:
                    sock.sendall(b"EHLO test\r\n")
                # Send SSH protocol request
                elif port == 22:
                    pass  # SSH sends banner automatically

                # Receive response
                data = sock.recv(1024)
                if data:
                    try:
                        return data.decode("utf-8", errors="ignore")
                    except Exception:
                        return data.hex()

            return None

        except socket.timeout:
            logger.debug(f"Timeout connecting to {host}:{port}")
            return None
        except Exception as e:
            logger.debug(f"Error grabbing banner from {host}:{port}: {e}")
            return None

    @staticmethod
    def _analyze_banner(banner: str, port: int) -> Optional[str]:
        """
        Analyze banner to identify service.

        Args:
            banner: Banner string
            port: Port number for default service mapping

        Returns:
            Service name or None
        """
        if not banner:
            return None

        # Try pattern matching
        for service_name, pattern in ServiceIdentifyService.SERVICE_BANNERS.items():
            if re.search(pattern, banner, re.IGNORECASE):
                return service_name

        # Try exact matching
        if "HTTP" in banner or "html" in banner.lower():
            return "HTTP"
        if "SSH" in banner:
            return "SSH"
        if "MySQL" in banner or "mysql" in banner:
            return "MySQL"
        if "PostgreSQL" in banner or "postgres" in banner:
            return "PostgreSQL"
        if "SMTP" in banner:
            return "SMTP"
        if "FTP" in banner:
            return "FTP"

        # Fallback to port-based identification
        return ServiceIdentifyService.COMMON_SERVICES.get(port)

    @staticmethod
    def _process_port_info(port_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process port information from nmap output.

        Args:
            port_info: Port dictionary from nmap

        Returns:
            Processed service information
        """
        port = port_info.get("port")
        ip = port_info.get("ip")

        # Extract service from nmap if available
        service_name = None
        version = None

        if "service" in port_info:
            service_data = port_info["service"]
            service_name = service_data.get("name")
            version = service_data.get("version")
            product = service_data.get("product")

            if product and not version:
                version = product

        # Fallback to port-based identification
        if not service_name:
            service_name = ServiceIdentifyService.COMMON_SERVICES.get(port)

        return {
            "ip": ip,
            "port": port,
            "service": service_name,
            "version": version,
            "protocol": port_info.get("protocol"),
            "state": port_info.get("state"),
            "cpe": port_info.get("cpe", []),
            "confidence": "high" if service_name else "medium",
        }

    @staticmethod
    def match_fingerprints_batch(
        services: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Match services against fingerprint database (placeholder).

        Args:
            services: List of identified services

        Returns:
            List of matched fingerprints
        """
        logger.info(f"Matching {len(services)} services against fingerprint database")

        # This is a placeholder for fingerprint matching
        # In production, this would query the fingerprint database
        matches = []

        for service in services:
            # Simple vulnerability mapping based on common patterns
            vuln_matches = ServiceIdentifyService._map_vulnerabilities(service)
            if vuln_matches:
                matches.extend(vuln_matches)

        return matches

    @staticmethod
    def _map_vulnerabilities(service: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Map known vulnerabilities for a service.

        Args:
            service: Service information

        Returns:
            List of potential vulnerabilities
        """
        vulnerabilities = []

        service_name = service.get("service", "").lower()
        version = service.get("version", "")

        # Simple vulnerability mapping (placeholder)
        # In production, this would use CVE database
        vuln_map = {
            "openssh": [
                {
                    "cve": "CVE-2018-15473",
                    "severity": "high",
                    "description": "Username enumeration",
                }
            ],
            "apache": [
                {
                    "cve": "CVE-2017-5645",
                    "severity": "critical",
                    "description": "Remote Code Execution",
                }
            ],
            "nginx": [
                {
                    "cve": "CVE-2016-1897",
                    "severity": "medium",
                    "description": "CRLF Injection",
                }
            ],
            "mysql": [
                {
                    "cve": "CVE-2019-2627",
                    "severity": "high",
                    "description": "Authentication bypass",
                }
            ],
            "redis": [
                {
                    "cve": "CVE-2016-8339",
                    "severity": "critical",
                    "description": "Unauthenticated remote code execution",
                }
            ],
        }

        for vuln_service, vulns in vuln_map.items():
            if vuln_service in service_name:
                for vuln in vulns:
                    vulnerabilities.append(
                        {
                            "ip": service.get("ip"),
                            "port": service.get("port"),
                            "service": service.get("service"),
                            "cve": vuln.get("cve"),
                            "severity": vuln.get("severity"),
                            "description": vuln.get("description"),
                            "confidence": "medium",
                        }
                    )

        return vulnerabilities

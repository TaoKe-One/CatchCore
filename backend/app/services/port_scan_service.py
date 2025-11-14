"""Port scanning service using nmap."""

import subprocess
import logging
import re
import json
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional, Any

logger = logging.getLogger(__name__)


class PortScanService:
    """Service for port scanning using nmap."""

    # Common ports for quick scans
    COMMON_PORTS = "22,25,53,80,110,143,443,445,465,587,993,995,3306,3389,5432,5984,6379,8080,8443,9200,27017"

    @staticmethod
    def scan_with_nmap(
        target: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute nmap port scan.

        Args:
            target: Target IP or CIDR range
            options: Optional scan parameters
                - ports: Port range (default: 1-65535)
                - timing: Timing template T0-T5 (default: 4)
                - scan_type: syn, connect, udp (default: syn)
                - skip_ping: Skip ping check (default: True)
                - service_detection: Enable service detection (default: True)
                - os_detection: Enable OS detection (default: False)

        Returns:
            List of discovered ports with details
        """
        if options is None:
            options = {}

        ports = options.get("ports", "1-65535")
        timing = options.get("timing", "4")
        scan_type = options.get("scan_type", "syn")
        skip_ping = options.get("skip_ping", True)
        service_detection = options.get("service_detection", True)
        os_detection = options.get("os_detection", False)

        logger.info(f"Starting nmap scan on {target} with ports {ports}")

        try:
            # Build nmap command
            cmd = ["nmap"]

            # Output format: XML (parseable)
            cmd.extend(["-oX", "-"])

            # Skip ping if requested
            if skip_ping:
                cmd.append("-Pn")

            # Set timing template
            cmd.extend(["-T", str(timing)])

            # Set scan type
            if scan_type == "syn":
                cmd.append("-sS")  # SYN scan (default for privileged users)
            elif scan_type == "connect":
                cmd.append("-sT")  # Connect scan
            elif scan_type == "udp":
                cmd.append("-sU")  # UDP scan
            else:
                cmd.append("-sS")  # Default to SYN

            # Port specification
            cmd.extend(["-p", ports])

            # Service detection
            if service_detection:
                cmd.append("-sV")

            # OS detection
            if os_detection:
                cmd.append("-O")

            # Target
            cmd.append(target)

            logger.debug(f"Executing command: {' '.join(cmd)}")

            # Execute nmap
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=15 * 60,  # 15 minute timeout
            )

            if result.returncode not in [0, 1]:  # 0 = success, 1 = warning
                logger.error(f"nmap error: {result.stderr}")
                raise RuntimeError(f"nmap failed: {result.stderr}")

            # Parse XML output
            ports_data = PortScanService._parse_nmap_xml(result.stdout)
            logger.info(f"Scan completed: {len(ports_data)} ports found")

            return ports_data

        except subprocess.TimeoutExpired:
            logger.error(f"nmap scan timeout for {target}")
            raise TimeoutError(f"nmap scan timeout for {target}")
        except FileNotFoundError:
            logger.error("nmap not found. Please install nmap")
            raise RuntimeError("nmap not installed")
        except Exception as e:
            logger.error(f"nmap scan error: {e}")
            raise

    @staticmethod
    def _parse_nmap_xml(xml_output: str) -> List[Dict[str, Any]]:
        """
        Parse nmap XML output.

        Args:
            xml_output: XML string from nmap

        Returns:
            List of port dictionaries
        """
        ports = []

        try:
            root = ET.fromstring(xml_output)

            for host in root.findall(".//host"):
                # Get host IP
                host_ip = None
                for addr in host.findall("address"):
                    if addr.get("addrtype") == "ipv4":
                        host_ip = addr.get("addr")
                        break

                if not host_ip:
                    continue

                # Get host status
                host_status = None
                host_status_elem = host.find("status")
                if host_status_elem is not None:
                    host_status = host_status_elem.get("state")

                # Parse ports
                for port_elem in host.findall(".//port"):
                    port_num = port_elem.get("portid")
                    protocol = port_elem.get("protocol")

                    state_elem = port_elem.find("state")
                    state = state_elem.get("state") if state_elem is not None else "unknown"

                    # Only include open ports
                    if state != "open":
                        continue

                    port_data = {
                        "ip": host_ip,
                        "port": int(port_num),
                        "protocol": protocol,
                        "state": state,
                    }

                    # Get service information
                    service_elem = port_elem.find("service")
                    if service_elem is not None:
                        service_data = {
                            "name": service_elem.get("name"),
                            "product": service_elem.get("product"),
                            "version": service_elem.get("version"),
                            "extrainfo": service_elem.get("extrainfo"),
                            "ostype": service_elem.get("ostype"),
                            "method": service_elem.get("method"),
                            "conf": service_elem.get("conf"),
                        }
                        # Remove None values
                        port_data["service"] = {
                            k: v for k, v in service_data.items() if v is not None
                        }

                    # Get CPE information (if available)
                    cpe_list = []
                    for cpe_elem in port_elem.findall(".//cpe"):
                        if cpe_elem.text:
                            cpe_list.append(cpe_elem.text)
                    if cpe_list:
                        port_data["cpe"] = cpe_list

                    ports.append(port_data)

            logger.debug(f"Parsed {len(ports)} open ports from nmap output")
            return ports

        except ET.ParseError as e:
            logger.error(f"Failed to parse nmap XML: {e}")
            raise RuntimeError(f"Failed to parse nmap output: {e}")

    @staticmethod
    def scan_quick(target: str) -> List[Dict[str, Any]]:
        """
        Quick scan of common ports.

        Args:
            target: Target IP or range

        Returns:
            List of discovered ports
        """
        logger.info(f"Starting quick scan on {target}")
        return PortScanService.scan_with_nmap(
            target,
            options={
                "ports": PortScanService.COMMON_PORTS,
                "timing": "4",
                "service_detection": True,
            },
        )

    @staticmethod
    def scan_aggressive(target: str) -> List[Dict[str, Any]]:
        """
        Aggressive scan with all ports and OS detection.

        Args:
            target: Target IP or range

        Returns:
            List of discovered ports
        """
        logger.info(f"Starting aggressive scan on {target}")
        return PortScanService.scan_with_nmap(
            target,
            options={
                "ports": "1-65535",
                "timing": "3",
                "service_detection": True,
                "os_detection": True,
            },
        )

    @staticmethod
    def validate_target(target: str) -> bool:
        """
        Validate target IP or CIDR.

        Args:
            target: IP address or CIDR range

        Returns:
            True if valid, False otherwise
        """
        # Simple regex for IP validation
        ipv4_pattern = r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}(?:/[0-9]{1,2})?$"
        ipv6_pattern = r"^(?:[0-9a-f]{0,4}:){2,7}[0-9a-f]{0,4}(?:/[0-9]{1,3})?$"

        return bool(
            re.match(ipv4_pattern, target) or re.match(ipv6_pattern, target, re.I)
        )

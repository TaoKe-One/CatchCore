"""Integration with external security tools (afrog, dddd, fscan, nuclei, dirsearch)."""

import subprocess
import logging
import json
import os
import re
from typing import List, Dict, Optional, Any
from pathlib import Path
from datetime import datetime
import shutil

logger = logging.getLogger(__name__)


class ToolIntegration:
    """Service for integrating external security scanning tools."""

    # Tool detection and paths
    TOOLS = {
        "afrog": {
            "name": "Afrog",
            "description": "Framework for security scanning and PoC verification",
            "url": "https://github.com/zan8in/afrog",
            "capabilities": ["vulnerability_scanning", "poc_execution"],
            "output_format": "json",
        },
        "dddd": {
            "name": "DDDD",
            "description": "Advanced vulnerability scanning tool",
            "url": "https://github.com/SleepingBag945/dddd",
            "capabilities": ["vulnerability_scanning", "host_discovery"],
            "output_format": "json",
        },
        "fscan": {
            "name": "FScan",
            "description": "High-performance network scanner",
            "url": "https://github.com/shadow1ng/fscan",
            "capabilities": ["port_scanning", "service_detection"],
            "output_format": "json",
        },
        "nuclei": {
            "name": "Nuclei",
            "description": "Fast and customizable vulnerability scanner",
            "url": "https://github.com/projectdiscovery/nuclei",
            "capabilities": ["vulnerability_scanning", "poc_execution", "web_scanning"],
            "output_format": "json",
        },
        "dirsearch": {
            "name": "DirSearch",
            "description": "Directory enumeration and discovery tool",
            "url": "https://github.com/maurosoria/dirsearch",
            "capabilities": ["directory_enumeration", "web_enumeration"],
            "output_format": "text",
        },
    }

    @staticmethod
    def check_tool_installed(tool_name: str) -> bool:
        """
        Check if a tool is installed on the system.

        Args:
            tool_name: Name of the tool (afrog, dddd, fscan, nuclei, dirsearch)

        Returns:
            True if tool is installed, False otherwise
        """
        try:
            result = shutil.which(tool_name)
            if result:
                logger.info(f"Tool '{tool_name}' found at: {result}")
                return True

            # Alternative check - try running the tool with help flag
            result = subprocess.run(
                [tool_name, "-h"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0 or "help" in result.stdout.lower()

        except Exception as e:
            logger.warning(f"Tool '{tool_name}' not found: {e}")
            return False

    @staticmethod
    def get_installed_tools() -> Dict[str, bool]:
        """
        Get list of installed tools.

        Returns:
            Dictionary with tool names and installation status
        """
        installed = {}
        for tool_name in ToolIntegration.TOOLS.keys():
            installed[tool_name] = ToolIntegration.check_tool_installed(tool_name)
        return installed

    @staticmethod
    async def scan_with_afrog(
        target: str,
        poc_file: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute Afrog vulnerability scan.

        Args:
            target: Target URL or IP
            poc_file: Path to POC file
            options: Additional options

        Returns:
            Scan results
        """
        if options is None:
            options = {}

        logger.info(f"Starting Afrog scan on {target}")

        try:
            cmd = ["afrog", "-t", target]

            if poc_file and os.path.exists(poc_file):
                cmd.extend(["-poc", poc_file])

            # Add output format
            cmd.extend(["-o", "json"])

            # Add timeout
            if options.get("timeout"):
                cmd.extend(["-timeout", str(options["timeout"])])

            # Add thread count
            if options.get("threads"):
                cmd.extend(["-thread", str(options["threads"])])

            logger.debug(f"Executing: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes
            )

            # Parse JSON output
            vulnerabilities = []
            try:
                output = json.loads(result.stdout)
                if isinstance(output, list):
                    vulnerabilities = output
                elif isinstance(output, dict) and "results" in output:
                    vulnerabilities = output["results"]
            except json.JSONDecodeError:
                logger.warning("Failed to parse Afrog JSON output")
                vulnerabilities = []

            return {
                "tool": "afrog",
                "target": target,
                "status": "success" if result.returncode == 0 else "warning",
                "vulnerabilities_found": len(vulnerabilities),
                "results": vulnerabilities,
                "raw_output": result.stdout[:1000],  # First 1000 chars
            }

        except FileNotFoundError:
            logger.error("Afrog not found. Please install: https://github.com/zan8in/afrog")
            return {
                "tool": "afrog",
                "target": target,
                "status": "error",
                "error": "Afrog not installed",
            }

        except subprocess.TimeoutExpired:
            return {
                "tool": "afrog",
                "target": target,
                "status": "error",
                "error": "Scan timeout",
            }

        except Exception as e:
            logger.error(f"Afrog scan error: {e}")
            return {
                "tool": "afrog",
                "target": target,
                "status": "error",
                "error": str(e),
            }

    @staticmethod
    async def scan_with_dddd(
        target: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute DDDD vulnerability scan.

        Args:
            target: Target IP or domain
            options: Additional options

        Returns:
            Scan results
        """
        if options is None:
            options = {}

        logger.info(f"Starting DDDD scan on {target}")

        try:
            cmd = ["dddd", "-u", target]

            # Add output format
            if options.get("output_format"):
                cmd.extend(["-of", options["output_format"]])

            # Add timeout
            if options.get("timeout"):
                cmd.extend(["-timeout", str(options["timeout"])])

            logger.debug(f"Executing: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )

            # Parse output
            vulnerabilities = []
            try:
                output = json.loads(result.stdout)
                if isinstance(output, list):
                    vulnerabilities = output
                elif isinstance(output, dict) and "data" in output:
                    vulnerabilities = output["data"]
            except json.JSONDecodeError:
                logger.warning("Failed to parse DDDD JSON output")

            return {
                "tool": "dddd",
                "target": target,
                "status": "success" if result.returncode == 0 else "warning",
                "vulnerabilities_found": len(vulnerabilities),
                "results": vulnerabilities,
                "raw_output": result.stdout[:1000],
            }

        except FileNotFoundError:
            logger.error("DDDD not found. Please install: https://github.com/SleepingBag945/dddd")
            return {
                "tool": "dddd",
                "target": target,
                "status": "error",
                "error": "DDDD not installed",
            }

        except Exception as e:
            logger.error(f"DDDD scan error: {e}")
            return {
                "tool": "dddd",
                "target": target,
                "status": "error",
                "error": str(e),
            }

    @staticmethod
    async def scan_with_fscan(
        target: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute FScan port and service scan.

        Args:
            target: Target IP or CIDR range
            options: Additional options

        Returns:
            Scan results
        """
        if options is None:
            options = {}

        logger.info(f"Starting FScan on {target}")

        try:
            cmd = ["fscan"]

            # Target
            if "/" in target:
                cmd.extend(["-cidr", target])
            else:
                cmd.extend(["-h", target])

            # Add ports
            if options.get("ports"):
                cmd.extend(["-p", options["ports"]])

            # Add timeout
            if options.get("timeout"):
                cmd.extend(["-time", str(options["timeout"])])

            # Add thread count
            if options.get("threads"):
                cmd.extend(["-thread", str(options["threads"])])

            # JSON output
            cmd.append("-json")

            logger.debug(f"Executing: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minutes
            )

            # Parse results
            ports = []
            try:
                # FScan outputs one JSON object per line
                for line in result.stdout.split('\n'):
                    if line.strip():
                        try:
                            obj = json.loads(line)
                            ports.append(obj)
                        except json.JSONDecodeError:
                            pass
            except Exception as e:
                logger.warning(f"Failed to parse FScan output: {e}")

            return {
                "tool": "fscan",
                "target": target,
                "status": "success" if result.returncode == 0 else "warning",
                "ports_found": len(ports),
                "results": ports,
                "raw_output": result.stdout[:1000],
            }

        except FileNotFoundError:
            logger.error("FScan not found. Please install: https://github.com/shadow1ng/fscan")
            return {
                "tool": "fscan",
                "target": target,
                "status": "error",
                "error": "FScan not installed",
            }

        except Exception as e:
            logger.error(f"FScan scan error: {e}")
            return {
                "tool": "fscan",
                "target": target,
                "status": "error",
                "error": str(e),
            }

    @staticmethod
    async def scan_with_nuclei(
        target: str,
        templates: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute Nuclei vulnerability scan.

        Args:
            target: Target URL or IP
            templates: Template filter
            options: Additional options

        Returns:
            Scan results
        """
        if options is None:
            options = {}

        logger.info(f"Starting Nuclei scan on {target}")

        try:
            cmd = ["nuclei", "-target", target]

            # Add templates
            if templates:
                cmd.extend(["-t", templates])
            else:
                # Use default templates if not specified
                cmd.extend(["-t", "cves,osint"])

            # Output format
            cmd.extend(["-o", "/tmp/nuclei_output.json", "-json"])

            # Add timeout
            if options.get("timeout"):
                cmd.extend(["-timeout", str(options["timeout"])])

            # Add severity filter
            if options.get("severity"):
                cmd.extend(["-severity", options["severity"]])

            # Concurrency
            if options.get("threads"):
                cmd.extend(["-c", str(options["threads"])])

            logger.debug(f"Executing: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,
            )

            # Parse output
            vulnerabilities = []
            output_file = "/tmp/nuclei_output.json"

            if os.path.exists(output_file):
                try:
                    with open(output_file, 'r') as f:
                        for line in f:
                            if line.strip():
                                try:
                                    obj = json.loads(line)
                                    vulnerabilities.append(obj)
                                except json.JSONDecodeError:
                                    pass
                    os.remove(output_file)
                except Exception as e:
                    logger.warning(f"Failed to read Nuclei output: {e}")

            return {
                "tool": "nuclei",
                "target": target,
                "status": "success" if result.returncode == 0 else "warning",
                "vulnerabilities_found": len(vulnerabilities),
                "results": vulnerabilities,
                "raw_output": result.stderr[:1000],  # Nuclei uses stderr
            }

        except FileNotFoundError:
            logger.error("Nuclei not found. Please install: https://github.com/projectdiscovery/nuclei")
            return {
                "tool": "nuclei",
                "target": target,
                "status": "error",
                "error": "Nuclei not installed",
            }

        except Exception as e:
            logger.error(f"Nuclei scan error: {e}")
            return {
                "tool": "nuclei",
                "target": target,
                "status": "error",
                "error": str(e),
            }

    @staticmethod
    async def scan_with_dirsearch(
        target: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute DirSearch directory enumeration.

        Args:
            target: Target URL
            options: Additional options

        Returns:
            Scan results
        """
        if options is None:
            options = {}

        logger.info(f"Starting DirSearch on {target}")

        try:
            cmd = ["dirsearch", "-u", target]

            # Add wordlist
            if options.get("wordlist"):
                cmd.extend(["-w", options["wordlist"]])
            else:
                # Use default wordlist
                cmd.append("-r")

            # Add extensions
            if options.get("extensions"):
                cmd.extend(["-e", options["extensions"]])

            # Output format
            cmd.extend(["-o", "/tmp/dirsearch_output.json", "-f"])

            # Timeout
            if options.get("timeout"):
                cmd.extend(["-t", str(options["timeout"])])

            # Thread count
            if options.get("threads"):
                cmd.extend(["-T", str(options["threads"])])

            logger.debug(f"Executing: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,
            )

            # Parse output
            directories = []
            output_file = "/tmp/dirsearch_output.json"

            if os.path.exists(output_file):
                try:
                    with open(output_file, 'r') as f:
                        output = json.load(f)
                        if isinstance(output, list):
                            directories = output
                        elif isinstance(output, dict) and "results" in output:
                            directories = output["results"]
                    os.remove(output_file)
                except Exception as e:
                    logger.warning(f"Failed to parse DirSearch output: {e}")

            return {
                "tool": "dirsearch",
                "target": target,
                "status": "success" if result.returncode == 0 else "warning",
                "directories_found": len(directories),
                "results": directories,
                "raw_output": result.stdout[:1000],
            }

        except FileNotFoundError:
            logger.error("DirSearch not found. Please install: https://github.com/maurosoria/dirsearch")
            return {
                "tool": "dirsearch",
                "target": target,
                "status": "error",
                "error": "DirSearch not installed",
            }

        except Exception as e:
            logger.error(f"DirSearch scan error: {e}")
            return {
                "tool": "dirsearch",
                "target": target,
                "status": "error",
                "error": str(e),
            }

    @staticmethod
    async def execute_tool_chain(
        target: str,
        tools: List[str],
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute multiple tools in sequence.

        Args:
            target: Target IP or URL
            tools: List of tools to execute (afrog, dddd, fscan, nuclei, dirsearch)
            options: Options for all tools

        Returns:
            Combined results from all tools
        """
        if options is None:
            options = {}

        logger.info(f"Starting tool chain on {target} with tools: {tools}")

        results = {
            "target": target,
            "timestamp": datetime.now().isoformat(),
            "tools_executed": [],
            "total_vulnerabilities": 0,
            "total_services": 0,
            "total_directories": 0,
            "tool_results": {},
        }

        for tool in tools:
            tool = tool.lower()

            if tool not in ToolIntegration.TOOLS:
                logger.warning(f"Unknown tool: {tool}")
                continue

            if not ToolIntegration.check_tool_installed(tool):
                logger.warning(f"Tool not installed: {tool}")
                results["tool_results"][tool] = {
                    "status": "error",
                    "error": f"{tool} not installed",
                }
                continue

            try:
                if tool == "afrog":
                    result = await ToolIntegration.scan_with_afrog(target, options=options)

                elif tool == "dddd":
                    result = await ToolIntegration.scan_with_dddd(target, options=options)

                elif tool == "fscan":
                    result = await ToolIntegration.scan_with_fscan(target, options=options)

                elif tool == "nuclei":
                    result = await ToolIntegration.scan_with_nuclei(target, options=options)

                elif tool == "dirsearch":
                    # Check if target is URL
                    if not target.startswith(("http://", "https://")):
                        logger.warning(f"DirSearch requires URL target, skipping for {target}")
                        continue

                    result = await ToolIntegration.scan_with_dirsearch(target, options=options)

                results["tool_results"][tool] = result
                results["tools_executed"].append(tool)

                # Aggregate results
                if "vulnerabilities_found" in result:
                    results["total_vulnerabilities"] += result["vulnerabilities_found"]

                if "ports_found" in result:
                    results["total_services"] += result["ports_found"]

                if "directories_found" in result:
                    results["total_directories"] += result["directories_found"]

            except Exception as e:
                logger.error(f"Error executing {tool}: {e}")
                results["tool_results"][tool] = {
                    "status": "error",
                    "error": str(e),
                }

        return results

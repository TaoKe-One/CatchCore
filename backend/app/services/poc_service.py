"""POC management and execution service."""

import logging
import subprocess
import json
import re
import yaml
from typing import List, Dict, Optional, Any
from datetime import datetime
import time

logger = logging.getLogger(__name__)


class POCService:
    """Service for managing and executing POCs."""

    # Supported POC types and their execution methods
    SUPPORTED_TYPES = {
        "nuclei": "nuclei",
        "afrog": "afrog",
        "custom": "custom",
        "http": "http",
        "bash": "bash",
        "metasploit": "metasploit",
    }

    @staticmethod
    def validate_poc_content(content: str, poc_type: str) -> bool:
        """
        Validate POC content format.

        Args:
            content: POC script/YAML content
            poc_type: Type of POC

        Returns:
            True if valid, False otherwise
        """
        if not content or not content.strip():
            return False

        if poc_type == "nuclei":
            try:
                # Nuclei POCs are YAML files
                yaml.safe_load(content)
                return True
            except yaml.YAMLError:
                logger.warning(f"Invalid nuclei YAML: {content[:100]}")
                return False

        elif poc_type == "custom" or poc_type == "bash":
            # Custom scripts should at least have shebang or common patterns
            return "#" in content or "#!/" in content or "curl" in content or "python" in content

        elif poc_type == "http":
            # HTTP POCs should have HTTP methods
            return any(method in content.upper() for method in ["GET", "POST", "PUT", "DELETE"])

        # For other types, just check if content exists
        return True

    @staticmethod
    async def execute_poc(
        target: str,
        port: Optional[int] = None,
        poc_content: str = "",
        poc_type: str = "http",
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a POC against a target.

        Args:
            target: Target IP or hostname
            port: Target port (optional)
            poc_content: POC script/YAML content
            poc_type: Type of POC
            options: Additional execution options

        Returns:
            Execution result dictionary
        """
        if options is None:
            options = {}

        logger.info(f"Executing {poc_type} POC on {target}:{port}")

        start_time = time.time()
        result = {
            "target": target,
            "port": port,
            "vulnerable": False,
            "output": "",
            "error": None,
            "execution_time": 0.0,
        }

        try:
            if poc_type == "nuclei":
                result = await POCService._execute_nuclei(target, port, poc_content, options)

            elif poc_type == "http":
                result = await POCService._execute_http_poc(target, port, poc_content, options)

            elif poc_type == "custom" or poc_type == "bash":
                result = await POCService._execute_bash_poc(target, port, poc_content, options)

            elif poc_type == "afrog":
                result = await POCService._execute_afrog(target, port, poc_content, options)

            else:
                result["error"] = f"Unsupported POC type: {poc_type}"

        except Exception as e:
            logger.error(f"Error executing POC: {e}")
            result["error"] = str(e)

        result["execution_time"] = time.time() - start_time
        return result

    @staticmethod
    async def _execute_nuclei(
        target: str,
        port: Optional[int],
        poc_content: str,
        options: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute Nuclei POC."""
        result = {
            "target": target,
            "port": port,
            "vulnerable": False,
            "output": "",
            "error": None,
            "execution_time": 0.0,
        }

        try:
            # Save POC to temporary file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                f.write(poc_content)
                poc_file = f.name

            # Build nuclei command
            cmd = ["nuclei", "-t", poc_file]

            # Add target
            if port:
                cmd.extend(["-target", f"http://{target}:{port}"])
            else:
                cmd.extend(["-target", f"http://{target}"])

            # Add options
            if options.get("severity"):
                cmd.extend(["-severity", options["severity"]])

            if options.get("timeout"):
                cmd.extend(["-timeout", str(options["timeout"])])

            # Execute
            try:
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60,  # 60 second timeout
                )

                result["output"] = proc.stdout
                result["vulnerable"] = proc.returncode == 0

                if proc.stderr:
                    result["error"] = proc.stderr

            except subprocess.TimeoutExpired:
                result["error"] = "Nuclei execution timeout"

            finally:
                # Clean up temporary file
                import os
                if os.path.exists(poc_file):
                    os.remove(poc_file)

        except Exception as e:
            logger.error(f"Error executing Nuclei: {e}")
            result["error"] = str(e)

        return result

    @staticmethod
    async def _execute_http_poc(
        target: str,
        port: Optional[int],
        poc_content: str,
        options: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute HTTP-based POC."""
        result = {
            "target": target,
            "port": port,
            "vulnerable": False,
            "output": "",
            "error": None,
            "execution_time": 0.0,
        }

        try:
            import requests

            # Parse HTTP POC (simple format: METHOD /path HTTP/1.1)
            lines = poc_content.split('\n')
            if not lines:
                result["error"] = "Invalid HTTP POC format"
                return result

            # Extract method and path
            first_line = lines[0].strip()
            parts = first_line.split()

            if len(parts) < 2:
                result["error"] = "Invalid HTTP POC format"
                return result

            method = parts[0].upper()
            path = parts[1]

            # Build URL
            scheme = options.get("scheme", "http")
            if port:
                url = f"{scheme}://{target}:{port}{path}"
            else:
                url = f"{scheme}://{target}{path}"

            # Execute HTTP request
            headers = {}
            data = None

            # Parse headers from POC
            for line in lines[1:]:
                if ": " in line:
                    key, value = line.split(": ", 1)
                    headers[key.strip()] = value.strip()
                elif line.strip().startswith('{') or line.strip().startswith('['):
                    data = line.strip()
                elif not line.strip():
                    break

            # Make request
            timeout = options.get("timeout", 10)
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                data=data,
                timeout=timeout,
                verify=False,
            )

            result["output"] = f"Status: {response.status_code}\n{response.text[:500]}"
            result["vulnerable"] = response.status_code < 400

            # Check for success indicators
            if options.get("success_indicator"):
                indicator = options["success_indicator"]
                result["vulnerable"] = indicator.lower() in response.text.lower()

        except Exception as e:
            logger.error(f"Error executing HTTP POC: {e}")
            result["error"] = str(e)

        return result

    @staticmethod
    async def _execute_bash_poc(
        target: str,
        port: Optional[int],
        poc_content: str,
        options: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute Bash-based POC."""
        result = {
            "target": target,
            "port": port,
            "vulnerable": False,
            "output": "",
            "error": None,
            "execution_time": 0.0,
        }

        try:
            # Replace placeholders
            script = poc_content
            script = script.replace("${TARGET}", target)
            script = script.replace("$TARGET", target)
            script = script.replace("${PORT}", str(port or 80))
            script = script.replace("$PORT", str(port or 80))

            # Execute script
            timeout = options.get("timeout", 30)
            proc = subprocess.run(
                script,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            result["output"] = proc.stdout
            result["vulnerable"] = proc.returncode == 0

            if proc.stderr:
                result["error"] = proc.stderr

        except subprocess.TimeoutExpired:
            result["error"] = "Script execution timeout"

        except Exception as e:
            logger.error(f"Error executing Bash POC: {e}")
            result["error"] = str(e)

        return result

    @staticmethod
    async def _execute_afrog(
        target: str,
        port: Optional[int],
        poc_content: str,
        options: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute Afrog POC."""
        result = {
            "target": target,
            "port": port,
            "vulnerable": False,
            "output": "",
            "error": None,
            "execution_time": 0.0,
        }

        try:
            # Save POC to temporary file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                f.write(poc_content)
                poc_file = f.name

            # Build afrog command
            cmd = ["afrog"]

            # Add target
            if port:
                cmd.extend(["-t", f"{target}:{port}"])
            else:
                cmd.extend(["-t", target])

            # Add POC
            cmd.extend(["-p", poc_file])

            # Add options
            if options.get("threads"):
                cmd.extend(["-c", str(options["threads"])])

            # Execute
            try:
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )

                result["output"] = proc.stdout
                result["vulnerable"] = proc.returncode == 0

                if proc.stderr:
                    result["error"] = proc.stderr

            except subprocess.TimeoutExpired:
                result["error"] = "Afrog execution timeout"

            finally:
                # Clean up temporary file
                import os
                if os.path.exists(poc_file):
                    os.remove(poc_file)

        except Exception as e:
            logger.error(f"Error executing Afrog: {e}")
            result["error"] = str(e)

        return result

    @staticmethod
    def parse_poc_metadata(content: str, poc_type: str) -> Dict[str, Any]:
        """
        Parse metadata from POC content.

        Args:
            content: POC script/YAML content
            poc_type: Type of POC

        Returns:
            Extracted metadata
        """
        metadata = {
            "name": None,
            "description": None,
            "cve_ids": [],
            "severity": None,
        }

        if poc_type == "nuclei":
            try:
                data = yaml.safe_load(content)
                if isinstance(data, dict):
                    metadata["name"] = data.get("id")
                    metadata["description"] = data.get("info", {}).get("description")
                    metadata["severity"] = data.get("info", {}).get("severity")

                    # Extract CVE IDs
                    references = data.get("info", {}).get("reference", [])
                    if isinstance(references, str):
                        references = [references]

                    for ref in references:
                        if isinstance(ref, str) and "CVE" in ref:
                            # Extract CVE ID
                            cve_match = re.search(r"CVE-\d+-\d+", ref)
                            if cve_match:
                                metadata["cve_ids"].append(cve_match.group())
            except yaml.YAMLError:
                pass

        # Try to extract CVE IDs from content
        cve_pattern = r"CVE-\d+-\d+"
        found_cves = re.findall(cve_pattern, content)
        metadata["cve_ids"].extend(found_cves)
        metadata["cve_ids"] = list(set(metadata["cve_ids"]))  # Remove duplicates

        return metadata

    @staticmethod
    def get_poc_statistics(pocs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate POC statistics.

        Args:
            pocs: List of POC dictionaries

        Returns:
            Statistics dictionary
        """
        stats = {
            "total_pocs": len(pocs),
            "by_severity": {},
            "by_type": {},
            "by_source": {},
            "by_tag": {},
            "total_cves": 0,
        }

        cve_set = set()

        for poc in pocs:
            # By severity
            severity = poc.get("severity", "unknown")
            stats["by_severity"][severity] = stats["by_severity"].get(severity, 0) + 1

            # By type
            poc_type = poc.get("poc_type", "unknown")
            stats["by_type"][poc_type] = stats["by_type"].get(poc_type, 0) + 1

            # By source
            source = poc.get("source", "unknown")
            stats["by_source"][source] = stats["by_source"].get(source, 0) + 1

            # By tag
            if "tags" in poc:
                for tag in poc["tags"]:
                    tag_name = tag.get("tag") if isinstance(tag, dict) else tag
                    stats["by_tag"][tag_name] = stats["by_tag"].get(tag_name, 0) + 1

            # CVE count
            if poc.get("cve_id"):
                cve_set.add(poc["cve_id"])

        stats["total_cves"] = len(cve_set)

        return stats

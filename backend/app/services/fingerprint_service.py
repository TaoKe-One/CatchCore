"""Fingerprint matching service for vulnerability identification."""

import logging
import re
from typing import List, Dict, Optional, Any
from functools import lru_cache

logger = logging.getLogger(__name__)


class FingerprintService:
    """Service for matching service fingerprints against known patterns."""

    # Sample fingerprint database (52,000+ patterns in production)
    FINGERPRINTS = {
        "Apache": [
            {
                "pattern": r"Apache/2\.[024]",
                "cve": ["CVE-2018-1312", "CVE-2019-10082"],
                "severity": "high",
            },
            {
                "pattern": r"Apache/2\.0",
                "cve": ["CVE-2005-3352"],
                "severity": "critical",
            },
        ],
        "OpenSSH": [
            {
                "pattern": r"OpenSSH_7\.[0-5]",
                "cve": ["CVE-2018-15473"],
                "severity": "medium",
            },
            {
                "pattern": r"OpenSSH_6\.",
                "cve": ["CVE-2015-3646"],
                "severity": "high",
            },
        ],
        "Nginx": [
            {
                "pattern": r"nginx/1\.1[0-5]",
                "cve": ["CVE-2016-4897"],
                "severity": "medium",
            },
        ],
        "MySQL": [
            {
                "pattern": r"MySQL 5\.[0-5]",
                "cve": ["CVE-2019-2627"],
                "severity": "high",
            },
        ],
        "PostgreSQL": [
            {
                "pattern": r"PostgreSQL 9\.[0-6]",
                "cve": ["CVE-2017-7546"],
                "severity": "medium",
            },
        ],
        "Redis": [
            {
                "pattern": r"redis_version:([0-3]\.)",
                "cve": ["CVE-2016-8339"],
                "severity": "critical",
            },
        ],
        "Tomcat": [
            {
                "pattern": r"Tomcat/7\.",
                "cve": ["CVE-2019-0232"],
                "severity": "critical",
            },
        ],
        "IIS": [
            {
                "pattern": r"IIS/7\.[0-5]",
                "cve": ["CVE-2012-1077"],
                "severity": "high",
            },
        ],
    }

    # Cache for loaded fingerprints
    _fingerprint_cache: Optional[Dict[str, List[Dict[str, Any]]]] = None

    @staticmethod
    def load_fingerprints() -> Dict[str, List[Dict[str, Any]]]:
        """
        Load fingerprint database (with caching).

        Returns:
            Dictionary of service -> fingerprints
        """
        if FingerprintService._fingerprint_cache is not None:
            return FingerprintService._fingerprint_cache

        logger.info("Loading fingerprint database")

        # In production, this would load from:
        # - JSON file
        # - Database
        # - External CVE database API
        # For now, use built-in definitions

        FingerprintService._fingerprint_cache = FingerprintService.FINGERPRINTS
        logger.info(
            f"Loaded {len(FingerprintService._fingerprint_cache)} service fingerprints"
        )

        return FingerprintService._fingerprint_cache

    @staticmethod
    def match_fingerprints(
        asset_id: int, service_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Match service against fingerprint database.

        Args:
            asset_id: Asset ID
            service_data: Service information including banner/version

        Returns:
            List of matched fingerprints with CVE data
        """
        logger.info(
            f"Matching fingerprints for asset {asset_id}, service {service_data.get('service')}"
        )

        matches = []
        fingerprints = FingerprintService.load_fingerprints()

        banner = service_data.get("banner", "") or service_data.get("version", "")
        service_name = service_data.get("service", "")

        if not banner:
            logger.warning(f"No banner/version for service {service_name}")
            return matches

        # Match against all fingerprints
        for service_type, patterns in fingerprints.items():
            for fingerprint in patterns:
                pattern = fingerprint.get("pattern")
                if not pattern:
                    continue

                try:
                    if re.search(pattern, banner, re.IGNORECASE):
                        matches.append(
                            {
                                "asset_id": asset_id,
                                "service": service_name,
                                "service_type": service_type,
                                "pattern_matched": pattern,
                                "cve": fingerprint.get("cve", []),
                                "severity": fingerprint.get("severity"),
                                "confidence": "high",
                            }
                        )
                except re.error as e:
                    logger.warning(f"Invalid regex pattern {pattern}: {e}")
                    continue

        logger.info(f"Found {len(matches)} fingerprint matches")
        return matches

    @staticmethod
    def match_fingerprints_batch(
        services: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Match multiple services against fingerprint database.

        Args:
            services: List of service dictionaries

        Returns:
            List of all matched fingerprints
        """
        logger.info(f"Batch matching {len(services)} services")

        all_matches = []
        fingerprints = FingerprintService.load_fingerprints()

        for service in services:
            try:
                banner = service.get("banner") or service.get("version", "")
                service_name = service.get("service", "")
                ip = service.get("ip")
                port = service.get("port")

                if not banner:
                    continue

                # Match against all fingerprints
                for service_type, patterns in fingerprints.items():
                    for fingerprint in patterns:
                        pattern = fingerprint.get("pattern")
                        if not pattern:
                            continue

                        try:
                            if re.search(pattern, banner, re.IGNORECASE):
                                all_matches.append(
                                    {
                                        "ip": ip,
                                        "port": port,
                                        "service": service_name,
                                        "service_type": service_type,
                                        "pattern_matched": pattern,
                                        "cve": fingerprint.get("cve", []),
                                        "severity": fingerprint.get("severity"),
                                        "banner": banner[:100],
                                        "confidence": "high",
                                    }
                                )
                        except re.error as e:
                            logger.warning(f"Invalid regex pattern {pattern}: {e}")
                            continue

            except Exception as e:
                logger.warning(f"Error processing service {service}: {e}")
                continue

        logger.info(f"Found {len(all_matches)} total matches in batch")
        return all_matches

    @staticmethod
    def get_cve_details(cve_id: str) -> Optional[Dict[str, Any]]:
        """
        Get CVE details (placeholder for CVE database lookup).

        Args:
            cve_id: CVE identifier (e.g., CVE-2019-1234)

        Returns:
            CVE details or None
        """
        # Placeholder for actual CVE database lookup
        # In production, would query NIST CVE API or local database

        cve_map = {
            "CVE-2018-15473": {
                "description": "OpenSSH username enumeration",
                "cvss_score": 5.3,
                "cvss_vector": "CVSS:3.0/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N",
                "references": ["https://www.cvedetails.com/cve/CVE-2018-15473/"],
            },
            "CVE-2016-8339": {
                "description": "Redis unauthenticated RCE",
                "cvss_score": 9.8,
                "cvss_vector": "CVSS:3.0/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
                "references": ["https://www.cvedetails.com/cve/CVE-2016-8339/"],
            },
            "CVE-2019-2627": {
                "description": "MySQL authentication bypass",
                "cvss_score": 9.8,
                "cvss_vector": "CVSS:3.0/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
                "references": ["https://www.cvedetails.com/cve/CVE-2019-2627/"],
            },
        }

        return cve_map.get(cve_id)

    @staticmethod
    def clear_cache() -> None:
        """Clear fingerprint cache."""
        FingerprintService._fingerprint_cache = None
        logger.info("Fingerprint cache cleared")

    @staticmethod
    def get_cache_size() -> int:
        """Get number of cached fingerprints."""
        if FingerprintService._fingerprint_cache is None:
            return 0
        return sum(
            len(patterns)
            for patterns in FingerprintService._fingerprint_cache.values()
        )

    @staticmethod
    def get_statistics() -> Dict[str, Any]:
        """
        Get fingerprint database statistics.

        Returns:
            Dictionary of statistics
        """
        fingerprints = FingerprintService.load_fingerprints()

        total_patterns = sum(len(patterns) for patterns in fingerprints.values())
        services_count = len(fingerprints)

        cve_set = set()
        for patterns in fingerprints.values():
            for pattern_data in patterns:
                cves = pattern_data.get("cve", [])
                cve_set.update(cves)

        return {
            "total_services": services_count,
            "total_patterns": total_patterns,
            "total_cves": len(cve_set),
            "cache_status": "loaded"
            if FingerprintService._fingerprint_cache is not None
            else "unloaded",
        }

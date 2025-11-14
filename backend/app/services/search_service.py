"""Advanced search and filtering service."""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy import and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.vulnerability import Vulnerability
from app.models.asset import Asset
from app.models.task import Task

logger = logging.getLogger(__name__)


class SearchService:
    """Service for advanced search and filtering."""

    # Supported search operators
    OPERATORS = {
        "=": lambda field, value: field == value,
        "!=": lambda field, value: field != value,
        ">": lambda field, value: field > value,
        "<": lambda field, value: field < value,
        ">=": lambda field, value: field >= value,
        "<=": lambda field, value: field <= value,
        "in": lambda field, value: field.in_(value.split(",")),
        "like": lambda field, value: field.ilike(f"%{value}%"),
        "regex": lambda field, value: field.regexp_match(value),
    }

    @staticmethod
    def parse_query(query: str) -> List[Tuple[str, str, str]]:
        """
        Parse advanced search query.

        Format: field:operator:value OR field=value (default operator is =)

        Args:
            query: Search query string

        Returns:
            List of (field, operator, value) tuples
        """
        conditions = []

        # Split by logical operators (AND, OR)
        # Simple parsing - can be enhanced with proper lexer
        parts = re.split(r'\s+(AND|OR)\s+', query, flags=re.IGNORECASE)

        for i, part in enumerate(parts):
            if part.upper() in ['AND', 'OR']:
                continue

            part = part.strip()
            if not part:
                continue

            # Parse individual condition
            # Format: field:operator:value or field=value
            if ':' in part:
                components = part.split(':', 2)
                if len(components) == 3:
                    field, operator, value = components
                    conditions.append((field.strip(), operator.strip(), value.strip()))
            elif '=' in part:
                field, value = part.split('=', 1)
                conditions.append((field.strip(), '=', value.strip()))
            elif '>' in part or '<' in part:
                # Handle comparison operators
                if '>=' in part:
                    field, value = part.split('>=', 1)
                    conditions.append((field.strip(), '>=', value.strip()))
                elif '<=' in part:
                    field, value = part.split('<=', 1)
                    conditions.append((field.strip(), '<=', value.strip()))
                elif '!=' in part:
                    field, value = part.split('!=', 1)
                    conditions.append((field.strip(), '!=', value.strip()))
                elif '>' in part:
                    field, value = part.split('>', 1)
                    conditions.append((field.strip(), '>', value.strip()))
                elif '<' in part:
                    field, value = part.split('<', 1)
                    conditions.append((field.strip(), '<', value.strip()))

        return conditions

    @staticmethod
    async def search_vulnerabilities(
        db: AsyncSession,
        query: str = "",
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Advanced search for vulnerabilities.

        Args:
            db: Database session
            query: Search query (advanced syntax)
            filters: Additional filters
            page: Page number
            page_size: Page size

        Returns:
            Tuple of (vulnerabilities, total_count)
        """
        if filters is None:
            filters = {}

        # Build base query
        base_query = select(Vulnerability)
        filters_list = []

        # Parse and apply advanced query
        if query:
            conditions = SearchService.parse_query(query)

            for field, operator, value in conditions:
                try:
                    # Map field names to model attributes
                    if field.lower() == "cve":
                        attr = Vulnerability.cve_id
                    elif field.lower() == "severity":
                        attr = Vulnerability.severity
                    elif field.lower() == "status":
                        attr = Vulnerability.status
                    elif field.lower() == "ip":
                        attr = Vulnerability.affected_asset_ip
                    else:
                        continue

                    # Apply operator
                    if operator == "=":
                        filters_list.append(attr == value)
                    elif operator == "!=":
                        filters_list.append(attr != value)
                    elif operator == ">":
                        filters_list.append(attr > value)
                    elif operator == "<":
                        filters_list.append(attr < value)
                    elif operator == ">=":
                        filters_list.append(attr >= value)
                    elif operator == "<=":
                        filters_list.append(attr <= value)
                    elif operator == "like":
                        filters_list.append(attr.ilike(f"%{value}%"))
                    elif operator == "in":
                        filters_list.append(attr.in_(value.split(",")))

                except Exception as e:
                    logger.warning(f"Error parsing condition {field} {operator} {value}: {e}")

        # Apply standard filters
        if filters:
            if filters.get("severity"):
                filters_list.append(Vulnerability.severity == filters["severity"])

            if filters.get("status"):
                filters_list.append(Vulnerability.status == filters["status"])

            if filters.get("cve_id"):
                filters_list.append(Vulnerability.cve_id == filters["cve_id"])

            if filters.get("asset_id"):
                filters_list.append(Vulnerability.asset_id == filters["asset_id"])

            if filters.get("date_from"):
                date_from = datetime.fromisoformat(filters["date_from"])
                filters_list.append(Vulnerability.discovered_at >= date_from)

            if filters.get("date_to"):
                date_to = datetime.fromisoformat(filters["date_to"])
                filters_list.append(Vulnerability.discovered_at <= date_to)

        # Combine filters
        if filters_list:
            base_query = base_query.where(and_(*filters_list) if len(filters_list) > 1 else filters_list[0])

        # Get total count
        count_query = select(func.count(Vulnerability.id))
        if filters_list:
            count_query = count_query.where(and_(*filters_list) if len(filters_list) > 1 else filters_list[0])

        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # Apply pagination
        query = base_query.order_by(Vulnerability.discovered_at.desc()).offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        vulnerabilities = result.scalars().all()

        return vulnerabilities, total

    @staticmethod
    async def search_assets(
        db: AsyncSession,
        query: str = "",
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Advanced search for assets.

        Args:
            db: Database session
            query: Search query
            filters: Additional filters
            page: Page number
            page_size: Page size

        Returns:
            Tuple of (assets, total_count)
        """
        if filters is None:
            filters = {}

        base_query = select(Asset)
        filters_list = []

        # Parse and apply advanced query
        if query:
            conditions = SearchService.parse_query(query)

            for field, operator, value in conditions:
                if field.lower() == "ip":
                    attr = Asset.ip_address
                elif field.lower() == "hostname":
                    attr = Asset.hostname
                elif field.lower() == "status":
                    attr = Asset.status
                elif field.lower() == "department":
                    attr = Asset.department
                else:
                    continue

                if operator == "=":
                    filters_list.append(attr == value)
                elif operator == "like":
                    filters_list.append(attr.ilike(f"%{value}%"))
                elif operator == "!=":
                    filters_list.append(attr != value)

        # Apply standard filters
        if filters:
            if filters.get("status"):
                filters_list.append(Asset.status == filters["status"])

            if filters.get("department"):
                filters_list.append(Asset.department == filters["department"])

            if filters.get("environment"):
                filters_list.append(Asset.environment == filters["environment"])

        # Combine filters
        if filters_list:
            base_query = base_query.where(and_(*filters_list) if len(filters_list) > 1 else filters_list[0])

        # Get total count
        count_query = select(func.count(Asset.id))
        if filters_list:
            count_query = count_query.where(and_(*filters_list) if len(filters_list) > 1 else filters_list[0])

        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # Apply pagination
        query = base_query.order_by(Asset.created_at.desc()).offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        assets = result.scalars().all()

        return assets, total

    @staticmethod
    async def search_tasks(
        db: AsyncSession,
        query: str = "",
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Advanced search for tasks.

        Args:
            db: Database session
            query: Search query
            filters: Additional filters
            page: Page number
            page_size: Page size

        Returns:
            Tuple of (tasks, total_count)
        """
        if filters is None:
            filters = {}

        base_query = select(Task)
        filters_list = []

        # Parse and apply advanced query
        if query:
            conditions = SearchService.parse_query(query)

            for field, operator, value in conditions:
                if field.lower() == "name":
                    attr = Task.name
                elif field.lower() == "status":
                    attr = Task.status
                elif field.lower() == "type":
                    attr = Task.task_type
                else:
                    continue

                if operator == "=":
                    filters_list.append(attr == value)
                elif operator == "like":
                    filters_list.append(attr.ilike(f"%{value}%"))
                elif operator == "!=":
                    filters_list.append(attr != value)

        # Apply standard filters
        if filters:
            if filters.get("status"):
                filters_list.append(Task.status == filters["status"])

            if filters.get("task_type"):
                filters_list.append(Task.task_type == filters["task_type"])

            if filters.get("priority"):
                filters_list.append(Task.priority >= filters["priority"])

        # Combine filters
        if filters_list:
            base_query = base_query.where(and_(*filters_list) if len(filters_list) > 1 else filters_list[0])

        # Get total count
        count_query = select(func.count(Task.id))
        if filters_list:
            count_query = count_query.where(and_(*filters_list) if len(filters_list) > 1 else filters_list[0])

        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # Apply pagination
        query = base_query.order_by(Task.created_at.desc()).offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        tasks = result.scalars().all()

        return tasks, total

    @staticmethod
    def get_search_suggestions(search_type: str = "vulnerability") -> Dict[str, Any]:
        """
        Get search syntax suggestions.

        Args:
            search_type: Type of search (vulnerability, asset, task)

        Returns:
            Dictionary with search suggestions
        """
        suggestions = {
            "operators": [
                {"symbol": "=", "name": "equals", "example": "severity=critical"},
                {"symbol": "!=", "name": "not equals", "example": "status!=fixed"},
                {"symbol": ">", "name": "greater than", "example": "cvss_score>7"},
                {"symbol": "<", "name": "less than", "example": "cvss_score<5"},
                {"symbol": ">=", "name": "greater or equal", "example": "priority>=8"},
                {"symbol": "<=", "name": "less or equal", "example": "priority<=5"},
                {"symbol": "like", "name": "contains", "example": "name:like:Apache"},
                {"symbol": "in", "name": "in list", "example": "status:in:open,fixed"},
            ],
            "logical_operators": [
                {"symbol": "AND", "description": "Both conditions must be true"},
                {"symbol": "OR", "description": "At least one condition must be true"},
            ],
        }

        if search_type == "vulnerability":
            suggestions["fields"] = [
                {"name": "cve", "type": "string", "example": "CVE-2021-1234"},
                {"name": "severity", "type": "enum", "values": ["critical", "high", "medium", "low", "info"]},
                {"name": "status", "type": "enum", "values": ["open", "fixed", "verified", "false_positive"]},
                {"name": "ip", "type": "ip", "example": "192.168.1.1"},
            ]

            suggestions["examples"] = [
                "severity=critical AND status=open",
                "cve=CVE-2021-1234",
                "severity:like:high OR severity:like:critical",
            ]

        elif search_type == "asset":
            suggestions["fields"] = [
                {"name": "ip", "type": "ip", "example": "192.168.1.0/24"},
                {"name": "hostname", "type": "string", "example": "server1"},
                {"name": "status", "type": "enum", "values": ["active", "inactive", "archived"]},
                {"name": "department", "type": "string", "example": "IT"},
            ]

            suggestions["examples"] = [
                "ip=192.168.1.100",
                "department:like:IT AND status=active",
                "hostname:like:server",
            ]

        elif search_type == "task":
            suggestions["fields"] = [
                {"name": "name", "type": "string", "example": "Port Scan"},
                {"name": "status", "type": "enum", "values": ["pending", "running", "completed", "failed"]},
                {"name": "type", "type": "string", "example": "port_scan"},
            ]

            suggestions["examples"] = [
                "status=completed",
                "type=port_scan AND status=running",
                "name:like:DMZ",
            ]

        return suggestions

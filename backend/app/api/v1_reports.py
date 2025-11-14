"""Report generation API routes."""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import io
import json

from app.core.database import get_db
from app.models.task import Task, TaskResult
from app.models.user import User
from app.api.deps import get_current_user
from app.services.report_service import ReportService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/task/{task_id}", response_model=dict)
async def get_task_report(
    task_id: int,
    format: str = Query("html", regex="^(html|json|csv|md|markdown|pdf)$"),
    organization: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate and retrieve a report for a specific task."""
    # Get task
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # Get task results
    results = await db.execute(
        select(TaskResult).where(TaskResult.task_id == task_id)
    )
    task_results = results.scalars().all()

    # Reconstruct scan data from results
    scan_data = {
        "vulnerabilities": [],
        "assets": [],
        "summary": {
            "total_vulnerabilities": 0,
            "total_assets": 0,
        },
    }

    for result in task_results:
        if result.result_type == "vulnerability":
            scan_data["vulnerabilities"].append(result.result_data)
        elif result.result_type == "asset":
            scan_data["assets"].append(result.result_data)

    scan_data["summary"]["total_vulnerabilities"] = len(scan_data["vulnerabilities"])
    scan_data["summary"]["total_assets"] = len(scan_data["assets"])

    # Generate report
    org_name = organization or "CatchCore Organization"

    try:
        report = ReportService.export_report(
            scan_data,
            format=format,
            task_name=task.name,
            organization=org_name,
        )

        if format == "html":
            return HTMLResponse(content=report)

        elif format == "json":
            return JSONResponse(content=report)

        elif format == "csv":
            return StreamingResponse(
                iter([report]),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=task_{task_id}.csv"},
            )

        elif format in ["md", "markdown"]:
            return StreamingResponse(
                iter([report]),
                media_type="text/markdown",
                headers={"Content-Disposition": f"attachment; filename=task_{task_id}.md"},
            )

        elif format == "pdf":
            # Return HTML as base64 encoded string (placeholder for actual PDF)
            return {
                "code": 0,
                "message": "PDF report generated",
                "data": {
                    "format": "html_base64",
                    "content": report,
                    "note": "PDF generation requires additional dependencies",
                },
            }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    except Exception as e:
        logger.error(f"Error generating report for task {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate report",
        )


@router.post("/generate", response_model=dict)
async def generate_custom_report(
    task_ids: list[int] = Query(...),
    format: str = Query("html", regex="^(html|json|csv|md|markdown|pdf)$"),
    organization: Optional[str] = Query(None),
    include_recommendations: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a custom report from multiple tasks."""
    if not task_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one task ID must be provided",
        )

    # Aggregate data from multiple tasks
    combined_scan_data = {
        "vulnerabilities": [],
        "assets": set(),
        "summary": {
            "total_vulnerabilities": 0,
            "total_assets": 0,
        },
    }

    for task_id in task_ids[:10]:  # Limit to 10 tasks to prevent memory issues
        # Get task
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()

        if not task:
            continue

        # Get task results
        results = await db.execute(
            select(TaskResult).where(TaskResult.task_id == task_id)
        )
        task_results = results.scalars().all()

        for task_result in task_results:
            if task_result.result_type == "vulnerability":
                combined_scan_data["vulnerabilities"].append(task_result.result_data)
            elif task_result.result_type == "asset":
                asset_ip = task_result.result_data.get("ip")
                if asset_ip:
                    combined_scan_data["assets"].add(asset_ip)

    # Convert set to list
    combined_scan_data["assets"] = [{"ip": ip} for ip in combined_scan_data["assets"]]
    combined_scan_data["summary"]["total_vulnerabilities"] = len(
        combined_scan_data["vulnerabilities"]
    )
    combined_scan_data["summary"]["total_assets"] = len(combined_scan_data["assets"])

    # Generate report
    org_name = organization or "CatchCore Organization"
    task_name = f"Combined Report ({len(task_ids)} tasks)"

    try:
        report = ReportService.export_report(
            combined_scan_data,
            format=format,
            task_name=task_name,
            organization=org_name,
        )

        if format == "html":
            return HTMLResponse(content=report)

        elif format == "json":
            return JSONResponse(content=report)

        elif format == "csv":
            return StreamingResponse(
                iter([report]),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=combined_report.csv"},
            )

        elif format in ["md", "markdown"]:
            return StreamingResponse(
                iter([report]),
                media_type="text/markdown",
                headers={"Content-Disposition": "attachment; filename=combined_report.md"},
            )

        else:
            return {
                "code": 0,
                "message": "Report generated",
                "data": {
                    "format": format,
                    "content": report if isinstance(report, (str, dict)) else "Report generated",
                },
            }

    except Exception as e:
        logger.error(f"Error generating custom report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate report",
        )


@router.get("/formats", response_model=dict)
async def get_supported_formats(
    current_user: User = Depends(get_current_user),
):
    """Get list of supported report formats."""
    formats = {
        "html": {
            "name": "HTML Report",
            "description": "Interactive HTML report with styling",
            "extension": ".html",
            "media_type": "text/html",
        },
        "json": {
            "name": "JSON Report",
            "description": "Structured JSON format for integration",
            "extension": ".json",
            "media_type": "application/json",
        },
        "csv": {
            "name": "CSV Report",
            "description": "Comma-separated values for spreadsheet import",
            "extension": ".csv",
            "media_type": "text/csv",
        },
        "markdown": {
            "name": "Markdown Report",
            "description": "Markdown format for documentation",
            "extension": ".md",
            "media_type": "text/markdown",
        },
        "pdf": {
            "name": "PDF Report",
            "description": "Portable document format (requires additional setup)",
            "extension": ".pdf",
            "media_type": "application/pdf",
        },
    }

    return {
        "code": 0,
        "message": "success",
        "data": formats,
    }


@router.get("/statistics", response_model=dict)
async def get_report_statistics(
    task_ids: Optional[list[int]] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get statistics for report generation."""
    # If no task IDs provided, get all tasks
    if not task_ids:
        result = await db.execute(select(Task))
        tasks = result.scalars().all()
        task_ids = [task.id for task in tasks]

    # Aggregate statistics
    severity_distribution = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "info": 0,
    }

    service_distribution = {}
    total_vulnerabilities = 0
    total_assets = set()

    for task_id in task_ids[:100]:  # Limit to 100 tasks
        results = await db.execute(
            select(TaskResult).where(TaskResult.task_id == task_id)
        )
        task_results = results.scalars().all()

        for task_result in task_results:
            if task_result.result_type == "vulnerability":
                vuln = task_result.result_data
                severity = vuln.get("severity", "info").lower()
                if severity in severity_distribution:
                    severity_distribution[severity] += 1

                service = vuln.get("service", "unknown")
                service_distribution[service] = service_distribution.get(service, 0) + 1

                total_vulnerabilities += 1

            elif task_result.result_type == "asset":
                asset_ip = task_result.result_data.get("ip")
                if asset_ip:
                    total_assets.add(asset_ip)

    return {
        "code": 0,
        "message": "success",
        "data": {
            "total_vulnerabilities": total_vulnerabilities,
            "total_assets": len(total_assets),
            "severity_distribution": severity_distribution,
            "service_distribution": service_distribution,
            "report_sources": len(task_ids),
        },
    }

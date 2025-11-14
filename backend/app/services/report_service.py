"""Vulnerability report generation service."""

import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import base64
from io import BytesIO

logger = logging.getLogger(__name__)


class ReportService:
    """Service for generating vulnerability reports in various formats."""

    @staticmethod
    def generate_html_report(
        scan_data: Dict[str, Any],
        task_name: str = "Security Scan",
        organization: str = "Organization",
    ) -> str:
        """
        Generate HTML vulnerability report.

        Args:
            scan_data: Scan results dictionary
            task_name: Name of the scan task
            organization: Organization name

        Returns:
            HTML report as string
        """
        vulnerabilities = scan_data.get("vulnerabilities", [])
        assets = scan_data.get("assets", [])
        summary = scan_data.get("summary", {})

        # Calculate statistics
        critical_count = len([v for v in vulnerabilities if v.get("severity") == "critical"])
        high_count = len([v for v in vulnerabilities if v.get("severity") == "high"])
        medium_count = len([v for v in vulnerabilities if v.get("severity") == "medium"])
        low_count = len([v for v in vulnerabilities if v.get("severity") == "low"])

        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{task_name} - Vulnerability Report</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}

                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    color: #333;
                    background: #f5f5f5;
                }}

                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    background: white;
                    padding: 40px;
                }}

                .header {{
                    border-bottom: 3px solid #0066cc;
                    padding-bottom: 20px;
                    margin-bottom: 30px;
                }}

                .header h1 {{
                    color: #0066cc;
                    font-size: 32px;
                    margin-bottom: 10px;
                }}

                .header p {{
                    color: #666;
                    font-size: 14px;
                }}

                .summary {{
                    display: grid;
                    grid-template-columns: repeat(4, 1fr);
                    gap: 20px;
                    margin: 30px 0;
                }}

                .summary-card {{
                    padding: 20px;
                    border-radius: 8px;
                    text-align: center;
                    background: #f9f9f9;
                    border: 1px solid #ddd;
                }}

                .summary-card.critical {{
                    background: #fff5f5;
                    border-color: #ff4d4f;
                }}

                .summary-card.high {{
                    background: #fff7e6;
                    border-color: #fa8c16;
                }}

                .summary-card.medium {{
                    background: #fffbe6;
                    border-color: #faad14;
                }}

                .summary-card.low {{
                    background: #f0f5ff;
                    border-color: #1890ff;
                }}

                .summary-card .count {{
                    font-size: 36px;
                    font-weight: bold;
                    margin: 10px 0;
                }}

                .summary-card.critical .count {{
                    color: #ff4d4f;
                }}

                .summary-card.high .count {{
                    color: #fa8c16;
                }}

                .summary-card.medium .count {{
                    color: #faad14;
                }}

                .summary-card.low .count {{
                    color: #1890ff;
                }}

                .section {{
                    margin: 30px 0;
                    page-break-inside: avoid;
                }}

                .section h2 {{
                    font-size: 20px;
                    color: #0066cc;
                    border-left: 4px solid #0066cc;
                    padding-left: 10px;
                    margin-bottom: 20px;
                }}

                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 20px;
                }}

                thead {{
                    background: #f0f0f0;
                }}

                th {{
                    padding: 12px;
                    text-align: left;
                    font-weight: 600;
                    border-bottom: 2px solid #ddd;
                }}

                td {{
                    padding: 10px 12px;
                    border-bottom: 1px solid #ddd;
                }}

                tr:hover {{
                    background: #f9f9f9;
                }}

                .severity-critical {{
                    color: #ff4d4f;
                    font-weight: bold;
                }}

                .severity-high {{
                    color: #fa8c16;
                    font-weight: bold;
                }}

                .severity-medium {{
                    color: #faad14;
                    font-weight: bold;
                }}

                .severity-low {{
                    color: #1890ff;
                    font-weight: bold;
                }}

                .vulnerability-detail {{
                    background: #f9f9f9;
                    padding: 15px;
                    margin: 15px 0;
                    border-left: 4px solid #0066cc;
                    border-radius: 4px;
                }}

                .vulnerability-detail h4 {{
                    margin-bottom: 10px;
                    color: #333;
                }}

                .vulnerability-detail p {{
                    margin: 5px 0;
                    font-size: 14px;
                    color: #666;
                }}

                .footer {{
                    margin-top: 40px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    text-align: center;
                    color: #999;
                    font-size: 12px;
                }}

                @media print {{
                    body {{
                        background: white;
                    }}
                    .container {{
                        padding: 0;
                    }}
                    .section {{
                        page-break-inside: avoid;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔒 Security Vulnerability Report</h1>
                    <p><strong>Organization:</strong> {organization}</p>
                    <p><strong>Scan Task:</strong> {task_name}</p>
                    <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>

                <div class="section">
                    <h2>Executive Summary</h2>
                    <div class="summary">
                        <div class="summary-card critical">
                            <div>Critical</div>
                            <div class="count">{critical_count}</div>
                        </div>
                        <div class="summary-card high">
                            <div>High</div>
                            <div class="count">{high_count}</div>
                        </div>
                        <div class="summary-card medium">
                            <div>Medium</div>
                            <div class="count">{medium_count}</div>
                        </div>
                        <div class="summary-card low">
                            <div>Low</div>
                            <div class="count">{low_count}</div>
                        </div>
                    </div>
                    <p style="margin-top: 20px; color: #666;">
                        Total vulnerabilities found: <strong>{len(vulnerabilities)}</strong><br>
                        Assets scanned: <strong>{len(assets)}</strong>
                    </p>
                </div>

                <div class="section">
                    <h2>Vulnerability Summary</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>IP Address</th>
                                <th>Port</th>
                                <th>Service</th>
                                <th>CVE ID</th>
                                <th>Severity</th>
                                <th>Description</th>
                            </tr>
                        </thead>
                        <tbody>
        """

        for vuln in vulnerabilities[:50]:  # Limit to first 50 for brevity
            severity = vuln.get("severity", "unknown").lower()
            severity_class = f"severity-{severity}"

            html += f"""
                            <tr>
                                <td>{vuln.get('ip', 'N/A')}</td>
                                <td>{vuln.get('port', 'N/A')}</td>
                                <td>{vuln.get('service', 'N/A')}</td>
                                <td>{vuln.get('cve', 'N/A')}</td>
                                <td><span class="{severity_class}">{severity.upper()}</span></td>
                                <td>{vuln.get('description', 'N/A')[:50]}...</td>
                            </tr>
            """

        html += """
                        </tbody>
                    </table>
                </div>

                <div class="section">
                    <h2>Detailed Findings</h2>
        """

        # Add detailed vulnerability information
        for vuln in vulnerabilities[:10]:  # Show detailed info for first 10
            severity = vuln.get("severity", "unknown").lower()
            html += f"""
                    <div class="vulnerability-detail">
                        <h4>{vuln.get('cve', 'Unknown CVE')} - {vuln.get('service', 'Unknown Service')}</h4>
                        <p><strong>Severity:</strong> <span class="severity-{severity}">{severity.upper()}</span></p>
                        <p><strong>Target:</strong> {vuln.get('ip', 'N/A')}:{vuln.get('port', 'N/A')}</p>
                        <p><strong>Description:</strong> {vuln.get('description', 'N/A')}</p>
                        <p><strong>Recommendation:</strong> {vuln.get('recommendation', 'Update to latest version')}</p>
                    </div>
            """

        html += """
                </div>

                <div class="footer">
                    <p>This report was automatically generated by CatchCore Security Scanner</p>
                    <p>For more information, visit: https://catchcore.io</p>
                </div>
            </div>
        </body>
        </html>
        """

        return html

    @staticmethod
    def generate_json_report(
        scan_data: Dict[str, Any],
        task_name: str = "Security Scan",
    ) -> Dict[str, Any]:
        """
        Generate JSON vulnerability report.

        Args:
            scan_data: Scan results dictionary
            task_name: Name of the scan task

        Returns:
            JSON report dictionary
        """
        vulnerabilities = scan_data.get("vulnerabilities", [])
        assets = scan_data.get("assets", [])

        # Calculate statistics
        severity_dist = {}
        for vuln in vulnerabilities:
            severity = vuln.get("severity", "unknown")
            severity_dist[severity] = severity_dist.get(severity, 0) + 1

        report = {
            "metadata": {
                "title": task_name,
                "generated_at": datetime.now().isoformat(),
                "version": "1.0",
            },
            "summary": {
                "total_vulnerabilities": len(vulnerabilities),
                "total_assets": len(assets),
                "severity_distribution": severity_dist,
            },
            "vulnerabilities": vulnerabilities,
            "assets": assets,
        }

        return report

    @staticmethod
    def generate_csv_report(
        scan_data: Dict[str, Any],
    ) -> str:
        """
        Generate CSV vulnerability report.

        Args:
            scan_data: Scan results dictionary

        Returns:
            CSV report as string
        """
        vulnerabilities = scan_data.get("vulnerabilities", [])

        csv = "IP,Port,Service,CVE,Severity,Description,Recommendation\n"

        for vuln in vulnerabilities:
            ip = vuln.get("ip", "N/A").replace(",", ";")
            port = vuln.get("port", "N/A")
            service = vuln.get("service", "N/A").replace(",", ";")
            cve = vuln.get("cve", "N/A")
            severity = vuln.get("severity", "N/A")
            description = vuln.get("description", "N/A").replace(",", ";")
            recommendation = vuln.get("recommendation", "N/A").replace(",", ";")

            csv += f'"{ip}",{port},"{service}",{cve},{severity},"{description}","{recommendation}"\n'

        return csv

    @staticmethod
    def generate_pdf_report(
        scan_data: Dict[str, Any],
        task_name: str = "Security Scan",
        organization: str = "Organization",
    ) -> bytes:
        """
        Generate PDF vulnerability report.

        Args:
            scan_data: Scan results dictionary
            task_name: Name of the scan task
            organization: Organization name

        Returns:
            PDF report as bytes

        Note:
            This requires additional dependencies (weasyprint or reportlab).
            For now, we'll return HTML as base64 encoded.
        """
        html_report = ReportService.generate_html_report(
            scan_data, task_name, organization
        )

        # TODO: Convert HTML to PDF using weasyprint or similar
        # For now, return HTML encoded in base64
        return base64.b64encode(html_report.encode()).decode()

    @staticmethod
    def generate_markdown_report(
        scan_data: Dict[str, Any],
        task_name: str = "Security Scan",
    ) -> str:
        """
        Generate Markdown vulnerability report.

        Args:
            scan_data: Scan results dictionary
            task_name: Name of the scan task

        Returns:
            Markdown report as string
        """
        vulnerabilities = scan_data.get("vulnerabilities", [])
        assets = scan_data.get("assets", [])

        # Calculate statistics
        critical_count = len([v for v in vulnerabilities if v.get("severity") == "critical"])
        high_count = len([v for v in vulnerabilities if v.get("severity") == "high"])
        medium_count = len([v for v in vulnerabilities if v.get("severity") == "medium"])
        low_count = len([v for v in vulnerabilities if v.get("severity") == "low"])

        md = f"""# {task_name} - Vulnerability Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary

| Severity | Count |
|----------|-------|
| 🔴 Critical | {critical_count} |
| 🟠 High | {high_count} |
| 🟡 Medium | {medium_count} |
| 🔵 Low | {low_count} |

**Total Vulnerabilities:** {len(vulnerabilities)}
**Assets Scanned:** {len(assets)}

## Vulnerability Details

"""

        for vuln in vulnerabilities:
            severity_emoji = {
                "critical": "🔴",
                "high": "🟠",
                "medium": "🟡",
                "low": "🔵",
            }.get(vuln.get("severity", "unknown"), "⚪")

            md += f"""### {severity_emoji} {vuln.get('cve', 'Unknown CVE')} - {vuln.get('service', 'Unknown')}

- **Target:** {vuln.get('ip', 'N/A')}:{vuln.get('port', 'N/A')}
- **Severity:** {vuln.get('severity', 'Unknown').upper()}
- **Description:** {vuln.get('description', 'N/A')}
- **Recommendation:** {vuln.get('recommendation', 'Update to latest version')}

---

"""

        md += """## Recommendations

1. Prioritize patching critical and high severity vulnerabilities
2. Perform regular security assessments
3. Keep systems and software up to date
4. Implement proper access controls
5. Monitor systems for suspicious activity

---

*This report was generated by CatchCore Security Scanner*
"""

        return md

    @staticmethod
    def export_report(
        scan_data: Dict[str, Any],
        format: str = "html",
        task_name: str = "Security Scan",
        organization: str = "Organization",
    ) -> Any:
        """
        Export report in specified format.

        Args:
            scan_data: Scan results dictionary
            format: Report format (html, json, csv, md, pdf)
            task_name: Name of the scan task
            organization: Organization name

        Returns:
            Report in specified format
        """
        format = format.lower()

        if format == "html":
            return ReportService.generate_html_report(scan_data, task_name, organization)

        elif format == "json":
            return ReportService.generate_json_report(scan_data, task_name)

        elif format == "csv":
            return ReportService.generate_csv_report(scan_data)

        elif format == "md" or format == "markdown":
            return ReportService.generate_markdown_report(scan_data, task_name)

        elif format == "pdf":
            return ReportService.generate_pdf_report(scan_data, task_name, organization)

        else:
            raise ValueError(f"Unsupported report format: {format}")

"""Report generation service.

Generates PDF reports from Analysis data with executive summary,
findings table, and standard references.
"""

from datetime import datetime
from io import BytesIO
from typing import TYPE_CHECKING

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.schemas.enums import AnalysisVerdict, FindingSeverity
from app.schemas.report import ReportData, ReportFinding, SeverityCounts

if TYPE_CHECKING:
    from app.db.models.analysis import Analysis


class ReportService:
    """Service for generating PDF reports from analysis data.

    Provides static methods for:
    - Converting Analysis ORM model to ReportData schema
    - Generating professional PDF reports with ReportLab
    """

    # Severity color mapping (light backgrounds for readability)
    SEVERITY_COLORS = {
        FindingSeverity.CRITICAL: colors.Color(1, 0.8, 0.8),  # Light red
        FindingSeverity.MAJOR: colors.Color(1, 0.95, 0.8),  # Light yellow
        FindingSeverity.MINOR: colors.white,
        FindingSeverity.INFO: colors.white,
    }

    # Verdict color mapping
    VERDICT_COLORS = {
        AnalysisVerdict.APPROVED: colors.Color(0.2, 0.7, 0.2),  # Green
        AnalysisVerdict.REVIEW: colors.Color(0.9, 0.7, 0.1),  # Yellow/Orange
        AnalysisVerdict.REJECTED: colors.Color(0.8, 0.2, 0.2),  # Red
    }

    @staticmethod
    def from_analysis(analysis: "Analysis") -> ReportData:
        """Convert an Analysis ORM model to ReportData schema.

        Extracts all relevant data from the Analysis, counts findings by
        severity, and builds the ReportData structure for PDF generation.

        Args:
            analysis: Analysis ORM model with findings relationship loaded.

        Returns:
            ReportData schema ready for PDF generation.
        """
        # Count findings by severity
        severity_counts = SeverityCounts(critical=0, major=0, minor=0, info=0)
        findings_list: list[ReportFinding] = []

        for finding in analysis.findings:
            severity = FindingSeverity(finding.severity)

            # Update counts
            if severity == FindingSeverity.CRITICAL:
                severity_counts.critical += 1
            elif severity == FindingSeverity.MAJOR:
                severity_counts.major += 1
            elif severity == FindingSeverity.MINOR:
                severity_counts.minor += 1
            elif severity == FindingSeverity.INFO:
                severity_counts.info += 1

            # Extract standard_reference from evidence dict
            standard_ref = "N/A"
            if finding.evidence and isinstance(finding.evidence, dict):
                standard_ref = finding.evidence.get("standard_reference", "N/A")

            findings_list.append(
                ReportFinding(
                    rule_id=finding.rule_id,
                    severity=severity,
                    message=finding.message,
                    remediation=finding.remediation,
                    standard_reference=standard_ref,
                )
            )

        # Parse verdict if present
        verdict = None
        if analysis.verdict:
            verdict = AnalysisVerdict(analysis.verdict)

        return ReportData(
            analysis_id=analysis.id,
            equipment_type=analysis.equipment_type,
            test_type=analysis.test_type,
            equipment_tag=analysis.equipment_tag,
            verdict=verdict,
            compliance_score=analysis.compliance_score,
            confidence_score=analysis.confidence_score,
            severity_counts=severity_counts,
            findings=findings_list,
            generated_at=datetime.utcnow(),
        )

    @staticmethod
    def generate_pdf(data: ReportData) -> bytes:
        """Generate a PDF report from ReportData.

        Creates a professional, engineer-focused PDF with:
        - Header with report number and date
        - Executive summary with verdict, scores, and severity counts
        - Findings table with color-coded severity
        - Footer with generation timestamp

        Args:
            data: ReportData schema with analysis results.

        Returns:
            PDF document as bytes.
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=72,
            rightMargin=72,
            topMargin=72,
            bottomMargin=72,
        )

        styles = getSampleStyleSheet()
        story = []

        # Custom styles
        title_style = ParagraphStyle(
            "Title",
            parent=styles["Heading1"],
            fontSize=18,
            spaceAfter=20,
            alignment=1,  # Center
        )
        heading_style = ParagraphStyle(
            "Heading",
            parent=styles["Heading2"],
            fontSize=14,
            spaceBefore=15,
            spaceAfter=10,
        )
        normal_style = styles["Normal"]

        # === HEADER ===
        story.append(Paragraph("AuditEng Analysis Report", title_style))
        story.append(
            Paragraph(
                f"Report ID: {str(data.analysis_id)[:8]}",
                ParagraphStyle("ReportID", parent=normal_style, alignment=1),
            )
        )
        story.append(
            Paragraph(
                f"Generated: {data.generated_at.strftime('%Y-%m-%d %H:%M UTC')}",
                ParagraphStyle("Date", parent=normal_style, alignment=1),
            )
        )
        story.append(Spacer(1, 20))

        # === EXECUTIVE SUMMARY ===
        story.append(Paragraph("Executive Summary", heading_style))

        # Verdict badge
        verdict_text = data.verdict.value.upper() if data.verdict else "PENDING"
        verdict_color = (
            ReportService.VERDICT_COLORS.get(data.verdict, colors.gray)
            if data.verdict
            else colors.gray
        )

        # Summary info table
        compliance_str = (
            f"{data.compliance_score:.1f}%" if data.compliance_score is not None else "N/A"
        )
        confidence_str = (
            f"{data.confidence_score:.1%}" if data.confidence_score is not None else "N/A"
        )

        summary_data = [
            ["Verdict", verdict_text],
            ["Compliance Score", compliance_str],
            ["Extraction Confidence", confidence_str],
            ["Equipment Type", data.equipment_type.upper()],
            ["Test Type", data.test_type.upper()],
        ]
        if data.equipment_tag:
            summary_data.append(["Equipment Tag", data.equipment_tag])

        summary_table = Table(summary_data, colWidths=[2 * inch, 3 * inch])
        summary_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.Color(0.95, 0.95, 0.95)),
                    ("BACKGROUND", (1, 0), (1, 0), verdict_color),
                    ("TEXTCOLOR", (1, 0), (1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.gray),
                    ("PADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(summary_table)
        story.append(Spacer(1, 15))

        # Severity counts table
        story.append(Paragraph("Severity Distribution", heading_style))
        severity_data = [
            ["CRITICAL", "MAJOR", "MINOR", "INFO"],
            [
                str(data.severity_counts.critical),
                str(data.severity_counts.major),
                str(data.severity_counts.minor),
                str(data.severity_counts.info),
            ],
        ]
        severity_table = Table(severity_data, colWidths=[1.2 * inch] * 4)
        severity_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, 0), colors.Color(1, 0.8, 0.8)),  # Critical
                    ("BACKGROUND", (1, 0), (1, 0), colors.Color(1, 0.95, 0.8)),  # Major
                    ("BACKGROUND", (2, 0), (2, 0), colors.Color(0.95, 0.95, 0.95)),  # Minor
                    ("BACKGROUND", (3, 0), (3, 0), colors.Color(0.9, 0.9, 0.9)),  # Info
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTNAME", (0, 1), (-1, 1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.gray),
                    ("PADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        story.append(severity_table)
        story.append(Spacer(1, 20))

        # === FINDINGS TABLE ===
        story.append(Paragraph("Findings", heading_style))

        if data.findings:
            # Table header
            findings_data = [["Code", "Severity", "Description", "Remediation", "Standard"]]

            # Wrap style for long text
            wrap_style = ParagraphStyle(
                "Wrap",
                parent=normal_style,
                fontSize=8,
                leading=10,
            )

            for finding in data.findings:
                # Truncate/wrap long text
                message = finding.message[:200] + "..." if len(finding.message) > 200 else finding.message
                remediation = (finding.remediation or "N/A")
                if len(remediation) > 150:
                    remediation = remediation[:150] + "..."

                findings_data.append(
                    [
                        finding.rule_id,
                        finding.severity.value.upper(),
                        Paragraph(message, wrap_style),
                        Paragraph(remediation, wrap_style),
                        finding.standard_reference,
                    ]
                )

            # Column widths for A4 with 72pt margins
            col_widths = [0.7 * inch, 0.7 * inch, 2.2 * inch, 1.8 * inch, 1 * inch]
            findings_table = Table(findings_data, colWidths=col_widths, repeatRows=1)

            # Build row-level styling for severity colors
            table_style = [
                ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.3, 0.3, 0.3)),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("FONTSIZE", (0, 1), (-1, -1), 8),
                ("ALIGN", (0, 0), (1, -1), "CENTER"),
                ("ALIGN", (2, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.gray),
                ("PADDING", (0, 0), (-1, -1), 4),
            ]

            # Add severity row colors
            for i, finding in enumerate(data.findings, start=1):
                bg_color = ReportService.SEVERITY_COLORS.get(finding.severity, colors.white)
                table_style.append(("BACKGROUND", (0, i), (-1, i), bg_color))

            findings_table.setStyle(TableStyle(table_style))
            story.append(findings_table)
        else:
            story.append(
                Paragraph(
                    "No findings - analysis passed all validation checks.",
                    ParagraphStyle("NoFindings", parent=normal_style, textColor=colors.green),
                )
            )

        story.append(Spacer(1, 30))

        # === FOOTER ===
        footer_style = ParagraphStyle(
            "Footer",
            parent=normal_style,
            fontSize=8,
            textColor=colors.gray,
            alignment=1,
        )
        story.append(
            Paragraph(
                f"Generated by AuditEng | {data.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
                footer_style,
            )
        )

        # Build PDF
        doc.build(story)
        return buffer.getvalue()

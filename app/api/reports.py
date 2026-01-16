"""PDF report download API endpoint.

This module provides a protected API endpoint for downloading PDF reports
for completed analyses. Uses ReportService from app/services/report.py.
"""

from uuid import UUID

from fastapi import APIRouter, Response, status

from app.api.analyses import verify_analysis_ownership
from app.core.auth import CurrentUser
from app.core.dependencies import DbSession
from app.core.exceptions import ValidationError
from app.schemas.enums import TaskStatus
from app.services.report import ReportService

router = APIRouter(prefix="/api/analyses", tags=["reports"])


@router.get(
    "/{analysis_id}/report",
    summary="Download PDF report",
    description="Download a PDF report for a completed analysis. Requires authentication and ownership.",
    responses={
        200: {
            "description": "PDF report file",
            "content": {"application/pdf": {}},
        },
        400: {"description": "Analysis not complete"},
        401: {"description": "Not authenticated"},
        403: {"description": "Access denied"},
        404: {"description": "Analysis not found"},
    },
)
async def download_report(
    analysis_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> Response:
    """Download a PDF report for a completed analysis.

    Generates a PDF report with executive summary, findings, and compliance
    information for the specified analysis.

    Args:
        analysis_id: The analysis UUID.
        db: Database session.
        current_user: Authenticated user from JWT token.

    Returns:
        Response: PDF file with appropriate headers for download.

    Raises:
        HTTPException: 400 if analysis not complete.
        HTTPException: 401 for missing/invalid authentication.
        HTTPException: 403 if user doesn't own the analysis.
        HTTPException: 404 if analysis not found.
    """
    # Verify ownership and get analysis
    analysis = await verify_analysis_ownership(db, analysis_id, current_user.id)

    # Check that analysis is complete
    if analysis.task.status != TaskStatus.COMPLETED.value:
        raise ValidationError(
            detail="Analysis not complete. Report can only be generated for completed analyses.",
            error_code="REPORT_001",
        )

    # Generate report data from analysis
    report_data = ReportService.from_analysis(analysis)

    # Generate PDF
    pdf_bytes = ReportService.generate_pdf(report_data)

    # Return PDF with appropriate headers
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="report_{analysis_id}.pdf"'
        },
    )

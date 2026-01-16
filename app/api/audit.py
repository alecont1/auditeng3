"""Audit trail API endpoint for compliance verification.

This module provides the endpoint for retrieving the complete audit trail
of an analysis, enabling engineers to verify HOW each finding was generated.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.analyses import verify_analysis_ownership
from app.api.schemas import AuditEventResponse, AuditTrailResponse
from app.core.auth import CurrentUser
from app.core.dependencies import DbSession
from app.services.audit import AuditService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analyses", tags=["audit"])


@router.get(
    "/{analysis_id}/audit",
    response_model=AuditTrailResponse,
    summary="Get audit trail for analysis",
    description="Retrieve the complete audit trail showing all events for an analysis. "
    "Events are returned in chronological order (oldest first). "
    "Requires authentication and ownership of the analysis.",
    responses={
        200: {"description": "Audit trail retrieved successfully"},
        401: {"description": "Not authenticated"},
        403: {"description": "Access denied - user does not own this analysis"},
        404: {"description": "Analysis not found"},
    },
)
async def get_audit_trail(
    analysis_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
    skip: int = Query(default=0, ge=0, description="Number of events to skip"),
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum number of events to return"),
) -> AuditTrailResponse:
    """Get the complete audit trail for an analysis.

    The audit trail provides compliance traceability by recording all events
    during extraction and validation, including model versions, prompt versions,
    confidence scores, and validation rules applied.

    Args:
        analysis_id: The analysis UUID.
        db: Database session.
        current_user: Authenticated user from JWT token.
        skip: Number of events to skip (for pagination).
        limit: Maximum number of events to return (for pagination).

    Returns:
        AuditTrailResponse: The audit trail with chronological events.

    Raises:
        HTTPException: 401 for missing/invalid authentication.
        HTTPException: 403 if user doesn't own the analysis.
        HTTPException: 404 if analysis not found.
    """
    # Verify user owns this analysis (raises HTTPException if not)
    await verify_analysis_ownership(db, analysis_id, current_user.id)

    # Get audit trail
    audit_logs = await AuditService.get_audit_trail(db, analysis_id)

    # Apply pagination (logs are already in chronological order)
    total_count = len(audit_logs)
    paginated_logs = audit_logs[skip : skip + limit]

    # Convert to response models
    events = [
        AuditEventResponse(
            id=log.id,
            event_type=log.event_type,
            event_timestamp=log.event_timestamp,
            details=log.details,
            model_version=log.model_version,
            prompt_version=log.prompt_version,
            confidence_score=log.confidence_score,
            rule_id=log.rule_id,
        )
        for log in paginated_logs
    ]

    logger.info(
        f"Audit trail retrieved: analysis_id={analysis_id}, user_id={current_user.id}, "
        f"events={len(events)}/{total_count}"
    )

    return AuditTrailResponse(
        analysis_id=analysis_id,
        event_count=total_count,
        events=events,
    )

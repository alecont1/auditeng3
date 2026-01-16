"""Integration tests for audit trail API endpoint.

These tests verify authentication, authorization, and response format
for the audit trail retrieval endpoint.

Note: Tests that require full database integration with UUID support are
marked with pytest.mark.skip when running on SQLite. Run with PostgreSQL
for full integration testing.
"""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Analysis, Task, User
from app.db.models.audit_log import AuditLog


class TestAuditTrailAuth:
    """Tests for authentication requirements on audit trail endpoint."""

    @pytest.mark.asyncio
    async def test_get_audit_trail_requires_auth(self, client: AsyncClient) -> None:
        """Audit trail endpoint returns 401 without authentication."""
        fake_id = uuid4()
        response = await client.get(f"/api/analyses/{fake_id}/audit")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_audit_trail_with_invalid_token(
        self, client: AsyncClient
    ) -> None:
        """Audit trail endpoint returns 401 with invalid token."""
        fake_id = uuid4()
        headers = {"Authorization": "Bearer invalid-token"}
        response = await client.get(f"/api/analyses/{fake_id}/audit", headers=headers)
        assert response.status_code == 401


class TestAuditTrailRouterRegistration:
    """Tests to verify the audit router is correctly registered."""

    @pytest.mark.asyncio
    async def test_audit_route_exists(self, client: AsyncClient) -> None:
        """Audit route responds (not 404)."""
        fake_id = uuid4()
        response = await client.get(f"/api/analyses/{fake_id}/audit")
        # Should be 401 (auth required), not 404 (route not found)
        assert response.status_code != 404

    @pytest.mark.asyncio
    async def test_openapi_includes_audit(self, client: AsyncClient) -> None:
        """OpenAPI schema includes audit endpoint."""
        response = await client.get("/api/v1/openapi.json")
        assert response.status_code == 200
        schema = response.json()

        # Check that audit path exists
        paths = schema.get("paths", {})
        assert any("audit" in path for path in paths)

        # Check that audit tag exists
        tags = [tag["name"] for tag in schema.get("tags", [])]
        assert "audit" in tags


class TestAuditResponseSchemas:
    """Tests for audit response schema validation."""

    def test_audit_event_response_fields(self) -> None:
        """AuditEventResponse has all expected fields."""
        from app.api.schemas import AuditEventResponse

        event = AuditEventResponse(
            id=uuid4(),
            event_type="extraction_started",
            event_timestamp=datetime.now(timezone.utc),
            details={"status": "started"},
            model_version="claude-sonnet-4-20250514",
            prompt_version="grounding_v1",
            confidence_score=0.85,
            rule_id="GRND-001",
        )
        assert event.id is not None
        assert event.event_type == "extraction_started"
        assert event.event_timestamp is not None
        assert event.details == {"status": "started"}
        assert event.model_version == "claude-sonnet-4-20250514"
        assert event.prompt_version == "grounding_v1"
        assert event.confidence_score == 0.85
        assert event.rule_id == "GRND-001"

    def test_audit_event_response_optional_fields(self) -> None:
        """AuditEventResponse allows None for optional fields."""
        from app.api.schemas import AuditEventResponse

        event = AuditEventResponse(
            id=uuid4(),
            event_type="extraction_started",
            event_timestamp=datetime.now(timezone.utc),
            details=None,
            model_version=None,
            prompt_version=None,
            confidence_score=None,
            rule_id=None,
        )
        assert event.details is None
        assert event.model_version is None
        assert event.prompt_version is None
        assert event.confidence_score is None
        assert event.rule_id is None

    def test_audit_trail_response_fields(self) -> None:
        """AuditTrailResponse has required fields."""
        from app.api.schemas import AuditEventResponse, AuditTrailResponse

        event = AuditEventResponse(
            id=uuid4(),
            event_type="extraction_started",
            event_timestamp=datetime.now(timezone.utc),
        )
        trail = AuditTrailResponse(
            analysis_id=uuid4(),
            event_count=1,
            events=[event],
        )
        assert trail.analysis_id is not None
        assert trail.event_count == 1
        assert len(trail.events) == 1
        assert trail.events[0].event_type == "extraction_started"

    def test_audit_trail_response_empty_events(self) -> None:
        """AuditTrailResponse handles empty events list."""
        from app.api.schemas import AuditTrailResponse

        trail = AuditTrailResponse(
            analysis_id=uuid4(),
            event_count=0,
            events=[],
        )
        assert trail.event_count == 0
        assert len(trail.events) == 0


class TestAuditService:
    """Unit tests for AuditService.get_audit_trail method."""

    @pytest.mark.asyncio
    async def test_get_audit_trail_returns_list(
        self, db_session: AsyncSession
    ) -> None:
        """AuditService.get_audit_trail returns a list."""
        from app.services.audit import AuditService

        # Create a random analysis_id that doesn't exist
        analysis_id = uuid4()
        result = await AuditService.get_audit_trail(db_session, analysis_id)
        assert isinstance(result, list)
        assert len(result) == 0

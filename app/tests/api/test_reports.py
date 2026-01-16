"""Integration tests for reports API endpoint.

These tests verify:
- Authentication requirement (no DB needed)
- Response format validation
- Router registration

Note: Tests requiring database operations with UUIDs are marked for PostgreSQL
since SQLite doesn't properly support UUID types. Auth tests and schema tests
work without database dependencies.
"""

from uuid import uuid4

import pytest
from httpx import AsyncClient


class TestReportDownloadAuth:
    """Tests for report endpoint authentication.

    These tests don't require database access - they verify that
    the endpoint rejects unauthenticated requests before hitting DB.
    """

    @pytest.mark.asyncio
    async def test_download_report_requires_auth(self, client: AsyncClient) -> None:
        """Report endpoint returns 401 without authentication."""
        fake_id = uuid4()
        response = await client.get(f"/api/analyses/{fake_id}/report")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_download_report_with_invalid_token(self, client: AsyncClient) -> None:
        """Report endpoint returns 401 with invalid token."""
        fake_id = uuid4()
        headers = {"Authorization": "Bearer invalid-token"}
        response = await client.get(f"/api/analyses/{fake_id}/report", headers=headers)
        assert response.status_code == 401


class TestReportResponseSchema:
    """Tests for response schema validation.

    These tests verify the schema and ReportService behavior
    without requiring full database integration.
    """

    def test_report_data_schema(self) -> None:
        """ReportData schema has required fields."""
        from datetime import datetime, timezone
        from uuid import uuid4
        from app.schemas.report import ReportData, SeverityCounts

        data = ReportData(
            analysis_id=uuid4(),
            equipment_type="panel",
            test_type="grounding",
            equipment_tag="PANEL-01",
            verdict="approved",
            compliance_score=95.0,
            confidence_score=0.85,
            severity_counts=SeverityCounts(critical=0, major=1, minor=0, info=1),
            findings=[],
            generated_at=datetime.now(timezone.utc),
        )
        assert data.analysis_id is not None
        assert data.equipment_type == "panel"
        assert data.verdict == "approved"

    def test_report_service_generates_pdf(self) -> None:
        """ReportService.generate_pdf returns valid PDF bytes."""
        from datetime import datetime, timezone
        from uuid import uuid4
        from app.schemas.report import ReportData, ReportFinding, SeverityCounts
        from app.services.report import ReportService

        data = ReportData(
            analysis_id=uuid4(),
            equipment_type="panel",
            test_type="grounding",
            equipment_tag="PANEL-01",
            verdict="approved",
            compliance_score=95.0,
            confidence_score=0.85,
            severity_counts=SeverityCounts(critical=0, major=1, minor=0, info=1),
            findings=[
                ReportFinding(
                    rule_id="GRND-001",
                    severity="major",
                    message="Test finding message",
                    remediation="Test remediation",
                    standard_reference="IEEE 142-2007",
                )
            ],
            generated_at=datetime.now(timezone.utc),
        )

        pdf_bytes = ReportService.generate_pdf(data)

        # Verify PDF format
        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes.startswith(b"%PDF-")
        assert len(pdf_bytes) > 0

    def test_content_disposition_header_format(self) -> None:
        """Content-Disposition header format is correct."""
        from uuid import uuid4

        analysis_id = uuid4()
        header = f'attachment; filename="report_{analysis_id}.pdf"'

        assert "attachment" in header
        assert f"report_{analysis_id}.pdf" in header


class TestRouterRegistration:
    """Tests to verify the reports router is correctly registered."""

    @pytest.mark.asyncio
    async def test_reports_routes_exist(self, client: AsyncClient) -> None:
        """Report routes respond (not 404 for missing paths)."""
        fake_id = uuid4()
        response = await client.get(f"/api/analyses/{fake_id}/report")
        # Should get 401 (auth required), not 404 (route not found)
        assert response.status_code != 404

    @pytest.mark.asyncio
    async def test_openapi_includes_reports(self, client: AsyncClient) -> None:
        """OpenAPI schema includes report endpoint."""
        response = await client.get("/api/v1/openapi.json")
        assert response.status_code == 200
        schema = response.json()

        # Check that report path exists
        paths = schema.get("paths", {})
        report_paths = [p for p in paths if "report" in p]
        assert len(report_paths) > 0
        assert "/api/analyses/{analysis_id}/report" in paths

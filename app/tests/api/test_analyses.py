"""Integration tests for analyses API endpoints.

These tests verify authentication and authorization behavior.
Full integration tests require PostgreSQL with UUID support.
"""

import pytest
from httpx import AsyncClient


class TestSubmitEndpoint:
    """Tests for POST /api/analyses/submit endpoint."""

    @pytest.mark.asyncio
    async def test_submit_requires_auth(self, client: AsyncClient) -> None:
        """Submit endpoint returns 401 without authentication."""
        response = await client.post("/api/analyses/submit")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_submit_with_invalid_token(self, client: AsyncClient) -> None:
        """Submit endpoint returns 401 with invalid token."""
        headers = {"Authorization": "Bearer invalid-token"}
        response = await client.post("/api/analyses/submit", headers=headers)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_submit_with_expired_token(self, client: AsyncClient) -> None:
        """Submit endpoint returns 401 with expired token."""
        # This is a JWT that was signed but has expired
        # Header: {"alg": "HS256", "typ": "JWT"}
        # Payload: {"sub": "test-user", "exp": 1000000000} (expired in 2001)
        expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0LXVzZXIiLCJleHAiOjEwMDAwMDAwMDB9.signature"
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = await client.post("/api/analyses/submit", headers=headers)
        assert response.status_code == 401


class TestStatusEndpoint:
    """Tests for GET /api/analyses/{id}/status endpoint."""

    @pytest.mark.asyncio
    async def test_status_requires_auth(self, client: AsyncClient) -> None:
        """Status endpoint returns 401 without authentication."""
        from uuid import uuid4
        fake_id = uuid4()
        response = await client.get(f"/api/analyses/{fake_id}/status")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_status_with_invalid_token(self, client: AsyncClient) -> None:
        """Status endpoint returns 401 with invalid token."""
        from uuid import uuid4
        fake_id = uuid4()
        headers = {"Authorization": "Bearer invalid-token"}
        response = await client.get(f"/api/analyses/{fake_id}/status", headers=headers)
        assert response.status_code == 401


class TestResultsEndpoint:
    """Tests for GET /api/analyses/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_results_requires_auth(self, client: AsyncClient) -> None:
        """Results endpoint returns 401 without authentication."""
        from uuid import uuid4
        fake_id = uuid4()
        response = await client.get(f"/api/analyses/{fake_id}")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_results_with_invalid_token(self, client: AsyncClient) -> None:
        """Results endpoint returns 401 with invalid token."""
        from uuid import uuid4
        fake_id = uuid4()
        headers = {"Authorization": "Bearer invalid-token"}
        response = await client.get(f"/api/analyses/{fake_id}", headers=headers)
        assert response.status_code == 401


class TestAnalysisResponseSchemas:
    """Tests for response schema validation."""

    def test_analysis_submit_response_fields(self) -> None:
        """AnalysisSubmitResponse has required fields."""
        from uuid import uuid4
        from app.api.schemas import AnalysisSubmitResponse

        response = AnalysisSubmitResponse(
            task_id=uuid4(),
            status="queued",
        )
        assert response.task_id is not None
        assert response.status == "queued"

    def test_analysis_status_response_fields(self) -> None:
        """AnalysisStatusResponse has required fields."""
        from uuid import uuid4
        from app.api.schemas import AnalysisStatusResponse

        response = AnalysisStatusResponse(
            analysis_id=uuid4(),
            status="completed",
            message="Analysis complete",
        )
        assert response.analysis_id is not None
        assert response.status == "completed"
        assert response.message == "Analysis complete"

    def test_finding_detail_fields(self) -> None:
        """FindingDetail has required fields."""
        from app.api.schemas import FindingDetail, FindingEvidence

        evidence = FindingEvidence(
            extracted_value=7.5,
            threshold=5.0,
            standard_reference="IEEE 142-2007",
        )
        finding = FindingDetail(
            rule_id="GRND-001",
            severity="critical",
            message="Ground resistance exceeds maximum",
            field_path="measurements[0].resistance",
            evidence=evidence,
            remediation="Reduce ground resistance",
        )
        assert finding.rule_id == "GRND-001"
        assert finding.severity == "critical"
        assert finding.evidence.extracted_value == 7.5
        assert finding.evidence.standard_reference == "IEEE 142-2007"

    def test_analysis_response_fields(self) -> None:
        """AnalysisResponse has required fields."""
        from datetime import datetime, timezone
        from uuid import uuid4
        from app.api.schemas import AnalysisResponse, FindingDetail

        response = AnalysisResponse(
            id=uuid4(),
            equipment_type="panel",
            test_type="grounding",
            equipment_tag="PANEL-01",
            verdict="approved",
            compliance_score=95.0,
            confidence_score=0.85,
            findings=[
                FindingDetail(
                    rule_id="GRND-001",
                    severity="major",
                    message="Test finding",
                )
            ],
            extraction_result={"raw_data": {}},
            created_at=datetime.now(timezone.utc),
        )
        assert response.id is not None
        assert response.equipment_type == "panel"
        assert response.verdict == "approved"
        assert response.compliance_score == 95.0
        assert len(response.findings) == 1


class TestRouterRegistration:
    """Tests to verify the analyses router is correctly registered."""

    @pytest.mark.asyncio
    async def test_analyses_routes_exist(self, client: AsyncClient) -> None:
        """Analyses routes respond (not 404 for method not allowed paths)."""
        # POST /api/analyses/submit should exist (401 without auth, not 404)
        response = await client.post("/api/analyses/submit")
        assert response.status_code != 404

    @pytest.mark.asyncio
    async def test_openapi_includes_analyses(self, client: AsyncClient) -> None:
        """OpenAPI schema includes analyses endpoints."""
        response = await client.get("/api/v1/openapi.json")
        assert response.status_code == 200
        schema = response.json()

        # Check that analyses paths exist
        paths = schema.get("paths", {})
        assert "/api/analyses/submit" in paths
        assert any("analyses" in path and "status" in path for path in paths)

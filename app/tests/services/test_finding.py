"""Tests for finding generation service."""

from uuid import uuid4

import pytest

from app.core.validation.schemas import (
    Finding as ValidationFinding,
    ValidationResult,
    ValidationSeverity,
)
from app.schemas.enums import FindingSeverity
from app.services.finding import FindingService, generate_findings_from_validation


@pytest.fixture
def sample_validation_finding() -> ValidationFinding:
    """Create a sample validation finding for testing."""
    return ValidationFinding(
        rule_id="GRND-001",
        severity=ValidationSeverity.CRITICAL,
        message="Ground resistance exceeds maximum threshold",
        field_path="measurements[0].resistance_value",
        extracted_value=7.5,
        threshold=5.0,
        standard_reference="IEEE 142-2007",
        remediation="Reduce ground resistance to below 5 ohms",
    )


@pytest.fixture
def sample_validation_result() -> ValidationResult:
    """Create a sample validation result with multiple findings."""
    return ValidationResult(
        test_type="grounding",
        equipment_tag="PANEL-01",
        findings=[
            ValidationFinding(
                rule_id="GRND-001",
                severity=ValidationSeverity.CRITICAL,
                message="Ground resistance exceeds maximum",
                field_path="measurements[0].resistance_value",
                extracted_value=7.5,
                threshold=5.0,
                standard_reference="IEEE 142-2007",
                remediation="Reduce ground resistance",
            ),
            ValidationFinding(
                rule_id="GRND-002",
                severity=ValidationSeverity.MAJOR,
                message="Multiple grounds not bonded",
                field_path="bonding_status",
                extracted_value=False,
                threshold=True,
                standard_reference="NFPA 70",
                remediation="Ensure proper bonding",
            ),
            ValidationFinding(
                rule_id="GRND-003",
                severity=ValidationSeverity.MINOR,
                message="Documentation incomplete",
                field_path="documentation.complete",
                extracted_value=False,
                threshold=True,
            ),
        ],
    )


class TestFindingService:
    """Tests for FindingService."""

    def test_generate_finding_preserves_fields(
        self, sample_validation_finding: ValidationFinding
    ) -> None:
        """Check that all fields are mapped correctly."""
        analysis_id = uuid4()

        result = FindingService.generate_finding_from_validation(
            sample_validation_finding, analysis_id
        )

        assert result.analysis_id == analysis_id
        assert result.rule_id == "GRND-001"
        assert result.severity == FindingSeverity.CRITICAL
        assert result.message == "Ground resistance exceeds maximum threshold"
        assert result.remediation == "Reduce ground resistance to below 5 ohms"

    def test_generate_findings_batch(
        self, sample_validation_result: ValidationResult
    ) -> None:
        """Multiple findings from ValidationResult are converted."""
        analysis_id = uuid4()

        results = FindingService.generate_findings_from_validation(
            sample_validation_result, analysis_id
        )

        assert len(results) == 3
        assert all(f.analysis_id == analysis_id for f in results)
        assert results[0].rule_id == "GRND-001"
        assert results[1].rule_id == "GRND-002"
        assert results[2].rule_id == "GRND-003"

    def test_evidence_structure(
        self, sample_validation_finding: ValidationFinding
    ) -> None:
        """Evidence dict has correct keys and values."""
        analysis_id = uuid4()

        result = FindingService.generate_finding_from_validation(
            sample_validation_finding, analysis_id
        )

        assert result.evidence is not None
        assert result.evidence.extracted_value == 7.5
        assert result.evidence.threshold == 5.0
        assert result.evidence.standard_reference == "IEEE 142-2007"

    def test_evidence_default_standard_reference(self) -> None:
        """Evidence uses 'N/A' when standard_reference is None."""
        finding = ValidationFinding(
            rule_id="TEST-001",
            severity=ValidationSeverity.INFO,
            message="Test message",
            field_path="test_path",
            extracted_value=100,
            threshold=50,
            standard_reference=None,
        )
        analysis_id = uuid4()

        result = FindingService.generate_finding_from_validation(finding, analysis_id)

        assert result.evidence is not None
        assert result.evidence.standard_reference == "N/A"

    def test_empty_findings_list(self) -> None:
        """Empty validation result produces empty list."""
        result = ValidationResult(
            test_type="grounding",
            findings=[],
        )
        analysis_id = uuid4()

        findings = FindingService.generate_findings_from_validation(result, analysis_id)

        assert findings == []


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_generate_findings_from_validation(
        self, sample_validation_result: ValidationResult
    ) -> None:
        """Convenience function works the same as class method."""
        analysis_id = uuid4()

        results = generate_findings_from_validation(sample_validation_result, analysis_id)

        assert len(results) == 3
        assert all(f.analysis_id == analysis_id for f in results)

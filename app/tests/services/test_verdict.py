"""Tests for verdict service with scoring logic."""

import pytest

from app.core.extraction.schemas import (
    BaseExtractionResult,
    ExtractionMetadata,
    FieldConfidence,
)
from app.core.validation.schemas import (
    Finding,
    ValidationResult,
    ValidationSeverity,
)
from app.schemas.enums import AnalysisVerdict
from app.services.verdict import (
    VerdictService,
    compute_compliance_score,
    compute_verdict,
)
from datetime import datetime


class MockExtractionResult(BaseExtractionResult):
    """Mock extraction result for testing."""

    test_field: FieldConfidence | None = None


@pytest.fixture
def perfect_validation_result() -> ValidationResult:
    """Validation result with no findings."""
    return ValidationResult(
        test_type="grounding",
        findings=[],
    )


@pytest.fixture
def validation_with_critical() -> ValidationResult:
    """Validation result with CRITICAL finding."""
    return ValidationResult(
        test_type="grounding",
        findings=[
            Finding(
                rule_id="GRND-001",
                severity=ValidationSeverity.CRITICAL,
                message="Critical issue",
                field_path="test_path",
                extracted_value=10,
                threshold=5,
            ),
        ],
    )


@pytest.fixture
def validation_with_mixed_findings() -> ValidationResult:
    """Validation result with multiple finding severities."""
    return ValidationResult(
        test_type="grounding",
        findings=[
            Finding(
                rule_id="GRND-001",
                severity=ValidationSeverity.MAJOR,
                message="Major issue",
                field_path="test_path",
                extracted_value=10,
                threshold=5,
            ),
            Finding(
                rule_id="GRND-002",
                severity=ValidationSeverity.MINOR,
                message="Minor issue",
                field_path="test_path_2",
                extracted_value=6,
                threshold=5,
            ),
        ],
    )


@pytest.fixture
def high_confidence_extraction() -> MockExtractionResult:
    """Extraction result with high confidence."""
    return MockExtractionResult(
        overall_confidence=0.95,
        test_field=FieldConfidence(value="test", confidence=0.95),
    )


@pytest.fixture
def low_confidence_extraction() -> MockExtractionResult:
    """Extraction result with low confidence."""
    return MockExtractionResult(
        overall_confidence=0.5,
        test_field=FieldConfidence(value="test", confidence=0.5),
    )


class TestComplianceScore:
    """Tests for compliance score calculation."""

    def test_compliance_score_perfect(
        self, perfect_validation_result: ValidationResult
    ) -> None:
        """No findings returns 100.0."""
        score = VerdictService.compute_compliance_score(perfect_validation_result)
        assert score == 100.0

    def test_compliance_score_with_findings(
        self, validation_with_mixed_findings: ValidationResult
    ) -> None:
        """Score deducts correctly for MAJOR and MINOR."""
        # 100 - 10 (MAJOR) - 2 (MINOR) = 88
        score = VerdictService.compute_compliance_score(validation_with_mixed_findings)
        assert score == 88.0

    def test_compliance_score_clamped_to_zero(self) -> None:
        """Many findings clamp score to 0."""
        result = ValidationResult(
            test_type="grounding",
            findings=[
                Finding(
                    rule_id=f"GRND-{i:03d}",
                    severity=ValidationSeverity.CRITICAL,
                    message="Critical issue",
                    field_path=f"path_{i}",
                    extracted_value=i,
                    threshold=0,
                )
                for i in range(10)  # 10 CRITICAL = -250 points
            ],
        )

        score = VerdictService.compute_compliance_score(result)
        assert score == 0.0

    def test_compliance_score_with_all_severity_levels(self) -> None:
        """Score calculation with all severity levels."""
        result = ValidationResult(
            test_type="grounding",
            findings=[
                Finding(
                    rule_id="GRND-001",
                    severity=ValidationSeverity.CRITICAL,
                    message="Critical",
                    field_path="p1",
                    extracted_value=1,
                    threshold=0,
                ),
                Finding(
                    rule_id="GRND-002",
                    severity=ValidationSeverity.MAJOR,
                    message="Major",
                    field_path="p2",
                    extracted_value=2,
                    threshold=0,
                ),
                Finding(
                    rule_id="GRND-003",
                    severity=ValidationSeverity.MINOR,
                    message="Minor",
                    field_path="p3",
                    extracted_value=3,
                    threshold=0,
                ),
                Finding(
                    rule_id="GRND-004",
                    severity=ValidationSeverity.INFO,
                    message="Info",
                    field_path="p4",
                    extracted_value=4,
                    threshold=0,
                ),
            ],
        )

        # 100 - 25 (CRITICAL) - 10 (MAJOR) - 2 (MINOR) - 0 (INFO) = 63
        score = VerdictService.compute_compliance_score(result)
        assert score == 63.0


class TestConfidenceScore:
    """Tests for confidence score calculation."""

    def test_confidence_from_overall(
        self, high_confidence_extraction: MockExtractionResult
    ) -> None:
        """Uses overall_confidence when available."""
        score = VerdictService.compute_confidence_score(high_confidence_extraction)
        assert score == 0.95

    def test_confidence_low_value(
        self, low_confidence_extraction: MockExtractionResult
    ) -> None:
        """Low confidence is correctly returned."""
        score = VerdictService.compute_confidence_score(low_confidence_extraction)
        assert score == 0.5


class TestVerdictDetermination:
    """Tests for verdict determination."""

    def test_verdict_rejected_on_critical(
        self,
        validation_with_critical: ValidationResult,
        high_confidence_extraction: MockExtractionResult,
    ) -> None:
        """CRITICAL finding results in REJECTED verdict."""
        compliance = VerdictService.compute_compliance_score(validation_with_critical)
        confidence = VerdictService.compute_confidence_score(high_confidence_extraction)

        verdict = VerdictService.compute_verdict(
            validation_with_critical, compliance, confidence
        )

        assert verdict == AnalysisVerdict.REJECTED

    def test_verdict_review_low_score(
        self,
        validation_with_mixed_findings: ValidationResult,
        high_confidence_extraction: MockExtractionResult,
    ) -> None:
        """Score < 95 results in REVIEW verdict."""
        # 100 - 10 - 2 = 88 < 95
        compliance = VerdictService.compute_compliance_score(
            validation_with_mixed_findings
        )
        confidence = VerdictService.compute_confidence_score(high_confidence_extraction)

        verdict = VerdictService.compute_verdict(
            validation_with_mixed_findings, compliance, confidence
        )

        assert verdict == AnalysisVerdict.REVIEW

    def test_verdict_review_low_confidence(
        self,
        perfect_validation_result: ValidationResult,
        low_confidence_extraction: MockExtractionResult,
    ) -> None:
        """Confidence < 0.7 results in REVIEW verdict."""
        compliance = VerdictService.compute_compliance_score(perfect_validation_result)
        confidence = VerdictService.compute_confidence_score(low_confidence_extraction)

        verdict = VerdictService.compute_verdict(
            perfect_validation_result, compliance, confidence
        )

        assert verdict == AnalysisVerdict.REVIEW

    def test_verdict_approved(
        self,
        perfect_validation_result: ValidationResult,
        high_confidence_extraction: MockExtractionResult,
    ) -> None:
        """No CRITICAL, score >= 95, confidence >= 0.7 results in APPROVED."""
        compliance = VerdictService.compute_compliance_score(perfect_validation_result)
        confidence = VerdictService.compute_confidence_score(high_confidence_extraction)

        verdict = VerdictService.compute_verdict(
            perfect_validation_result, compliance, confidence
        )

        assert verdict == AnalysisVerdict.APPROVED

    def test_verdict_approved_at_boundary(self) -> None:
        """Test exact boundary values for APPROVED verdict."""
        # Score exactly 95, confidence exactly 0.7
        result = ValidationResult(
            test_type="grounding",
            findings=[
                Finding(
                    rule_id="GRND-001",
                    severity=ValidationSeverity.MINOR,
                    message="Minor 1",
                    field_path="p1",
                    extracted_value=1,
                    threshold=0,
                ),
                Finding(
                    rule_id="GRND-002",
                    severity=ValidationSeverity.MINOR,
                    message="Minor 2",
                    field_path="p2",
                    extracted_value=2,
                    threshold=0,
                ),
                Finding(
                    rule_id="GRND-003",
                    severity=ValidationSeverity.INFO,
                    message="Info",
                    field_path="p3",
                    extracted_value=3,
                    threshold=0,
                ),
            ],
        )

        # 100 - 2 - 2 - 0 = 96 >= 95, confidence = 0.7
        compliance = VerdictService.compute_compliance_score(result)
        assert compliance == 96.0

        verdict = VerdictService.compute_verdict(result, compliance, 0.7)
        assert verdict == AnalysisVerdict.APPROVED


class TestAnalysisVerdict:
    """Tests for complete analysis verdict computation."""

    def test_compute_analysis_verdict(
        self,
        perfect_validation_result: ValidationResult,
        high_confidence_extraction: MockExtractionResult,
    ) -> None:
        """Complete verdict computation returns all three values."""
        verdict, compliance, confidence = VerdictService.compute_analysis_verdict(
            perfect_validation_result, high_confidence_extraction
        )

        assert verdict == AnalysisVerdict.APPROVED
        assert compliance == 100.0
        assert confidence == 0.95


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_compute_verdict_function(
        self, perfect_validation_result: ValidationResult
    ) -> None:
        """Convenience function works the same as class method."""
        verdict = compute_verdict(perfect_validation_result, 100.0, 0.9)
        assert verdict == AnalysisVerdict.APPROVED

    def test_compute_compliance_score_function(
        self, perfect_validation_result: ValidationResult
    ) -> None:
        """Convenience function works the same as class method."""
        score = compute_compliance_score(perfect_validation_result)
        assert score == 100.0

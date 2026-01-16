"""Verdict service with scoring logic.

Computes compliance scores and determines verdict based on validation results
and extraction confidence.
"""

from app.core.extraction.schemas import BaseExtractionResult, FieldConfidence
from app.core.validation.schemas import ValidationResult
from app.schemas.enums import AnalysisVerdict


class VerdictService:
    """Service for computing compliance scores and verdicts.

    Implements scoring logic per FIND-05 through FIND-07 requirements:
    - FIND-05: Compliance score calculation
    - FIND-06: Confidence score from extraction
    - FIND-07: Verdict determination rules
    """

    @staticmethod
    def compute_compliance_score(validation_result: ValidationResult) -> float:
        """Calculate compliance score from validation result.

        Score calculation:
        - Start at 100.0
        - CRITICAL finding: -25 points
        - MAJOR finding: -10 points
        - MINOR finding: -2 points
        - INFO finding: 0 points

        Score is clamped to 0-100 range and rounded to 2 decimal places.

        Args:
            validation_result: ValidationResult with finding counts.

        Returns:
            Compliance score (0.0 to 100.0).
        """
        score = 100.0

        score -= validation_result.critical_count * 25
        score -= validation_result.major_count * 10
        score -= validation_result.minor_count * 2

        # Clamp to 0-100 range
        score = max(0.0, min(100.0, score))

        return round(score, 2)

    @staticmethod
    def compute_confidence_score(extraction_result: BaseExtractionResult) -> float:
        """Calculate confidence score from extraction result.

        Uses overall_confidence from extraction metadata if available,
        otherwise calculates average from all FieldConfidence values.

        Args:
            extraction_result: Extraction result with field confidences.

        Returns:
            Confidence score (0.0 to 1.0).
        """
        # First try overall_confidence from extraction result
        if extraction_result.overall_confidence is not None:
            return round(extraction_result.overall_confidence, 2)

        # Fall back to computing average from fields
        confidences: list[float] = []

        # Recursively collect confidences from all FieldConfidence objects
        def collect_confidences(obj: object) -> None:
            if isinstance(obj, FieldConfidence):
                confidences.append(obj.confidence)
            elif hasattr(obj, "__dict__"):
                for value in vars(obj).values():
                    if isinstance(value, list):
                        for item in value:
                            collect_confidences(item)
                    elif value is not None:
                        collect_confidences(value)

        collect_confidences(extraction_result)

        if not confidences:
            return 0.0

        avg_confidence = sum(confidences) / len(confidences)
        return round(avg_confidence, 2)

    @staticmethod
    def compute_verdict(
        validation_result: ValidationResult,
        compliance_score: float,
        confidence_score: float,
    ) -> AnalysisVerdict:
        """Determine verdict based on validation and scores.

        Verdict rules (per FIND-07):
        - REJECTED: Any CRITICAL finding exists
        - REVIEW: compliance_score < 95 OR confidence_score < 0.7
        - APPROVED: No CRITICAL, score >= 95, confidence >= 0.7

        Args:
            validation_result: ValidationResult with finding counts.
            compliance_score: Calculated compliance score (0-100).
            confidence_score: Extraction confidence score (0-1).

        Returns:
            AnalysisVerdict enum value.
        """
        # Rule 1: REJECTED if any CRITICAL finding
        if validation_result.critical_count > 0:
            return AnalysisVerdict.REJECTED

        # Rule 2: REVIEW if low compliance or low confidence
        if compliance_score < 95 or confidence_score < 0.7:
            return AnalysisVerdict.REVIEW

        # Rule 3: APPROVED otherwise
        return AnalysisVerdict.APPROVED

    @staticmethod
    def compute_analysis_verdict(
        validation_result: ValidationResult,
        extraction_result: BaseExtractionResult,
    ) -> tuple[AnalysisVerdict, float, float]:
        """Compute complete verdict for an analysis.

        Combines score calculations and verdict determination
        into a single call.

        Args:
            validation_result: ValidationResult with findings.
            extraction_result: Extraction result with confidences.

        Returns:
            Tuple of (verdict, compliance_score, confidence_score).
        """
        compliance_score = VerdictService.compute_compliance_score(validation_result)
        confidence_score = VerdictService.compute_confidence_score(extraction_result)
        verdict = VerdictService.compute_verdict(
            validation_result, compliance_score, confidence_score
        )

        return verdict, compliance_score, confidence_score


def compute_verdict(
    validation_result: ValidationResult,
    compliance_score: float,
    confidence_score: float,
) -> AnalysisVerdict:
    """Convenience function for verdict computation.

    Args:
        validation_result: ValidationResult with finding counts.
        compliance_score: Calculated compliance score (0-100).
        confidence_score: Extraction confidence score (0-1).

    Returns:
        AnalysisVerdict enum value.
    """
    return VerdictService.compute_verdict(
        validation_result, compliance_score, confidence_score
    )


def compute_compliance_score(validation_result: ValidationResult) -> float:
    """Convenience function for compliance score calculation.

    Args:
        validation_result: ValidationResult with finding counts.

    Returns:
        Compliance score (0.0 to 100.0).
    """
    return VerdictService.compute_compliance_score(validation_result)

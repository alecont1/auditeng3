"""Base validator class for all test-type validators.

This module defines the abstract base class that all specific
validators (Grounding, Megger, Thermography) inherit from.

VALD-07: Validators are deterministic - same input always produces same output.
VALD-09: Same extraction can be validated against different standards.
"""

from abc import ABC, abstractmethod
from typing import Any

from app.core.extraction.schemas import BaseExtractionResult
from app.core.validation.config import ValidationConfig, get_validation_config
from app.core.validation.schemas import (
    Finding,
    RuleEvaluation,
    ValidationResult,
    ValidationSeverity,
)
from app.core.validation.standards import StandardProfile


class BaseValidator(ABC):
    """Abstract base class for test-type validators.

    Validators are deterministic: same input always produces same output.
    No randomness, no timestamps in comparison, no external API calls.

    Subclasses implement validate() for specific test types.

    Attributes:
        standard: Active standard profile (NETA or MICROSOFT).
        config: Validation configuration with thresholds.
    """

    def __init__(
        self,
        config: ValidationConfig | None = None,
        standard: StandardProfile = StandardProfile.NETA,
    ) -> None:
        """Initialize with optional custom config and standard profile.

        Args:
            config: Optional custom configuration. If None, builds from standard.
            standard: Which standard profile to use (NETA or MICROSOFT).
                      Ignored if config is provided explicitly.
        """
        self.standard = standard
        self.config = config or get_validation_config(standard)

    @property
    @abstractmethod
    def test_type(self) -> str:
        """Return test type this validator handles.

        Returns:
            str: One of 'grounding', 'megger', 'thermography'.
        """
        pass

    @abstractmethod
    def validate(self, extraction: BaseExtractionResult) -> ValidationResult:
        """Validate extraction result and return findings.

        Must be deterministic: same extraction = same result.

        Args:
            extraction: The extraction result to validate.

        Returns:
            ValidationResult with findings list.
        """
        pass

    def _get_default_reference(self) -> str:
        """Get default standard reference based on test type and active standard.

        Returns:
            Standard reference string for audit traceability.
        """
        # Map test type to config attribute
        ref_map = {
            "grounding": self.config.grounding.standard_reference,
            "megger": self.config.megger.standard_reference,
            "thermography": self.config.thermography.standard_reference,
            "calibration": self.config.calibration.standard_reference,
        }
        return ref_map.get(self.test_type, f"{self.standard.value.upper()} Standard")

    def track_rule(
        self,
        rules: list[RuleEvaluation],
        rule_id: str,
        passed: bool,
        details: dict | None = None,
    ) -> None:
        """Track a rule evaluation (passed or failed).

        Args:
            rules: List to append the evaluation to.
            rule_id: Unique rule identifier.
            passed: Whether the rule passed.
            details: Optional context (threshold, extracted_value).
        """
        rules.append(
            RuleEvaluation(
                rule_id=rule_id,
                passed=passed,
                details=details,
            )
        )

    def add_finding(
        self,
        findings: list[Finding],
        rule_id: str,
        severity: ValidationSeverity,
        message: str,
        field_path: str,
        extracted_value: Any,
        threshold: Any,
        standard_reference: str | None = None,
        remediation: str | None = None,
        rules_evaluated: list[RuleEvaluation] | None = None,
    ) -> None:
        """Helper to add a finding to the list.

        Also tracks the rule as failed in rules_evaluated if provided.

        Args:
            findings: List to append the finding to.
            rule_id: Unique rule identifier.
            severity: Finding severity level.
            message: Human-readable description.
            field_path: Path to the validated field.
            extracted_value: The value that was validated.
            threshold: The threshold used for comparison.
            standard_reference: Optional standard reference. If None, uses
                              config's reference for this test type.
            remediation: Optional suggested fix.
            rules_evaluated: Optional list to track the rule evaluation.
        """
        # Use config's reference as default if none provided
        if standard_reference is None:
            standard_reference = self._get_default_reference()

        findings.append(
            Finding(
                rule_id=rule_id,
                severity=severity,
                message=message,
                field_path=field_path,
                extracted_value=extracted_value,
                threshold=threshold,
                standard_reference=standard_reference,
                remediation=remediation,
            )
        )

        # Track the rule as failed if rules_evaluated list is provided
        if rules_evaluated is not None:
            self.track_rule(
                rules_evaluated,
                rule_id,
                passed=False,
                details={"threshold": threshold, "extracted_value": extracted_value},
            )

    def create_result(
        self,
        findings: list[Finding],
        equipment_tag: str | None = None,
        rules_evaluated: list[RuleEvaluation] | None = None,
    ) -> ValidationResult:
        """Create a ValidationResult from findings.

        Args:
            findings: List of validation findings.
            equipment_tag: Optional equipment identifier.
            rules_evaluated: Optional list of all rule evaluations.

        Returns:
            ValidationResult with summary calculated.
        """
        return ValidationResult(
            test_type=self.test_type,
            equipment_tag=equipment_tag,
            findings=findings,
            rules_evaluated=rules_evaluated or [],
        )

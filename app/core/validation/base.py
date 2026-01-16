"""Base validator class for all test-type validators.

This module defines the abstract base class that all specific
validators (Grounding, Megger, Thermography) inherit from.

VALD-07: Validators are deterministic - same input always produces same output.
"""

from abc import ABC, abstractmethod
from typing import Any

from app.core.extraction.schemas import BaseExtractionResult
from app.core.validation.config import ValidationConfig, get_validation_config
from app.core.validation.schemas import (
    Finding,
    ValidationResult,
    ValidationSeverity,
)


class BaseValidator(ABC):
    """Abstract base class for test-type validators.

    Validators are deterministic: same input always produces same output.
    No randomness, no timestamps in comparison, no external API calls.

    Subclasses implement validate() for specific test types.

    Attributes:
        config: Validation configuration with thresholds.
    """

    def __init__(self, config: ValidationConfig | None = None) -> None:
        """Initialize with optional custom config for testing.

        Args:
            config: Optional custom configuration. Uses default if None.
        """
        self.config = config or get_validation_config()

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
    ) -> None:
        """Helper to add a finding to the list.

        Args:
            findings: List to append the finding to.
            rule_id: Unique rule identifier.
            severity: Finding severity level.
            message: Human-readable description.
            field_path: Path to the validated field.
            extracted_value: The value that was validated.
            threshold: The threshold used for comparison.
            standard_reference: Optional standard reference.
            remediation: Optional suggested fix.
        """
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

    def create_result(
        self,
        findings: list[Finding],
        equipment_tag: str | None = None,
    ) -> ValidationResult:
        """Create a ValidationResult from findings.

        Args:
            findings: List of validation findings.
            equipment_tag: Optional equipment identifier.

        Returns:
            ValidationResult with summary calculated.
        """
        return ValidationResult(
            test_type=self.test_type,
            equipment_tag=equipment_tag,
            findings=findings,
        )

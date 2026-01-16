"""Validation orchestrator.

Coordinates all validators to produce complete validation results.
"""

from app.core.extraction.grounding import GroundingExtractionResult
from app.core.extraction.megger import MeggerExtractionResult
from app.core.extraction.schemas import BaseExtractionResult
from app.core.extraction.thermography import ThermographyExtractionResult
from app.core.validation.calibration import CalibrationValidator
from app.core.validation.config import ValidationConfig, get_validation_config
from app.core.validation.cross_field import CrossFieldValidator
from app.core.validation.grounding import GroundingValidator
from app.core.validation.megger import MeggerValidator
from app.core.validation.schemas import Finding, ValidationResult
from app.core.validation.thermography import ThermographyValidator


class ValidationOrchestrator:
    """Orchestrates validation across all validators.

    Coordinates test-type-specific validators with common validators
    to produce a complete validation result.

    Attributes:
        config: Validation configuration with thresholds.
    """

    def __init__(self, config: ValidationConfig | None = None) -> None:
        """Initialize orchestrator with optional config.

        Args:
            config: Optional custom configuration. Uses default if None.
        """
        self.config = config or get_validation_config()
        self.grounding_validator = GroundingValidator(self.config)
        self.megger_validator = MeggerValidator(self.config)
        self.thermography_validator = ThermographyValidator(self.config)
        self.calibration_validator = CalibrationValidator(self.config)
        self.cross_field_validator = CrossFieldValidator(self.config)

    def validate(self, extraction: BaseExtractionResult) -> ValidationResult:
        """Validate extraction using appropriate validators.

        Args:
            extraction: The extraction result to validate.

        Returns:
            ValidationResult with all findings combined.
        """
        all_findings: list[Finding] = []
        test_type = "unknown"
        equipment_tag = None

        # Determine test type and apply test-specific validator
        if isinstance(extraction, GroundingExtractionResult):
            test_type = "grounding"
            result = self.grounding_validator.validate(extraction)
            all_findings.extend(result.findings)
            equipment_tag = result.equipment_tag
        elif isinstance(extraction, MeggerExtractionResult):
            test_type = "megger"
            result = self.megger_validator.validate(extraction)
            all_findings.extend(result.findings)
            equipment_tag = result.equipment_tag
        elif isinstance(extraction, ThermographyExtractionResult):
            test_type = "thermography"
            result = self.thermography_validator.validate(extraction)
            all_findings.extend(result.findings)
            equipment_tag = result.equipment_tag

        # Apply calibration validation
        calib_result = self.calibration_validator.validate(extraction)
        all_findings.extend(calib_result.findings)

        # Apply cross-field validation
        cross_result = self.cross_field_validator.validate(extraction)
        all_findings.extend(cross_result.findings)

        return ValidationResult(
            test_type=test_type,
            equipment_tag=equipment_tag,
            findings=all_findings,
        )


def validate_extraction(extraction: BaseExtractionResult) -> ValidationResult:
    """Convenience function to validate an extraction.

    Args:
        extraction: The extraction result to validate.

    Returns:
        ValidationResult with all findings.
    """
    orchestrator = ValidationOrchestrator()
    return orchestrator.validate(extraction)

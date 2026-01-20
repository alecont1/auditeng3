"""Validation orchestrator.

Coordinates all validators to produce complete validation results.
"""

from app.core.extraction.fat import FATExtractionResult
from app.core.extraction.grounding import GroundingExtractionResult
from app.core.extraction.megger import MeggerExtractionResult
from app.core.extraction.ocr import CertificateOCRResult, HygrometerOCRResult
from app.core.extraction.schemas import BaseExtractionResult
from app.core.extraction.thermography import ThermographyExtractionResult
from app.core.validation.calibration import CalibrationValidator
from app.core.validation.complementary import ComplementaryValidator
from app.core.validation.config import ValidationConfig, get_validation_config
from app.core.validation.cross_field import CrossFieldValidator
from app.core.validation.fat import FATValidator
from app.core.validation.grounding import GroundingValidator
from app.core.validation.instrument_serial import InstrumentSerialValidator
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
        self.fat_validator = FATValidator(self.config)
        self.calibration_validator = CalibrationValidator(self.config)
        self.cross_field_validator = CrossFieldValidator(self.config)
        self.complementary_validator = ComplementaryValidator(self.config)
        self.instrument_serial_validator = InstrumentSerialValidator(self.config)

    def validate(
        self,
        extraction: BaseExtractionResult,
        certificate_ocr: CertificateOCRResult | None = None,
        hygrometer_ocr: HygrometerOCRResult | None = None,
        report_comments: str | None = None,
        expected_phases: list[str] | None = None,
    ) -> ValidationResult:
        """Validate extraction using appropriate validators.

        Args:
            extraction: The extraction result to validate.
            certificate_ocr: Optional OCR result from calibration certificate.
            hygrometer_ocr: Optional OCR result from thermo-hygrometer photo.
            report_comments: Optional comments section text for SPEC compliance.
            expected_phases: Optional list of expected phase identifiers.

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
        elif isinstance(extraction, FATExtractionResult):
            test_type = "fat"
            result = self.fat_validator.validate(extraction)
            all_findings.extend(result.findings)
            equipment_tag = result.equipment_tag

        # Apply calibration validation (not for FAT which has its own handling)
        if not isinstance(extraction, FATExtractionResult):
            calib_result = self.calibration_validator.validate(extraction)
            all_findings.extend(calib_result.findings)

        # Apply cross-field validation
        cross_result = self.cross_field_validator.validate(extraction)
        all_findings.extend(cross_result.findings)

        # Apply instrument serial validation for all test types (except FAT)
        # Per CAL-03: Serial instrumento != serial certificado = CRITICAL
        if certificate_ocr and not isinstance(extraction, FATExtractionResult):
            serial_result = self.instrument_serial_validator.validate(
                extraction, certificate_ocr=certificate_ocr
            )
            all_findings.extend(serial_result.findings)

        # Apply complementary validations (for thermography only)
        if isinstance(extraction, ThermographyExtractionResult):
            comp_result = self.complementary_validator.validate(
                extraction,
                certificate_ocr=certificate_ocr,
                hygrometer_ocr=hygrometer_ocr,
                expected_phases=expected_phases,
                report_comments=report_comments,
            )
            all_findings.extend(comp_result.findings)

        return ValidationResult(
            test_type=test_type,
            equipment_tag=equipment_tag,
            findings=all_findings,
        )

    def calculate_compliance_score(self, result: ValidationResult) -> float:
        """Calculate compliance score from validation result.

        Score calculation:
        - Start at 100%
        - CRITICAL finding: -25%
        - MAJOR finding: -10%
        - MINOR finding: -2%
        - INFO finding: 0%

        Args:
            result: ValidationResult to score.

        Returns:
            float: Compliance score (0-100).
        """
        score = 100.0

        score -= result.critical_count * 25
        score -= result.major_count * 10
        score -= result.minor_count * 2

        return max(0.0, score)


def validate_extraction(extraction: BaseExtractionResult) -> ValidationResult:
    """Convenience function to validate an extraction.

    Args:
        extraction: The extraction result to validate.

    Returns:
        ValidationResult with all findings.
    """
    orchestrator = ValidationOrchestrator()
    return orchestrator.validate(extraction)

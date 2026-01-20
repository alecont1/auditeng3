"""Validation module for deterministic rule-based validation.

This module provides the validation framework for checking extraction
results against NETA/IEEE standards. All validation is deterministic:
same input always produces identical output.

Key components:
- BaseValidator: Abstract base class for test-type validators
- ValidationResult: Complete validation result with findings
- Finding: Individual validation finding with evidence
- ValidationSeverity: Severity levels (CRITICAL, MAJOR, MINOR, INFO)
- ValidationConfig: Externalized thresholds configuration
- ValidationOrchestrator: Coordinates all validators
- validate_extraction: Convenience function
"""

from app.core.validation.base import BaseValidator
from app.core.validation.calibration import CalibrationValidator
from app.core.validation.config import (
    CalibrationConfig,
    FATConfig,
    GroundingThresholds,
    MeggerThresholds,
    ThermographyThresholds,
    ValidationConfig,
    get_config_for_standard,
    get_validation_config,
)
from app.core.validation.standards import StandardProfile
from app.core.validation.cross_field import CrossFieldValidator
from app.core.validation.fat import FATValidator
from app.core.validation.grounding import GroundingValidator
from app.core.validation.megger import MeggerValidator
from app.core.validation.orchestrator import ValidationOrchestrator, validate_extraction
from app.core.validation.schemas import (
    Finding,
    ValidationResult,
    ValidationRule,
    ValidationSeverity,
)
from app.core.validation.complementary import ComplementaryValidator
from app.core.validation.instrument_serial import InstrumentSerialValidator
from app.core.validation.thermography import ThermographyValidator

__all__ = [
    # Base
    "BaseValidator",
    # Validators
    "GroundingValidator",
    "MeggerValidator",
    "ThermographyValidator",
    "FATValidator",
    "CalibrationValidator",
    "CrossFieldValidator",
    "ComplementaryValidator",
    "InstrumentSerialValidator",
    # Orchestration
    "ValidationOrchestrator",
    "validate_extraction",
    # Schemas
    "Finding",
    "ValidationResult",
    "ValidationRule",
    "ValidationSeverity",
    # Config
    "CalibrationConfig",
    "FATConfig",
    "GroundingThresholds",
    "MeggerThresholds",
    "ThermographyThresholds",
    "ValidationConfig",
    "get_config_for_standard",
    "get_validation_config",
    # Standards
    "StandardProfile",
]

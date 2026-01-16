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
"""

from app.core.validation.base import BaseValidator
from app.core.validation.config import (
    CalibrationConfig,
    GroundingThresholds,
    MeggerThresholds,
    ThermographyThresholds,
    ValidationConfig,
    get_validation_config,
)
from app.core.validation.schemas import (
    Finding,
    ValidationResult,
    ValidationRule,
    ValidationSeverity,
)

__all__ = [
    # Base
    "BaseValidator",
    # Schemas
    "Finding",
    "ValidationResult",
    "ValidationRule",
    "ValidationSeverity",
    # Config
    "CalibrationConfig",
    "GroundingThresholds",
    "MeggerThresholds",
    "ThermographyThresholds",
    "ValidationConfig",
    "get_validation_config",
]

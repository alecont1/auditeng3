"""Validation result and finding schemas.

This module defines the core schemas for validation results including:
- ValidationSeverity: Severity levels for findings
- Finding: Individual validation findings with evidence
- ValidationResult: Complete validation result with summary
- ValidationRule: Rule definition for validation
"""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ValidationSeverity(StrEnum):
    """Severity levels for validation findings.

    Per project requirements, findings are classified by severity
    to enable proper prioritization and response.
    """

    CRITICAL = "critical"  # Immediate action required
    MAJOR = "major"  # Significant issue
    MINOR = "minor"  # Minor deviation
    INFO = "info"  # Informational


class Finding(BaseModel):
    """Single validation finding with evidence.

    Represents a discrete validation result for a specific field,
    including the rule that triggered it, severity, and evidence
    for auditability.

    Attributes:
        rule_id: Unique rule identifier (e.g., "GRND-001").
        severity: Finding severity level.
        message: Human-readable finding description.
        field_path: Path to the field being validated (e.g., "measurements[0].resistance_value").
        extracted_value: The value that was extracted and validated.
        threshold: The threshold value used for comparison.
        standard_reference: Optional reference to standard (e.g., "IEEE 43 Table 1").
        remediation: Optional suggested corrective action.
    """

    rule_id: str
    severity: ValidationSeverity
    message: str
    field_path: str
    extracted_value: Any
    threshold: Any
    standard_reference: str | None = None
    remediation: str | None = None


class RuleEvaluation(BaseModel):
    """Record of a single rule evaluation (passed or failed).

    Used to track all rule checks for compliance auditing.
    Both passed and failed rules are recorded.

    Attributes:
        rule_id: Unique rule identifier (e.g., "GRND-001").
        passed: Whether the rule passed.
        details: Optional context (threshold, extracted_value, etc.).
    """

    rule_id: str
    passed: bool
    details: dict | None = None


class ValidationResult(BaseModel):
    """Complete validation result for an extraction.

    Contains all findings from validating an extraction result,
    plus summary counts for each severity level and rule evaluations.

    Attributes:
        test_type: Type of test validated (grounding, megger, thermography).
        equipment_tag: Equipment identifier if available.
        findings: List of validation findings (failed rules).
        rules_evaluated: List of all rule evaluations (passed and failed).
        is_valid: True if no CRITICAL findings.
        critical_count: Count of CRITICAL findings.
        major_count: Count of MAJOR findings.
        minor_count: Count of MINOR findings.
        info_count: Count of INFO findings.
    """

    test_type: str
    equipment_tag: str | None = None
    findings: list[Finding] = Field(default_factory=list)
    rules_evaluated: list[RuleEvaluation] = Field(default_factory=list)

    # Derived summary (calculated in model_post_init)
    is_valid: bool = True
    critical_count: int = 0
    major_count: int = 0
    minor_count: int = 0
    info_count: int = 0

    def model_post_init(self, __context: Any) -> None:
        """Calculate summary counts from findings."""
        self.critical_count = 0
        self.major_count = 0
        self.minor_count = 0
        self.info_count = 0
        self.is_valid = True

        for finding in self.findings:
            if finding.severity == ValidationSeverity.CRITICAL:
                self.critical_count += 1
                self.is_valid = False
            elif finding.severity == ValidationSeverity.MAJOR:
                self.major_count += 1
            elif finding.severity == ValidationSeverity.MINOR:
                self.minor_count += 1
            else:
                self.info_count += 1


class ValidationRule(BaseModel):
    """Rule definition for validation.

    Defines a validation rule that can be applied to extraction results.
    Rules are externalized to configuration rather than hard-coded.

    Attributes:
        rule_id: Unique identifier for the rule.
        description: Human-readable description of what the rule validates.
        severity: Default severity when rule is violated.
        threshold: Threshold value used for comparison.
        standard_reference: Optional reference to the standard this rule implements.
    """

    rule_id: str
    description: str
    severity: ValidationSeverity
    threshold: Any
    standard_reference: str | None = None

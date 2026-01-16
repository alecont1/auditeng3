"""Multi-standard profile support for validation.

This module defines standard profiles (NETA, Microsoft) and their
threshold definitions with full traceability to source standards.

Each threshold value has a reference to the specific standard section
for audit compliance.

VALD-09: Same extraction can be validated against different standards
VALD-10: Every threshold has traceable standard reference
"""

from enum import StrEnum
from pydantic import BaseModel


class StandardProfile(StrEnum):
    """Available validation standard profiles.

    NETA: General NETA ATS requirements - industry standard for electrical testing.
    MICROSOFT: Microsoft Data Center CxPOR requirements - more restrictive for
               critical infrastructure.
    """

    NETA = "neta"
    MICROSOFT = "microsoft"


class ThresholdReference(BaseModel):
    """Threshold value with standard reference for traceability.

    Attributes:
        value: The threshold value (float, int, or dict for complex thresholds).
        standard: Standard name (e.g., "NETA ATS-2025", "Microsoft CxPOR v2.0").
        section: Section reference (e.g., "Table 100.1", "Section 5.3.1").
        description: Human-readable explanation of the threshold.
    """

    value: float | int | dict[int, float]
    standard: str
    section: str
    description: str


# =============================================================================
# NETA Thresholds
# =============================================================================
# Based on NETA Acceptance Testing Specifications (ATS) 2025
# and NETA Maintenance Testing Specifications (MTS) 2023

NETA_THRESHOLDS: dict[str, dict[str, ThresholdReference]] = {
    "grounding": {
        "general_max": ThresholdReference(
            value=5.0,
            standard="NETA ATS-2025",
            section="Table 100.1",
            description="Maximum grounding resistance for general equipment (ohms)",
        ),
        "data_center_max": ThresholdReference(
            value=5.0,
            standard="NETA ATS-2025",
            section="Table 100.1",
            description="Maximum grounding resistance for data center equipment (ohms)",
        ),
        "panel_max": ThresholdReference(
            value=5.0,
            standard="NETA ATS-2025",
            section="Table 100.1",
            description="Maximum grounding resistance for panels (ohms)",
        ),
        "ups_max": ThresholdReference(
            value=5.0,
            standard="NETA ATS-2025",
            section="Table 100.1",
            description="Maximum grounding resistance for UPS systems (ohms)",
        ),
        "ats_max": ThresholdReference(
            value=5.0,
            standard="NETA ATS-2025",
            section="Table 100.1",
            description="Maximum grounding resistance for ATS (ohms)",
        ),
        "gen_max": ThresholdReference(
            value=5.0,
            standard="NETA ATS-2025",
            section="Table 100.1",
            description="Maximum grounding resistance for generators (ohms)",
        ),
        "xfmr_max": ThresholdReference(
            value=5.0,
            standard="NETA ATS-2025",
            section="Table 100.1",
            description="Maximum grounding resistance for transformers (ohms)",
        ),
        "ground_bond_max": ThresholdReference(
            value=0.1,
            standard="NETA ATS-2025",
            section="Table 100.1",
            description="Maximum ground bond resistance (ohms)",
        ),
    },
    "megger": {
        "min_ir_megohms": ThresholdReference(
            value=100.0,
            standard="IEEE 43-2013",
            section="Section 12.3",
            description="Minimum 1-minute insulation resistance (megohms)",
        ),
        "excellent_ir_megohms": ThresholdReference(
            value=1000.0,
            standard="IEEE 43-2013",
            section="Section 12.3",
            description="Excellent insulation resistance threshold (megohms)",
        ),
        "min_pi": ThresholdReference(
            value=2.0,
            standard="IEEE 43-2013",
            section="Table 3",
            description="Minimum acceptable Polarization Index",
        ),
        "excellent_pi": ThresholdReference(
            value=4.0,
            standard="IEEE 43-2013",
            section="Table 3",
            description="Excellent Polarization Index threshold",
        ),
        "min_dar": ThresholdReference(
            value=1.25,
            standard="IEEE 43-2013",
            section="Section 12.2",
            description="Minimum Dielectric Absorption Ratio (60s/30s)",
        ),
        "min_ir_by_voltage": ThresholdReference(
            value={500: 25.0, 1000: 100.0, 2500: 500.0, 5000: 1000.0},
            standard="IEEE 43-2013",
            section="Table 4",
            description="Minimum IR by test voltage (V: megohms)",
        ),
    },
    "thermography": {
        "normal_max": ThresholdReference(
            value=10.0,
            standard="NETA MTS-2023",
            section="Table 100.18",
            description="Maximum delta-T for normal classification (Celsius)",
        ),
        "attention_max": ThresholdReference(
            value=25.0,
            standard="NETA MTS-2023",
            section="Table 100.18",
            description="Maximum delta-T for attention classification (Celsius)",
        ),
        "serious_max": ThresholdReference(
            value=40.0,
            standard="NETA MTS-2023",
            section="Table 100.18",
            description="Maximum delta-T for serious classification (Celsius)",
        ),
        "critical_max": ThresholdReference(
            value=50.0,
            standard="NETA MTS-2023",
            section="Table 100.18",
            description="Maximum delta-T for critical classification (Celsius)",
        ),
    },
    "calibration": {
        "max_days_expired": ThresholdReference(
            value=0,
            standard="NETA ATS-2025",
            section="Section 7.2",
            description="Maximum days equipment can be expired (0 = no expired allowed)",
        ),
        "warn_days_before_expiry": ThresholdReference(
            value=30,
            standard="NETA ATS-2025",
            section="Section 7.2",
            description="Days before expiry to warn",
        ),
    },
}


# =============================================================================
# Microsoft Data Center Thresholds
# =============================================================================
# Based on Microsoft Commissioning/Pre-Operational Requirements (CxPOR) v2.0
# More restrictive thresholds for critical data center infrastructure

MICROSOFT_THRESHOLDS: dict[str, dict[str, ThresholdReference]] = {
    "grounding": {
        "general_max": ThresholdReference(
            value=5.0,
            standard="Microsoft CxPOR v2.0",
            section="Section 5.3.1",
            description="Maximum grounding resistance for general equipment (ohms)",
        ),
        "data_center_max": ThresholdReference(
            value=1.0,
            standard="Microsoft CxPOR v2.0",
            section="Section 5.3.1",
            description="Maximum grounding resistance for data center equipment (ohms) - MORE RESTRICTIVE",
        ),
        "panel_max": ThresholdReference(
            value=5.0,
            standard="Microsoft CxPOR v2.0",
            section="Section 5.3.1",
            description="Maximum grounding resistance for panels (ohms)",
        ),
        "ups_max": ThresholdReference(
            value=1.0,
            standard="Microsoft CxPOR v2.0",
            section="Section 5.3.1",
            description="Maximum grounding resistance for UPS systems (ohms) - MORE RESTRICTIVE",
        ),
        "ats_max": ThresholdReference(
            value=5.0,
            standard="Microsoft CxPOR v2.0",
            section="Section 5.3.1",
            description="Maximum grounding resistance for ATS (ohms)",
        ),
        "gen_max": ThresholdReference(
            value=5.0,
            standard="Microsoft CxPOR v2.0",
            section="Section 5.3.1",
            description="Maximum grounding resistance for generators (ohms)",
        ),
        "xfmr_max": ThresholdReference(
            value=5.0,
            standard="Microsoft CxPOR v2.0",
            section="Section 5.3.1",
            description="Maximum grounding resistance for transformers (ohms)",
        ),
        "ground_bond_max": ThresholdReference(
            value=0.1,
            standard="Microsoft CxPOR v2.0",
            section="Section 5.3.1",
            description="Maximum ground bond resistance (ohms)",
        ),
    },
    "megger": {
        # Megger thresholds same as NETA (IEEE 43 is universal)
        "min_ir_megohms": ThresholdReference(
            value=100.0,
            standard="IEEE 43-2013",
            section="Section 12.3",
            description="Minimum 1-minute insulation resistance (megohms)",
        ),
        "excellent_ir_megohms": ThresholdReference(
            value=1000.0,
            standard="IEEE 43-2013",
            section="Section 12.3",
            description="Excellent insulation resistance threshold (megohms)",
        ),
        "min_pi": ThresholdReference(
            value=2.0,
            standard="IEEE 43-2013",
            section="Table 3",
            description="Minimum acceptable Polarization Index",
        ),
        "excellent_pi": ThresholdReference(
            value=4.0,
            standard="IEEE 43-2013",
            section="Table 3",
            description="Excellent Polarization Index threshold",
        ),
        "min_dar": ThresholdReference(
            value=1.25,
            standard="IEEE 43-2013",
            section="Section 12.2",
            description="Minimum Dielectric Absorption Ratio (60s/30s)",
        ),
        "min_ir_by_voltage": ThresholdReference(
            value={500: 25.0, 1000: 100.0, 2500: 500.0, 5000: 1000.0},
            standard="IEEE 43-2013",
            section="Table 4",
            description="Minimum IR by test voltage (V: megohms)",
        ),
    },
    "thermography": {
        # Microsoft has stricter thermography thresholds
        "normal_max": ThresholdReference(
            value=3.0,
            standard="Microsoft CxPOR v2.0",
            section="Section 5.4.2",
            description="Maximum delta-T for normal classification (Celsius) - MORE RESTRICTIVE",
        ),
        "attention_max": ThresholdReference(
            value=10.0,
            standard="Microsoft CxPOR v2.0",
            section="Section 5.4.2",
            description="Maximum delta-T for attention classification (Celsius) - MORE RESTRICTIVE",
        ),
        "serious_max": ThresholdReference(
            value=20.0,
            standard="Microsoft CxPOR v2.0",
            section="Section 5.4.2",
            description="Maximum delta-T for serious classification (Celsius) - MORE RESTRICTIVE",
        ),
        "critical_max": ThresholdReference(
            value=30.0,
            standard="Microsoft CxPOR v2.0",
            section="Section 5.4.2",
            description="Maximum delta-T for critical classification (Celsius) - MORE RESTRICTIVE",
        ),
    },
    "calibration": {
        "max_days_expired": ThresholdReference(
            value=0,
            standard="Microsoft CxPOR v2.0",
            section="Section 7.1",
            description="Maximum days equipment can be expired (0 = no expired allowed)",
        ),
        "warn_days_before_expiry": ThresholdReference(
            value=30,
            standard="Microsoft CxPOR v2.0",
            section="Section 7.1",
            description="Days before expiry to warn",
        ),
    },
}


def get_thresholds_for_standard(
    standard: StandardProfile,
) -> dict[str, dict[str, ThresholdReference]]:
    """Get threshold dictionary for a standard profile.

    Args:
        standard: The standard profile to get thresholds for.

    Returns:
        Complete threshold dictionary with references.
    """
    if standard == StandardProfile.MICROSOFT:
        return MICROSOFT_THRESHOLDS
    return NETA_THRESHOLDS


def get_standard_reference(
    standard: StandardProfile,
    category: str,
    threshold_name: str,
) -> str:
    """Get formatted standard reference for a specific threshold.

    Args:
        standard: The active standard profile.
        category: Threshold category (grounding, megger, thermography, calibration).
        threshold_name: Name of the specific threshold.

    Returns:
        Formatted reference string (e.g., "NETA ATS-2025 Table 100.1").
    """
    thresholds = get_thresholds_for_standard(standard)
    if category in thresholds and threshold_name in thresholds[category]:
        ref = thresholds[category][threshold_name]
        return f"{ref.standard} {ref.section}"
    return f"{standard.value.upper()} Standard"

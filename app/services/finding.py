"""Finding generation service.

Converts validation findings to database findings with evidence.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.validation.schemas import Finding as ValidationFinding
from app.core.validation.schemas import ValidationResult
from app.db.models.finding import Finding as FindingModel
from app.schemas.enums import FindingSeverity
from app.schemas.finding import FindingCreate, FindingEvidence


class FindingService:
    """Service for generating and persisting findings.

    Converts validation findings to database format and handles
    persistence operations.
    """

    @staticmethod
    def generate_finding_from_validation(
        validation_finding: ValidationFinding,
        analysis_id: UUID,
    ) -> FindingCreate:
        """Convert a validation Finding to a database FindingCreate.

        Maps validation finding fields to database schema format,
        building evidence dict with extracted_value, threshold, and
        standard_reference.

        Args:
            validation_finding: Finding from validation engine.
            analysis_id: UUID of the parent Analysis.

        Returns:
            FindingCreate schema ready for persistence.
        """
        # Build evidence from validation finding
        evidence = FindingEvidence(
            extracted_value=validation_finding.extracted_value,
            threshold=validation_finding.threshold,
            standard_reference=validation_finding.standard_reference or "N/A",
        )

        # Map validation severity to schema severity
        severity_val = validation_finding.severity.value if hasattr(validation_finding.severity, 'value') else validation_finding.severity
        severity = FindingSeverity(severity_val)

        return FindingCreate(
            analysis_id=analysis_id,
            severity=severity,
            rule_id=validation_finding.rule_id,
            message=validation_finding.message,
            evidence=evidence,
            remediation=validation_finding.remediation,
        )

    @staticmethod
    def generate_findings_from_validation(
        validation_result: ValidationResult,
        analysis_id: UUID,
    ) -> list[FindingCreate]:
        """Convert all findings from a ValidationResult to FindingCreate schemas.

        Batch conversion of validation findings to database format.

        Args:
            validation_result: Complete validation result with findings.
            analysis_id: UUID of the parent Analysis.

        Returns:
            List of FindingCreate schemas for persistence.
        """
        return [
            FindingService.generate_finding_from_validation(finding, analysis_id)
            for finding in validation_result.findings
        ]

    @staticmethod
    async def persist_findings(
        db: AsyncSession,
        findings: list[FindingCreate],
    ) -> list[FindingModel]:
        """Persist findings to the database.

        Bulk inserts findings and returns persisted ORM objects.

        Args:
            db: Async database session.
            findings: List of FindingCreate schemas to persist.

        Returns:
            List of persisted Finding ORM objects.
        """
        if not findings:
            return []

        # Convert to ORM models
        db_findings = [
            FindingModel(
                analysis_id=finding.analysis_id,
                severity=finding.severity.value if hasattr(finding.severity, 'value') else finding.severity,
                rule_id=finding.rule_id,
                message=finding.message,
                evidence=finding.evidence.model_dump() if finding.evidence else None,
                remediation=finding.remediation,
            )
            for finding in findings
        ]

        # Bulk add
        db.add_all(db_findings)
        await db.flush()

        # Refresh to get IDs
        for finding in db_findings:
            await db.refresh(finding)

        return db_findings


def generate_findings_from_validation(
    validation_result: ValidationResult,
    analysis_id: UUID,
) -> list[FindingCreate]:
    """Convenience function for batch finding generation.

    Args:
        validation_result: Complete validation result with findings.
        analysis_id: UUID of the parent Analysis.

    Returns:
        List of FindingCreate schemas for persistence.
    """
    return FindingService.generate_findings_from_validation(
        validation_result, analysis_id
    )

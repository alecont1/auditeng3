"""FAT (Factory Acceptance Test) validator.

Validates FAT report completeness, signatures, and specification compliance.
"""

from typing import Any

from app.core.extraction.fat import FATExtractionResult, FATChecklistItem, FATSignature
from app.core.validation.base import BaseValidator
from app.core.validation.schemas import Finding, ValidationResult, ValidationSeverity


class FATValidator(BaseValidator):
    """Validator for Factory Acceptance Test reports.

    Validates:
    - Documentation completeness
    - All required signatures present
    - No failing checklist items
    - Specification compliance
    - Cross-reference with purchase order/specs
    """

    # Required signature roles
    REQUIRED_SIGNATURES = ["manufacturer", "client"]

    @property
    def test_type(self) -> str:
        """Return test type identifier."""
        return "fat"

    def validate(self, extraction: FATExtractionResult) -> ValidationResult:
        """Validate FAT extraction.

        Args:
            extraction: FAT extraction result to validate.

        Returns:
            ValidationResult with findings.
        """
        findings: list[Finding] = []
        equipment_tag = extraction.equipment.equipment_tag.value

        # Validate checklist items
        self._validate_checklist(findings, extraction)

        # Validate signatures
        self._validate_signatures(findings, extraction)

        # Validate specifications
        self._validate_specifications(findings, extraction)

        # Validate completeness
        self._validate_completeness(findings, extraction)

        return self.create_result(findings, equipment_tag=equipment_tag)

    def _validate_checklist(
        self,
        findings: list[Finding],
        extraction: FATExtractionResult,
    ) -> None:
        """Validate checklist items."""
        if not extraction.checklist_items:
            self.add_finding(
                findings=findings,
                rule_id="FAT-001",
                severity=ValidationSeverity.CRITICAL,
                message="No FAT checklist items found",
                field_path="checklist_items",
                extracted_value=0,
                threshold="At least 1 checklist item required",
                remediation="Ensure FAT document includes complete checklist",
            )
            return

        for i, item in enumerate(extraction.checklist_items):
            status = str(item.status.value).lower() if item.status.value else "unknown"

            if status == "fail":
                self.add_finding(
                    findings=findings,
                    rule_id="FAT-002",
                    severity=ValidationSeverity.CRITICAL,
                    message=f"FAT checklist item failed: {item.description.value}",
                    field_path=f"checklist_items[{i}].status",
                    extracted_value=status,
                    threshold="pass",
                    standard_reference="FAT Requirements",
                    remediation="Address failing item before equipment acceptance",
                )
            elif status == "pending" or status == "unknown":
                self.add_finding(
                    findings=findings,
                    rule_id="FAT-003",
                    severity=ValidationSeverity.MAJOR,
                    message=f"FAT checklist item pending: {item.description.value}",
                    field_path=f"checklist_items[{i}].status",
                    extracted_value=status,
                    threshold="pass",
                    remediation="Complete pending verification before acceptance",
                )
            else:
                self.add_finding(
                    findings=findings,
                    rule_id="FAT-004",
                    severity=ValidationSeverity.INFO,
                    message=f"FAT checklist item passed: {item.item_id.value}",
                    field_path=f"checklist_items[{i}].status",
                    extracted_value=status,
                    threshold="pass",
                )

    def _validate_signatures(
        self,
        findings: list[Finding],
        extraction: FATExtractionResult,
    ) -> None:
        """Validate required signatures are present."""
        if not extraction.signatures:
            self.add_finding(
                findings=findings,
                rule_id="FAT-005",
                severity=ValidationSeverity.CRITICAL,
                message="No signatures found on FAT document",
                field_path="signatures",
                extracted_value=0,
                threshold="Required signatures: manufacturer, client",
                remediation="Obtain all required signatures before acceptance",
            )
            return

        # Check for required signatures
        signature_roles = [
            s.role.value.lower() if s.role.value else ""
            for s in extraction.signatures
        ]

        for required_role in self.REQUIRED_SIGNATURES:
            if required_role not in signature_roles:
                self.add_finding(
                    findings=findings,
                    rule_id="FAT-006",
                    severity=ValidationSeverity.CRITICAL,
                    message=f"Missing required signature: {required_role}",
                    field_path="signatures",
                    extracted_value=signature_roles,
                    threshold=f"{required_role} signature required",
                    remediation=f"Obtain {required_role} signature before acceptance",
                )
            else:
                # Find the signature and check if actually signed
                sig = next(
                    (s for s in extraction.signatures
                     if s.role.value and s.role.value.lower() == required_role),
                    None
                )
                if sig and not sig.is_signed:
                    self.add_finding(
                        findings=findings,
                        rule_id="FAT-007",
                        severity=ValidationSeverity.MAJOR,
                        message=f"{required_role.capitalize()} signature field exists but not signed",
                        field_path="signatures",
                        extracted_value="unsigned",
                        threshold="signed",
                        remediation=f"Ensure {required_role} signs the document",
                    )
                elif sig and sig.is_signed:
                    self.add_finding(
                        findings=findings,
                        rule_id="FAT-008",
                        severity=ValidationSeverity.INFO,
                        message=f"{required_role.capitalize()} signature present",
                        field_path="signatures",
                        extracted_value="signed",
                        threshold="signed",
                    )

    def _validate_specifications(
        self,
        findings: list[Finding],
        extraction: FATExtractionResult,
    ) -> None:
        """Validate specification compliance."""
        for i, spec in enumerate(extraction.specifications):
            if spec.is_compliant is False:
                self.add_finding(
                    findings=findings,
                    rule_id="FAT-009",
                    severity=ValidationSeverity.CRITICAL,
                    message=f"Specification non-compliant: {spec.parameter.value}",
                    field_path=f"specifications[{i}]",
                    extracted_value=spec.measured_value.value if spec.measured_value else None,
                    threshold=spec.specified_value.value,
                    remediation="Equipment does not meet specifications. Review with manufacturer.",
                )
            elif spec.is_compliant is True:
                self.add_finding(
                    findings=findings,
                    rule_id="FAT-010",
                    severity=ValidationSeverity.INFO,
                    message=f"Specification compliant: {spec.parameter.value}",
                    field_path=f"specifications[{i}]",
                    extracted_value=spec.measured_value.value if spec.measured_value else None,
                    threshold=spec.specified_value.value,
                )
            else:
                # Compliance not verified
                self.add_finding(
                    findings=findings,
                    rule_id="FAT-011",
                    severity=ValidationSeverity.MINOR,
                    message=f"Specification compliance not verified: {spec.parameter.value}",
                    field_path=f"specifications[{i}]",
                    extracted_value=None,
                    threshold=spec.specified_value.value,
                    remediation="Verify specification compliance during FAT",
                )

    def _validate_completeness(
        self,
        findings: list[Finding],
        extraction: FATExtractionResult,
    ) -> None:
        """Validate FAT document completeness."""
        # Check test date
        if not extraction.test_conditions.test_date.value:
            self.add_finding(
                findings=findings,
                rule_id="FAT-012",
                severity=ValidationSeverity.MAJOR,
                message="FAT test date not specified",
                field_path="test_conditions.test_date",
                extracted_value=None,
                threshold="Test date required",
                remediation="Ensure FAT date is clearly documented",
            )

        # Check witness presence (for critical equipment)
        if not extraction.test_conditions.witness_present:
            self.add_finding(
                findings=findings,
                rule_id="FAT-013",
                severity=ValidationSeverity.MINOR,
                message="No client witness indicated for FAT",
                field_path="test_conditions.witness_present",
                extracted_value=False,
                threshold="Client witness recommended",
                remediation="Consider having client witness present for critical equipment FAT",
            )

        # Summary finding
        if extraction.overall_status == "passed":
            self.add_finding(
                findings=findings,
                rule_id="FAT-014",
                severity=ValidationSeverity.INFO,
                message=f"FAT complete: {extraction.pass_count} items passed",
                field_path="overall_status",
                extracted_value=extraction.overall_status,
                threshold="passed",
            )
        elif extraction.overall_status == "failed":
            self.add_finding(
                findings=findings,
                rule_id="FAT-015",
                severity=ValidationSeverity.CRITICAL,
                message=f"FAT failed: {extraction.fail_count} items failed",
                field_path="overall_status",
                extracted_value=extraction.overall_status,
                threshold="passed",
                remediation="Address all failing items before equipment acceptance",
            )

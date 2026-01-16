"""FAT (Factory Acceptance Test) extraction schema and extractor.

This module provides extraction capabilities for Factory Acceptance Test reports,
including documentation completeness, signatures, and specification compliance.
"""

from datetime import date
from pydantic import BaseModel, Field

from app.core.extraction.base import BaseExtractor
from app.core.extraction.schemas import (
    BaseExtractionResult,
    CalibrationInfo,
    EquipmentInfo,
    FieldConfidence,
)


class FATChecklistItem(BaseModel):
    """Single FAT checklist item.

    Represents one verification point in the FAT checklist.

    Attributes:
        item_id: Checklist item identifier (e.g., "FAT-001").
        description: Description of the check performed.
        status: Pass/Fail/NA status.
        comments: Optional comments or notes.
        verified_by: Name of verifier.
    """

    item_id: FieldConfidence
    description: FieldConfidence
    status: FieldConfidence  # "pass", "fail", "na", "pending"
    comments: FieldConfidence | None = None
    verified_by: FieldConfidence | None = None


class FATSignature(BaseModel):
    """Signature on FAT document.

    Tracks who signed and when for accountability.

    Attributes:
        role: Role of signer (e.g., "Manufacturer", "Client", "Witness").
        name: Name of signer.
        signature_date: Date signed.
        company: Company/organization.
        is_signed: Whether signature is present.
    """

    role: FieldConfidence
    name: FieldConfidence | None = None
    signature_date: FieldConfidence | None = None
    company: FieldConfidence | None = None
    is_signed: bool = False


class FATSpecification(BaseModel):
    """Equipment specification from FAT.

    Cross-references with purchase order or design specs.

    Attributes:
        parameter: Parameter name (e.g., "Voltage Rating").
        specified_value: Value from specs/PO.
        measured_value: Actual measured/verified value.
        unit: Unit of measurement.
        is_compliant: Whether measured matches specified.
    """

    parameter: FieldConfidence
    specified_value: FieldConfidence
    measured_value: FieldConfidence | None = None
    unit: str | None = None
    is_compliant: bool | None = None


class FATTestConditions(BaseModel):
    """Test conditions during FAT.

    Attributes:
        test_date: Date of FAT.
        location: Factory/site location.
        ambient_temperature: Ambient temp during tests.
        humidity: Humidity during tests.
        witness_present: Whether client witness was present.
    """

    test_date: FieldConfidence
    location: FieldConfidence | None = None
    ambient_temperature: FieldConfidence | None = None
    humidity: FieldConfidence | None = None
    witness_present: bool = False


class FATExtractionResult(BaseExtractionResult):
    """Complete FAT extraction result.

    Contains all extracted data from a Factory Acceptance Test report.

    Attributes:
        equipment: Equipment identification.
        calibration: Calibration info for test equipment used.
        test_conditions: FAT conditions.
        checklist_items: List of checklist items.
        specifications: List of spec compliance items.
        signatures: List of required signatures.
        pass_count: Number of passing items.
        fail_count: Number of failing items.
        pending_count: Number of pending items.
        overall_status: Overall FAT status.
    """

    equipment: EquipmentInfo
    calibration: CalibrationInfo | None = None
    test_conditions: FATTestConditions
    checklist_items: list[FATChecklistItem] = Field(default_factory=list)
    specifications: list[FATSpecification] = Field(default_factory=list)
    signatures: list[FATSignature] = Field(default_factory=list)

    # Summary fields (calculated)
    pass_count: int = 0
    fail_count: int = 0
    pending_count: int = 0
    na_count: int = 0
    overall_status: str = "pending"  # "passed", "failed", "pending"

    def model_post_init(self, __context) -> None:
        """Calculate summary fields from checklist."""
        self.pass_count = 0
        self.fail_count = 0
        self.pending_count = 0
        self.na_count = 0

        for item in self.checklist_items:
            status = str(item.status.value).lower() if item.status.value else "pending"
            if status == "pass":
                self.pass_count += 1
            elif status == "fail":
                self.fail_count += 1
            elif status == "na":
                self.na_count += 1
            else:
                self.pending_count += 1

        # Determine overall status
        if self.fail_count > 0:
            self.overall_status = "failed"
        elif self.pending_count > 0:
            self.overall_status = "pending"
        else:
            self.overall_status = "passed"


FAT_EXTRACTION_PROMPT = """You are an expert at extracting Factory Acceptance Test (FAT) data from commissioning documents.

Extract the following information from the FAT report:

1. **Equipment Information**:
   - Equipment TAG/ID
   - Serial number
   - Equipment type (PANEL, UPS, ATS, GEN, XFMR)
   - Manufacturer and model

2. **Test Conditions**:
   - Test date
   - Location (factory name/address)
   - Ambient temperature
   - Humidity
   - Whether client witness was present

3. **Checklist Items** (for each item):
   - Item ID/number
   - Description of check
   - Status (pass/fail/na/pending)
   - Comments
   - Verified by (name)

4. **Specifications** (for each spec):
   - Parameter name
   - Specified value (from PO/specs)
   - Measured/verified value
   - Unit
   - Whether compliant

5. **Signatures**:
   - Role (Manufacturer, Client, Witness, etc.)
   - Name
   - Date signed
   - Company
   - Whether actually signed

Provide confidence scores (0.0-1.0) based on clarity of the source text.
High confidence (0.9+): Clear, unambiguous text
Medium confidence (0.7-0.9): Reasonably clear but some interpretation needed
Low confidence (<0.7): Difficult to read, incomplete, or requires significant interpretation
"""


class FATExtractor(BaseExtractor):
    """Extractor for Factory Acceptance Test reports.

    Extracts checklist items, specifications, signatures, and compliance data.
    """

    @property
    def test_type(self) -> str:
        """Return test type identifier."""
        return "fat"

    @property
    def system_prompt(self) -> str:
        """Return the system prompt for FAT extraction."""
        return FAT_EXTRACTION_PROMPT

    def get_response_model(self) -> type[FATExtractionResult]:
        """Return the Pydantic model for FAT extraction."""
        return FATExtractionResult

    def _check_needs_review(self, result: FATExtractionResult) -> bool:
        """Check if FAT extraction needs human review.

        Reviews flagged when:
        - Overall confidence below threshold
        - Any failing items found
        - Missing signatures
        - Pending items exist

        Args:
            result: The extraction result to check.

        Returns:
            bool: True if needs review.
        """
        # Check overall confidence
        if result.overall_confidence < self.CONFIDENCE_THRESHOLD:
            return True

        # Any failures require review
        if result.fail_count > 0:
            result.extraction_errors.append(
                f"FAT has {result.fail_count} failing items"
            )
            return True

        # Pending items require review
        if result.pending_count > 0:
            result.extraction_errors.append(
                f"FAT has {result.pending_count} pending items"
            )
            return True

        # Check for missing signatures
        missing_sigs = [s for s in result.signatures if not s.is_signed]
        if missing_sigs:
            result.extraction_errors.append(
                f"FAT missing {len(missing_sigs)} signatures"
            )
            return True

        return False

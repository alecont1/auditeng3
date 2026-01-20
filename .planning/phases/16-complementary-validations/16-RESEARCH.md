# Phase 16: Complementary Validations - Research

**Researched:** 2026-01-19
**Domain:** Cross-validation rules for thermography reports
**Confidence:** HIGH

## Summary

This research documents the current validation architecture in AuditEng and identifies integration points for adding the 5 missing complementary validations (CALIBRATION_EXPIRED, SERIAL_MISMATCH, VALUE_MISMATCH, PHOTO_MISSING, SPEC_NON_COMPLIANCE).

The codebase follows a clean architecture with validators extending `BaseValidator`, using a deterministic validation approach where AI extraction is followed by rule-based comparison. The existing `ValidationOrchestrator` aggregates findings from multiple validators - the new complementary validators will plug directly into this pattern.

**Primary recommendation:** Create a new `ComplementaryValidator` class (extending `BaseValidator`) containing all 5 cross-validation rules. Register it in `ValidationOrchestrator.validate()` to run after existing validators.

## 1. Current Architecture - Validation Engine

### Validator Pattern

All validators inherit from `BaseValidator` (`/home/xande/app/core/validation/base.py`):

```python
class BaseValidator(ABC):
    """Abstract base class for test-type validators."""

    def __init__(
        self,
        config: ValidationConfig | None = None,
        standard: StandardProfile = StandardProfile.NETA,
    ) -> None:
        self.standard = standard
        self.config = config or get_validation_config(standard)

    @property
    @abstractmethod
    def test_type(self) -> str:
        """Return test type this validator handles."""
        pass

    @abstractmethod
    def validate(self, extraction: BaseExtractionResult) -> ValidationResult:
        """Validate extraction result and return findings."""
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
        rules_evaluated: list[RuleEvaluation] | None = None,
    ) -> None:
        """Helper to add a finding to the list."""
        pass

    def create_result(
        self,
        findings: list[Finding],
        equipment_tag: str | None = None,
        rules_evaluated: list[RuleEvaluation] | None = None,
    ) -> ValidationResult:
        """Create a ValidationResult from findings."""
        pass
```

**Key insight:** Validators are deterministic - same input produces same output. No randomness, timestamps in comparison, or external API calls during validation.

### Orchestrator Pattern

The `ValidationOrchestrator` (`/home/xande/app/core/validation/orchestrator.py`) coordinates all validators:

```python
class ValidationOrchestrator:
    def __init__(self, config: ValidationConfig | None = None) -> None:
        self.config = config or get_validation_config()
        self.grounding_validator = GroundingValidator(self.config)
        self.megger_validator = MeggerValidator(self.config)
        self.thermography_validator = ThermographyValidator(self.config)
        self.fat_validator = FATValidator(self.config)
        self.calibration_validator = CalibrationValidator(self.config)
        self.cross_field_validator = CrossFieldValidator(self.config)

    def validate(self, extraction: BaseExtractionResult) -> ValidationResult:
        """Validate extraction using appropriate validators."""
        all_findings: list[Finding] = []

        # 1. Test-type specific validation
        if isinstance(extraction, ThermographyExtractionResult):
            result = self.thermography_validator.validate(extraction)
            all_findings.extend(result.findings)

        # 2. Calibration validation
        calib_result = self.calibration_validator.validate(extraction)
        all_findings.extend(calib_result.findings)

        # 3. Cross-field validation
        cross_result = self.cross_field_validator.validate(extraction)
        all_findings.extend(cross_result.findings)

        return ValidationResult(
            test_type=test_type,
            equipment_tag=equipment_tag,
            findings=all_findings,  # ALL findings aggregated
        )
```

**Integration point:** New `ComplementaryValidator` will be added as step 4, after cross-field validation.

### Existing Validators

| Validator | Location | Purpose |
|-----------|----------|---------|
| `GroundingValidator` | `grounding.py` | Ground resistance thresholds |
| `MeggerValidator` | `megger.py` | Insulation resistance thresholds |
| `ThermographyValidator` | `thermography.py` | Delta-T temperature thresholds |
| `FATValidator` | `fat.py` | Factory acceptance test checks |
| `CalibrationValidator` | `calibration.py` | Certificate expiration check |
| `CrossFieldValidator` | `cross_field.py` | Equipment TAG presence, units |

**Note:** `CalibrationValidator` already checks expiration but uses `extraction.calibration.expiration_date` vs `test_conditions.test_date`. The new CALIBRATION_EXPIRED rule needs to check measurement_date against calibration_date from certificate.

## 2. Finding Creation - Schema and Storage

### Validation Finding Schema

Location: `/home/xande/app/core/validation/schemas.py`

```python
class ValidationSeverity(StrEnum):
    CRITICAL = "critical"  # Immediate action required
    MAJOR = "major"        # Significant issue
    MINOR = "minor"        # Minor deviation
    INFO = "info"          # Informational

class Finding(BaseModel):
    rule_id: str           # e.g., "CALIB-004", "SERIAL-001"
    severity: ValidationSeverity
    message: str           # Human-readable description
    field_path: str        # e.g., "calibration.expiration_date"
    extracted_value: Any   # The value that was validated
    threshold: Any         # The threshold used for comparison
    standard_reference: str | None = None  # e.g., "ISO/IEC 17025"
    remediation: str | None = None  # Suggested corrective action
```

### Database Finding Schema

Location: `/home/xande/app/schemas/finding.py`

```python
class FindingEvidence(BaseSchema):
    extracted_value: Any
    threshold: Any
    standard_reference: str

class FindingCreate(FindingBase):
    analysis_id: UUID
    severity: FindingSeverity
    rule_id: str
    message: str
    evidence: FindingEvidence | None = None
    remediation: str | None = None
```

### Mapping Process

The `FindingService` (`/home/xande/app/services/finding.py`) converts validation findings to database format:

```python
def generate_finding_from_validation(
    validation_finding: ValidationFinding,
    analysis_id: UUID,
) -> FindingCreate:
    evidence = FindingEvidence(
        extracted_value=validation_finding.extracted_value,
        threshold=validation_finding.threshold,
        standard_reference=validation_finding.standard_reference or "N/A",
    )
    return FindingCreate(
        analysis_id=analysis_id,
        severity=FindingSeverity(validation_finding.severity.value),
        rule_id=validation_finding.rule_id,
        message=validation_finding.message,
        evidence=evidence,
        remediation=validation_finding.remediation,
    )
```

**New finding codes to add:**
- `CALIB-EXP` or reuse `CALIB-004`: Calibration expired (already exists, may need enhancement)
- `SERIAL-001`: Serial number mismatch
- `TEMP-001`: Reflected temperature mismatch
- `PHOTO-001`: Photo missing for phase
- `SPEC-001`: Non-compliance with SPEC (delta > 10C without documentation)

## 3. Verdict Logic - Blocker Integration

### Current Verdict Rules

Location: `/home/xande/app/services/verdict.py`

```python
class VerdictService:
    @staticmethod
    def compute_verdict(
        validation_result: ValidationResult,
        compliance_score: float,
        confidence_score: float,
    ) -> AnalysisVerdict:
        # Rule 1: REJECTED if any CRITICAL finding
        if validation_result.critical_count > 0:
            return AnalysisVerdict.REJECTED

        # Rule 2: REVIEW if low compliance or low confidence
        if compliance_score < 95 or confidence_score < 0.7:
            return AnalysisVerdict.REVIEW

        # Rule 3: APPROVED otherwise
        return AnalysisVerdict.APPROVED
```

**Key insight:** The verdict logic already uses `critical_count` from ValidationResult. New blocker findings just need to use `ValidationSeverity.CRITICAL` severity.

### Blocker Mapping (from CONTEXT.md)

| Finding Code | Blocker | Severity |
|--------------|---------|----------|
| CALIBRATION_EXPIRED | Yes | CRITICAL |
| SERIAL_MISMATCH | Yes | CRITICAL |
| VALUE_MISMATCH | Yes | CRITICAL |
| PHOTO_MISSING | Yes | CRITICAL |
| PHOTO_ILLEGIBLE | Yes | CRITICAL |
| SPEC_NON_COMPLIANCE | Yes | CRITICAL |
| SERIAL_ILLEGIBLE | No | MAJOR (low confidence) |
| TEMP_EXCEEDED | No | MINOR (OK if documented) |

**Implementation:** Use `ValidationSeverity.CRITICAL` for all blockers. No code changes needed in VerdictService.

## 4. Thermography Extraction - Current Output Fields

### ThermographyExtractionResult Schema

Location: `/home/xande/app/core/extraction/thermography.py`

```python
class ThermalImageData(BaseModel):
    image_id: str | None = None
    ambient_temperature: FieldConfidence | None = None
    reflected_temperature: FieldConfidence | None = None  # KEY for VALUE_MISMATCH
    emissivity: FieldConfidence | None = None
    distance: FieldConfidence | None = None
    humidity: FieldConfidence | None = None

class ThermographyTestConditions(BaseModel):
    inspection_date: FieldConfidence     # KEY for CALIBRATION_EXPIRED
    inspector_name: FieldConfidence | None = None
    load_conditions: FieldConfidence | None = None
    camera_model: FieldConfidence | None = None
    camera_serial: FieldConfidence | None = None  # KEY for SERIAL_MISMATCH

class Hotspot(BaseModel):
    location: FieldConfidence        # KEY for PHOTO_MISSING (which phases)
    component: FieldConfidence | None = None
    max_temperature: FieldConfidence
    reference_temperature: FieldConfidence
    delta_t: float | None = None     # KEY for SPEC_NON_COMPLIANCE (>10C check)
    severity: HotspotSeverity | None = None

class ThermographyExtractionResult(BaseExtractionResult):
    equipment: EquipmentInfo
    calibration: CalibrationInfo | None = None  # KEY for CALIBRATION_EXPIRED
    test_conditions: ThermographyTestConditions
    thermal_data: ThermalImageData  # Contains reflected_temperature
    hotspots: list[Hotspot] = []
    max_delta_t: float | None = None
```

### Fields Available for New Validations

| Validation | Required Fields | Currently Extracted |
|------------|-----------------|---------------------|
| CALIBRATION_EXPIRED | `calibration.expiration_date`, `test_conditions.inspection_date` | YES |
| SERIAL_MISMATCH | `test_conditions.camera_serial`, OCR from certificate photo | PARTIAL (need OCR) |
| VALUE_MISMATCH | `thermal_data.reflected_temperature`, OCR from thermo-hygrometer photo | PARTIAL (need OCR) |
| PHOTO_MISSING | `hotspots[].location`, list of expected phases | PARTIAL (need phase list) |
| SPEC_NON_COMPLIANCE | `hotspots[].delta_t`, report comments section | PARTIAL (need comments) |

### Fields Needing Addition

New extraction fields or secondary extraction needed:

1. **Certificate serial number from photo** - Claude Vision OCR
2. **Thermo-hygrometer temperature reading** - Claude Vision OCR
3. **Report comments section** - Text extraction or Vision
4. **Phase list from report structure** - Text extraction

## 5. Vision API Patterns - Existing Claude Vision Usage

### Extraction Client

Location: `/home/xande/app/core/extraction/client.py`

```python
def _build_image_content(images: list[str]) -> list[dict]:
    """Build image content blocks for Claude Vision."""
    content = []
    for img_data in images:
        media_type = "image/jpeg"
        # Handle data URL format
        if img_data.startswith("data:"):
            # Extract media type from header
            ...
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": img_data,
            },
        })
    return content

async def extract_structured(
    prompt: str,
    response_model: type[T],
    images: list[str] | None = None,
    text_content: str | None = None,
    model: str = "claude-sonnet-4-20250514",
) -> tuple[T, ExtractionMetadata]:
    """Extract structured data using Instructor and Claude."""
    client = get_instructor_client()

    user_content = []
    if images:
        user_content.extend(_build_image_content(images))
    if text_content:
        user_content.append({"type": "text", "text": text_content})

    response = client.messages.create(
        model=model,
        max_tokens=4096,
        max_retries=3,
        system=prompt,
        messages=[{"role": "user", "content": user_content}],
        response_model=response_model,
    )
    return response, metadata
```

### Usage Pattern in ThermographyExtractor

```python
class ThermographyExtractor(BaseExtractor):
    BATCH_SIZE: int = 10

    async def extract_from_images(
        self,
        images: list[bytes],
        page_numbers: list[int] | None = None,
    ) -> ThermographyExtractionResult:
        # Process in batches for large documents
        if len(images) <= self.BATCH_SIZE:
            b64_images = [base64.b64encode(img).decode() for img in images]
            return await self.extract(content=b64_images, page_numbers=page_numbers)

        # Batch processing for many images
        all_results = []
        for batch in batches:
            result = await self.extract(content=b64_images, page_numbers=batch_pages)
            all_results.append(result)
        return self._merge_results(all_results)
```

### Pattern for New OCR Extractions

For SERIAL_MISMATCH and VALUE_MISMATCH, create targeted extraction schemas:

```python
# Example for serial number OCR
class CertificateOCRResult(BaseModel):
    serial_number: FieldConfidence
    calibration_lab: FieldConfidence | None = None

CERTIFICATE_OCR_PROMPT = """Extract the serial number visible on this calibration certificate image.
Look for:
- "Serial No:", "S/N:", "Serial Number:"
- Camera/device serial number (usually alphanumeric)
Return the exact text visible, with confidence based on legibility."""

# Usage in ComplementaryValidator
async def extract_certificate_serial(image: bytes) -> CertificateOCRResult:
    b64_image = base64.b64encode(image).decode()
    return await extract_structured(
        prompt=CERTIFICATE_OCR_PROMPT,
        response_model=CertificateOCRResult,
        images=[b64_image],
    )
```

## 6. Test Structure - Fixtures and Benchmarks

### Test Directory Structure

```
app/tests/
├── __init__.py
├── api/
│   ├── conftest.py          # HTTP client, auth fixtures
│   ├── test_analyses.py
│   └── test_reports.py
├── middleware/
│   └── test_rate_limit.py
├── services/
│   ├── test_finding.py
│   ├── test_verdict.py
│   └── test_report.py
└── validation/
    ├── test_grounding.py
    ├── test_megger.py
    ├── test_thermography.py  # Example for new tests
    └── test_orchestrator.py
```

### Existing Test Patterns

From `/home/xande/app/tests/validation/test_thermography.py`:

```python
@pytest.fixture
def validator():
    """Create a ThermographyValidator instance."""
    return ThermographyValidator()

@pytest.fixture
def basic_equipment():
    """Create basic equipment info."""
    return EquipmentInfo(
        equipment_tag=FieldConfidence(value="QD-01", confidence=0.9),
        equipment_type=FieldConfidence(value="panel", confidence=0.9),
    )

def create_hotspot(max_temp: float, ref_temp: float, location: str = "Breaker 1") -> Hotspot:
    """Helper to create a hotspot."""
    return Hotspot(
        location=FieldConfidence(value=location, confidence=0.9),
        max_temperature=FieldConfidence(value=max_temp, confidence=0.9),
        reference_temperature=FieldConfidence(value=ref_temp, confidence=0.9),
    )

class TestThermographyValidator:
    def test_critical_delta(self, validator, basic_equipment, ...):
        extraction = ThermographyExtractionResult(
            equipment=basic_equipment,
            hotspots=[create_hotspot(max_temp=55.0, ref_temp=30.0)],  # 25C delta
            overall_confidence=0.9,
        )
        result = validator.validate(extraction)
        assert not result.is_valid
        assert result.critical_count >= 1
```

### Benchmark Structure (Proposed)

Per CONTEXT.md, ground truth at `/tests/fixtures/ground_truth.json`:

```python
# Proposed structure
{
  "version": "1.0",
  "reports": [
    {
      "report_id": "report_001",
      "file_path": "tests/fixtures/reports/rejected_001.pdf",
      "expected_verdict": "rejected",
      "expected_findings": [
        {
          "code": "CALIBRATION_EXPIRED",
          "blocker": true,
          "message_contains": "expired"
        },
        {
          "code": "SERIAL_MISMATCH",
          "blocker": true
        }
      ],
      "pair_with": "report_002"  # Corrected version
    },
    {
      "report_id": "report_002",
      "file_path": "tests/fixtures/reports/approved_001.pdf",
      "expected_verdict": "approved",
      "expected_findings": []
    }
  ]
}
```

### Benchmark Test Implementation

```python
# tests/validation/test_benchmark.py
import json
import pytest
from pathlib import Path

GROUND_TRUTH_PATH = Path("tests/fixtures/ground_truth.json")

@pytest.fixture
def ground_truth():
    with open(GROUND_TRUTH_PATH) as f:
        return json.load(f)

class TestBenchmark:
    @pytest.mark.parametrize("report", ground_truth()["reports"])
    async def test_recall(self, report, validator):
        """Each expected finding must be detected."""
        result = await process_and_validate(report["file_path"])

        found_codes = {f.rule_id for f in result.findings}
        for expected in report["expected_findings"]:
            assert expected["code"] in found_codes, (
                f"Missing finding: {expected['code']}"
            )

    def test_overall_recall(self, ground_truth):
        """Aggregate recall must be >= 90%."""
        total_expected = sum(len(r["expected_findings"]) for r in ground_truth["reports"])
        total_found = ...  # Count matched
        recall = total_found / total_expected
        assert recall >= 0.90, f"Recall {recall:.1%} below 90% threshold"
```

## 7. Integration Points - Where New Validators Plug In

### Validator Registration

Add to `/home/xande/app/core/validation/orchestrator.py`:

```python
from app.core.validation.complementary import ComplementaryValidator

class ValidationOrchestrator:
    def __init__(self, config: ValidationConfig | None = None) -> None:
        # ... existing validators ...
        self.complementary_validator = ComplementaryValidator(self.config)

    def validate(self, extraction: BaseExtractionResult) -> ValidationResult:
        # ... existing validation flow ...

        # 4. Complementary validations (new)
        if isinstance(extraction, ThermographyExtractionResult):
            comp_result = self.complementary_validator.validate(extraction)
            all_findings.extend(comp_result.findings)

        return ValidationResult(...)
```

### New File Structure

```
app/core/validation/
├── __init__.py              # Add ComplementaryValidator export
├── complementary.py         # NEW: All 5 cross-validations
└── prompts/
    └── complementary.py     # NEW: OCR prompts for serial, temp readings
```

### Config Extension

Add to `/home/xande/app/core/validation/config.py`:

```python
class ComplementaryConfig(BaseModel):
    """Complementary validation settings."""

    # SPEC compliance threshold (Microsoft standard)
    spec_delta_t_threshold: float = 10.0
    spec_required_keywords: list[str] = [
        "terminals", "insulators", "torque", "conductors"
    ]

    # Serial match tolerance (for OCR)
    serial_confidence_threshold: float = 0.7

    # Temperature match tolerance
    temp_match_tolerance: float = 2.0  # degrees C

class ValidationConfig(BaseModel):
    # ... existing ...
    complementary: ComplementaryConfig = Field(default_factory=ComplementaryConfig)
```

### Module Exports

Update `/home/xande/app/core/validation/__init__.py`:

```python
from app.core.validation.complementary import ComplementaryValidator

__all__ = [
    # ... existing ...
    "ComplementaryValidator",
]
```

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Date comparison | Custom date parsing | `datetime.date` comparison | Edge cases: leap years, timezones |
| OCR confidence | Custom confidence calculation | Existing `FieldConfidence.confidence` | Consistency with extraction |
| Finding aggregation | Manual list management | `ValidationResult` auto-counting | `model_post_init` handles severity counts |
| API retry logic | Custom retry loop | `tenacity` decorator (already used) | Exponential backoff, max retries |

## Common Pitfalls

### Pitfall 1: Async in Validators

**What goes wrong:** Validators must be deterministic. Calling async Claude API during validation breaks this.
**Why it happens:** Tempting to do OCR inline during validation.
**How to avoid:** Extract ALL needed data BEFORE validation. Pass pre-extracted data to validators.
**Pattern:**
```python
# WRONG: Async during validation
def validate(self, extraction):
    serial = await self.ocr_certificate(image)  # BAD

# CORRECT: Pre-extract, then validate
extraction = await extract_all(document)  # All OCR here
result = validator.validate(extraction)   # Deterministic
```

### Pitfall 2: Modifying is_valid Directly

**What goes wrong:** ValidationResult.is_valid is auto-calculated in model_post_init
**Why it happens:** Trying to set is_valid manually
**How to avoid:** Let model_post_init calculate from findings. Use CRITICAL severity for blockers.

### Pitfall 3: Missing Standard Reference

**What goes wrong:** Findings without standard_reference break audit trail
**Why it happens:** Forgetting to add reference in add_finding call
**How to avoid:** Use `_get_default_reference()` from BaseValidator or explicit reference

### Pitfall 4: Confidence Threshold Confusion

**What goes wrong:** Blocking on low confidence instead of flagging for review
**Why it happens:** Treating low confidence as error
**How to avoid:**
- Low confidence OCR = MAJOR (SERIAL_ILLEGIBLE), not CRITICAL
- Let human verify, don't auto-reject

## Code Examples

### Creating a New Validator

```python
# /home/xande/app/core/validation/complementary.py
from app.core.validation.base import BaseValidator
from app.core.validation.schemas import Finding, ValidationResult, ValidationSeverity

class ComplementaryValidator(BaseValidator):
    """Complementary validations for thermography reports."""

    @property
    def test_type(self) -> str:
        return "complementary"

    def validate(self, extraction: ThermographyExtractionResult) -> ValidationResult:
        findings: list[Finding] = []

        # Run all validations (no short-circuit per CONTEXT.md)
        self._check_calibration_expired(findings, extraction)
        self._check_serial_mismatch(findings, extraction)
        self._check_value_mismatch(findings, extraction)
        self._check_photo_missing(findings, extraction)
        self._check_spec_compliance(findings, extraction)

        return self.create_result(
            findings,
            equipment_tag=extraction.equipment.equipment_tag.value
        )

    def _check_calibration_expired(
        self,
        findings: list[Finding],
        extraction: ThermographyExtractionResult
    ) -> None:
        """Check if calibration date < measurement date."""
        calibration = extraction.calibration
        if not calibration or not calibration.expiration_date.value:
            return  # Handled by existing CalibrationValidator

        inspection_date = extraction.test_conditions.inspection_date.value
        exp_date = self._parse_date(calibration.expiration_date.value)
        insp_date = self._parse_date(inspection_date)

        if exp_date and insp_date and exp_date < insp_date:
            self.add_finding(
                findings=findings,
                rule_id="CALIB-EXP",
                severity=ValidationSeverity.CRITICAL,  # blocker=True
                message=f"Calibration expired before inspection: exp={exp_date}, inspection={insp_date}",
                field_path="calibration.expiration_date",
                extracted_value=str(exp_date),
                threshold=f"Must be >= {insp_date}",
                standard_reference="ISO/IEC 17025",
                remediation="Recalibrate instrument before use. Test results invalid.",
            )
```

### Adding Finding with Blocker Severity

```python
def _check_serial_mismatch(
    self,
    findings: list[Finding],
    extraction: ThermographyExtractionResult,
    certificate_ocr: CertificateOCRResult,
) -> None:
    """Compare serial from photo OCR vs report serial."""
    report_serial = extraction.test_conditions.camera_serial
    photo_serial = certificate_ocr.serial_number

    if not report_serial or not photo_serial:
        return

    # Normalize for comparison
    report_val = str(report_serial.value).strip().upper()
    photo_val = str(photo_serial.value).strip().upper()

    # Check confidence first
    if photo_serial.confidence < self.config.complementary.serial_confidence_threshold:
        self.add_finding(
            findings=findings,
            rule_id="SERIAL-ILL",
            severity=ValidationSeverity.MAJOR,  # Not a blocker - flag for review
            message=f"Serial number illegible (confidence: {photo_serial.confidence:.0%})",
            field_path="certificate.serial_number",
            extracted_value=photo_val,
            threshold="Confidence >= 70%",
            remediation="Manual verification required",
        )
        return

    if report_val != photo_val:
        self.add_finding(
            findings=findings,
            rule_id="SERIAL-001",
            severity=ValidationSeverity.CRITICAL,  # blocker=True
            message=f"Serial mismatch: report='{report_val}', certificate='{photo_val}'",
            field_path="test_conditions.camera_serial",
            extracted_value=report_val,
            threshold=f"Expected: {photo_val}",
            standard_reference="Microsoft SPEC 26 05 00",
            remediation="Verify correct calibration certificate is attached",
        )
```

## Open Questions

1. **OCR Timing**: Should certificate/hygrometer OCR run during extraction phase (before validation) or as a separate step?
   - Recommendation: During extraction phase for determinism

2. **Phase List Source**: Where does expected phase list come from for PHOTO_MISSING check?
   - Need to investigate report structure extraction

3. **Comments Section Format**: How is the COMMENTS section structured in thermography reports?
   - May need sample reports to determine extraction approach

## Sources

### Primary (HIGH confidence)
- `/home/xande/app/core/validation/base.py` - Validator base class
- `/home/xande/app/core/validation/orchestrator.py` - Validation orchestration
- `/home/xande/app/core/validation/schemas.py` - Finding schemas
- `/home/xande/app/core/extraction/thermography.py` - Extraction schemas
- `/home/xande/app/core/extraction/client.py` - Vision API patterns
- `/home/xande/app/services/verdict.py` - Verdict logic
- `/home/xande/app/tests/validation/test_thermography.py` - Test patterns

### Context Documents (HIGH confidence)
- `/home/xande/.planning/phases/16-complementary-validations/16-CONTEXT.md` - Phase decisions

## Metadata

**Confidence breakdown:**
- Current Architecture: HIGH - Direct codebase analysis
- Finding Creation: HIGH - Direct codebase analysis
- Verdict Logic: HIGH - Direct codebase analysis
- Thermography Extraction: HIGH - Direct codebase analysis
- Vision API Patterns: HIGH - Direct codebase analysis
- Test Structure: HIGH - Direct codebase analysis
- Integration Points: HIGH - Follows existing patterns

**Research date:** 2026-01-19
**Valid until:** 30 days (stable architecture)

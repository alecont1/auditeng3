# Phase 16: Complementary Validations - Context

**Gathered:** 2026-01-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Add cross-validation rules to catch critical errors that the current system misses. The benchmark shows 50% recall with 5 error patterns not being detected: CALIBRATION_EXPIRED, SERIAL_MISMATCH, VALUE_MISMATCH, PHOTO_MISSING, SPEC_NON_COMPLIANCE. Target: >95% recall on the 10-report ground truth dataset.

These validations COMPLEMENT the existing analysis pipeline - they do not replace it.

</domain>

<decisions>
## Implementation Decisions

### Validation Flow
- Run ALL validations and aggregate findings (no short-circuit)
- Show ALL problems at once so technician can fix everything in one revision
- Order: Calibration → Serial → Temperature → Photo Coverage → SPEC Compliance

### Cross-Validation Approach
- **Hybrid: AI extraction + deterministic comparison**
- Claude extracts data (OCR serial from photo, date from certificate)
- Comparison is deterministic (`if serial_foto != serial_relatorio → REJECT`)
- This ensures consistency and reproducibility

### Finding Codes & Severity
```python
# CRITICAL blockers = automatic rejection
CALIBRATION_EXPIRED: blocker=True
SERIAL_MISMATCH: blocker=True
VALUE_MISMATCH: blocker=True
PHOTO_MISSING: blocker=True
PHOTO_ILLEGIBLE: blocker=True

# MAJOR blocker = rejection
SPEC_NON_COMPLIANCE: blocker=True

# Non-blockers = warnings only
SERIAL_ILLEGIBLE: blocker=False  # Low confidence extraction
TEMP_EXCEEDED: blocker=False     # OK if documented
```

### Verdict Logic
- If ANY finding has `blocker=True` → REJECTED
- Multiple blockers: list all, don't stop at first

### Low Confidence Extraction
- When AI extraction confidence is low → create finding (e.g., SERIAL_ILLEGIBLE)
- Let human verify - flag for review, don't auto-reject

### Temperature Mismatch Detection (VALUE_MISMATCH)
- **Primary:** Compare reflected temp in report vs OCR from thermo-hygrometer photo
- **Fallback:** If ALL reflected temps are identical across multiple readings, flag as suspicious copy-paste

### SPEC Compliance Validation (SPEC_NON_COMPLIANCE)
- Triggered when ΔT > 10°C (Microsoft standard)
- Check for **keywords** in COMMENTS section: terminals, insulators, torque, conductors
- Section must exist AND contain relevant keywords

### Phase Coverage Detection (PHOTO_MISSING)
- **Combined approach:** metadata + Vision AI
- Parse report structure to find which phases SHOULD exist
- Use Claude Vision to CONFIRM images actually show those phases
- More reliable than either approach alone

### Benchmark Integration
- Ground truth dataset at `/tests/fixtures/ground_truth.json`
- Run benchmark automatically in CI/CD on every PR/deploy
- **Quality gate:** If recall < 90%, fail the build
- Regression testing prevents future degradations

</decisions>

<specifics>
## Specific Ideas

- Dataset has 10 gabaritados reports: 5 rejected + 5 approved (after correction)
- Each rejected/approved pair teaches the same error pattern
- NETA/ANSI ATS-2021 as secondary reference for temperature thresholds
- Microsoft SPEC 26 05 00 as primary reference

## Reference Limits

**Microsoft Standard (primary):**
- ΔT max: 10°C
- Phase-to-phase: must address if > 3°C

**NETA/ANSI ATS-2021 (secondary):**
- Phase-to-phase > 15°C: repair immediately
- Component vs ambient > 40°C: repair immediately

</specifics>

<deferred>
## Deferred Ideas

None - discussion stayed within phase scope

</deferred>

---

*Phase: 16-complementary-validations*
*Context gathered: 2026-01-19*

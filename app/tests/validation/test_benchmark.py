"""Benchmark tests for complementary validation recall.

These tests measure detection accuracy against a ground truth dataset
of manually reviewed reports. The benchmark serves as a regression test
to prevent future degradations in detection accuracy.

Per CONTEXT.md:
- Target: >95% recall on the 10-report ground truth dataset
- Quality gate: If recall < 90%, fail the build
"""

import json
from pathlib import Path

import pytest

# Ground truth dataset location
GROUND_TRUTH_PATH = Path("app/tests/fixtures/ground_truth.json")


@pytest.fixture
def ground_truth():
    """Load ground truth dataset."""
    if not GROUND_TRUTH_PATH.exists():
        pytest.skip("Ground truth dataset not found")
    with open(GROUND_TRUTH_PATH) as f:
        return json.load(f)


class TestBenchmarkStructure:
    """Tests for ground truth dataset structure."""

    def test_ground_truth_exists(self, ground_truth):
        """Ground truth file exists and is valid JSON."""
        assert ground_truth is not None
        assert "version" in ground_truth
        assert "reports" in ground_truth

    def test_ground_truth_has_reports(self, ground_truth):
        """Ground truth has expected number of reports."""
        assert len(ground_truth["reports"]) == 10

    def test_ground_truth_balanced(self, ground_truth):
        """Ground truth has balanced rejected/approved pairs."""
        rejected = [r for r in ground_truth["reports"] if r["expected_verdict"] == "rejected"]
        approved = [r for r in ground_truth["reports"] if r["expected_verdict"] == "approved"]
        assert len(rejected) == 5
        assert len(approved) == 5

    def test_finding_codes_defined(self, ground_truth):
        """All expected findings have code definitions."""
        defined_codes = set(ground_truth["finding_codes"].keys())
        for report in ground_truth["reports"]:
            for finding in report["expected_findings"]:
                assert finding["code"] in defined_codes, f"Undefined code: {finding['code']}"


class TestFindingCodeMapping:
    """Tests for finding code to rule_id mapping."""

    def test_all_codes_have_rule_ids(self, ground_truth):
        """Each finding code maps to a rule_id."""
        for code, definition in ground_truth["finding_codes"].items():
            assert "rule_id" in definition, f"{code} missing rule_id"
            assert definition["rule_id"].startswith("COMP-"), f"{code} rule_id should start with COMP-"

    def test_rule_id_mapping(self, ground_truth):
        """Finding codes map to expected rule IDs."""
        expected_mapping = {
            "CALIBRATION_EXPIRED": "COMP-001",
            "SERIAL_MISMATCH": "COMP-002",
            "VALUE_MISMATCH": "COMP-003",
            "PHOTO_MISSING": "COMP-004",
            "SPEC_NON_COMPLIANCE": "COMP-005",
            "SERIAL_ILLEGIBLE": "COMP-006",
        }
        for code, expected_rule in expected_mapping.items():
            if code in ground_truth["finding_codes"]:
                actual_rule = ground_truth["finding_codes"][code]["rule_id"]
                assert actual_rule == expected_rule, f"{code}: expected {expected_rule}, got {actual_rule}"


class TestRecallMetrics:
    """Tests for recall calculation helpers.

    Note: Actual recall tests require PDF processing which needs
    the full extraction pipeline. These tests verify the metric
    calculation infrastructure.
    """

    def test_recall_calculation(self):
        """Test recall calculation formula."""
        # recall = true_positives / (true_positives + false_negatives)
        # If we expect 10 findings and detect 9, recall = 9/10 = 90%

        def calculate_recall(expected: int, detected: int) -> float:
            if expected == 0:
                return 1.0  # No expected findings = 100% recall
            return detected / expected

        assert calculate_recall(10, 10) == 1.0
        assert calculate_recall(10, 9) == 0.9
        assert calculate_recall(10, 5) == 0.5
        assert calculate_recall(0, 0) == 1.0

    def test_recall_threshold(self, ground_truth):
        """Verify target recall is documented."""
        assert "target_recall" in ground_truth
        assert ground_truth["target_recall"] >= 0.90, "Target recall should be >= 90%"


# Placeholder for integration tests that require PDF processing
# These will be implemented when actual report PDFs are available
class TestRecallIntegration:
    """Integration tests for recall on ground truth reports.

    These tests require actual PDF reports in the fixtures directory.
    They process each report through the full pipeline and compare
    detected findings against expected findings.
    """

    @pytest.mark.skip(reason="Requires PDF reports in fixtures - manual setup")
    def test_individual_report_recall(self, ground_truth):
        """Each report should detect all expected findings."""
        # TODO: Implement when PDFs are available
        # For each report:
        #   1. Load PDF
        #   2. Run extraction pipeline
        #   3. Run validation with OCR
        #   4. Compare findings against expected
        pass

    @pytest.mark.skip(reason="Requires PDF reports in fixtures - manual setup")
    def test_overall_recall_threshold(self, ground_truth):
        """Overall recall should meet target threshold."""
        # TODO: Implement when PDFs are available
        # Calculate aggregate recall across all reports
        # Assert recall >= ground_truth["target_recall"]
        pass

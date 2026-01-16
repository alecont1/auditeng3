"""Tests for report generation service."""

from datetime import datetime
from uuid import uuid4

import pytest

from app.schemas.enums import AnalysisVerdict, FindingSeverity
from app.schemas.report import ReportData, ReportFinding, SeverityCounts
from app.services.report import ReportService


@pytest.fixture
def sample_findings() -> list[ReportFinding]:
    """Create sample findings with mixed severities."""
    return [
        ReportFinding(
            rule_id="GND-01",
            severity=FindingSeverity.CRITICAL,
            message="Ground resistance exceeds maximum threshold of 5 ohms",
            remediation="Reduce ground resistance to below 5 ohms by adding ground rods",
            standard_reference="NETA 7.1.2",
        ),
        ReportFinding(
            rule_id="GND-02",
            severity=FindingSeverity.CRITICAL,
            message="Bonding connection missing between panels",
            remediation="Install bonding jumper between panels A and B",
            standard_reference="NETA 7.1.3",
        ),
        ReportFinding(
            rule_id="THM-01",
            severity=FindingSeverity.MAJOR,
            message="Temperature delta exceeds 15C threshold",
            remediation="Retorque connection and retest thermography",
            standard_reference="NETA 9.3.1",
        ),
        ReportFinding(
            rule_id="THM-02",
            severity=FindingSeverity.MAJOR,
            message="Phase imbalance detected",
            remediation="Investigate load distribution across phases",
            standard_reference="NETA 9.3.2",
        ),
        ReportFinding(
            rule_id="THM-03",
            severity=FindingSeverity.MAJOR,
            message="Hot spot identified at breaker terminal",
            remediation="Check terminal torque specification",
            standard_reference="NETA 9.3.1",
        ),
        ReportFinding(
            rule_id="DOC-01",
            severity=FindingSeverity.MINOR,
            message="Equipment serial number not documented",
            remediation="Add serial number to test documentation",
            standard_reference="N/A",
        ),
    ]


@pytest.fixture
def sample_report_data(sample_findings: list[ReportFinding]) -> ReportData:
    """Create sample ReportData for PDF generation."""
    return ReportData(
        analysis_id=uuid4(),
        equipment_type="panel",
        test_type="grounding",
        equipment_tag="MCC-01-A",
        verdict=AnalysisVerdict.REJECTED,
        compliance_score=45.0,
        confidence_score=0.85,
        severity_counts=SeverityCounts(critical=2, major=3, minor=1, info=0),
        findings=sample_findings,
        generated_at=datetime(2026, 1, 16, 12, 0, 0),
    )


class MockFinding:
    """Mock finding for from_analysis tests."""

    def __init__(
        self,
        rule_id: str,
        severity: str,
        message: str,
        remediation: str | None = None,
        evidence: dict | None = None,
    ):
        self.rule_id = rule_id
        self.severity = severity
        self.message = message
        self.remediation = remediation
        self.evidence = evidence


class MockAnalysis:
    """Mock Analysis ORM model for testing."""

    def __init__(
        self,
        equipment_type: str = "panel",
        test_type: str = "grounding",
        equipment_tag: str | None = "PANEL-01",
        verdict: str | None = "approved",
        compliance_score: float | None = 95.0,
        confidence_score: float | None = 0.9,
        findings: list | None = None,
    ):
        self.id = uuid4()
        self.equipment_type = equipment_type
        self.test_type = test_type
        self.equipment_tag = equipment_tag
        self.verdict = verdict
        self.compliance_score = compliance_score
        self.confidence_score = confidence_score
        self.findings = findings or []


class TestFromAnalysis:
    """Tests for ReportService.from_analysis()."""

    def test_from_analysis_creates_report_data(self) -> None:
        """Converting Analysis to ReportData preserves basic fields."""
        analysis = MockAnalysis(
            equipment_type="panel",
            test_type="grounding",
            equipment_tag="PANEL-01",
            verdict="approved",
            compliance_score=95.0,
            confidence_score=0.9,
            findings=[
                MockFinding(
                    rule_id="GND-01",
                    severity="minor",
                    message="Documentation note",
                    evidence={"standard_reference": "NETA 7.1.1"},
                )
            ],
        )

        result = ReportService.from_analysis(analysis)

        assert result.analysis_id == analysis.id
        assert result.equipment_type == "panel"
        assert result.test_type == "grounding"
        assert result.equipment_tag == "PANEL-01"
        assert result.verdict == AnalysisVerdict.APPROVED
        assert result.compliance_score == 95.0
        assert result.confidence_score == 0.9

    def test_from_analysis_counts_severities(self) -> None:
        """Severity counts match actual findings."""
        analysis = MockAnalysis(
            findings=[
                MockFinding(rule_id="F1", severity="critical", message="Critical finding 1"),
                MockFinding(rule_id="F2", severity="critical", message="Critical finding 2"),
                MockFinding(rule_id="F3", severity="major", message="Major finding 1"),
                MockFinding(rule_id="F4", severity="major", message="Major finding 2"),
                MockFinding(rule_id="F5", severity="major", message="Major finding 3"),
                MockFinding(rule_id="F6", severity="minor", message="Minor finding"),
            ]
        )

        result = ReportService.from_analysis(analysis)

        assert result.severity_counts.critical == 2
        assert result.severity_counts.major == 3
        assert result.severity_counts.minor == 1
        assert result.severity_counts.info == 0

    def test_from_analysis_extracts_standard_reference(self) -> None:
        """Standard reference is extracted from evidence dict."""
        analysis = MockAnalysis(
            findings=[
                MockFinding(
                    rule_id="GND-01",
                    severity="critical",
                    message="Test finding",
                    evidence={"standard_reference": "IEEE 142-2007"},
                )
            ]
        )

        result = ReportService.from_analysis(analysis)

        assert len(result.findings) == 1
        assert result.findings[0].standard_reference == "IEEE 142-2007"

    def test_from_analysis_handles_missing_evidence(self) -> None:
        """Standard reference defaults to N/A when evidence is None."""
        analysis = MockAnalysis(
            findings=[
                MockFinding(
                    rule_id="TEST-01",
                    severity="info",
                    message="Info finding",
                    evidence=None,
                )
            ]
        )

        result = ReportService.from_analysis(analysis)

        assert result.findings[0].standard_reference == "N/A"


class TestGeneratePdf:
    """Tests for ReportService.generate_pdf()."""

    def test_generate_pdf_returns_bytes(self, sample_report_data: ReportData) -> None:
        """PDF generation returns bytes."""
        result = ReportService.generate_pdf(sample_report_data)

        assert isinstance(result, bytes)

    def test_generate_pdf_starts_with_pdf_magic_number(
        self, sample_report_data: ReportData
    ) -> None:
        """PDF starts with %PDF- magic number."""
        result = ReportService.generate_pdf(sample_report_data)

        assert result.startswith(b"%PDF-")

    def test_generate_pdf_includes_findings(self, sample_report_data: ReportData) -> None:
        """PDF has substantial content when findings present."""
        result = ReportService.generate_pdf(sample_report_data)

        # PDF with findings should be reasonably large
        assert len(result) > 1000

    def test_generate_pdf_handles_empty_findings(self) -> None:
        """PDF generates successfully with no findings."""
        data = ReportData(
            analysis_id=uuid4(),
            equipment_type="panel",
            test_type="grounding",
            verdict=AnalysisVerdict.APPROVED,
            compliance_score=100.0,
            confidence_score=0.95,
            severity_counts=SeverityCounts(),
            findings=[],
        )

        result = ReportService.generate_pdf(data)

        assert isinstance(result, bytes)
        assert result.startswith(b"%PDF-")

    def test_generate_pdf_handles_long_text(self) -> None:
        """PDF handles findings with very long text."""
        long_remediation = "A" * 600  # 600 character remediation text
        long_message = "B" * 400  # 400 character message

        data = ReportData(
            analysis_id=uuid4(),
            equipment_type="panel",
            test_type="grounding",
            verdict=AnalysisVerdict.REVIEW,
            compliance_score=75.0,
            confidence_score=0.8,
            severity_counts=SeverityCounts(major=1),
            findings=[
                ReportFinding(
                    rule_id="LONG-01",
                    severity=FindingSeverity.MAJOR,
                    message=long_message,
                    remediation=long_remediation,
                    standard_reference="NETA 7.1.2.3.4.5",
                )
            ],
        )

        result = ReportService.generate_pdf(data)

        assert isinstance(result, bytes)
        assert result.startswith(b"%PDF-")
        # Should not crash and produce valid PDF

    def test_generate_pdf_handles_none_verdict(self) -> None:
        """PDF handles pending (None) verdict."""
        data = ReportData(
            analysis_id=uuid4(),
            equipment_type="ups",
            test_type="megger",
            verdict=None,
            compliance_score=None,
            confidence_score=None,
            severity_counts=SeverityCounts(),
            findings=[],
        )

        result = ReportService.generate_pdf(data)

        assert isinstance(result, bytes)
        assert result.startswith(b"%PDF-")

    def test_generate_pdf_all_severity_levels(self) -> None:
        """PDF generates with findings of all severity levels."""
        data = ReportData(
            analysis_id=uuid4(),
            equipment_type="xfmr",
            test_type="thermography",
            verdict=AnalysisVerdict.REVIEW,
            compliance_score=80.0,
            confidence_score=0.88,
            severity_counts=SeverityCounts(critical=1, major=1, minor=1, info=1),
            findings=[
                ReportFinding(
                    rule_id="C-01",
                    severity=FindingSeverity.CRITICAL,
                    message="Critical issue",
                    standard_reference="NETA 9.1",
                ),
                ReportFinding(
                    rule_id="M-01",
                    severity=FindingSeverity.MAJOR,
                    message="Major issue",
                    standard_reference="NETA 9.2",
                ),
                ReportFinding(
                    rule_id="I-01",
                    severity=FindingSeverity.MINOR,
                    message="Minor issue",
                    standard_reference="NETA 9.3",
                ),
                ReportFinding(
                    rule_id="N-01",
                    severity=FindingSeverity.INFO,
                    message="Informational note",
                    standard_reference="N/A",
                ),
            ],
        )

        result = ReportService.generate_pdf(data)

        assert isinstance(result, bytes)
        assert result.startswith(b"%PDF-")
        assert len(result) > 1000

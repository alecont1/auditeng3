"""Tests for audit service."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.models import Analysis, AuditLog, Task, User
from app.core.validation.schemas import RuleEvaluation, ValidationResult
from app.services.audit import AuditService, EventType, log_event


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    """Create test database engine with in-memory SQLite."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine) -> AsyncSession:
    """Create test database session."""
    async_session = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        id=uuid4(),
        email="test@example.com",
        hashed_password="$2b$12$dummyhashfortestingpurposesonly12345678901234567890",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_task(db_session: AsyncSession, test_user: User) -> Task:
    """Create a test task."""
    task = Task(
        id=uuid4(),
        user_id=test_user.id,
        status="completed",
        original_filename="test_report.pdf",
        file_path="/tmp/test_report.pdf",
        file_size=1024,
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)
    return task


@pytest_asyncio.fixture
async def test_analysis(db_session: AsyncSession, test_task: Task) -> Analysis:
    """Create a test analysis."""
    analysis = Analysis(
        id=uuid4(),
        task_id=test_task.id,
        equipment_type="panel",
        test_type="grounding",
        equipment_tag="PANEL-01",
        verdict="approved",
        compliance_score=95.0,
        confidence_score=0.85,
    )
    db_session.add(analysis)
    await db_session.commit()
    await db_session.refresh(analysis)
    return analysis


class TestLogEvent:
    """Tests for the log_event convenience function."""

    @pytest.mark.asyncio
    async def test_log_event_creates_record(
        self, db_session: AsyncSession, test_analysis: Analysis
    ) -> None:
        """Call log_event with event_type and details - assert record created."""
        log = await log_event(
            db_session,
            EventType.EXTRACTION_STARTED,
            test_analysis.id,
            status="test_started",
            extra_field="extra_value",
        )
        await db_session.commit()

        assert log.id is not None
        assert log.analysis_id == test_analysis.id
        assert log.event_type == EventType.EXTRACTION_STARTED
        assert log.event_timestamp is not None
        assert log.details is not None
        assert log.details["status"] == "test_started"
        assert log.details["extra_field"] == "extra_value"

    @pytest.mark.asyncio
    async def test_log_event_with_column_kwargs(
        self, db_session: AsyncSession, test_analysis: Analysis
    ) -> None:
        """Log event with model_version, prompt_version, confidence_score, rule_id."""
        log = await log_event(
            db_session,
            EventType.EXTRACTION_COMPLETED,
            test_analysis.id,
            model_version="claude-sonnet-4",
            prompt_version="grounding_v1",
            confidence_score=0.95,
            rule_id="GRND-001",
        )
        await db_session.commit()

        assert log.model_version == "claude-sonnet-4"
        assert log.prompt_version == "grounding_v1"
        assert log.confidence_score == 0.95
        assert log.rule_id == "GRND-001"


class TestAuditService:
    """Tests for AuditService methods."""

    @pytest.mark.asyncio
    async def test_log_extraction_start(
        self, db_session: AsyncSession, test_analysis: Analysis
    ) -> None:
        """Call log_extraction_start - assert event_type is EXTRACTION_STARTED."""
        log = await AuditService.log_extraction_start(
            db_session,
            test_analysis.id,
            model_version="claude-sonnet-4-20250514",
            prompt_version="grounding_v1",
        )
        await db_session.commit()

        assert log.event_type == EventType.EXTRACTION_STARTED
        assert log.analysis_id == test_analysis.id
        assert log.model_version == "claude-sonnet-4-20250514"
        assert log.prompt_version == "grounding_v1"
        assert log.details is not None
        assert log.details["status"] == "started"

    @pytest.mark.asyncio
    async def test_log_extraction_complete(
        self, db_session: AsyncSession, test_analysis: Analysis
    ) -> None:
        """Call log_extraction_complete with confidence_score - assert stored."""
        log = await AuditService.log_extraction_complete(
            db_session,
            test_analysis.id,
            confidence_score=0.87,
            field_count=15,
        )
        await db_session.commit()

        assert log.event_type == EventType.EXTRACTION_COMPLETED
        assert log.confidence_score == 0.87
        assert log.details is not None
        assert log.details["status"] == "completed"
        assert log.details["field_count"] == 15

    @pytest.mark.asyncio
    async def test_log_extraction_failed(
        self, db_session: AsyncSession, test_analysis: Analysis
    ) -> None:
        """Call log_extraction_failed with error_message."""
        log = await AuditService.log_extraction_failed(
            db_session,
            test_analysis.id,
            error_message="Connection timeout",
        )
        await db_session.commit()

        assert log.event_type == EventType.EXTRACTION_FAILED
        assert log.details is not None
        assert log.details["status"] == "failed"
        assert log.details["error_message"] == "Connection timeout"

    @pytest.mark.asyncio
    async def test_log_validation_rule(
        self, db_session: AsyncSession, test_analysis: Analysis
    ) -> None:
        """Call log_validation_rule with rule_id and passed=True."""
        log = await AuditService.log_validation_rule(
            db_session,
            test_analysis.id,
            rule_id="GRND-001",
            passed=True,
            details={"threshold": 5.0, "actual": 3.2},
        )
        await db_session.commit()

        assert log.event_type == EventType.VALIDATION_RULE_APPLIED
        assert log.rule_id == "GRND-001"
        assert log.details is not None
        assert log.details["passed"] is True
        assert log.details["threshold"] == 5.0
        assert log.details["actual"] == 3.2

    @pytest.mark.asyncio
    async def test_log_finding_generated(
        self, db_session: AsyncSession, test_analysis: Analysis
    ) -> None:
        """Call log_finding_generated with rule_id, severity, message."""
        log = await AuditService.log_finding_generated(
            db_session,
            test_analysis.id,
            rule_id="GRND-001",
            severity="critical",
            message="Ground resistance exceeds maximum threshold",
        )
        await db_session.commit()

        assert log.event_type == EventType.FINDING_GENERATED
        assert log.rule_id == "GRND-001"
        assert log.details is not None
        assert log.details["severity"] == "critical"
        assert log.details["message"] == "Ground resistance exceeds maximum threshold"

    @pytest.mark.asyncio
    async def test_log_validation_complete(
        self, db_session: AsyncSession, test_analysis: Analysis
    ) -> None:
        """Call log_validation_complete with verdict and compliance_score."""
        log = await AuditService.log_validation_complete(
            db_session,
            test_analysis.id,
            verdict="approved",
            compliance_score=95.0,
        )
        await db_session.commit()

        assert log.event_type == EventType.VALIDATION_COMPLETED
        assert log.details is not None
        assert log.details["status"] == "completed"
        assert log.details["verdict"] == "approved"
        assert log.details["compliance_score"] == 95.0

    @pytest.mark.asyncio
    async def test_get_audit_trail_ordered(
        self, db_session: AsyncSession, test_analysis: Analysis
    ) -> None:
        """Create multiple audit logs with different timestamps - verify order."""
        # Create logs in a specific order
        await AuditService.log_extraction_start(
            db_session, test_analysis.id, "claude-sonnet-4", "grounding_v1"
        )
        await AuditService.log_extraction_complete(
            db_session, test_analysis.id, 0.9, 10
        )
        await AuditService.log_finding_generated(
            db_session, test_analysis.id, "GRND-001", "major", "Test finding"
        )
        await AuditService.log_validation_complete(
            db_session, test_analysis.id, "approved", 90.0
        )
        await db_session.commit()

        # Get audit trail
        trail = await AuditService.get_audit_trail(db_session, test_analysis.id)

        assert len(trail) == 4
        # Verify chronological order (oldest first)
        assert trail[0].event_type == EventType.EXTRACTION_STARTED
        assert trail[1].event_type == EventType.EXTRACTION_COMPLETED
        assert trail[2].event_type == EventType.FINDING_GENERATED
        assert trail[3].event_type == EventType.VALIDATION_COMPLETED

        # Verify timestamps are in order
        for i in range(len(trail) - 1):
            assert trail[i].event_timestamp <= trail[i + 1].event_timestamp

    @pytest.mark.asyncio
    async def test_audit_logs_are_immutable(
        self, db_session: AsyncSession, test_analysis: Analysis
    ) -> None:
        """Verify no update method exists on AuditService (app-level immutability)."""
        # Document that AuditService has no update or delete methods
        # This is app-level immutability enforcement
        assert not hasattr(AuditService, "update_audit_log")
        assert not hasattr(AuditService, "delete_audit_log")
        assert not hasattr(AuditService, "update")
        assert not hasattr(AuditService, "delete")

        # Create a log and verify it can be retrieved but service has no modify methods
        log = await AuditService.log_extraction_start(
            db_session, test_analysis.id, "claude-sonnet-4", "grounding_v1"
        )
        await db_session.commit()

        # Log exists and can be retrieved
        trail = await AuditService.get_audit_trail(db_session, test_analysis.id)
        assert len(trail) == 1
        assert trail[0].id == log.id


class TestValidationRuleLogging:
    """Tests for validation rule logging integration."""

    @pytest.mark.asyncio
    async def test_validation_rules_logged_during_extraction(
        self, db_session: AsyncSession, test_analysis: Analysis
    ) -> None:
        """Simulate validation with rules_evaluated and verify audit logging.

        This test verifies that both passed and failed rules are logged
        to the audit trail via AuditService.log_validation_rule().
        """
        # Create a ValidationResult with both passed and failed rules
        rules_evaluated = [
            RuleEvaluation(
                rule_id="GRND-001",
                passed=True,
                details={"threshold": 5.0, "extracted_value": 3.2},
            ),
            RuleEvaluation(
                rule_id="GRND-002",
                passed=False,
                details={"threshold": 25.0, "extracted_value": 30.5},
            ),
            RuleEvaluation(
                rule_id="GRND-003",
                passed=True,
                details={"threshold": 10.0, "extracted_value": 8.0},
            ),
        ]

        validation_result = ValidationResult(
            test_type="grounding",
            equipment_tag="PANEL-01",
            rules_evaluated=rules_evaluated,
        )

        # Simulate the extraction worker logging each rule
        for rule_eval in validation_result.rules_evaluated:
            await AuditService.log_validation_rule(
                db=db_session,
                analysis_id=test_analysis.id,
                rule_id=rule_eval.rule_id,
                passed=rule_eval.passed,
                details=rule_eval.details,
            )
        await db_session.commit()

        # Query audit logs for VALIDATION_RULE_APPLIED events
        trail = await AuditService.get_audit_trail(db_session, test_analysis.id)
        rule_logs = [
            log for log in trail if log.event_type == EventType.VALIDATION_RULE_APPLIED
        ]

        # Assert all rules are logged
        assert len(rule_logs) == 3

        # Verify passed and failed rules are both present
        rule_ids = {log.rule_id for log in rule_logs}
        assert rule_ids == {"GRND-001", "GRND-002", "GRND-003"}

        # Verify passed/failed status is captured
        for log in rule_logs:
            if log.rule_id == "GRND-001":
                assert log.details["passed"] is True
                assert log.details["threshold"] == 5.0
            elif log.rule_id == "GRND-002":
                assert log.details["passed"] is False
                assert log.details["threshold"] == 25.0
            elif log.rule_id == "GRND-003":
                assert log.details["passed"] is True

    @pytest.mark.asyncio
    async def test_rules_evaluated_empty_no_logs(
        self, db_session: AsyncSession, test_analysis: Analysis
    ) -> None:
        """Verify no rule logs created when rules_evaluated is empty."""
        validation_result = ValidationResult(
            test_type="grounding",
            rules_evaluated=[],
        )

        # Simulate extraction worker with no rules
        for rule_eval in validation_result.rules_evaluated:
            await AuditService.log_validation_rule(
                db=db_session,
                analysis_id=test_analysis.id,
                rule_id=rule_eval.rule_id,
                passed=rule_eval.passed,
                details=rule_eval.details,
            )
        await db_session.commit()

        # Query audit logs
        trail = await AuditService.get_audit_trail(db_session, test_analysis.id)
        rule_logs = [
            log for log in trail if log.event_type == EventType.VALIDATION_RULE_APPLIED
        ]

        assert len(rule_logs) == 0

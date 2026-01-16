"""Test fixtures for API integration tests."""

import asyncio
from datetime import datetime, timezone
from typing import AsyncGenerator
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.core.auth import create_access_token
from app.db.base import Base
from app.db.models import Analysis, Finding, Task, User
from app.main import app
from app.core.dependencies import get_db

# Get test settings
settings = get_settings()

# Test database URL - use a separate test database
TEST_DATABASE_URL = settings.DATABASE_URL.replace(
    settings.DATABASE_URL.split("/")[-1],
    f"{settings.DATABASE_URL.split('/')[-1]}_test"
)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for session-scoped fixtures."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    """Create test database engine."""
    # Use in-memory SQLite for fast tests
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
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client with overridden database dependency."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    # Use a pre-computed hash to avoid bcrypt issues in tests
    # This is a hash of "testpass123" - not used for actual login in these tests
    fake_hash = "$2b$12$dummyhashfortestingpurposesonly12345678901234567890"
    user = User(
        id=uuid4(),
        email="test@example.com",
        hashed_password=fake_hash,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def other_user(db_session: AsyncSession) -> User:
    """Create another test user for ownership tests."""
    # Use a pre-computed hash to avoid bcrypt issues in tests
    fake_hash = "$2b$12$dummyhashfortestingpurposesonly12345678901234567890"
    user = User(
        id=uuid4(),
        email="other@example.com",
        hashed_password=fake_hash,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_token(test_user: User) -> str:
    """Create auth token for test user."""
    return create_access_token(data={"sub": str(test_user.id)})


@pytest_asyncio.fixture
async def auth_headers(auth_token: str) -> dict:
    """Get authentication headers for test user."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest_asyncio.fixture
async def other_auth_token(other_user: User) -> str:
    """Create auth token for other user."""
    return create_access_token(data={"sub": str(other_user.id)})


@pytest_asyncio.fixture
async def other_auth_headers(other_auth_token: str) -> dict:
    """Get authentication headers for other user."""
    return {"Authorization": f"Bearer {other_auth_token}"}


@pytest_asyncio.fixture
async def sample_task(db_session: AsyncSession, test_user: User) -> Task:
    """Create a sample task for the test user."""
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
async def sample_analysis(db_session: AsyncSession, sample_task: Task) -> Analysis:
    """Create a sample analysis for the test task."""
    analysis = Analysis(
        id=uuid4(),
        task_id=sample_task.id,
        equipment_type="panel",
        test_type="grounding",
        equipment_tag="PANEL-01",
        verdict="approved",
        compliance_score=95.0,
        confidence_score=0.85,
        extraction_result={
            "raw_data": {"test": "data"},
            "extraction_errors": [],
            "needs_review": False,
        },
        validation_result={
            "is_valid": True,
            "test_type": "grounding",
            "critical_count": 0,
            "major_count": 1,
            "minor_count": 0,
            "info_count": 1,
        },
    )
    db_session.add(analysis)
    await db_session.commit()
    await db_session.refresh(analysis)
    return analysis


@pytest_asyncio.fixture
async def sample_findings(db_session: AsyncSession, sample_analysis: Analysis) -> list[Finding]:
    """Create sample findings for the test analysis."""
    findings = [
        Finding(
            id=uuid4(),
            analysis_id=sample_analysis.id,
            severity="major",
            rule_id="GRND-001",
            message="Ground resistance slightly elevated",
            evidence={
                "extracted_value": 4.5,
                "threshold": 5.0,
                "standard_reference": "IEEE 142-2007",
            },
            remediation="Monitor and retest in 6 months",
        ),
        Finding(
            id=uuid4(),
            analysis_id=sample_analysis.id,
            severity="info",
            rule_id="GRND-INFO-001",
            message="Test completed successfully",
            evidence={
                "extracted_value": "completed",
                "threshold": "completed",
                "standard_reference": "N/A",
            },
            remediation=None,
        ),
    ]
    db_session.add_all(findings)
    await db_session.commit()
    for finding in findings:
        await db_session.refresh(finding)
    return findings


@pytest_asyncio.fixture
async def complete_analysis(
    sample_analysis: Analysis, sample_findings: list[Finding]
) -> Analysis:
    """Return analysis with findings attached."""
    return sample_analysis

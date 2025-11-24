"""Tests for Daily Log Service."""

from datetime import date, datetime, timezone
from unittest.mock import Mock

import pytest

from habit_homepage.application.daily_log_service import DailyLogService
from habit_homepage.domain.daily_log import DailyLog
from habit_homepage.domain.exceptions import HabitNotFoundError, InvalidDateRangeError
from habit_homepage.domain.habit import Habit
from habit_homepage.domain.habit_entry import HabitEntry
from habit_homepage.domain.value_objects import CategoryType, HabitSource


@pytest.fixture
def mock_log_repo():
    """Mock daily log repository."""
    return Mock()


@pytest.fixture
def mock_habit_repo():
    """Mock habit repository."""
    return Mock()


@pytest.fixture
def service(mock_log_repo, mock_habit_repo):
    """Create Daily Log Service with mocked dependencies."""
    return DailyLogService(mock_log_repo, mock_habit_repo)


@pytest.fixture
def sample_habit():
    """Create a sample habit for testing."""
    return Habit(
        id="steps",
        name="Daily Steps",
        unit="steps",
        source=HabitSource.MANUAL,
        description="Track daily steps",
        category_id=CategoryType.HEALTH,
    )


def test_get_or_create_existing_log(service, mock_log_repo):
    """Test getting an existing daily log."""
    target_date = date(2024, 1, 15)
    existing_log = DailyLog(date=target_date)
    mock_log_repo.get_by_date.return_value = existing_log

    result = service.get_or_create(target_date)

    assert result == existing_log
    mock_log_repo.get_by_date.assert_called_once_with(target_date)


def test_get_or_create_new_log(service, mock_log_repo):
    """Test creating a new daily log when none exists."""
    target_date = date(2024, 1, 15)
    mock_log_repo.get_by_date.return_value = None

    result = service.get_or_create(target_date)

    assert isinstance(result, DailyLog)
    assert result.date == target_date
    assert len(result.entries) == 0


def test_get_by_date_range_valid(service, mock_log_repo):
    """Test getting logs for a valid date range."""
    start = date(2024, 1, 1)
    end = date(2024, 1, 7)
    expected_logs = [DailyLog(date=start), DailyLog(date=end)]
    mock_log_repo.get_by_date_range.return_value = expected_logs

    result = service.get_by_date_range(start, end)

    assert result == expected_logs
    mock_log_repo.get_by_date_range.assert_called_once_with(start, end)


def test_get_by_date_range_invalid(service):
    """Test that invalid date range raises exception."""
    start = date(2024, 1, 7)
    end = date(2024, 1, 1)  # End before start

    with pytest.raises(InvalidDateRangeError):
        service.get_by_date_range(start, end)


def test_record_habit_success(service, mock_log_repo, mock_habit_repo, sample_habit):
    """Test successfully recording a habit entry."""
    target_date = date(2024, 1, 15)
    value = 5000.0

    mock_habit_repo.get_by_id.return_value = sample_habit
    mock_log_repo.get_by_date.return_value = None  # No existing log

    result = service.record_habit(target_date, sample_habit.id, value)

    # Verify habit lookup
    mock_habit_repo.get_by_id.assert_called_once_with(sample_habit.id)

    # Verify log save
    mock_log_repo.save.assert_called_once()
    saved_log = mock_log_repo.save.call_args[0][0]
    assert saved_log.date == target_date
    assert sample_habit.id in saved_log.entries
    assert saved_log.entries[sample_habit.id].value == value
    assert saved_log.entries[sample_habit.id].source == HabitSource.MANUAL


def test_record_habit_nonexistent_habit(service, mock_habit_repo):
    """Test recording a habit that doesn't exist raises exception."""
    target_date = date(2024, 1, 15)
    mock_habit_repo.get_by_id.return_value = None

    with pytest.raises(HabitNotFoundError):
        service.record_habit(target_date, "nonexistent", 100.0)


def test_record_habit_updates_existing_log(
    service, mock_log_repo, mock_habit_repo, sample_habit
):
    """Test that recording a habit updates an existing log."""
    target_date = date(2024, 1, 15)
    existing_log = DailyLog(date=target_date)

    mock_habit_repo.get_by_id.return_value = sample_habit
    mock_log_repo.get_by_date.return_value = existing_log

    service.record_habit(target_date, sample_habit.id, 10000.0)

    # Verify the entry was added to existing log
    mock_log_repo.save.assert_called_once()
    saved_log = mock_log_repo.save.call_args[0][0]
    assert saved_log == existing_log
    assert sample_habit.id in saved_log.entries


def test_sync_automatic_habits_no_providers(service, mock_log_repo, mock_habit_repo):
    """Test syncing when no data providers are configured."""
    target_date = date(2024, 1, 15)
    automatic_habit = Habit(
        id="auto_steps",
        name="Auto Steps",
        unit="steps",
        source=HabitSource.AUTOMATIC,
        provider_config={"provider": "garmin", "metric": "steps"},
    )

    mock_habit_repo.get_all.return_value = [automatic_habit]
    mock_log_repo.get_by_date.return_value = None

    result = service.sync_automatic_habits(target_date)

    # Should create empty log (no providers available)
    assert isinstance(result, DailyLog)
    mock_log_repo.save.assert_called_once()


def test_sync_automatic_habits_with_provider(
    service, mock_log_repo, mock_habit_repo
):
    """Test syncing habits with a configured provider."""
    target_date = date(2024, 1, 15)

    # Create automatic habit
    automatic_habit = Habit(
        id="auto_steps",
        name="Auto Steps",
        unit="steps",
        source=HabitSource.AUTOMATIC,
        provider_config={"provider": "test_provider", "metric": "steps"},
    )

    # Create mock provider
    mock_provider = Mock()
    mock_provider.provider_name = "test_provider"
    mock_provider.fetch_data.return_value = 5000.0

    # Configure service with provider
    service.data_providers = [mock_provider]

    mock_habit_repo.get_all.return_value = [automatic_habit]
    mock_log_repo.get_by_date.return_value = None

    result = service.sync_automatic_habits(target_date)

    # Verify provider was called
    mock_provider.fetch_data.assert_called_once_with(
        automatic_habit, target_date.isoformat()
    )

    # Verify entry was recorded
    assert automatic_habit.id in result.entries
    assert result.entries[automatic_habit.id].value == 5000.0
    assert result.entries[automatic_habit.id].source == HabitSource.AUTOMATIC


def test_sync_automatic_habits_skips_manual(service, mock_log_repo, mock_habit_repo):
    """Test that syncing skips manual habits."""
    target_date = date(2024, 1, 15)

    manual_habit = Habit(
        id="manual_steps",
        name="Manual Steps",
        unit="steps",
        source=HabitSource.MANUAL,
    )

    mock_habit_repo.get_all.return_value = [manual_habit]
    mock_log_repo.get_by_date.return_value = None

    result = service.sync_automatic_habits(target_date)

    # Should create empty log (manual habits are skipped)
    assert len(result.entries) == 0
    mock_log_repo.save.assert_called_once()


def test_get_entries_by_habit(service, mock_log_repo):
    """Test retrieving entries for a specific habit."""
    habit_id = "steps"
    start = date(2024, 1, 1)
    end = date(2024, 1, 7)

    expected_entries = [
        HabitEntry(
            habit_id=habit_id,
            date=start,
            value=5000.0,
            recorded_at=datetime.now(timezone.utc),
            source=HabitSource.MANUAL,
        )
    ]

    mock_log_repo.get_entries_by_habit.return_value = expected_entries

    result = service.get_entries_by_habit(habit_id, start, end)

    assert result == expected_entries
    mock_log_repo.get_entries_by_habit.assert_called_once_with(habit_id, start, end)

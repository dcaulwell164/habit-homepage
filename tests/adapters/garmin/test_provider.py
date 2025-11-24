from unittest.mock import patch

import pytest

from habit_homepage.adapters.garmin.provider import GarminHabitDataProvider
from habit_homepage.domain.habit import Habit


@pytest.fixture
def mock_garmin_client():
    with patch("habit_homepage.adapters.garmin.provider.Garmin") as MockGarmin:
        mock_instance = MockGarmin.return_value
        # Mock login to avoid actual network calls
        mock_instance.login.return_value = True
        yield mock_instance


@pytest.fixture
def provider(mock_garmin_client):
    # We also need to mock init_api to return our mock_client
    with patch.object(
        GarminHabitDataProvider, "init_api", return_value=mock_garmin_client
    ):
        return GarminHabitDataProvider("test@example.com", "password")


def test_get_steps(provider, mock_garmin_client):
    # Setup mock return value
    mock_garmin_client.get_user_summary.return_value = {"totalSteps": 5000}

    habit = Habit(
        id="1",
        name="Walk",
        description="Daily walk",
        frequency="daily",
        target_value=10000,
        provider_config={"metric": "steps"},
    )

    steps = provider.fetch_data(habit, "2023-10-27")

    assert steps == 5000
    mock_garmin_client.get_user_summary.assert_called_with("2023-10-27")


def test_get_heart_rate(provider, mock_garmin_client):
    # Setup mock return value
    mock_garmin_client.get_user_summary.return_value = {"restingHeartRate": 55}

    habit = Habit(
        id="2",
        name="Rest",
        description="Resting HR",
        frequency="daily",
        target_value=60,
        provider_config={"metric": "heart_rate"},
    )

    hr = provider.fetch_data(habit, "2023-10-27")

    assert hr == 55
    mock_garmin_client.get_user_summary.assert_called_with("2023-10-27")


def test_get_exercise_minutes(provider, mock_garmin_client):
    # Setup mock return value
    mock_garmin_client.get_activities_by_date.return_value = [
        {"duration": 1800, "activityType": {"typeKey": "running"}},  # 30 mins
        {"duration": 900, "activityType": {"typeKey": "cycling"}},  # 15 mins
    ]

    habit = Habit(
        id="3",
        name="Exercise",
        description="Daily exercise",
        frequency="daily",
        target_value=30,
        provider_config={"metric": "exercise"},
    )

    # Test total minutes (no type filter)
    minutes = provider.fetch_data(habit, "2023-10-27")
    assert minutes == 45  # (1800 + 900) / 60

    # Test with type filter
    habit_running = Habit(
        id="4",
        name="Run",
        description="Daily run",
        frequency="daily",
        target_value=30,
        provider_config={"metric": "exercise", "activity_type": "running"},
    )

    minutes_running = provider.fetch_data(habit_running, "2023-10-27")
    assert minutes_running == 30


def test_fetch_data_invalid_config(provider):
    habit = Habit(
        id="5",
        name="Bad Config",
        description="Invalid",
        frequency="daily",
        target_value=10,
        provider_config={},  # Missing metric
    )

    result = provider.fetch_data(habit, "2023-10-27")
    assert result is None


def test_api_error_handling(provider, mock_garmin_client):
    mock_garmin_client.get_user_summary.side_effect = Exception("API Error")

    habit = Habit(
        id="1",
        name="Walk",
        description="Daily walk",
        frequency="daily",
        target_value=10000,
        provider_config={"metric": "steps"},
    )

    # Should return 0 on error as per implementation
    steps = provider.fetch_data(habit, "2023-10-27")
    assert steps == 0

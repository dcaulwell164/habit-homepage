from enum import Enum
from pathlib import Path
from typing import Any

from garminconnect import (
    Garmin,
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
)
from garth.exc import GarthException, GarthHTTPError

from habit_homepage.config.logging import get_logger
from habit_homepage.domain.habit import Habit
from habit_homepage.domain.value_objects import ProviderType
from habit_homepage.ports.providers.habit_data_provider import HabitDataProvider

logger = get_logger(__name__)

TOKEN_STORE_PATH = Path("~/.garminconnect").expanduser()


class GarminAuthError(Exception):
    """Raised when Garmin authentication fails."""

    pass


class GarminMetric(Enum):
    """
    Enum for Garmin-specific metrics that can be tracked.
    Provides type safety for metric names in provider configuration.
    """

    STEPS = "steps"
    HEART_RATE = "heart_rate"
    EXERCISE = "exercise"


class GarminHabitDataProvider(HabitDataProvider):
    """Adapter for fetching data from Garmin Connect."""

    def __init__(self, email: str, password: str) -> None:
        self.email = email
        self.password = password
        self._client: Garmin | None = None

    @property
    def provider_name(self) -> str:
        return ProviderType.GARMIN.value

    @property
    def client(self) -> Garmin:
        """Lazy-load and cache the Garmin client."""
        if self._client is None:
            self._client = self._init_api()
        return self._client

    def fetch_data(self, habit: Habit, date: str) -> float | None:
        """Fetch data from Garmin based on the habit configuration."""
        if not habit.provider_config:
            return None

        metric_str = habit.provider_config.get("metric")
        if not metric_str:
            return None

        try:
            metric = GarminMetric(metric_str)
        except ValueError:
            logger.warning("Unknown Garmin metric: %s", metric_str)
            return None

        if metric == GarminMetric.STEPS:
            return self._get_steps(date)
        elif metric == GarminMetric.HEART_RATE:
            return self._get_heart_rate(date)
        elif metric == GarminMetric.EXERCISE:
            activity_type = habit.provider_config.get("activity_type")
            return self._get_exercise_minutes(date, activity_type)

        return None

    def _get_steps(self, date: str) -> float:
        """Fetch total steps for the given date."""
        try:
            summary: dict[str, Any] = self.client.get_user_summary(date)
            return float(summary.get("totalSteps", 0))
        except Exception as e:
            logger.error("Error fetching steps for %s: %s", date, e)
            return 0.0

    def _get_heart_rate(self, date: str) -> float:
        """Fetch resting heart rate for the given date."""
        try:
            summary: dict[str, Any] = self.client.get_user_summary(date)
            return float(summary.get("restingHeartRate", 0))
        except Exception as e:
            logger.error("Error fetching heart rate for %s: %s", date, e)
            return 0.0

    def _get_exercise_minutes(self, date: str, activity_type: str | None) -> float:
        """Fetch total duration (in minutes) of activities for the given date."""
        try:
            activities: list[dict[str, Any]] = self.client.get_activities_by_date(
                date, date
            )
            total_seconds = 0.0

            for activity in activities:
                if activity_type:
                    act_type_key = activity.get("activityType", {}).get("typeKey")
                    if act_type_key != activity_type:
                        continue
                total_seconds += float(activity.get("duration", 0))

            return total_seconds / 60
        except Exception as e:
            logger.error("Error fetching exercise minutes for %s: %s", date, e)
            return 0.0

    def _init_api(self) -> Garmin:
        """Initialize Garmin API with token-based or credential-based auth."""
        # Try cached tokens first
        if TOKEN_STORE_PATH.exists():
            try:
                garmin = Garmin()
                garmin.login(str(TOKEN_STORE_PATH))
                return garmin
            except (
                FileNotFoundError,
                GarthHTTPError,
                GarminConnectAuthenticationError,
                GarminConnectConnectionError,
            ):
                pass  # Fall through to credential login

        # Login with credentials
        garmin = Garmin(
            email=self.email, password=self.password, is_cn=False, return_on_mfa=True
        )
        result = garmin.login()

        if result[0] == "needs_mfa":
            self._handle_mfa(garmin, result[1])

        garmin.garth.dump(str(TOKEN_STORE_PATH))
        return garmin

    def _handle_mfa(self, garmin: Garmin, mfa_state: Any) -> None:
        """Handle MFA authentication flow."""
        logger.info("MFA required")
        mfa_code = input("Enter MFA code: ")

        try:
            garmin.resume_login(mfa_state, mfa_code)
        except GarthHTTPError as e:
            error_str = str(e)
            if "429" in error_str:
                raise GarminAuthError("Too many MFA attempts. Wait 30 minutes.") from e
            elif "401" in error_str or "403" in error_str:
                raise GarminAuthError("Invalid MFA code.") from e
            raise GarminAuthError(f"MFA authentication failed: {e}") from e
        except GarthException as e:
            raise GarminAuthError(f"MFA authentication failed: {e}") from e

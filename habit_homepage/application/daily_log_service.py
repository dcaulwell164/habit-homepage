from datetime import date, datetime, timezone

from habit_homepage.domain.daily_log import DailyLog
from habit_homepage.domain.habit import Habit
from habit_homepage.domain.habit_entry import HabitEntry
from habit_homepage.domain.value_objects import HabitSource
from habit_homepage.ports.providers.habit_data_provider import HabitDataProvider
from habit_homepage.ports.repositories.daily_log_repo import DailyLogRepository
from habit_homepage.ports.repositories.habit_repo import HabitRepository


class DailyLogService:
    """
    Application service for daily log management.
    - Orchestrates use cases for habit tracking.
    - Contains no DB or HTTP logic.
    - Uses ports to interact with infrastructure.

    Follows hexagonal architecture:
    - Application layer orchestrates domain entities
    - Depends on ports (interfaces), not concrete implementations
    - Can integrate with multiple data providers through the port
    """

    def __init__(
        self,
        log_repo: DailyLogRepository,
        habit_repo: HabitRepository,
        data_providers: list[HabitDataProvider] | None = None,
    ):
        self.log_repo = log_repo
        self.habit_repo = habit_repo
        self.data_providers = data_providers or []

    def get_or_create(self, target_date: date) -> DailyLog:
        """Get existing daily log or create a new empty one."""
        log = self.log_repo.get_by_date(target_date)
        if log:
            return log

        # Create empty log (no entries yet)
        log = DailyLog(date=target_date)
        return log

    def get_by_date_range(self, start: date, end: date) -> list[DailyLog]:
        """Get all daily logs within a date range."""
        return self.log_repo.get_by_date_range(start, end)

    def get_entries_by_habit(
        self, habit_id: str, start: date, end: date
    ) -> list[HabitEntry]:
        """Get all entries for a specific habit within a date range."""
        return self.log_repo.get_entries_by_habit(habit_id, start, end)

    def record_habit(self, target_date: date, habit_id: str, value: float) -> DailyLog:
        """
        Record a habit entry manually.

        Use case:
        - Verify habit exists
        - Load or create the daily log
        - Create/update habit entry
        - Persist the change
        """
        # Verify habit exists
        habit = self.habit_repo.get_by_id(habit_id)
        if not habit:
            raise ValueError(f"Habit '{habit_id}' does not exist")

        # Get or create log
        log = self.get_or_create(target_date)

        # Create entry
        entry = HabitEntry(
            habit_id=habit_id,
            date=target_date,
            value=value,
            recorded_at=datetime.now(timezone.utc),
            source=HabitSource.MANUAL,
        )

        # Apply domain logic
        log.add_or_update_entry(entry)

        # Persist
        self.log_repo.save(log)
        return log

    def sync_automatic_habits(self, target_date: date) -> DailyLog:
        """
        Fetch and record all automatic habits for a date.

        Use case:
        - Find all automatic habits
        - For each habit, find a compatible provider
        - Fetch data from provider
        - Record entries
        - Persist changes
        """
        log = self.get_or_create(target_date)

        # Get all automatic habits
        all_habits = self.habit_repo.get_all()
        automatic_habits = [h for h in all_habits if h.is_automatic()]

        for habit in automatic_habits:
            # Find a provider that supports this habit
            provider = self._find_provider(habit)
            if not provider:
                continue

            # Fetch data (providers still use ISO string for external API compatibility)
            value = provider.fetch_data(habit, target_date.isoformat())
            if value is None:
                continue

            # Create entry
            entry = HabitEntry(
                habit_id=habit.id,
                date=target_date,
                value=value,
                recorded_at=datetime.now(timezone.utc),
                source=HabitSource.AUTOMATIC,
            )

            log.add_or_update_entry(entry)

        # Persist all changes
        self.log_repo.save(log)
        return log

    def _find_provider(self, habit: Habit) -> HabitDataProvider | None:
        """Find a data provider that supports the given habit."""
        if not habit.provider_config:
            return None

        target_provider = habit.provider_config.get("provider")
        if not target_provider:
            return None

        for provider in self.data_providers:
            if provider.provider_name == target_provider:
                return provider
        return None

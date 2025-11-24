from abc import ABC, abstractmethod
from datetime import date

from habit_homepage.domain.daily_log import DailyLog
from habit_homepage.domain.habit_entry import HabitEntry


class DailyLogRepository(ABC):
    """
    Outbound port: the application depends on this interface.
    Infrastructure implements it.
    """

    @abstractmethod
    def get_by_date(self, date: date) -> DailyLog | None: ...

    @abstractmethod
    def get_by_date_range(self, start: date, end: date) -> list[DailyLog]:
        """Retrieve all daily logs within a date range (inclusive)."""
        ...

    @abstractmethod
    def get_entries_by_habit(
        self, habit_id: str, start: date, end: date
    ) -> list[HabitEntry]:
        """Retrieve all entries for a specific habit within a date range."""
        ...

    @abstractmethod
    def save(self, log: DailyLog) -> None: ...

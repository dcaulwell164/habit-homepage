from dataclasses import dataclass
from datetime import date, datetime

from habit_homepage.domain.value_objects import HabitSource


@dataclass
class HabitEntry:
    """
    Domain entity: represents a single habit measurement for a specific date.
    Contains pure business data with no infrastructure dependencies.
    """

    habit_id: str
    date: date
    value: float
    recorded_at: datetime
    source: HabitSource  # Track if manual or auto-recorded

    def is_automatic(self) -> bool:
        """Check if this entry was automatically recorded."""
        return self.source == HabitSource.AUTOMATIC

    def is_manual(self) -> bool:
        """Check if this entry was manually recorded."""
        return self.source == HabitSource.MANUAL

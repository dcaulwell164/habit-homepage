from dataclasses import dataclass, field
from datetime import date

from habit_homepage.domain.habit_entry import HabitEntry


@dataclass
class DailyLog:
    """
    Domain entity: aggregates all habit entries for a single day.
    Pure business data + rules.
    Contains no infrastructure or framework dependencies.
    """

    date: date
    entries: dict[str, HabitEntry] = field(default_factory=dict)

    def add_or_update_entry(self, entry: HabitEntry) -> None:
        """
        Add or update a habit entry for this day.
        Domain rule: one entry per habit per day.
        """
        if entry.date != self.date:
            raise ValueError(
                f"Entry date {entry.date} does not match log date {self.date}"
            )
        self.entries[entry.habit_id] = entry

    def get_entry(self, habit_id: str) -> HabitEntry | None:
        """Get entry for a specific habit."""
        return self.entries.get(habit_id)

    def has_entry(self, habit_id: str) -> bool:
        """Check if an entry exists for a specific habit."""
        return habit_id in self.entries

    def get_all_entries(self) -> list[HabitEntry]:
        """Get all habit entries for this day."""
        return list(self.entries.values())

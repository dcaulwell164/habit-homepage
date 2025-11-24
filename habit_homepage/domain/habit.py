from dataclasses import dataclass
from typing import Any

from habit_homepage.domain.value_objects import CategoryType, HabitSource


@dataclass
class Habit:
    """
    Domain entity: represents a trackable habit definition.
    Contains pure business data and rules.
    No infrastructure or framework dependencies.
    """

    id: str  # e.g., "reading", "exercise", "meditation"
    name: str  # Display name
    unit: str  # "pages", "minutes", "count", "kilometers", etc.
    source: HabitSource  # MANUAL or AUTOMATIC
    description: str = ""
    category_id: CategoryType | None = None  # Optional category reference

    # For automatic habits: provider-specific configuration
    # e.g., {"provider": "goodreads", "api_key": "...", "user_id": "..."}
    provider_config: dict[str, Any] | None = None

    def is_automatic(self) -> bool:
        """Check if this habit is automatically tracked."""
        return self.source == HabitSource.AUTOMATIC

    def is_manual(self) -> bool:
        """Check if this habit is manually tracked."""
        return self.source == HabitSource.MANUAL

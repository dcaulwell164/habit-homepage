"""
Domain-level habit definitions.

This module defines all habits that can be tracked in the application.
Habits are application configuration, not user-managed data.

Following hexagonal architecture:
- Domain defines what habits exist (business rules)
- Application ensures these habits are available
- Infrastructure stores them for querying
"""

from dataclasses import dataclass

from habit_homepage.domain.habit import Habit
from habit_homepage.domain.value_objects import CategoryType, HabitSource, ProviderType


@dataclass(frozen=True)
class HabitDefinition:
    """
    Immutable habit definition.
    Represents a habit that can be tracked in the system.
    """

    id: str
    name: str
    unit: str
    source: HabitSource
    category_id: CategoryType
    description: str
    provider_config: dict | None = None

    def to_habit(self) -> Habit:
        """Convert definition to a Habit entity."""
        return Habit(
            id=self.id,
            name=self.name,
            unit=self.unit,
            source=self.source,
            description=self.description,
            category_id=self.category_id,
            provider_config=self.provider_config,
        )


class HabitDefinitions:
    """
    Registry of all habits supported by the application.
    This is the single source of truth for what habits can be tracked.
    """

    # Garmin-synced health habits
    STEPS = HabitDefinition(
        id="steps",
        name="Daily Steps",
        unit="steps",
        source=HabitSource.AUTOMATIC,
        category_id=CategoryType.HEALTH,
        description="Total steps walked per day",
        provider_config={
            "provider": ProviderType.GARMIN.value,
            "metric": "steps",
        },
    )

    HEART_RATE = HabitDefinition(
        id="heart_rate",
        name="Resting Heart Rate",
        unit="bpm",
        source=HabitSource.AUTOMATIC,
        category_id=CategoryType.HEALTH,
        description="Resting heart rate measurement",
        provider_config={
            "provider": ProviderType.GARMIN.value,
            "metric": "heart_rate",
        },
    )

    EXERCISE = HabitDefinition(
        id="exercise",
        name="Total Exercise",
        unit="minutes",
        source=HabitSource.AUTOMATIC,
        category_id=CategoryType.HEALTH,
        description="All exercise activities combined",
        provider_config={
            "provider": ProviderType.GARMIN.value,
            "metric": "exercise",
        },
    )

    # Manual tracking habits (examples - customize as needed)
    READING = HabitDefinition(
        id="reading",
        name="Reading",
        unit="pages",
        source=HabitSource.MANUAL,
        category_id=CategoryType.LEARNING,
        description="Pages read per day",
        provider_config=None,
    )

    # Goodreads-synced learning habits
    # NOTE: Goodreads API is deprecated. This may require manual tracking.
    GOODREADS_BOOKS = HabitDefinition(
        id="goodreads_books",
        name="Books Completed",
        unit="books",
        source=HabitSource.AUTOMATIC,
        category_id=CategoryType.LEARNING,
        description="Books finished on Goodreads (limited due to API deprecation)",
        provider_config={
            "provider": ProviderType.GOODREADS.value,
            "metric": "books_read",
        },
    )

    MEDITATION = HabitDefinition(
        id="meditation",
        name="Meditation",
        unit="minutes",
        source=HabitSource.MANUAL,
        category_id=CategoryType.HEALTH,
        description="Daily meditation practice",
        provider_config=None,
    )

    DEEP_WORK = HabitDefinition(
        id="deep_work",
        name="Deep Work",
        unit="hours",
        source=HabitSource.MANUAL,
        category_id=CategoryType.PRODUCTIVITY,
        description="Focused work sessions",
        provider_config=None,
    )

    # GitHub-synced productivity habits
    GITHUB_CONTRIBUTIONS = HabitDefinition(
        id="github_contributions",
        name="GitHub Contributions",
        unit="contributions",
        source=HabitSource.AUTOMATIC,
        category_id=CategoryType.PRODUCTIVITY,
        description="Daily GitHub contributions (commits + PRs + issues)",
        provider_config={
            "provider": ProviderType.GITHUB.value,
            "metric": "contributions",
        },
    )

    @classmethod
    def get_all(cls) -> list[HabitDefinition]:
        """Get all defined habits."""
        return [
            cls.STEPS,
            cls.HEART_RATE,
            cls.EXERCISE,
            cls.READING,
            cls.GOODREADS_BOOKS,
            cls.MEDITATION,
            cls.DEEP_WORK,
            cls.GITHUB_CONTRIBUTIONS,
        ]

    @classmethod
    def get_by_id(cls, habit_id: str) -> HabitDefinition | None:
        """Get a habit definition by ID."""
        for habit_def in cls.get_all():
            if habit_def.id == habit_id:
                return habit_def
        return None

    @classmethod
    def exists(cls, habit_id: str) -> bool:
        """Check if a habit is defined."""
        return cls.get_by_id(habit_id) is not None

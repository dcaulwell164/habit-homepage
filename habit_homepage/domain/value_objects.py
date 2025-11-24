from enum import Enum


class HabitSource(Enum):
    """
    Domain value object: represents the source of a habit entry.
    Pure domain concept with no infrastructure dependencies.
    """

    MANUAL = "manual"
    AUTOMATIC = "automatic"


class CategoryType(Enum):
    """
    Domain value object: represents predefined habit categories.
    Provides type safety and prevents typos in category IDs.
    """

    HEALTH = "health"
    LEARNING = "learning"
    PRODUCTIVITY = "productivity"
    SOCIAL = "social"
    FINANCE = "finance"


class ProviderType(Enum):
    """
    Domain value object: represents external data providers.
    Used for automatic habit tracking integrations.
    """

    GARMIN = "garmin"
    GOODREADS = "goodreads"
    GITHUB = "github"
    TODOIST = "todoist"
    RESCUETIME = "rescuetime"
    WITHINGS = "withings"

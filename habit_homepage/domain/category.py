from dataclasses import dataclass

from habit_homepage.domain.value_objects import CategoryType


@dataclass
class Category:
    """
    Domain entity: represents a category for grouping habits.
    Examples: Health, Learning, Productivity, Social, Finance.
    Contains pure business data with no infrastructure dependencies.
    """

    id: CategoryType  # Type-safe category identifier
    name: str  # Display name
    description: str = ""
    color: str = "#808080"  # Hex color for UI display

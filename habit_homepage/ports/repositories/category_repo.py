from abc import ABC, abstractmethod

from habit_homepage.domain.category import Category
from habit_homepage.domain.value_objects import CategoryType


class CategoryRepository(ABC):
    """
    Outbound port: the application depends on this interface.
    Infrastructure implements it.
    """

    @abstractmethod
    def get_by_id(self, category_id: CategoryType) -> Category | None:
        """Retrieve a category by its ID."""
        ...

    @abstractmethod
    def get_all(self) -> list[Category]:
        """Retrieve all categories."""
        ...

    @abstractmethod
    def save(self, category: Category) -> None:
        """Save or update a category."""
        ...

    @abstractmethod
    def delete(self, category_id: CategoryType) -> None:
        """Delete a category by its ID."""
        ...

from habit_homepage.config.logging import get_logger
from habit_homepage.domain.habit import Habit
from habit_homepage.domain.habit_definitions import HabitDefinitions
from habit_homepage.ports.repositories.habit_repo import HabitRepository

logger = get_logger(__name__)


class HabitService:
    """
    Application service for habit management.

    Business rules:
    - Habits are defined by the application, not created by users
    - Users can only query available habits
    - Habits are initialized on application startup

    Follows hexagonal architecture:
    - Application layer defines what habits exist
    - Domain layer defines habit structure and definitions
    - Infrastructure layer persists habits for querying
    """

    def __init__(self, repo: HabitRepository):
        self.repo = repo

    def initialize_habits(self) -> None:
        """
        Initialize all application-defined habits.

        This ensures the repository contains all habits defined in HabitDefinitions.
        Called once on application startup.
        """
        logger.info("Initializing application-defined habits...")

        for habit_def in HabitDefinitions.get_all():
            habit = habit_def.to_habit()
            self.repo.save(habit)
            logger.info(f"Initialized habit: {habit.id} ({habit.name})")

        logger.info(f"Initialized {len(HabitDefinitions.get_all())} habits")

    def get_habit(self, habit_id: str) -> Habit | None:
        """
        Retrieve a habit by ID.

        Returns:
            Habit if it exists and is defined in HabitDefinitions, None otherwise
        """
        # Verify habit is defined in the application
        if not HabitDefinitions.exists(habit_id):
            return None

        return self.repo.get_by_id(habit_id)

    def get_all_habits(self) -> list[Habit]:
        """
        Retrieve all application-defined habits.

        Returns only habits that are defined in HabitDefinitions.
        """
        return self.repo.get_all()

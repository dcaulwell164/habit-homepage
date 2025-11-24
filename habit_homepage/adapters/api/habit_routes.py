from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from habit_homepage.application.habit_service import HabitService

# Type aliases for API documentation (independent of domain layer)
# Note: Using Literal provides better OpenAPI documentation
CategoryId = Literal["health", "learning", "productivity", "social", "finance"]
HabitSourceStr = Literal["manual", "automatic"]


class HabitResponse(BaseModel):
    """
    Response model for habit data.

    Habits are application-defined and read-only from the API perspective.
    Users cannot create or delete habits - they can only query available habits.
    """

    id: str
    name: str
    unit: str
    source: str = Field(
        ...,
        description="Source of habit data: 'manual' or 'automatic'",
        json_schema_extra={"enum": ["manual", "automatic"]},
    )
    description: str
    category_id: str | None = Field(
        None,
        description="Category: 'health', 'learning', 'productivity', 'social', or 'finance'",
        json_schema_extra={
            "enum": ["health", "learning", "productivity", "social", "finance"]
        },
    )
    provider_config: dict | None


def create_habit_router(service: HabitService) -> APIRouter:
    """
    API adapter for habit querying.

    Business rule: Habits are application-defined configuration, not user data.
    Users can only query available habits, not create or delete them.

    To add new habits: Modify HabitDefinitions in the domain layer.

    Follows hexagonal architecture:
    - This is an inbound adapter (API/HTTP)
    - Translates external requests to application service calls
    - Uses only primitive types (no domain imports)
    """

    router = APIRouter()

    @router.get("/habits", response_model=list[HabitResponse])
    def list_habits() -> list[HabitResponse]:
        """
        List all available habits.

        Returns all habits defined by the application.
        Habits are read-only configuration, not user data.
        """
        habits = service.get_all_habits()
        return [
            HabitResponse(
                id=h.id,
                name=h.name,
                unit=h.unit,
                source=h.source.value,
                description=h.description,
                category_id=h.category_id.value if h.category_id else None,
                provider_config=h.provider_config,
            )
            for h in habits
        ]

    @router.get("/habits/{habit_id}", response_model=HabitResponse)
    def get_habit(habit_id: str) -> HabitResponse:
        """
        Get a specific habit by ID.

        Returns 404 if the habit is not defined in the application.
        """
        habit = service.get_habit(habit_id)
        if not habit:
            raise HTTPException(
                status_code=404,
                detail=f"Habit '{habit_id}' not found. "
                "Habits are application-defined and cannot be created dynamically.",
            )

        return HabitResponse(
            id=habit.id,
            name=habit.name,
            unit=habit.unit,
            source=habit.source.value,
            description=habit.description,
            category_id=habit.category_id.value if habit.category_id else None,
            provider_config=habit.provider_config,
        )

    return router

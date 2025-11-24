from datetime import date as date_type

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from habit_homepage.application.goal_service import GoalService
from habit_homepage.domain.goal import GoalComparison, GoalPeriod


class CreateGoalRequest(BaseModel):
    """Request model for creating a goal."""

    id: str = Field(..., description="Unique identifier for the goal")
    habit_id: str = Field(..., description="ID of the habit this goal is for")
    target_value: float = Field(..., description="Target value to achieve")
    comparison: str = Field(
        ..., description="Comparison operator: '>=', '<=', or '=='"
    )
    period: str = Field(..., description="Time period: 'daily', 'weekly', or 'monthly'")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str | None = Field(
        None, description="Optional end date (YYYY-MM-DD). None = ongoing"
    )
    description: str = Field("", description="Optional description")


class UpdateGoalRequest(BaseModel):
    """Request model for updating a goal."""

    target_value: float | None = Field(None, description="New target value")
    comparison: str | None = Field(None, description="New comparison operator")
    end_date: str | None = Field(None, description="New end date (YYYY-MM-DD)")
    description: str | None = Field(None, description="New description")


class GoalResponse(BaseModel):
    """Response model for a goal."""

    id: str
    habit_id: str
    target_value: float
    comparison: str
    period: str
    start_date: str
    end_date: str | None
    description: str


class GoalProgressResponse(BaseModel):
    """Response model for goal progress."""

    goal_id: str
    habit_id: str
    is_active: bool
    actual_value: float | None
    target_value: float | None = None
    comparison: str | None = None
    is_met: bool | None = None


def create_goal_router(service: GoalService) -> APIRouter:
    """
    API adapter for goal management.

    Follows hexagonal architecture:
    - This is an inbound adapter (API/HTTP)
    - Translates external requests to application service calls
    """

    router = APIRouter()

    @router.post("/habits/{habit_id}/goals", response_model=GoalResponse, status_code=201)
    def create_goal(habit_id: str, body: CreateGoalRequest) -> GoalResponse:
        """
        Create a new goal for a habit.

        The goal ID must be unique across all goals.
        """
        # Validate habit_id matches body
        if body.habit_id != habit_id:
            raise HTTPException(
                status_code=400,
                detail=f"Habit ID in URL ({habit_id}) does not match body ({body.habit_id})",
            )

        # Parse dates
        try:
            start_date = date_type.fromisoformat(body.start_date)
            end_date = (
                date_type.fromisoformat(body.end_date) if body.end_date else None
            )
        except ValueError as e:
            raise HTTPException(
                status_code=400, detail=f"Invalid date format: {e}"
            ) from e

        # Parse enums
        try:
            comparison = GoalComparison(body.comparison)
            period = GoalPeriod(body.period)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid comparison or period: {e}. "
                "Use '>=', '<=', or '==' for comparison, "
                "and 'daily', 'weekly', or 'monthly' for period.",
            ) from e

        try:
            goal = service.create_goal(
                goal_id=body.id,
                habit_id=body.habit_id,
                target_value=body.target_value,
                comparison=comparison,
                period=period,
                start_date=start_date,
                end_date=end_date,
                description=body.description,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

        return GoalResponse(
            id=goal.id,
            habit_id=goal.habit_id,
            target_value=goal.target_value,
            comparison=goal.comparison.value,
            period=goal.period.value,
            start_date=goal.start_date.isoformat(),
            end_date=goal.end_date.isoformat() if goal.end_date else None,
            description=goal.description,
        )

    @router.get("/habits/{habit_id}/goals", response_model=list[GoalResponse])
    def list_goals_for_habit(habit_id: str) -> list[GoalResponse]:
        """
        List all goals for a specific habit.
        """
        goals = service.get_goals_for_habit(habit_id)
        return [
            GoalResponse(
                id=g.id,
                habit_id=g.habit_id,
                target_value=g.target_value,
                comparison=g.comparison.value,
                period=g.period.value,
                start_date=g.start_date.isoformat(),
                end_date=g.end_date.isoformat() if g.end_date else None,
                description=g.description,
            )
            for g in goals
        ]

    @router.get("/goals", response_model=list[GoalResponse])
    def list_all_goals() -> list[GoalResponse]:
        """
        List all goals across all habits.
        """
        goals = service.get_all_goals()
        return [
            GoalResponse(
                id=g.id,
                habit_id=g.habit_id,
                target_value=g.target_value,
                comparison=g.comparison.value,
                period=g.period.value,
                start_date=g.start_date.isoformat(),
                end_date=g.end_date.isoformat() if g.end_date else None,
                description=g.description,
            )
            for g in goals
        ]

    @router.get("/goals/{goal_id}", response_model=GoalResponse)
    def get_goal(goal_id: str) -> GoalResponse:
        """
        Get a specific goal by ID.
        """
        goal = service.get_goal(goal_id)
        if not goal:
            raise HTTPException(status_code=404, detail=f"Goal '{goal_id}' not found")

        return GoalResponse(
            id=goal.id,
            habit_id=goal.habit_id,
            target_value=goal.target_value,
            comparison=goal.comparison.value,
            period=goal.period.value,
            start_date=goal.start_date.isoformat(),
            end_date=goal.end_date.isoformat() if goal.end_date else None,
            description=goal.description,
        )

    @router.put("/goals/{goal_id}", response_model=GoalResponse)
    def update_goal(goal_id: str, body: UpdateGoalRequest) -> GoalResponse:
        """
        Update an existing goal.

        Only provided fields will be updated.
        """
        # Parse optional values
        comparison = None
        if body.comparison:
            try:
                comparison = GoalComparison(body.comparison)
            except ValueError as e:
                raise HTTPException(
                    status_code=400, detail=f"Invalid comparison: {e}"
                ) from e

        end_date = None
        if body.end_date:
            try:
                end_date = date_type.fromisoformat(body.end_date)
            except ValueError as e:
                raise HTTPException(
                    status_code=400, detail=f"Invalid date format: {e}"
                ) from e

        try:
            goal = service.update_goal(
                goal_id=goal_id,
                target_value=body.target_value,
                comparison=comparison,
                end_date=end_date,
                description=body.description,
            )
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e

        return GoalResponse(
            id=goal.id,
            habit_id=goal.habit_id,
            target_value=goal.target_value,
            comparison=goal.comparison.value,
            period=goal.period.value,
            start_date=goal.start_date.isoformat(),
            end_date=goal.end_date.isoformat() if goal.end_date else None,
            description=goal.description,
        )

    @router.delete("/goals/{goal_id}", status_code=204)
    def delete_goal(goal_id: str) -> None:
        """
        Delete a goal.
        """
        try:
            service.delete_goal(goal_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e

    @router.get("/goals/{goal_id}/progress", response_model=GoalProgressResponse)
    def check_goal_progress(goal_id: str, date: str) -> GoalProgressResponse:
        """
        Check progress toward a goal for a specific date.

        Returns whether the goal is active, the actual value achieved,
        and whether the goal was met.
        """
        try:
            check_date = date_type.fromisoformat(date)
        except ValueError as e:
            raise HTTPException(
                status_code=400, detail=f"Invalid date format: {date}"
            ) from e

        try:
            progress = service.check_goal_progress(goal_id, check_date)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e

        goal = service.get_goal(goal_id)
        if not goal:
            raise HTTPException(status_code=404, detail=f"Goal '{goal_id}' not found")

        return GoalProgressResponse(
            goal_id=goal_id,
            habit_id=goal.habit_id,
            is_active=progress["is_active"],
            actual_value=progress.get("actual_value"),
            target_value=progress.get("target_value"),
            comparison=progress.get("comparison"),
            is_met=progress.get("is_met"),
        )

    @router.get("/daily-logs/{date}/goals", response_model=list[GoalProgressResponse])
    def check_daily_goals(date: str) -> list[GoalProgressResponse]:
        """
        Check all goals for a specific date.

        Returns progress for all active goals on that date.
        """
        try:
            check_date = date_type.fromisoformat(date)
        except ValueError as e:
            raise HTTPException(
                status_code=400, detail=f"Invalid date format: {date}"
            ) from e

        all_goals = service.get_all_goals()
        results = []

        for goal in all_goals:
            if not goal.is_active(check_date):
                continue

            progress = service.check_goal_progress(goal.id, check_date)
            results.append(
                GoalProgressResponse(
                    goal_id=goal.id,
                    habit_id=goal.habit_id,
                    is_active=progress["is_active"],
                    actual_value=progress.get("actual_value"),
                    target_value=progress.get("target_value"),
                    comparison=progress.get("comparison"),
                    is_met=progress.get("is_met"),
                )
            )

        return results

    return router

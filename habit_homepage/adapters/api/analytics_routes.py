from datetime import date as date_type

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from habit_homepage.application.analytics_service import AnalyticsService


class HabitStatisticsResponse(BaseModel):
    """Response model for habit statistics."""

    habit_id: str
    start_date: str
    end_date: str
    min: float
    max: float
    average: float
    total: float
    count: int
    days_logged: int
    days_in_range: int


class StreakResponse(BaseModel):
    """Response model for streak information."""

    habit_id: str
    current_streak: int


class LongestStreakResponse(BaseModel):
    """Response model for longest streak."""

    habit_id: str
    length: int
    start_date: str | None
    end_date: str | None


class CalendarDataPoint(BaseModel):
    """Single data point for calendar/heatmap."""

    date: str
    value: float


class CalendarDataResponse(BaseModel):
    """Response model for calendar data."""

    habit_id: str
    year: int
    month: int
    data: list[CalendarDataPoint]


class TrendDataResponse(BaseModel):
    """Response model for trend/time series data."""

    habit_id: str
    start_date: str
    end_date: str
    data: list[CalendarDataPoint]


class DailySummaryResponse(BaseModel):
    """Response model for daily summary."""

    date: str
    total_habits: int
    logged_habits: int
    logged_habit_ids: list[str]


class CompletionRateResponse(BaseModel):
    """Response model for completion rate."""

    habit_id: str
    completion_rate: float = Field(..., description="Percentage (0-100)")
    days_completed: int
    total_days: int


def create_analytics_router(service: AnalyticsService) -> APIRouter:
    """
    API adapter for habit analytics and insights.

    Follows hexagonal architecture:
    - This is an inbound adapter (API/HTTP)
    - Translates external requests to application service calls
    """

    router = APIRouter()

    @router.get("/habits/{habit_id}/stats", response_model=HabitStatisticsResponse)
    def get_habit_statistics(
        habit_id: str,
        start: str = Query(..., description="Start date (YYYY-MM-DD)"),
        end: str = Query(..., description="End date (YYYY-MM-DD)"),
    ) -> HabitStatisticsResponse:
        """
        Get statistical summary for a habit over a date range.

        Returns min, max, average, total, and count of entries.
        """
        try:
            start_date = date_type.fromisoformat(start)
            end_date = date_type.fromisoformat(end)
        except ValueError as e:
            raise HTTPException(
                status_code=400, detail=f"Invalid date format: {e}"
            ) from e

        if start_date > end_date:
            raise HTTPException(
                status_code=400, detail="Start date must be before or equal to end date"
            )

        try:
            stats = service.get_habit_statistics(habit_id, start_date, end_date)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e

        return HabitStatisticsResponse(
            habit_id=habit_id,
            start_date=start,
            end_date=end,
            min=stats["min"],
            max=stats["max"],
            average=stats["average"],
            total=stats["total"],
            count=stats["count"],
            days_logged=stats["days_logged"],
            days_in_range=stats["days_in_range"],
        )

    @router.get("/habits/{habit_id}/streak", response_model=StreakResponse)
    def get_current_streak(
        habit_id: str,
        as_of: str | None = Query(None, description="As of date (YYYY-MM-DD). Defaults to today."),
    ) -> StreakResponse:
        """
        Get the current streak for a habit.

        A streak is consecutive days with logged entries, going backwards from today.
        """
        as_of_date = None
        if as_of:
            try:
                as_of_date = date_type.fromisoformat(as_of)
            except ValueError as e:
                raise HTTPException(
                    status_code=400, detail=f"Invalid date format: {e}"
                ) from e

        try:
            streak = service.get_current_streak(habit_id, as_of_date)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e

        return StreakResponse(habit_id=habit_id, current_streak=streak)

    @router.get("/habits/{habit_id}/longest-streak", response_model=LongestStreakResponse)
    def get_longest_streak(
        habit_id: str,
        start: str = Query(..., description="Start date (YYYY-MM-DD)"),
        end: str = Query(..., description="End date (YYYY-MM-DD)"),
    ) -> LongestStreakResponse:
        """
        Find the longest streak for a habit within a date range.
        """
        try:
            start_date = date_type.fromisoformat(start)
            end_date = date_type.fromisoformat(end)
        except ValueError as e:
            raise HTTPException(
                status_code=400, detail=f"Invalid date format: {e}"
            ) from e

        if start_date > end_date:
            raise HTTPException(
                status_code=400, detail="Start date must be before or equal to end date"
            )

        try:
            streak_info = service.get_longest_streak(habit_id, start_date, end_date)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e

        return LongestStreakResponse(
            habit_id=habit_id,
            length=streak_info["length"],
            start_date=streak_info["start_date"],
            end_date=streak_info["end_date"],
        )

    @router.get("/habits/{habit_id}/calendar", response_model=CalendarDataResponse)
    def get_calendar_data(
        habit_id: str,
        year: int = Query(..., description="Year (e.g., 2024)"),
        month: int = Query(..., ge=1, le=12, description="Month (1-12)"),
    ) -> CalendarDataResponse:
        """
        Get habit data for a calendar month.

        Useful for generating heatmaps or calendar visualizations.
        Returns value for each day in the month.
        """
        try:
            data = service.get_calendar_data(habit_id, year, month)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e

        return CalendarDataResponse(
            habit_id=habit_id,
            year=year,
            month=month,
            data=[CalendarDataPoint(date=d["date"], value=d["value"]) for d in data],
        )

    @router.get("/habits/{habit_id}/trend", response_model=TrendDataResponse)
    def get_habit_trend(
        habit_id: str,
        start: str = Query(..., description="Start date (YYYY-MM-DD)"),
        end: str = Query(..., description="End date (YYYY-MM-DD)"),
    ) -> TrendDataResponse:
        """
        Get time series data for a habit.

        Useful for generating line charts or trend analysis.
        Returns value for each day in the range.
        """
        try:
            start_date = date_type.fromisoformat(start)
            end_date = date_type.fromisoformat(end)
        except ValueError as e:
            raise HTTPException(
                status_code=400, detail=f"Invalid date format: {e}"
            ) from e

        if start_date > end_date:
            raise HTTPException(
                status_code=400, detail="Start date must be before or equal to end date"
            )

        try:
            data = service.get_habit_trend(habit_id, start_date, end_date)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e

        return TrendDataResponse(
            habit_id=habit_id,
            start_date=start,
            end_date=end,
            data=[CalendarDataPoint(date=d["date"], value=d["value"]) for d in data],
        )

    @router.get("/daily-logs/{date}/summary", response_model=DailySummaryResponse)
    def get_daily_summary(date: str) -> DailySummaryResponse:
        """
        Get a summary of all habits for a specific day.

        Shows how many habits were logged vs total habits available.
        """
        try:
            check_date = date_type.fromisoformat(date)
        except ValueError as e:
            raise HTTPException(
                status_code=400, detail=f"Invalid date format: {date}"
            ) from e

        summary = service.get_daily_summary(check_date)

        return DailySummaryResponse(
            date=date,
            total_habits=summary["total_habits"],
            logged_habits=summary["logged_habits"],
            logged_habit_ids=summary["logged_habit_ids"],
        )

    @router.get("/habits/{habit_id}/completion-rate", response_model=CompletionRateResponse)
    def get_completion_rate(
        habit_id: str,
        start: str = Query(..., description="Start date (YYYY-MM-DD)"),
        end: str = Query(..., description="End date (YYYY-MM-DD)"),
        threshold: float = Query(
            0.0, description="Minimum value to consider a day 'complete'"
        ),
    ) -> CompletionRateResponse:
        """
        Calculate completion rate for a habit.

        A day is considered "complete" if the logged value exceeds the threshold.
        Returns percentage of days completed.
        """
        try:
            start_date = date_type.fromisoformat(start)
            end_date = date_type.fromisoformat(end)
        except ValueError as e:
            raise HTTPException(
                status_code=400, detail=f"Invalid date format: {e}"
            ) from e

        if start_date > end_date:
            raise HTTPException(
                status_code=400, detail="Start date must be before or equal to end date"
            )

        try:
            rate_info = service.get_completion_rate(
                habit_id, start_date, end_date, threshold
            )
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e

        return CompletionRateResponse(
            habit_id=habit_id,
            completion_rate=rate_info["completion_rate"],
            days_completed=rate_info["days_completed"],
            total_days=rate_info["total_days"],
        )

    return router

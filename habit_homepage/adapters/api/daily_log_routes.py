from datetime import date as date_type

from fastapi import APIRouter, HTTPException
from pydantic.main import BaseModel

from habit_homepage.application.daily_log_service import DailyLogService


class RecordHabitRequest(BaseModel):
    """Request model for recording a habit entry."""

    value: float


class HabitEntryResponse(BaseModel):
    """Response model for a habit entry."""

    habit_id: str
    value: float
    recorded_at: str
    source: str


class DailyLogResponse(BaseModel):
    """Response model for a daily log."""

    date: str
    entries: list[HabitEntryResponse]


def create_router(service: DailyLogService) -> APIRouter:
    """
    API adapter for daily log management.
    - Translates HTTP requests into application-service calls.
    - Knows about FastAPI (a framework concern).
    - Has NO logic and NO domain decisions.
    - Depends on application layer, never the other way around.

    Follows hexagonal architecture:
    - This is an inbound adapter (API/HTTP)
    - Translates external requests to application service calls
    """

    router = APIRouter()

    @router.get("/daily-logs/{date}", response_model=DailyLogResponse)
    def get_daily_log(date: str) -> DailyLogResponse:
        """Get all habit entries for a specific date."""
        try:
            date_obj = date_type.fromisoformat(date)
        except ValueError as e:
            raise HTTPException(
                status_code=400, detail=f"Invalid date format: {date}"
            ) from e

        log = service.get_or_create(date_obj)

        entries = [
            HabitEntryResponse(
                habit_id=entry.habit_id,
                value=entry.value,
                recorded_at=entry.recorded_at.isoformat(),
                source=entry.source.value,
            )
            for entry in log.get_all_entries()
        ]

        return DailyLogResponse(date=log.date.isoformat(), entries=entries)

    @router.post(
        "/daily-logs/{date}/habits/{habit_id}", response_model=DailyLogResponse
    )
    def record_habit(
        date: str, habit_id: str, body: RecordHabitRequest
    ) -> DailyLogResponse:
        """
        Record a habit entry for a specific date.

        This endpoint handles manual habit tracking.
        Input validation belongs here (FastAPI layer).
        Delegates to application service for logic.
        """
        try:
            date_obj = date_type.fromisoformat(date)
        except ValueError as e:
            raise HTTPException(
                status_code=400, detail=f"Invalid date format: {date}"
            ) from e

        try:
            log = service.record_habit(date_obj, habit_id, body.value)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e

        entries = [
            HabitEntryResponse(
                habit_id=entry.habit_id,
                value=entry.value,
                recorded_at=entry.recorded_at.isoformat(),
                source=entry.source.value,
            )
            for entry in log.get_all_entries()
        ]

        return DailyLogResponse(date=log.date.isoformat(), entries=entries)

    @router.post("/daily-logs/{date}/sync", response_model=DailyLogResponse)
    def sync_automatic_habits(date: str) -> DailyLogResponse:
        """
        Trigger sync of all automatic habits for a specific date.

        This will fetch data from configured external providers
        and record entries for all automatic habits.
        """
        try:
            date_obj = date_type.fromisoformat(date)
        except ValueError as e:
            raise HTTPException(
                status_code=400, detail=f"Invalid date format: {date}"
            ) from e

        log = service.sync_automatic_habits(date_obj)

        entries = [
            HabitEntryResponse(
                habit_id=entry.habit_id,
                value=entry.value,
                recorded_at=entry.recorded_at.isoformat(),
                source=entry.source.value,
            )
            for entry in log.get_all_entries()
        ]

        return DailyLogResponse(date=log.date.isoformat(), entries=entries)

    return router

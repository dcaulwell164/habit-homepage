from fastapi import FastAPI

from habit_homepage.adapters.api.analytics_routes import create_analytics_router
from habit_homepage.adapters.api.daily_log_routes import create_router
from habit_homepage.adapters.api.goal_routes import create_goal_router
from habit_homepage.adapters.api.habit_routes import create_habit_router
from habit_homepage.adapters.providers.garmin.provider import GarminHabitDataProvider
from habit_homepage.adapters.providers.github.provider import GitHubHabitDataProvider
from habit_homepage.adapters.repositories.sqlite.category_repo import (
    SQLiteCategoryRepository,
)
from habit_homepage.adapters.repositories.sqlite.daily_log_repo import (
    SQLiteDailyLogRepository,
)
from habit_homepage.adapters.repositories.sqlite.goal_repo import SQLiteGoalRepository
from habit_homepage.adapters.repositories.sqlite.habit_repo import SQLiteHabitRepository
from habit_homepage.application.analytics_service import AnalyticsService
from habit_homepage.application.daily_log_service import DailyLogService
from habit_homepage.application.goal_service import GoalService
from habit_homepage.application.habit_service import HabitService
from habit_homepage.config.logging import setup_logging
from habit_homepage.config.settings import settings
from habit_homepage.ports.providers.habit_data_provider import HabitDataProvider

"""
Main application entry point.

This is where we wire everything together following hexagonal architecture:
1. Infrastructure layer (adapters) - SQLite repositories
2. Application layer (services) - Business logic orchestration
3. API layer (adapters) - FastAPI routes

The dependency flow:
- API adapters depend on Application services
- Application services depend on Ports (interfaces)
- Infrastructure adapters implement Ports
- Domain layer has NO dependencies on outer layers
"""

# Setup logging
setup_logging()

app = FastAPI(title="Habit Tracker API")

# ============================================================================
# Dependency Injection - Hexagonal Architecture Wiring
# ============================================================================

# 1. Initialize Infrastructure Adapters (Outbound - Persistence)
# Note: Categories must be initialized before habits due to foreign key dependency
category_repo = SQLiteCategoryRepository(settings.database_path)
habit_repo = SQLiteHabitRepository(settings.database_path)
log_repo = SQLiteDailyLogRepository(settings.database_path)
goal_repo = SQLiteGoalRepository(settings.database_path)

# 2. Initialize Data Providers (Outbound - External APIs)
data_providers: list[HabitDataProvider] = []

# Garmin provider (if credentials provided)
if settings.garmin_email_address and settings.garmin_password:
    data_providers.append(
        GarminHabitDataProvider(
            email=settings.garmin_email_address,
            password=settings.garmin_password,
        )
    )

# GitHub provider (if credentials provided)
if settings.github_token and settings.github_username:
    data_providers.append(
        GitHubHabitDataProvider(
            token=settings.github_token,
            username=settings.github_username,
        )
    )

# 3. Initialize Application Services
# Services depend on ports (interfaces), not concrete implementations
habit_service = HabitService(habit_repo)
log_service = DailyLogService(log_repo, habit_repo, data_providers)
goal_service = GoalService(goal_repo, habit_repo, log_repo)
analytics_service = AnalyticsService(log_repo, habit_repo)

# 4. Initialize application-defined habits
# This ensures all habits from HabitDefinitions are available in the database
habit_service.initialize_habits()

# 5. Create API Routers (Inbound Adapters)
# Routers depend on application services
daily_log_router = create_router(log_service)
habit_router = create_habit_router(habit_service)
goal_router = create_goal_router(goal_service)
analytics_router = create_analytics_router(analytics_service)

# 6. Register Routers with FastAPI
app.include_router(daily_log_router, prefix="/api", tags=["Daily Logs"])
app.include_router(habit_router, prefix="/api", tags=["Habits"])
app.include_router(goal_router, prefix="/api", tags=["Goals"])
app.include_router(analytics_router, prefix="/api", tags=["Analytics"])


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Habit Tracker API - Multi-habit tracking system"}

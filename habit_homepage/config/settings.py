from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings.
    Loaded from environment variables and .env file.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_env: str = "development"
    app_port: int = 8000

    # Database configuration
    database_path: str = "habit.db"

    # Garmin configuration
    garmin_email_address: str = ""
    garmin_password: str = ""

    # GitHub configuration
    github_token: str = ""
    github_username: str = ""

    # Goodreads configuration
    goodreads_user_id: str = ""


# Singleton instance
settings = Settings()

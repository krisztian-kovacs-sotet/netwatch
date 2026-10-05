from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, read from NETWATCH_* environment variables or a .env file."""

    model_config = SettingsConfigDict(env_prefix="NETWATCH_", env_file=".env")

    database_url: str = "sqlite:///./netwatch.db"
    # Seconds between background scans. 0 disables the background scanner.
    scan_interval_seconds: int = 300

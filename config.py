"""Configuration settings for the bot."""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    """Bot configuration settings."""

    # Telegram Bot
    BOT_TOKEN: str
    ADMIN_IDS: str = ""

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///bot.db"

    # Quiz Settings
    QUIZ_END_DATE: str = "2025-12-30"
    WINNERS_COUNT: int = 30

    # Directories
    IMAGES_DIR: Path = Path("./images")
    USER_PHOTOS_DIR: Path = Path("./user_photos")
    GENERATED_PHOTOS_DIR: Path = Path("./generated_photos")

    # Logging
    LOG_LEVEL: str = "INFO"

    # AI Generation
    OPENAI_API_KEY: str = ""
    AI_GENERATION_ENABLED: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

    @property
    def admin_ids_list(self) -> List[int]:
        """Parse admin IDs from comma-separated string."""
        if not self.ADMIN_IDS:
            return []
        return [int(id.strip()) for id in self.ADMIN_IDS.split(",") if id.strip()]

    def create_directories(self):
        """Create necessary directories if they don't exist."""
        self.IMAGES_DIR.mkdir(exist_ok=True)
        self.USER_PHOTOS_DIR.mkdir(exist_ok=True)
        self.GENERATED_PHOTOS_DIR.mkdir(exist_ok=True)


# Global settings instance
settings = Settings()

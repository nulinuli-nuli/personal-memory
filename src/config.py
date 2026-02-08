"""Configuration management using Pydantic Settings."""
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def get_project_root() -> Path:
    """Get the project root directory."""
    # Start from the current file and go up to find project root
    current_file = Path(__file__).resolve()
    # src/config.py -> src -> project root
    return current_file.parent.parent


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=str(get_project_root() / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # AI Provider Configuration
    ai_provider: str = Field(default="openai", description="AI provider: openai, anthropic")
    ai_api_key: str = Field(default="", description="API key for the AI provider")
    ai_base_url: Optional[str] = Field(
        default=None,
        description="Custom base URL for AI API (for proxy/relay services)",
    )
    ai_model: Optional[str] = Field(default=None, description="AI model to use")

    # Feishu Bot Configuration
    feishu_app_id: Optional[str] = Field(default=None, description="Feishu app ID")
    feishu_app_secret: Optional[str] = Field(default=None, description="Feishu app secret")
    feishu_verification_token: Optional[str] = Field(default=None)
    feishu_encrypt_key: Optional[str] = Field(default=None)

    # Database Configuration
    database_url: str = Field(default="sqlite:///data/database.db")

    # Application Settings
    timezone: str = Field(default="Asia/Shanghai")
    debug: bool = Field(default=False)

    @property
    def data_dir(self) -> Path:
        """Get or create data directory."""
        db_path = Path(self.database_url.replace("sqlite:///", ""))
        data_dir = db_path.parent
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir

    @property
    def prompts_dir(self) -> Path:
        """Get prompts directory."""
        return Path(__file__).parent.parent / "prompts"


# Global settings instance
settings = Settings()

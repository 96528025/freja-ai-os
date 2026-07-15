from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Freja Personal AI OS"
    environment: str = "development"
    api_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./data/freja.db"
    chroma_path: str = "./data/chroma"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"]
    )
    brief_hour: int = 7
    brief_minute: int = 0
    timezone: str = "America/Los_Angeles"
    scheduler_enabled: bool = True
    collector_limit: int = 12
    news_sources: list[str] = Field(
        default=[
            "reddit",
            "xiaohongshu",
            "openai_blog",
            "anthropic_blog",
            "google_deepmind_blog",
            "cursor_blog",
            "github_trending",
        ]
    )
    opencli_path: str = str(
        Path.home() / ".agent-reach" / "npm" / "node_modules" / ".bin" / "opencli"
    )
    opencli_status_url: str = "http://127.0.0.1:19825/status"
    reddit_subreddits: list[str] = Field(
        default=["LocalLLaMA", "MachineLearning", "ChatGPT", "OpenAI", "ClaudeAI"]
    )
    reddit_max_age_hours: int = 72
    xiaohongshu_queries: list[str] = Field(
        default=["AI 编程", "Claude Code", "OpenAI"]
    )
    xiaohongshu_opencli_site: str = "rednote"

    def ensure_data_dirs(self) -> None:
        if self.database_url.startswith("sqlite:///"):
            Path(self.database_url.removeprefix("sqlite:///")).parent.mkdir(parents=True, exist_ok=True)
        Path(self.chroma_path).mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()

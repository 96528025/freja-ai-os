from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.asset import AssetStatus, AssetType


class AssetCreate(BaseModel):
    type: AssetType
    title: str = Field(min_length=1, max_length=500)
    content: str = ""
    summary: str | None = None
    source: str | None = None
    source_id: str | None = None
    url: str | None = None
    language: str = "en"
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    parent_id: str | None = None
    occurred_at: datetime | None = None


class IdeaCreate(BaseModel):
    content: str = Field(min_length=3, max_length=20_000)
    title: str | None = Field(default=None, max_length=500)


class AssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: AssetType
    status: AssetStatus
    title: str
    content: str
    summary: str | None
    source: str | None
    source_id: str | None
    url: str | None
    language: str
    tags: list[str]
    metadata: dict[str, Any] = Field(validation_alias="asset_metadata")
    parent_id: str | None
    occurred_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @field_validator("occurred_at", "created_at", "updated_at", mode="before")
    @classmethod
    def normalize_utc(cls, value: datetime | None) -> datetime | None:
        # SQLite drops timezone metadata; persisted timestamps are always UTC.
        if value is not None and value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value


class AssetList(BaseModel):
    items: list[AssetRead]
    total: int


class DashboardStats(BaseModel):
    total_assets: int
    ideas: int
    news: int
    research: int
    tasks: int


class DashboardRead(BaseModel):
    today_brief: AssetRead | None
    latest_ideas: list[AssetRead]
    recent_research: list[AssetRead]
    upcoming_tasks: list[AssetRead]
    stats: DashboardStats

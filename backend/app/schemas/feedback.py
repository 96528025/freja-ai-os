from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.feedback import FeedbackSignal
from app.schemas.asset import AssetRead


FeedbackReason = Literal[
    "not_relevant",
    "too_basic",
    "too_marketing",
    "repetitive",
    "source_not_useful",
    "other",
]


class ItemFeedbackWrite(BaseModel):
    signal: FeedbackSignal | None
    reason: FeedbackReason | None = None


class BriefFeedbackWrite(BaseModel):
    satisfaction: int = Field(ge=1, le=5)
    note: str | None = Field(default=None, max_length=2_000)


class FeedbackRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    brief_id: str
    asset_id: str | None
    signal: FeedbackSignal | None
    reason: str | None
    satisfaction: int | None
    note: str | None
    created_at: datetime
    updated_at: datetime

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def normalize_utc(cls, value: datetime) -> datetime:
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


class BriefItemRead(BaseModel):
    asset: AssetRead
    feedback: FeedbackRead | None


class BriefFeedbackState(BaseModel):
    satisfaction: FeedbackRead | None
    items: list[BriefItemRead]


class PreferenceProfileRead(BaseModel):
    total_item_feedback: int
    interested: int
    not_interested: int
    average_satisfaction: float | None
    preferred_topics: list[str]
    avoided_topics: list[str]

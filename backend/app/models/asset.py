import enum
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AssetType(str, enum.Enum):
    IDEA = "idea"
    NEWS = "news"
    BRIEF = "brief"
    RESEARCH = "research"
    LINK = "link"
    REPOSITORY = "repository"
    DOCUMENT = "document"
    NOTE = "note"
    TASK = "task"


class AssetStatus(str, enum.Enum):
    INBOX = "inbox"
    ACTIVE = "active"
    ARCHIVED = "archived"


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    type: Mapped[AssetType] = mapped_column(Enum(AssetType), index=True)
    status: Mapped[AssetStatus] = mapped_column(Enum(AssetStatus), default=AssetStatus.ACTIVE, index=True)
    title: Mapped[str] = mapped_column(String(500))
    content: Mapped[str] = mapped_column(Text, default="")
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    source_id: Mapped[str | None] = mapped_column(String(500), nullable=True)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    language: Mapped[str] = mapped_column(String(12), default="en")
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    asset_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict)
    parent_id: Mapped[str | None] = mapped_column(ForeignKey("assets.id"), nullable=True, index=True)
    embedding_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    occurred_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    parent: Mapped["Asset | None"] = relationship(remote_side=[id], back_populates="children")
    children: Mapped[list["Asset"]] = relationship(back_populates="parent")

    __table_args__ = (
        Index("ix_assets_source_source_id", "source", "source_id", unique=True),
        Index("ix_assets_type_created_at", "type", "created_at"),
    )


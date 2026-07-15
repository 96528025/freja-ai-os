import asyncio
import hashlib
import json
import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.asset import Asset, AssetType
from app.repositories.asset_repository import AssetRepository
from app.repositories.source_snapshot_repository import SourceSnapshotRepository
from app.schemas.asset import AssetCreate
from app.services.asset_service import AssetService
from app.services.collectors import enabled_collectors
from app.services.collectors.base import CollectedItem
from app.services.llm import LLMService
from app.services.source_registry import SourceRegistry

logger = logging.getLogger(__name__)
_generation_lock = asyncio.Lock()


class BriefGenerationInProgress(RuntimeError):
    pass


class BriefService:
    def __init__(self, session: Session, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.repository = AssetRepository(session)
        self.snapshots = SourceSnapshotRepository(session)
        self.assets = AssetService(session, settings)
        self.llm = LLMService(settings)

    async def generate(self, *, force_refresh: bool = False) -> Asset:
        if _generation_lock.locked():
            raise BriefGenerationInProgress("A brief generation is already running")
        async with _generation_lock:
            return await self._generate(force_refresh=force_refresh)

    async def _generate(self, *, force_refresh: bool) -> Asset:
        registry = SourceRegistry(self.session, self.settings)
        collectors = enabled_collectors(registry.enabled_ids(), self.settings)
        local_date = datetime.now(ZoneInfo(self.settings.timezone)).date()
        candidates: list[Asset] = []
        snapshot_usage: dict[str, str] = {}
        pending = []

        for collector in collectors:
            config_hash = self._snapshot_config_hash(collector.name)
            snapshot = None if force_refresh else self.snapshots.find_success(
                collector.name, local_date, config_hash
            )
            if snapshot is not None:
                cached_assets = [
                    asset
                    for asset_id in snapshot.asset_ids
                    if (asset := self.repository.get(asset_id)) is not None
                ]
                candidates.extend(cached_assets)
                snapshot_usage[collector.name] = "reused"
            else:
                pending.append((collector, config_hash))

        results = await asyncio.gather(
            *(collector.collect(self.settings.collector_limit) for collector, _ in pending),
            return_exceptions=True,
        )
        new_assets: list[Asset] = []
        for (collector, config_hash), result in zip(pending, results, strict=True):
            if isinstance(result, Exception):
                logger.warning("Collector %s failed: %s", collector.name, result)
                registry.record_result(collector.name, result)
                self.snapshots.save(
                    source_id=collector.name,
                    local_date=local_date,
                    config_hash=config_hash,
                    asset_ids=[],
                    error=result,
                )
                snapshot_usage[collector.name] = "failed"
                continue

            source_assets, created_assets = self._persist_items(result)
            candidates.extend(source_assets)
            new_assets.extend(created_assets)
            registry.record_result(collector.name)
            self.snapshots.save(
                source_id=collector.name,
                local_date=local_date,
                config_hash=config_hash,
                asset_ids=[asset.id for asset in source_assets],
            )
            snapshot_usage[collector.name] = "collected"

        self.assets.index_many(new_assets)
        ranked = sorted(candidates, key=self._importance, reverse=True)
        selected = ranked[:30]
        brief_markdown = self.llm.create_chinese_brief(
            [
                {
                    "id": asset.id,
                    "title": asset.title,
                    "source": asset.source,
                    "url": asset.url,
                    "occurred_at": asset.occurred_at.isoformat() if asset.occurred_at else None,
                    "metadata": asset.asset_metadata,
                }
                for asset in selected
            ]
        )
        now = datetime.now(timezone.utc)
        return self.assets.create(
            AssetCreate(
                type=AssetType.BRIEF,
                title=f"AI Morning Brief · {now:%Y-%m-%d}",
                content=brief_markdown,
                language="zh",
                tags=["ai", "daily-brief"],
                metadata={
                    "item_ids": [asset.id for asset in selected],
                    "candidate_count": len(candidates),
                    "source_snapshots": snapshot_usage,
                    "local_date": local_date.isoformat(),
                },
                occurred_at=now,
            )
        )

    def _persist_items(self, items: list[CollectedItem]) -> tuple[list[Asset], list[Asset]]:
        source_assets: list[Asset] = []
        new_assets: list[Asset] = []
        for item in items:
            existing = self.repository.find_by_source(item.source, item.source_id)
            if existing:
                source_assets.append(existing)
                continue
            asset_type = (
                AssetType.REPOSITORY
                if item.metadata.get("kind") == "repository"
                else AssetType.NEWS
            )
            created = self.assets.create(
                AssetCreate(
                    type=asset_type,
                    title=item.title,
                    content=item.content,
                    source=item.source,
                    source_id=item.source_id,
                    url=item.url,
                    metadata=item.metadata,
                    occurred_at=item.occurred_at,
                ),
                index=False,
            )
            source_assets.append(created)
            new_assets.append(created)
        return source_assets, new_assets

    def _snapshot_config_hash(self, source_id: str) -> str:
        source_config: dict[str, object] = {
            "version": 1,
            "source_id": source_id,
            "collector_limit": self.settings.collector_limit,
        }
        if source_id == "reddit":
            source_config.update(
                subreddits=self.settings.reddit_subreddits,
                max_age_hours=self.settings.reddit_max_age_hours,
            )
        elif source_id == "xiaohongshu":
            source_config.update(
                queries=self.settings.xiaohongshu_queries,
                site=self.settings.xiaohongshu_opencli_site,
            )
        serialized = json.dumps(source_config, ensure_ascii=True, sort_keys=True)
        return hashlib.sha256(serialized.encode()).hexdigest()

    @staticmethod
    def _importance(asset: Asset) -> float:
        metadata = asset.asset_metadata
        official_sources = {
            "openai_blog",
            "anthropic_blog",
            "google_deepmind_blog",
            "cursor_blog",
            "claude_code_blog",
            "codex_blog",
        }
        return (
            float(metadata.get("points", 0))
            + float(metadata.get("score", 0))
            + float(metadata.get("likes", 0))
            + float(metadata.get("comments", 0)) * 0.5
            + (25 if asset.source in official_sources else 0)
        )

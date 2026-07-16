from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.models.asset import AssetType
from app.models.source import SourceSnapshot, SourceSubscription
from app.db.base import Base
from app.services.asset_service import AssetService
from app.services.collectors import enabled_collectors
from app.services.collectors.base import CollectedItem
from app.services.brief_service import BriefService
from app.services.llm import LLMService


def test_importance_prefers_official_source():
    official = type("AssetLike", (), {"asset_metadata": {}, "source": "openai_blog"})()
    community = type("AssetLike", (), {"asset_metadata": {"score": 20}, "source": "reddit"})()
    assert BriefService._importance(official) > BriefService._importance(community)
    assert AssetType.BRIEF.value == "brief"


def test_only_requested_collectors_are_created():
    collectors = enabled_collectors(
        ["github_trending", "openai_blog"], Settings(openai_api_key=None)
    )
    assert {collector.name for collector in collectors} == {
        "github_trending",
        "openai_blog",
    }


def test_brief_markdown_fence_is_removed():
    assert LLMService.strip_markdown_fence("```markdown\n# Brief\n\nBody\n```") == "# Brief\n\nBody"


def test_brief_prefers_72_hours_then_falls_back_only_within_7_days():
    now = datetime(2026, 7, 16, 20, 0, tzinfo=timezone.utc)

    def candidate(name: str, age: timedelta, source: str | None = None):
        return type(
            "AssetLike",
            (),
            {
                "id": name,
                "source": source or name,
                "occurred_at": now - age,
                "created_at": now,
            },
        )()

    service = object.__new__(BriefService)
    service.settings = Settings(
        openai_api_key=None,
        scheduler_enabled=False,
        brief_fresh_hours=72,
        brief_max_age_days=7,
        brief_max_items=5,
    )
    service.preferences = type(
        "Ranker", (), {"rank": lambda self, items, limit: list(items)[:limit]}
    )()
    fresh = [candidate(f"fresh-{index}", timedelta(hours=24 + index)) for index in range(4)]
    fallback = [candidate(f"fallback-{index}", timedelta(days=4 + index)) for index in range(3)]
    expired = candidate("expired", timedelta(days=8))

    selected, stats = service._select_recent_candidates(
        [*fallback, expired, *fresh], now=now
    )

    assert [asset.id for asset in selected[:4]] == [asset.id for asset in fresh]
    assert expired not in selected
    assert len(selected) == 5
    assert stats == {"fresh": 4, "fallback": 3, "eligible": 7, "fallback_selected": 1}


def test_undated_daily_github_trending_is_allowed_but_undated_news_is_not():
    now = datetime(2026, 7, 16, 20, 0, tzinfo=timezone.utc)
    service = object.__new__(BriefService)
    service.settings = Settings(openai_api_key=None, scheduler_enabled=False)
    github = type(
        "AssetLike",
        (),
        {"source": "github_trending", "occurred_at": None, "created_at": now},
    )()
    undated_news = type(
        "AssetLike",
        (),
        {"source": "openai_blog", "occurred_at": None, "created_at": now},
    )()

    fresh, fallback = service._candidate_recency_tiers(
        [github, undated_news], now=now
    )

    assert fresh == [github]
    assert fallback == []


@pytest.mark.asyncio
async def test_same_day_source_snapshot_is_reused(monkeypatch, tmp_path):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    calls: dict[str, int] = {}

    class FakeCollector:
        def __init__(self, name):
            self.name = name

        async def collect(self, limit):
            calls[self.name] = calls.get(self.name, 0) + 1
            return [
                CollectedItem(
                    source=self.name,
                    source_id=f"{self.name}-release-1",
                    title=f"A current {self.name} release",
                    url=f"https://example.com/{self.name}-release-1",
                    occurred_at=datetime.now(timezone.utc),
                )
            ]

    monkeypatch.setattr(
        "app.services.brief_service.enabled_collectors",
        lambda sources, settings: [FakeCollector(source) for source in sources],
    )
    monkeypatch.setattr(AssetService, "index_many", lambda self, assets: None)
    settings = Settings(
        openai_api_key=None,
        news_sources=["openai_blog"],
        chroma_path=str(tmp_path / "chroma"),
        scheduler_enabled=False,
    )

    with Session(engine) as session:
        first = await BriefService(session, settings).generate()
        second = await BriefService(session, settings).generate()
        session.get(SourceSubscription, "anthropic_blog").enabled = True
        session.commit()
        third = await BriefService(session, settings).generate()
        snapshots = list(session.scalars(select(SourceSnapshot)))
        first_usage = first.asset_metadata["source_snapshots"]
        second_usage = second.asset_metadata["source_snapshots"]
        third_usage = third.asset_metadata["source_snapshots"]
        snapshot_counts = [snapshot.item_count for snapshot in snapshots]

    assert calls == {"openai_blog": 1, "anthropic_blog": 1}
    assert first_usage == {"openai_blog": "collected"}
    assert second_usage == {"openai_blog": "reused"}
    assert third_usage == {"openai_blog": "reused", "anthropic_blog": "collected"}
    assert len(snapshots) == 2
    assert snapshot_counts == [1, 1]


from app.core.config import Settings

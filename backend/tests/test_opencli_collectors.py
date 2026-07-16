from datetime import datetime, timedelta, timezone

from app.services.collectors.opencli import metric
from app.services.collectors.reddit import _is_recent


def test_social_metrics_are_parsed_without_llm_inference():
    assert metric("1.2万") == 12_000
    assert metric("2.5k") == 2_500
    assert metric("not-a-number") == 0


def test_reddit_daily_brief_rejects_stale_or_undated_posts():
    now = datetime(2026, 7, 14, 23, 0, tzinfo=timezone.utc)
    assert _is_recent(now - timedelta(hours=71), 72, now) is True
    assert _is_recent(now - timedelta(hours=73), 72, now) is False
    assert _is_recent(None, 72, now) is False

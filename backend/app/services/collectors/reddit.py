from datetime import datetime, timedelta, timezone

from app.core.config import Settings
from app.services.collectors.base import CollectedItem
from app.services.collectors.opencli import OpenCLIClient, metric


class RedditCollector:
    name = "reddit"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = OpenCLIClient(settings)

    async def collect(self, limit: int) -> list[CollectedItem]:
        subreddits = self.settings.reddit_subreddits
        if not subreddits:
            return []
        per_source = max(3, min(10, (limit + len(subreddits) - 1) // len(subreddits)))
        items: list[CollectedItem] = []
        errors: list[str] = []
        for subreddit in subreddits:
            try:
                result = await self.client.read(
                    "reddit", "subreddit", subreddit, "--sort", "hot", "--limit", str(per_source)
                )
            except Exception as error:
                errors.append(f"r/{subreddit}: {error}")
                continue
            for post in result:
                source_id = str(post.get("id") or "").strip()
                title = str(post.get("title") or "").strip()
                url = str(post.get("url") or "").strip()
                if not source_id or not title or not url:
                    continue
                created = _from_timestamp(post.get("created_utc"))
                if not _is_recent(created, self.settings.reddit_max_age_hours):
                    continue
                score = metric(post.get("score", post.get("upvotes")))
                comments = metric(post.get("comments"))
                items.append(
                    CollectedItem(
                        source=self.name,
                        source_id=source_id,
                        title=title,
                        url=url,
                        content=str(post.get("selftext") or "")[:6000],
                        occurred_at=created,
                        metadata={
                            "subreddit": str(post.get("subreddit") or subreddit),
                            "author": str(post.get("author") or ""),
                            "score": score,
                            "comments": comments,
                            "acquisition": "opencli_browser_session",
                        },
                    )
                )
        if not items and errors:
            raise RuntimeError("; ".join(errors))
        return sorted(
            items,
            key=lambda item: metric(item.metadata.get("score")) + metric(item.metadata.get("comments")),
            reverse=True,
        )[:limit]


def _from_timestamp(value: object) -> datetime | None:
    try:
        return datetime.fromtimestamp(float(str(value)), tz=timezone.utc)
    except (TypeError, ValueError, OSError):
        return None


def _is_recent(
    created: datetime | None,
    max_age_hours: int,
    now: datetime | None = None,
) -> bool:
    if created is None:
        return False
    reference = now or datetime.now(timezone.utc)
    normalized = created if created.tzinfo else created.replace(tzinfo=timezone.utc)
    return normalized >= reference - timedelta(hours=max_age_hours)

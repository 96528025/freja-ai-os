import asyncio
from calendar import timegm
from datetime import datetime, timezone

import feedparser

from app.services.collectors.base import CollectedItem


class RSSCollector:
    def __init__(self, name: str, publisher: str, url: str) -> None:
        self.name = name
        self.publisher = publisher
        self.url = url

    async def collect(self, limit: int) -> list[CollectedItem]:
        feed = await asyncio.to_thread(feedparser.parse, self.url)
        items = []
        for entry in feed.entries[:limit]:
            published = entry.get("published_parsed") or entry.get("updated_parsed")
            items.append(
                CollectedItem(
                    source=self.name,
                    source_id=entry.get("id") or entry.link,
                    title=entry.title,
                    url=entry.link,
                    content=entry.get("summary", "")[:6000],
                    occurred_at=(datetime.fromtimestamp(timegm(published), tz=timezone.utc) if published else None),
                    metadata={"publisher": self.publisher},
                )
            )
        return items

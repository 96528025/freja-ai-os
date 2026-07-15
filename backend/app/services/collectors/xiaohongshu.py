import re
from datetime import datetime, timezone

from app.core.config import Settings
from app.services.collectors.base import CollectedItem
from app.services.collectors.opencli import OpenCLIClient, metric


class XiaohongshuCollector:
    name = "xiaohongshu"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = OpenCLIClient(settings)

    async def collect(self, limit: int) -> list[CollectedItem]:
        queries = self.settings.xiaohongshu_queries
        if not queries:
            return []
        per_query = max(5, min(12, (limit + len(queries) - 1) // len(queries)))
        site = self.settings.xiaohongshu_opencli_site
        by_id: dict[str, CollectedItem] = {}
        errors: list[str] = []
        for query in queries:
            try:
                result = await self.client.read(site, "search", query, "--limit", str(per_query))
            except Exception as error:
                errors.append(f"{query}: {error}")
                continue
            for note in result:
                title = str(note.get("title") or "").strip()
                url = str(note.get("url") or "").strip()
                if not title or not url:
                    continue
                source_id = _note_id(url)
                likes = metric(note.get("likes"))
                by_id[source_id] = CollectedItem(
                    source=self.name,
                    source_id=source_id,
                    title=title,
                    url=url,
                    occurred_at=_published_at(note.get("published_at")),
                    metadata={
                        "author": str(note.get("author") or ""),
                        "likes": likes,
                        "query": query,
                        "platform_site": site,
                        "acquisition": "opencli_browser_session",
                    },
                )
        if not by_id and errors:
            raise RuntimeError("; ".join(errors))
        return sorted(by_id.values(), key=lambda item: metric(item.metadata.get("likes")), reverse=True)[:limit]


def _note_id(url: str) -> str:
    match = re.search(r"/(?:search_result|explore)/([a-zA-Z0-9]+)", url)
    return match.group(1) if match else url.split("?", 1)[0]


def _published_at(value: object) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return datetime.strptime(raw, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return None

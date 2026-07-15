import re

import httpx

from app.services.collectors.base import CollectedItem


class GitHubTrendingCollector:
    name = "github_trending"

    async def collect(self, limit: int) -> list[CollectedItem]:
        headers = {"User-Agent": "freja-personal-ai-os/0.1"}
        async with httpx.AsyncClient(timeout=15, headers=headers, follow_redirects=True) as client:
            response = await client.get("https://github.com/trending?since=daily")
            response.raise_for_status()
        repositories = re.findall(r'<h2[^>]*class="[^"]*h3[^"]*"[^>]*>\s*<a[^>]*href="/([^"?#]+)"', response.text)
        items = []
        for repo in repositories[:limit]:
            normalized = re.sub(r"\s+", "", repo)
            items.append(
                CollectedItem(
                    source=self.name,
                    source_id=normalized.lower(),
                    title=normalized,
                    url=f"https://github.com/{normalized}",
                    metadata={"kind": "repository", "period": "daily"},
                )
            )
        return items


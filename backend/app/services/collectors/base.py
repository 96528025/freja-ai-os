from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol


@dataclass(slots=True)
class CollectedItem:
    source: str
    source_id: str
    title: str
    url: str
    content: str = ""
    occurred_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class Collector(Protocol):
    name: str

    async def collect(self, limit: int) -> list[CollectedItem]: ...


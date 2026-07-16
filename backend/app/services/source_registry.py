from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.source import SourceSubscription
from app.services.collectors.opencli import OpenCLIClient


@dataclass(frozen=True, slots=True)
class SourceDefinition:
    id: str
    name: str
    description: str
    kind: str
    acquisition: str
    auth_mode: str
    availability: str


SOURCE_DEFINITIONS = [
    SourceDefinition("reddit", "Reddit", "AI community posts and discussions", "community", "OpenCLI · Chrome session", "browser_session", "needs_auth"),
    SourceDefinition("x", "Twitter / X", "Accounts, lists, and AI conversations", "community", "OpenCLI · Chrome session", "browser_session", "planned"),
    SourceDefinition("linkedin", "LinkedIn", "Professional posts and company updates", "community", "OpenCLI · Chrome session", "browser_session", "planned"),
    SourceDefinition("openai_blog", "OpenAI Blog", "Official OpenAI product and research updates", "official", "RSS", "none", "available"),
    SourceDefinition("anthropic_blog", "Anthropic Blog", "Official Anthropic news and research", "official", "RSS", "none", "available"),
    SourceDefinition("google_deepmind_blog", "Google DeepMind Blog", "Official DeepMind research updates", "official", "RSS", "none", "available"),
    SourceDefinition("cursor_blog", "Cursor Changelog", "Official Cursor product releases", "official", "RSS", "none", "available"),
    SourceDefinition("claude_code_blog", "Claude Code", "Official Claude Code releases", "official", "GitHub Releases Atom", "none", "available"),
    SourceDefinition("codex_blog", "Codex", "Official OpenAI Codex releases", "official", "GitHub Releases Atom", "none", "available"),
    SourceDefinition("github_trending", "GitHub Trending", "Daily trending repositories", "code", "Public HTML", "none", "available"),
]
SOURCE_MAP = {definition.id: definition for definition in SOURCE_DEFINITIONS}


class SourceRegistry:
    def __init__(self, session: Session, settings: Settings) -> None:
        self.session = session
        self.settings = settings

    def ensure_defaults(self) -> None:
        opencli_ready = self.opencli_ready
        subscriptions = {
            item.id: item for item in self.session.scalars(select(SourceSubscription))
        }
        for obsolete_id in set(subscriptions) - set(SOURCE_MAP):
            self.session.delete(subscriptions.pop(obsolete_id))
        existing = set(subscriptions)
        for definition in SOURCE_DEFINITIONS:
            if definition.id not in existing:
                self.session.add(
                    SourceSubscription(
                        id=definition.id,
                        enabled=(
                            definition.id in self.settings.news_sources
                            and (definition.id not in self.opencli_sources or opencli_ready)
                        ),
                        health="needs_auth" if definition.id in self.opencli_sources and not opencli_ready else "unknown",
                    )
                )
        for source_id in self.opencli_sources:
            subscription = subscriptions.get(source_id)
            if subscription and not opencli_ready:
                subscription.enabled = False
                subscription.health = "needs_auth"
            elif subscription and subscription.health == "needs_auth":
                subscription.health = "unknown"
        self.session.commit()

    @property
    def opencli_sources(self) -> set[str]:
        return {"reddit"}

    @property
    def opencli_ready(self) -> bool:
        return OpenCLIClient(self.settings).is_ready()

    def list(self) -> list[dict[str, object]]:
        self.ensure_defaults()
        subscriptions = {
            item.id: item for item in self.session.scalars(select(SourceSubscription))
        }
        opencli_ready = self.opencli_ready
        result = []
        for definition in SOURCE_DEFINITIONS:
            subscription = subscriptions[definition.id]
            availability = definition.availability
            if definition.id in self.opencli_sources and opencli_ready:
                availability = "available"
            result.append(
                {
                    **asdict(definition),
                    "availability": availability,
                    "enabled": subscription.enabled,
                    "health": subscription.health,
                    "last_error": subscription.last_error,
                    "last_success_at": subscription.last_success_at,
                }
            )
        return result

    def enabled_ids(self) -> list[str]:
        self.ensure_defaults()
        enabled = list(
            self.session.scalars(
                select(SourceSubscription.id).where(SourceSubscription.enabled.is_(True))
            )
        )
        return [
            source_id
            for source_id in enabled
            if source_id in SOURCE_MAP
            and SOURCE_MAP[source_id].availability != "planned"
            and (source_id not in self.opencli_sources or self.opencli_ready)
        ]

    def update(self, source_id: str, enabled: bool) -> None:
        self.ensure_defaults()
        definition = SOURCE_MAP[source_id]
        if enabled and definition.availability == "planned":
            raise ValueError("This source connector is not implemented yet")
        if enabled and source_id in self.opencli_sources and not self.opencli_ready:
            raise ValueError("OpenCLI requires its Chrome extension and a signed-in browser session")
        subscription = self.session.get(SourceSubscription, source_id)
        subscription.enabled = enabled
        if enabled and subscription.health == "needs_auth":
            subscription.health = "unknown"
        subscription.updated_at = datetime.now(timezone.utc)
        self.session.commit()

    def update_all(self, enabled: bool) -> None:
        self.ensure_defaults()
        opencli_ready = self.opencli_ready
        now = datetime.now(timezone.utc)
        subscriptions = {
            item.id: item for item in self.session.scalars(select(SourceSubscription))
        }
        for definition in SOURCE_DEFINITIONS:
            can_enable = (
                definition.availability != "planned"
                and (definition.id not in self.opencli_sources or opencli_ready)
            )
            subscription = subscriptions[definition.id]
            subscription.enabled = enabled and can_enable
            subscription.updated_at = now
        self.session.commit()

    def record_result(self, source_id: str, error: Exception | None = None) -> None:
        subscription = self.session.get(SourceSubscription, source_id)
        if not subscription:
            return
        if error:
            subscription.health = "error"
            subscription.last_error = str(error)[:1000]
        else:
            subscription.health = "healthy"
            subscription.last_error = None
            subscription.last_success_at = datetime.now(timezone.utc)
        self.session.commit()

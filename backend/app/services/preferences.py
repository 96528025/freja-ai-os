import math
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.models.feedback import FeedbackSignal
from app.repositories.asset_repository import AssetRepository
from app.repositories.feedback_repository import FeedbackRepository


TOPICS: dict[str, tuple[str, ...]] = {
    "模型发布": ("model", "gpt", "claude", "gemini", "llama", "模型", "benchmark"),
    "AI Agent": ("agent", "agents", "agentic", "智能体", "multi-agent"),
    "AI 编程": ("coding", "code", "codex", "cursor", "developer", "编程", "代码"),
    "开源项目": ("open source", "github", "repository", "开源", "repo"),
    "研究论文": ("research", "paper", "study", "arxiv", "研究", "论文"),
    "产品应用": ("launch", "product", "app", "feature", "产品", "应用", "发布"),
    "商业市场": ("funding", "revenue", "startup", "business", "融资", "商业", "市场"),
    "政策安全": ("policy", "regulation", "safety", "security", "政策", "监管", "安全"),
    "芯片算力": ("chip", "gpu", "nvidia", "compute", "芯片", "算力"),
}

MARKETING_TERMS = ("customer story", "case study", "partner", "partnership", "客户案例", "合作")
BASIC_TERMS = ("beginner", "introduction", "getting started", "101", "入门", "新手")
STOP_WORDS = {
    "about", "after", "from", "have", "into", "more", "new", "that", "their", "this",
    "using", "with", "your", "openai", "anthropic", "google", "official", "release",
}


def _text(asset: Asset) -> str:
    return " ".join(part for part in (asset.title, asset.summary, asset.content[:1_000]) if part).lower()


def topics_for(asset: Asset) -> list[str]:
    text = _text(asset)
    return [topic for topic, terms in TOPICS.items() if any(term in text for term in terms)]


def terms_for(asset: Asset) -> set[str]:
    words = set(re.findall(r"[a-z][a-z0-9.+-]{2,}", _text(asset)))
    return {word for word in words if word not in STOP_WORDS and not word.isdigit()}


@dataclass
class PreferenceProfile:
    topic_weights: Counter[str] = field(default_factory=Counter)
    source_weights: Counter[str] = field(default_factory=Counter)
    term_weights: Counter[str] = field(default_factory=Counter)
    quality_weights: Counter[str] = field(default_factory=Counter)
    disliked_asset_ids: set[str] = field(default_factory=set)
    interested: int = 0
    not_interested: int = 0

    def summary(self) -> dict[str, object]:
        preferred = [name for name, weight in self.topic_weights.most_common() if weight > 0][:5]
        avoided = [
            name
            for name, weight in sorted(self.topic_weights.items(), key=lambda item: item[1])
            if weight < 0
        ][:5]
        return {
            "total_item_feedback": self.interested + self.not_interested,
            "interested": self.interested,
            "not_interested": self.not_interested,
            "preferred_topics": preferred,
            "avoided_topics": avoided,
        }


class PreferenceService:
    def __init__(self, session: Session) -> None:
        self.assets = AssetRepository(session)
        self.feedback = FeedbackRepository(session)

    def build_profile(self) -> PreferenceProfile:
        profile = PreferenceProfile()
        for feedback in self.feedback.all_item_feedback():
            if not feedback.asset_id or not feedback.signal:
                continue
            asset = self.assets.get(feedback.asset_id)
            if asset is None:
                continue
            positive = feedback.signal == FeedbackSignal.INTERESTED
            direction = 1.0 if positive else -1.5
            if positive:
                profile.interested += 1
            else:
                profile.not_interested += 1
                profile.disliked_asset_ids.add(asset.id)

            topic_factor = 2.0 if feedback.reason == "not_relevant" else 1.0
            source_factor = 2.0 if feedback.reason == "source_not_useful" else 1.0
            term_factor = 1.75 if feedback.reason == "repetitive" else 1.0
            for topic in topics_for(asset):
                profile.topic_weights[topic] += direction * topic_factor
            if asset.source:
                profile.source_weights[asset.source] += direction * source_factor
            for term in terms_for(asset):
                profile.term_weights[term] += direction * term_factor
            if not positive and feedback.reason in {"too_marketing", "too_basic"}:
                profile.quality_weights[feedback.reason] -= 1.0
        return profile

    def score(self, asset: Asset, profile: PreferenceProfile) -> float:
        metadata = asset.asset_metadata or {}
        engagement = sum(
            self._number(metadata.get(name)) * multiplier
            for name, multiplier in (("points", 1), ("score", 1), ("likes", 1), ("comments", 0.5))
        )
        base = math.log1p(max(0.0, engagement)) * 4
        official = asset.source in {
            "openai_blog", "anthropic_blog", "google_deepmind_blog", "cursor_blog",
            "claude_code_blog", "codex_blog",
        }
        credibility = 7.0 if official else 2.0
        freshness = self._freshness(asset)
        topic_score = sum(profile.topic_weights[topic] for topic in topics_for(asset)) * 4
        source_score = profile.source_weights[asset.source] * 3 if asset.source else 0.0
        term_score = sum(profile.term_weights[term] for term in terms_for(asset)) * 1.5
        term_score = max(-24.0, min(18.0, term_score))
        text = _text(asset)
        quality_score = 0.0
        if any(term in text for term in MARKETING_TERMS):
            quality_score += profile.quality_weights["too_marketing"] * 8
        if any(term in text for term in BASIC_TERMS):
            quality_score += profile.quality_weights["too_basic"] * 8
        return base + credibility + freshness + topic_score + source_score + term_score + quality_score

    def rank(self, candidates: list[Asset], *, limit: int = 12) -> list[Asset]:
        profile = self.build_profile()
        ranked = sorted(candidates, key=lambda asset: self.score(asset, profile), reverse=True)
        selected: list[Asset] = []
        source_counts: Counter[str] = Counter()
        seen_ids: set[str] = set()
        for asset in ranked:
            if asset.id in seen_ids or asset.id in profile.disliked_asset_ids:
                continue
            source = asset.source or "unknown"
            if source_counts[source] >= 3:
                continue
            selected.append(asset)
            seen_ids.add(asset.id)
            source_counts[source] += 1
            if len(selected) >= limit:
                break
        return selected

    @staticmethod
    def _number(value: object) -> float:
        try:
            return float(value or 0)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _freshness(asset: Asset) -> float:
        occurred_at = asset.occurred_at or asset.created_at
        if occurred_at.tzinfo is None:
            occurred_at = occurred_at.replace(tzinfo=timezone.utc)
        age_days = max(0.0, (datetime.now(timezone.utc) - occurred_at).total_seconds() / 86_400)
        return max(0.0, 12.0 - age_days * 1.5)

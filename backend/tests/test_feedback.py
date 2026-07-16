from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models.asset import AssetType
from app.models.feedback import FeedbackSignal
from app.repositories.asset_repository import AssetRepository
from app.repositories.feedback_repository import FeedbackRepository
from app.schemas.asset import AssetCreate
from app.services.preferences import PreferenceService


def test_feedback_api_records_item_signal_and_satisfaction(client):
    news = client.post(
        "/api/v1/assets",
        json={
            "type": "news",
            "title": "A coding agent release",
            "source": "openai_blog",
            "source_id": "feedback-api-news",
        },
    ).json()
    brief = client.post(
        "/api/v1/assets",
        json={
            "type": "brief",
            "title": "Test brief",
            "metadata": {"item_ids": [news["id"]]},
        },
    ).json()

    item_response = client.put(
        f"/api/v1/briefs/{brief['id']}/items/{news['id']}/feedback",
        json={"signal": "not_interested", "reason": "too_basic"},
    )
    satisfaction_response = client.put(
        f"/api/v1/briefs/{brief['id']}/feedback", json={"satisfaction": 2}
    )
    state = client.get(f"/api/v1/briefs/{brief['id']}/feedback").json()
    profile = client.get("/api/v1/briefs/preferences/profile").json()

    assert item_response.status_code == 200
    assert satisfaction_response.status_code == 200
    assert state["items"][0]["feedback"]["reason"] == "too_basic"
    assert state["satisfaction"]["satisfaction"] == 2
    assert profile["not_interested"] == 1
    assert profile["average_satisfaction"] == 2.0


def test_negative_feedback_lowers_similar_news_and_excludes_exact_item():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    now = datetime.now(timezone.utc)

    with Session(engine) as session:
        assets = AssetRepository(session)
        disliked = assets.create(
            AssetCreate(
                type=AssetType.NEWS,
                title="Beginner coding agent tutorial",
                source="example_blog",
                source_id="disliked",
                occurred_at=now,
            )
        )
        similar = assets.create(
            AssetCreate(
                type=AssetType.NEWS,
                title="Another beginner coding agent tutorial",
                source="example_blog",
                source_id="similar",
                occurred_at=now,
            )
        )
        relevant = assets.create(
            AssetCreate(
                type=AssetType.NEWS,
                title="New AI chip architecture reaches production",
                source="research_lab",
                source_id="relevant",
                occurred_at=now,
            )
        )
        FeedbackRepository(session).upsert_item(
            brief_id=assets.create(
                AssetCreate(
                    type=AssetType.BRIEF,
                    title="Previous brief",
                    metadata={"item_ids": [disliked.id]},
                )
            ).id,
            asset_id=disliked.id,
            signal=FeedbackSignal.NOT_INTERESTED,
            reason="too_basic",
        )
        preferences = PreferenceService(session)
        profile = preferences.build_profile()
        ranked = preferences.rank([disliked, similar, relevant])

        assert disliked not in ranked
        assert preferences.score(similar, profile) < preferences.score(relevant, profile)

from sqlalchemy.orm import Session

from app.models.asset import Asset, AssetType
from app.repositories.asset_repository import AssetRepository
from app.repositories.feedback_repository import FeedbackRepository
from app.schemas.feedback import BriefFeedbackState, BriefItemRead, PreferenceProfileRead
from app.services.preferences import PreferenceService


class FeedbackService:
    def __init__(self, session: Session) -> None:
        self.assets = AssetRepository(session)
        self.feedback = FeedbackRepository(session)
        self.preferences = PreferenceService(session)

    def get_brief(self, brief_id: str) -> Asset:
        brief = self.assets.get(brief_id)
        if brief is None or brief.type != AssetType.BRIEF:
            raise LookupError("Brief not found")
        return brief

    def state(self, brief_id: str) -> BriefFeedbackState:
        brief = self.get_brief(brief_id)
        feedback = self.feedback.for_brief(brief_id)
        by_asset = {item.asset_id: item for item in feedback if item.asset_id}
        satisfaction = next((item for item in feedback if item.asset_id is None), None)
        items = []
        for asset_id in brief.asset_metadata.get("item_ids", []):
            asset = self.assets.get(asset_id)
            if asset is not None:
                items.append(BriefItemRead(asset=asset, feedback=by_asset.get(asset_id)))
        return BriefFeedbackState(satisfaction=satisfaction, items=items)

    def assert_brief_item(self, brief_id: str, asset_id: str) -> None:
        brief = self.get_brief(brief_id)
        if asset_id not in brief.asset_metadata.get("item_ids", []):
            raise LookupError("News item is not part of this brief")

    def profile(self) -> PreferenceProfileRead:
        summary = self.preferences.build_profile().summary()
        satisfaction = [item.satisfaction for item in self.feedback.all_satisfaction()]
        average = round(sum(satisfaction) / len(satisfaction), 1) if satisfaction else None
        return PreferenceProfileRead(**summary, average_satisfaction=average)

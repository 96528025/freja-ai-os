from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.asset import Asset, AssetType
from app.repositories.asset_repository import AssetRepository
from app.schemas.asset import AssetCreate, IdeaCreate
from app.services.llm import LLMService
from app.services.vector_store import VectorStore


class AssetService:
    def __init__(self, session: Session, settings: Settings) -> None:
        self.session = session
        self.repository = AssetRepository(session)
        self.llm = LLMService(settings)
        self.vectors = VectorStore(settings)

    def create(self, data: AssetCreate, *, index: bool = True) -> Asset:
        asset = self.repository.create(data)
        if index:
            embedding = self.llm.embedding(f"{asset.title}\n{asset.content}")
            self.vectors.index(asset, embedding)
            self.session.commit()
        return asset

    def index_many(self, assets: list[Asset]) -> None:
        texts = [f"{asset.title}\n{asset.content}" for asset in assets]
        self.vectors.index_many(assets, self.llm.embeddings(texts))
        self.session.commit()

    def capture_idea(self, data: IdeaCreate) -> Asset:
        classification = self.llm.classify_idea(data.content)
        return self.create(
            AssetCreate(
                type=AssetType.IDEA,
                title=data.title or str(classification["title"]),
                content=data.content,
                language="zh" if any("\u4e00" <= char <= "\u9fff" for char in data.content) else "en",
                tags=list(classification.get("tags", ["idea"])),
                metadata={"category": classification.get("category", "general"), "captured_via": "inbox"},
            )
        )

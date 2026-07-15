import logging

from app.core.config import Settings
from app.models.asset import Asset
from app.services.embeddings import deterministic_embedding

logger = logging.getLogger(__name__)


class VectorStore:
    """Chroma adapter. Indexing is optional so Freja remains usable without external services."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._collection = None

    def _get_collection(self):
        if self._collection is None:
            import chromadb

            client = chromadb.PersistentClient(path=self.settings.chroma_path)
            self._collection = client.get_or_create_collection(
                "freja_assets", metadata={"hnsw:space": "cosine"}
            )
        return self._collection

    def index(self, asset: Asset, embedding: list[float] | None = None) -> None:
        self.index_many([asset], [embedding] if embedding else None)

    def index_many(
        self, assets: list[Asset], embeddings: list[list[float]] | None = None
    ) -> None:
        records = [
            (
                asset,
                "\n".join(
                    part for part in [asset.title, asset.summary, asset.content] if part
                )[:50_000],
            )
            for asset in assets
        ]
        records = [(asset, document) for asset, document in records if document.strip()]
        if not records:
            return
        payload = {
            "ids": [asset.id for asset, _ in records],
            "documents": [document for _, document in records],
            "metadatas": [
                {"type": asset.type.value, "source": asset.source or "local"}
                for asset, _ in records
            ],
        }
        if embeddings:
            payload["embeddings"] = embeddings
        try:
            self._get_collection().upsert(**payload)
            for asset, _ in records:
                asset.embedding_id = asset.id
        except Exception:
            logger.exception("Vector indexing failed for %s assets", len(records))

    def search(
        self, query: str, limit: int = 10, embedding: list[float] | None = None
    ) -> list[str]:
        try:
            if embedding is None and self.settings.openai_api_key:
                logger.warning("OpenAI-backed vector search requires a query embedding")
                return []
            query_embedding = embedding or deterministic_embedding(query)
            result = self._get_collection().query(
                query_embeddings=[query_embedding], n_results=limit
            )
            return result.get("ids", [[]])[0]
        except Exception:
            logger.exception("Vector search failed; caller should use lexical fallback")
            return []

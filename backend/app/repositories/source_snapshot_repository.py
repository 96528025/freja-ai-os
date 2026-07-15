from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.source import SourceSnapshot


class SourceSnapshotRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def find_success(
        self, source_id: str, local_date: date, config_hash: str
    ) -> SourceSnapshot | None:
        return self.session.scalar(
            select(SourceSnapshot).where(
                SourceSnapshot.source_id == source_id,
                SourceSnapshot.local_date == local_date,
                SourceSnapshot.config_hash == config_hash,
                SourceSnapshot.status == "success",
            )
        )

    def save(
        self,
        *,
        source_id: str,
        local_date: date,
        config_hash: str,
        asset_ids: list[str],
        error: Exception | None = None,
    ) -> SourceSnapshot:
        snapshot = self.session.scalar(
            select(SourceSnapshot).where(
                SourceSnapshot.source_id == source_id,
                SourceSnapshot.local_date == local_date,
                SourceSnapshot.config_hash == config_hash,
            )
        )
        if snapshot is None:
            snapshot = SourceSnapshot(
                source_id=source_id,
                local_date=local_date,
                config_hash=config_hash,
            )
            self.session.add(snapshot)
        elif error and snapshot.status == "success":
            return snapshot
        snapshot.status = "error" if error else "success"
        snapshot.asset_ids = asset_ids
        snapshot.item_count = len(asset_ids)
        snapshot.error = str(error)[:1000] if error else None
        snapshot.collected_at = datetime.now(timezone.utc)
        self.session.commit()
        self.session.refresh(snapshot)
        return snapshot

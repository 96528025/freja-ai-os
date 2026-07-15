from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.asset import Asset, AssetType
from app.schemas.asset import AssetCreate


class AssetRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, data: AssetCreate) -> Asset:
        asset = Asset(**data.model_dump(exclude={"metadata"}), asset_metadata=data.metadata)
        self.session.add(asset)
        self.session.commit()
        self.session.refresh(asset)
        return asset

    def get(self, asset_id: str) -> Asset | None:
        return self.session.get(Asset, asset_id)

    def find_by_source(self, source: str, source_id: str) -> Asset | None:
        return self.session.scalar(
            select(Asset).where(Asset.source == source, Asset.source_id == source_id)
        )

    def list(
        self,
        *,
        asset_type: AssetType | None = None,
        query: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Asset], int]:
        statement = select(Asset)
        count_statement = select(func.count(Asset.id))
        filters = []
        if asset_type:
            filters.append(Asset.type == asset_type)
        if query:
            pattern = f"%{query}%"
            filters.append(or_(Asset.title.ilike(pattern), Asset.content.ilike(pattern), Asset.summary.ilike(pattern)))
        if filters:
            statement = statement.where(*filters)
            count_statement = count_statement.where(*filters)
        items = list(
            self.session.scalars(
                statement.order_by(Asset.created_at.desc()).limit(limit).offset(offset)
            )
        )
        return items, self.session.scalar(count_statement) or 0

    def recent(self, asset_type: AssetType, limit: int = 5) -> list[Asset]:
        return list(
            self.session.scalars(
                select(Asset)
                .where(Asset.type == asset_type)
                .order_by(Asset.created_at.desc())
                .limit(limit)
            )
        )

    def latest_brief_today(self, timezone_name: str = "UTC") -> Asset | None:
        local_now = datetime.now(ZoneInfo(timezone_name))
        return self.latest_brief_on(local_now.date(), timezone_name)

    def latest_brief_on(self, local_date: date, timezone_name: str) -> Asset | None:
        zone = ZoneInfo(timezone_name)
        start = datetime.combine(local_date, time.min, tzinfo=zone).astimezone(timezone.utc)
        end = datetime.combine(local_date, time.max, tzinfo=zone).astimezone(timezone.utc)
        return self.session.scalar(
            select(Asset)
            .where(
                Asset.type == AssetType.BRIEF,
                Asset.created_at >= start,
                Asset.created_at <= end,
            )
            .order_by(Asset.created_at.desc())
            .limit(1)
        )

    def counts(self) -> dict[AssetType, int]:
        rows = self.session.execute(select(Asset.type, func.count(Asset.id)).group_by(Asset.type))
        return {asset_type: count for asset_type, count in rows}

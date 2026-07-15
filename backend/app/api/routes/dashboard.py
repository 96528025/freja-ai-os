from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.models.asset import AssetType
from app.repositories.asset_repository import AssetRepository
from app.schemas.asset import DashboardRead, DashboardStats

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardRead)
def get_dashboard(
    session: Session = Depends(get_db), settings: Settings = Depends(get_settings)
):
    repository = AssetRepository(session)
    counts = repository.counts()
    return DashboardRead(
        today_brief=repository.latest_brief_today(settings.timezone),
        latest_ideas=repository.recent(AssetType.IDEA, 4),
        recent_research=repository.recent(AssetType.RESEARCH, 3),
        upcoming_tasks=repository.recent(AssetType.TASK, 4),
        stats=DashboardStats(
            total_assets=sum(counts.values()),
            ideas=counts.get(AssetType.IDEA, 0),
            news=counts.get(AssetType.NEWS, 0) + counts.get(AssetType.BRIEF, 0),
            research=counts.get(AssetType.RESEARCH, 0),
            tasks=counts.get(AssetType.TASK, 0),
        ),
    )

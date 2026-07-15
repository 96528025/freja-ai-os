from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import SessionLocal, get_db
from app.repositories.asset_repository import AssetRepository
from app.schemas.asset import AssetRead
from app.services.brief_service import BriefGenerationInProgress, BriefService

router = APIRouter(prefix="/briefs", tags=["briefs"])


@router.get("/today", response_model=AssetRead | None)
def today_brief(
    session: Session = Depends(get_db), settings: Settings = Depends(get_settings)
):
    return AssetRepository(session).latest_brief_today(settings.timezone)


async def _generate(settings: Settings, force_refresh: bool) -> None:
    with SessionLocal() as session:
        try:
            await BriefService(session, settings).generate(force_refresh=force_refresh)
        except BriefGenerationInProgress:
            return


@router.post("/generate", status_code=status.HTTP_202_ACCEPTED)
def generate_brief(
    background_tasks: BackgroundTasks,
    force_refresh: bool = False,
    settings: Settings = Depends(get_settings),
):
    background_tasks.add_task(_generate, settings, force_refresh)
    return {
        "status": "accepted",
        "message": "Brief generation started",
        "force_refresh": force_refresh,
    }

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import SessionLocal, get_db
from app.repositories.asset_repository import AssetRepository
from app.schemas.asset import AssetRead
from app.schemas.feedback import (
    BriefFeedbackState,
    BriefFeedbackWrite,
    FeedbackRead,
    ItemFeedbackWrite,
    PreferenceProfileRead,
)
from app.services.brief_service import BriefGenerationInProgress, BriefService
from app.services.feedback_service import FeedbackService

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


@router.get("/preferences/profile", response_model=PreferenceProfileRead)
def preference_profile(session: Session = Depends(get_db)):
    return FeedbackService(session).profile()


@router.get("/{brief_id}/feedback", response_model=BriefFeedbackState)
def brief_feedback(brief_id: str, session: Session = Depends(get_db)):
    try:
        return FeedbackService(session).state(brief_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.put("/{brief_id}/feedback", response_model=FeedbackRead)
def rate_brief(
    brief_id: str, payload: BriefFeedbackWrite, session: Session = Depends(get_db)
):
    service = FeedbackService(session)
    try:
        service.get_brief(brief_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return service.feedback.upsert_satisfaction(
        brief_id=brief_id, satisfaction=payload.satisfaction, note=payload.note
    )


@router.put("/{brief_id}/items/{asset_id}/feedback", response_model=FeedbackRead | None)
def rate_brief_item(
    brief_id: str,
    asset_id: str,
    payload: ItemFeedbackWrite,
    session: Session = Depends(get_db),
):
    service = FeedbackService(session)
    try:
        service.assert_brief_item(brief_id, asset_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    if payload.signal is None:
        service.feedback.clear_item(brief_id=brief_id, asset_id=asset_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return service.feedback.upsert_item(
        brief_id=brief_id,
        asset_id=asset_id,
        signal=payload.signal,
        reason=payload.reason,
    )

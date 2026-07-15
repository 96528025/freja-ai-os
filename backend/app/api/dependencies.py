from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.services.asset_service import AssetService


def get_asset_service(
    session: Session = Depends(get_db), settings: Settings = Depends(get_settings)
) -> AssetService:
    return AssetService(session, settings)


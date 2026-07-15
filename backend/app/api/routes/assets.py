from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_asset_service
from app.db.session import get_db
from app.models.asset import AssetType
from app.repositories.asset_repository import AssetRepository
from app.schemas.asset import AssetCreate, AssetList, AssetRead, IdeaCreate
from app.services.asset_service import AssetService

router = APIRouter(prefix="/assets", tags=["assets"])


@router.post("", response_model=AssetRead, status_code=201)
def create_asset(
    payload: AssetCreate, service: AssetService = Depends(get_asset_service)
):
    return service.create(payload)


@router.post("/ideas", response_model=AssetRead, status_code=201)
def capture_idea(payload: IdeaCreate, service: AssetService = Depends(get_asset_service)):
    return service.capture_idea(payload)


@router.get("", response_model=AssetList)
def list_assets(
    asset_type: AssetType | None = Query(default=None, alias="type"),
    query: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_db),
):
    items, total = AssetRepository(session).list(
        asset_type=asset_type, query=query, limit=limit, offset=offset
    )
    return AssetList(items=items, total=total)


@router.get("/{asset_id}", response_model=AssetRead)
def get_asset(asset_id: str, session: Session = Depends(get_db)):
    asset = AssetRepository(session).get(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.schemas.source import SourceDefinitionRead, SourceUpdate
from app.services.source_registry import SOURCE_MAP, SourceRegistry

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("", response_model=list[SourceDefinitionRead])
def list_sources(
    session: Session = Depends(get_db), settings: Settings = Depends(get_settings)
):
    return SourceRegistry(session, settings).list()


@router.patch("", response_model=list[SourceDefinitionRead])
def update_all_sources(
    payload: SourceUpdate,
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    registry = SourceRegistry(session, settings)
    registry.update_all(payload.enabled)
    return registry.list()


@router.patch("/{source_id}", response_model=list[SourceDefinitionRead])
def update_source(
    source_id: str,
    payload: SourceUpdate,
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    if source_id not in SOURCE_MAP:
        raise HTTPException(status_code=404, detail="Source not found")
    registry = SourceRegistry(session, settings)
    try:
        registry.update(source_id, payload.enabled)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return registry.list()

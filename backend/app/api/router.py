from fastapi import APIRouter

from app.api.routes import assets, briefs, dashboard, sources

api_router = APIRouter()
api_router.include_router(assets.router)
api_router.include_router(briefs.router)
api_router.include_router(dashboard.router)
api_router.include_router(sources.router)

from fastapi import APIRouter
from backend.api import health, citations, ui
api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(citations.router, prefix="/api", tags=["citations"])
api_router.include_router(ui.router, tags=["ui"])

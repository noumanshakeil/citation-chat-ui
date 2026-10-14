from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db import get_db
from backend.services import citations as svc

class SourceIn(BaseModel):
    title: str = Field(min_length=2)
    body: str = Field(min_length=20)
    url: str = ""

class AskIn(BaseModel):
    question: str = Field(min_length=3)

router = APIRouter()

@router.get("/sources")
async def sources(db: AsyncSession = Depends(get_db)):
    rows = await svc.list_sources(db)
    return {"sources": [{"id": s.id, "title": s.title, "url": s.url} for s in rows]}

@router.post("/sources")
async def attach(payload: SourceIn, db: AsyncSession = Depends(get_db)):
    return await svc.attach_source(db, payload.title, payload.body, payload.url)

@router.post("/chat")
async def chat(payload: AskIn, db: AsyncSession = Depends(get_db)):
    return await svc.chat(db, payload.question)

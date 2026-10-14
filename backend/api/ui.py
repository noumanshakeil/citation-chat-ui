from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db import get_db
from backend.services import citations as svc

router = APIRouter()
templates = Jinja2Templates(directory="backend/templates")

@router.get("/", response_class=HTMLResponse)
async def home(request: Request, db: AsyncSession = Depends(get_db)):
    return templates.TemplateResponse("index.html", {"request": request, "title": "Citation Chat UI", "sources": await svc.list_sources(db), "history": await svc.history(db), "result": None, "question": ""})

@router.post("/ui/source")
async def ui_source(title: str = Form(...), body: str = Form(...), url: str = Form(""), db: AsyncSession = Depends(get_db)):
    await svc.attach_source(db, title, body, url)
    return RedirectResponse("/", status_code=303)

@router.post("/ui/chat", response_class=HTMLResponse)
async def ui_chat(request: Request, question: str = Form(...), db: AsyncSession = Depends(get_db)):
    result = await svc.chat(db, question)
    return templates.TemplateResponse("index.html", {"request": request, "title": "Citation Chat UI", "sources": await svc.list_sources(db), "history": await svc.history(db), "result": result, "question": question})

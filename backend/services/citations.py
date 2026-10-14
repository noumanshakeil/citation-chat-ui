from __future__ import annotations
import json
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.llm import get_llm
from backend.models import ChatTurn, SourceChunk, SourceDoc
from backend.services.rag_core import Hit, chunk_text, pack_citations, score_chunk
from backend.utils.ids import short_id

async def attach_source(session: AsyncSession, title: str, body: str, url: str = "") -> dict:
    doc = SourceDoc(id=short_id(), title=title.strip()[:200], url=url.strip()[:400], body=body.strip())
    session.add(doc)
    await session.flush()
    n = 0
    for piece in chunk_text(body, size=320, overlap=40):
        session.add(SourceChunk(id=uuid.uuid4().hex[:12], doc_id=doc.id, text=piece))
        n += 1
    await session.commit()
    return {"doc_id": doc.id, "chunks": n}

async def list_sources(session: AsyncSession) -> list[SourceDoc]:
    return list((await session.execute(select(SourceDoc).order_by(SourceDoc.created_at.desc()))).scalars())

async def chat(session: AsyncSession, question: str) -> dict:
    chunks = list((await session.execute(select(SourceChunk))).scalars())
    docs = {d.id: d for d in (await session.execute(select(SourceDoc))).scalars()}
    hits: list[Hit] = []
    for ch in chunks:
        s = score_chunk(question, ch.text)
        if s <= 0:
            continue
        doc = docs.get(ch.doc_id)
        hits.append(
            Hit(
                chunk_id=ch.id,
                document_id=ch.doc_id,
                title=doc.title if doc else ch.doc_id,
                text=ch.text,
                score=s,
                meta={"url": getattr(doc, "url", "") if doc else ""},
            )
        )
    hits.sort(key=lambda h: h.score, reverse=True)
    hits = hits[:5]
    if not hits:
        turn = ChatTurn(id=short_id(), question=question.strip(), answer="I cannot answer without sources. Attach documents first.", refused=True, citations_json="[]")
        session.add(turn)
        await session.commit()
        return {"refused": True, "answer": turn.answer, "citations": []}
    context = pack_citations(hits)
    llm = get_llm()
    answer = await llm.complete(
        f"Answer ONLY using citations. Question: {question}\n\nSOURCES:\n{context}",
        system="Every claim must map to a citation index like [1]. If unsure, say you lack evidence.",
    )
    citations = [
        {"index": i, "doc_id": h.document_id, "title": h.title, "url": h.meta.get("url", ""), "snippet": h.text[:180], "score": round(h.score, 3)}
        for i, h in enumerate(hits, start=1)
    ]
    turn = ChatTurn(id=short_id(), question=question.strip(), answer=answer, refused=False, citations_json=json.dumps(citations))
    session.add(turn)
    await session.commit()
    return {"refused": False, "answer": answer, "citations": citations}

async def history(session: AsyncSession) -> list[ChatTurn]:
    return list((await session.execute(select(ChatTurn).order_by(ChatTurn.created_at.desc()).limit(20))).scalars())

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.shared.db import get_db
from backend.shared.config import get_settings
from backend.shared.rate_limit import RateLimitMiddleware
from backend.shared.logging_config import setup_logging
from .rag import retrieve
from .genai_clients import translate, reason, NimUnavailableError

setup_logging()
settings = get_settings()
app = FastAPI(title="StadiumPulse Fan Navigator")

app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    query: str
    lang: str = "en"
    accessibility_mode: bool = False


class AskResponse(BaseModel):
    answer: str
    sources: list


@app.get("/health")
def health():
    from .genai_clients import NIM_API_KEY
    return {
        "status": "ok",
        "service": "navigator",
        "nim_key_loaded": bool(NIM_API_KEY),
        "nim_key_prefix": NIM_API_KEY[:12] + "..." if NIM_API_KEY else None,
    }


@app.post("/ask", response_model=AskResponse)
async def ask(req: AskRequest, db: Session = Depends(get_db)):
    # 1. translate incoming query to English for retrieval if needed
    query_en = req.query if req.lang == "en" else await translate(req.query, "en")

    # 2. RAG retrieve relevant venue chunks
    chunks = retrieve(db, query_en, k=4)
    context = "\n".join(f"- {c['text']}" for c in chunks)

    accessibility_note = (
        "Prioritize wheelchair-safe routes and give short, screen-reader-friendly sentences."
        if req.accessibility_mode else ""
    )

    prompt = f"""You are a stadium wayfinding assistant. Answer the fan's question using only the venue context below.
{accessibility_note}

Venue context:
{context}

Fan question: {query_en}

Answer concisely (2-4 sentences), in English."""

    try:
        answer_en = await reason(prompt)
    except NimUnavailableError:
        raise HTTPException(
            status_code=503,
            detail="The navigator's AI service is temporarily unavailable. Please try again shortly.",
        )

    # 3. translate answer back to fan's language
    answer = answer_en if req.lang == "en" else await translate(answer_en, req.lang)

    return AskResponse(answer=answer, sources=[c["zone_id"] for c in chunks])


@app.get("/heatmap")
def heatmap(db: Session = Depends(get_db)):
    """Latest crowd density per zone — feeds the fan-side heatmap overlay."""
    from backend.shared.models import CrowdSignal
    from sqlalchemy import func

    subq = (
        db.query(CrowdSignal.zone_id, func.max(CrowdSignal.ts).label("max_ts"))
        .group_by(CrowdSignal.zone_id)
        .subquery()
    )
    rows = (
        db.query(CrowdSignal)
        .join(subq, (CrowdSignal.zone_id == subq.c.zone_id) & (CrowdSignal.ts == subq.c.max_ts))
        .all()
    )
    return [{"zone_id": r.zone_id, "density_pct": r.density_pct} for r in rows]


@app.websocket("/ws/heatmap")
async def ws_heatmap(websocket: WebSocket):
    """Push live crowd density updates to connected fan UIs."""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()  # ping/pong or filters from client
    except WebSocketDisconnect:
        pass

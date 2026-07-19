from dotenv import load_dotenv
load_dotenv()

import random
from datetime import timedelta

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.shared.db import get_db
from backend.shared.models import RecommendedAction, Volunteer
from backend.shared.config import get_settings
from backend.shared.logging_config import setup_logging
from backend.shared.rate_limit import RateLimitMiddleware
from .orchestrator_agent import build_recommended_actions
from .dispatch_ranker import rank_with_explanation
from .simulated_feeds import gen_crowd_tick, gen_transport_tick, maybe_gen_incident
from .auth import get_current_staff, create_token, authenticate_staff

setup_logging()
settings = get_settings()
app = FastAPI(title="StadiumPulse Ops Orchestrator")

app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

_rng = random.Random(42)  # seeded for reproducible demo


@app.get("/health")
def health():
    from backend.navigator.app.genai_clients import NIM_API_KEY
    return {
        "status": "ok",
        "service": "orchestrator",
        "nim_key_loaded": bool(NIM_API_KEY),
        "nim_key_prefix": NIM_API_KEY[:12] + "..." if NIM_API_KEY else None,
    }


class LoginRequest(BaseModel):
    username: str
    password: str


@app.post("/auth/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_staff(db, req.username, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="invalid credentials")
    return {"access_token": create_token(user.username)}


@app.post("/simulate/tick")
def simulate_tick(db: Session = Depends(get_db), _=Depends(get_current_staff)):
    """Advance the simulated feeds by one tick (crowd + transport + maybe incident)."""
    gen_crowd_tick(db, _rng)
    gen_transport_tick(db, _rng)
    maybe_gen_incident(db, _rng)
    return {"status": "ticked"}


@app.get("/actions")
async def get_recommended_actions(db: Session = Depends(get_db), _=Depends(get_current_staff)):
    """Correlated, severity-ranked recommended actions — the core ops dashboard feed."""
    from backend.navigator.app.genai_clients import NimUnavailableError
    try:
        actions = await build_recommended_actions(db)
    except NimUnavailableError:
        raise HTTPException(
            status_code=503,
            detail="AI recommendation service is temporarily unavailable. Signals are still being collected.",
        )
    for a in actions:
        db.add(
            RecommendedAction(
                zone_id=a["zone_id"],
                severity=int(a["severity"]),
                summary=f"Zone {a['zone_id']} severity {a['severity']}",
                action_text=a["action_text"],
                source_signals=a["signals"],
            )
        )
    db.commit()
    return actions


@app.get("/dispatch/rank")
async def dispatch_rank(
    zone_id: str, category: str, db: Session = Depends(get_db), _=Depends(get_current_staff)
):
    return await rank_with_explanation(db, zone_id, category)


@app.post("/dispatch/{volunteer_id}")
def dispatch(volunteer_id: int, db: Session = Depends(get_db), _=Depends(get_current_staff)):
    v = db.query(Volunteer).filter(Volunteer.id == volunteer_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="volunteer not found")
    v.available = False
    db.commit()
    return {"status": "dispatched", "volunteer_id": volunteer_id}

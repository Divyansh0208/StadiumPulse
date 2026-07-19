"""Crowd density signal agent. Reads latest CrowdSignal rows, flags zones over threshold."""
from sqlalchemy import func
from backend.shared.models import CrowdSignal

DENSITY_ALERT_THRESHOLD = 85.0


def read_signal(db) -> dict:
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
    return {
        r.zone_id: {
            "density_pct": r.density_pct,
            "alert": r.density_pct >= DENSITY_ALERT_THRESHOLD,
        }
        for r in rows
    }

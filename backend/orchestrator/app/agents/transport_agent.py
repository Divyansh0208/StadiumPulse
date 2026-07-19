from sqlalchemy import func
from backend.shared.models import TransportSignal

# links transit points to the gate zone they feed foot traffic into
TRANSIT_TO_ZONE = {"T1": "Z1", "T2": "Z2"}
DELAY_ALERT_THRESHOLD = 12.0


def read_signal(db) -> dict:
    subq = (
        db.query(TransportSignal.transit_point_id, func.max(TransportSignal.ts).label("max_ts"))
        .group_by(TransportSignal.transit_point_id)
        .subquery()
    )
    rows = (
        db.query(TransportSignal)
        .join(
            subq,
            (TransportSignal.transit_point_id == subq.c.transit_point_id)
            & (TransportSignal.ts == subq.c.max_ts),
        )
        .all()
    )
    out = {}
    for r in rows:
        zone_id = TRANSIT_TO_ZONE.get(r.transit_point_id)
        if not zone_id:
            continue
        out[zone_id] = {
            "delay_minutes": r.delay_minutes,
            "alert": r.delay_minutes >= DELAY_ALERT_THRESHOLD,
        }
    return out

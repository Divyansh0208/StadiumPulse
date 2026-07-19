from datetime import datetime, timedelta
from backend.shared.models import IncidentReport

LOOKBACK_MINUTES = 10


def read_signal(db) -> dict:
    cutoff = datetime.utcnow() - timedelta(minutes=LOOKBACK_MINUTES)
    rows = (
        db.query(IncidentReport)
        .filter(IncidentReport.ts >= cutoff, IncidentReport.resolved.is_(False))
        .all()
    )
    out: dict = {}
    for r in rows:
        entry = out.setdefault(r.zone_id, {"incidents": [], "max_severity": 0})
        entry["incidents"].append({"category": r.category, "severity": r.severity, "id": r.id})
        entry["max_severity"] = max(entry["max_severity"], r.severity)
    for zone in out.values():
        zone["alert"] = zone["max_severity"] >= 3
    return out

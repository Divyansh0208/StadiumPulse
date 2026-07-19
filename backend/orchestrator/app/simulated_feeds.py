"""Seeded random generators standing in for real sensor/CV/transit APIs (demo scope)."""
import random
from backend.shared.models import CrowdSignal, TransportSignal, IncidentReport

ZONE_IDS = ["Z1", "Z2", "Z3", "Z4", "Z5"]
TRANSIT_IDS = ["T1", "T2"]
INCIDENT_CATEGORIES = ["medical", "security", "crowd_crush", "facility"]


def gen_crowd_tick(db, rng: random.Random):
    for zone_id in ZONE_IDS:
        density = round(rng.uniform(20, 98), 1)
        db.add(CrowdSignal(zone_id=zone_id, density_pct=density))
    db.commit()


def gen_transport_tick(db, rng: random.Random):
    for tid in TRANSIT_IDS:
        delay = round(rng.uniform(0, 20), 1)
        db.add(TransportSignal(transit_point_id=tid, delay_minutes=delay))
    db.commit()


def maybe_gen_incident(db, rng: random.Random, p: float = 0.15):
    if rng.random() < p:
        zone_id = rng.choice(ZONE_IDS)
        db.add(
            IncidentReport(
                zone_id=zone_id,
                category=rng.choice(INCIDENT_CATEGORIES),
                severity=rng.randint(1, 5),
                description="Simulated report for demo.",
                reported_by="sim",
            )
        )
        db.commit()

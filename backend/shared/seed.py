"""Load data/venue_kb.json, chunk it, embed with sentence-transformers, insert into pgvector."""
from dotenv import load_dotenv
load_dotenv()

import json
import os
from sentence_transformers import SentenceTransformer
from .db import SessionLocal, init_db
from .models import VenueChunk

KB_PATH = os.getenv("VENUE_KB_PATH", "/app/data/venue_kb.json")

_model = None


def get_embedder():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def zone_to_text(zone: dict) -> str:
    amenities = ", ".join(zone.get("amenities", []))
    return f"{zone['name']} ({zone['type']}), capacity {zone.get('capacity','?')}. Amenities: {amenities}."


def route_to_text(route: dict) -> str:
    safe = "wheelchair-accessible" if route.get("wheelchair_safe") else "standard"
    return f"Route from {route['from']} to {route['to']} is {safe}."


def run_seed():
    init_db()
    with open(KB_PATH) as f:
        kb = json.load(f)

    embedder = get_embedder()
    db = SessionLocal()
    try:
        db.query(VenueChunk).delete()

        rows = []
        for zone in kb.get("zones", []):
            rows.append(("zone", zone["id"], zone_to_text(zone), zone))
        for route in kb.get("accessible_routes", []):
            rows.append(("route", route["from"], route_to_text(route), route))

        texts = [r[2] for r in rows]
        embeddings = embedder.encode(texts, normalize_embeddings=True)

        for (kind, zone_id, text, meta), emb in zip(rows, embeddings):
            db.add(VenueChunk(zone_id=zone_id, kind=kind, text=text,
                               embedding=emb.tolist(), meta=meta))
        db.commit()
        print(f"seeded {len(rows)} venue chunks")
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
    from . import seed_volunteers
    seed_volunteers.run()
    from . import seed_staff
    seed_staff.run()

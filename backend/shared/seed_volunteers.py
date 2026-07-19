"""Seed demo volunteers for dispatch ranker testing."""
from .db import SessionLocal
from .models import Volunteer

DEMO_VOLUNTEERS = [
    {"name": "Amit", "zone_id": "Z1", "skills": ["medical"]},
    {"name": "Priya", "zone_id": "Z2", "skills": ["crowd_control", "multilingual_es"]},
    {"name": "Rahul", "zone_id": "Z5", "skills": ["crowd_control"]},
    {"name": "Sara", "zone_id": "Z3", "skills": ["medical", "multilingual_ar"]},
    {"name": "Jon", "zone_id": "Z4", "skills": ["general"]},
]


def run():
    db = SessionLocal()
    try:
        db.query(Volunteer).delete()
        for v in DEMO_VOLUNTEERS:
            db.add(Volunteer(**v, available=True))
        db.commit()
        print(f"seeded {len(DEMO_VOLUNTEERS)} volunteers")
    finally:
        db.close()


if __name__ == "__main__":
    run()

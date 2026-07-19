"""Seed a default staff login. Real hashed password, not a hardcoded plaintext check.
Change the password after first login in any real deployment — this is a demo default.
"""
import os
from .db import SessionLocal
from .models import StaffUser

DEFAULT_USERNAME = os.getenv("SEED_STAFF_USERNAME", "staff")
DEFAULT_PASSWORD = os.getenv("SEED_STAFF_PASSWORD", "demo")  # override via env for real use


def run():
    from backend.orchestrator.app.auth import hash_password

    db = SessionLocal()
    try:
        existing = db.query(StaffUser).filter(StaffUser.username == DEFAULT_USERNAME).first()
        if existing:
            print(f"staff user '{DEFAULT_USERNAME}' already exists, skipping")
            return
        db.add(
            StaffUser(
                username=DEFAULT_USERNAME,
                password_hash=hash_password(DEFAULT_PASSWORD),
                role="admin",
                active=True,
            )
        )
        db.commit()
        print(f"seeded staff user '{DEFAULT_USERNAME}'")
    finally:
        db.close()


if __name__ == "__main__":
    run()

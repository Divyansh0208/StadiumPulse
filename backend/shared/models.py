"""Shared SQLAlchemy models — venue data layer (Postgres + pgvector)."""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base
from pgvector.sqlalchemy import Vector

Base = declarative_base()

EMBED_DIM = 384  # sentence-transformers all-MiniLM-L6-v2


class VenueChunk(Base):
    """RAG chunk: gate/seating/amenity/route text, embedded for retrieval."""
    __tablename__ = "venue_chunks"

    id = Column(Integer, primary_key=True)
    zone_id = Column(String, index=True)
    kind = Column(String)  # gate | seating | route | amenity
    text = Column(String)
    embedding = Column(Vector(EMBED_DIM))
    meta = Column(JSON, default={})


class CrowdSignal(Base):
    __tablename__ = "crowd_signals"

    id = Column(Integer, primary_key=True)
    zone_id = Column(String, index=True)
    density_pct = Column(Float)
    ts = Column(DateTime, default=datetime.utcnow)


class TransportSignal(Base):
    __tablename__ = "transport_signals"

    id = Column(Integer, primary_key=True)
    transit_point_id = Column(String, index=True)
    delay_minutes = Column(Float)
    ts = Column(DateTime, default=datetime.utcnow)


class IncidentReport(Base):
    __tablename__ = "incident_reports"

    id = Column(Integer, primary_key=True)
    zone_id = Column(String, index=True)
    category = Column(String)  # medical | security | crowd_crush | facility
    severity = Column(Integer)  # 1-5
    description = Column(String)
    reported_by = Column(String, nullable=True)
    ts = Column(DateTime, default=datetime.utcnow)
    resolved = Column(Boolean, default=False)


class Volunteer(Base):
    __tablename__ = "volunteers"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    zone_id = Column(String, index=True)  # current location
    skills = Column(JSON, default=[])  # e.g. ["medical","crowd_control","multilingual_es"]
    available = Column(Boolean, default=True)


class StaffUser(Base):
    """Ops dashboard login — replaces the hardcoded staff/demo credential."""
    __tablename__ = "staff_users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(String, default="staff")  # staff | admin
    active = Column(Boolean, default=True)


class RecommendedAction(Base):
    """Output of orchestrator correlation — what ops dashboard shows."""
    __tablename__ = "recommended_actions"

    id = Column(Integer, primary_key=True)
    zone_id = Column(String, index=True)
    severity = Column(Integer)
    summary = Column(String)
    action_text = Column(String)
    source_signals = Column(JSON, default={})  # {crowd:.., transport:.., incident:..}
    dispatched_volunteer_id = Column(Integer, nullable=True)
    ts = Column(DateTime, default=datetime.utcnow)
    resolved = Column(Boolean, default=False)

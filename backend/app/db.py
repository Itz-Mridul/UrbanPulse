"""
Database setup — async SQLAlchemy engine + PostGIS models.
"""
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON, Text, func
from geoalchemy2 import Geometry

from app.config import settings

engine = create_async_engine(settings.database_url, echo=False, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# ORM Models (mirrors Section 3 SQL schema)
# ---------------------------------------------------------------------------

class Region(Base):
    __tablename__ = "regions"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    boundary = Column(Geometry("POLYGON", srid=4326))
    description = Column(Text)
    pilot = Column(Boolean, default=True)


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True)
    region_id = Column(Integer, ForeignKey("regions.id"))
    source = Column(String, nullable=False)   # IMD_RAINFALL | CWC_DISCHARGE | GSI_LANDSLIDE | SYNTHETIC
    metric = Column(String, nullable=False)   # rainfall_mm | river_level_m | soil_moisture
    value = Column(Float, nullable=False)
    recorded_at = Column(DateTime(timezone=True), nullable=False)
    location = Column(Geometry("POINT", srid=4326))


class HazardEvent(Base):
    __tablename__ = "hazard_events"

    id = Column(Integer, primary_key=True)
    region_id = Column(Integer, ForeignKey("regions.id"))
    hazard_type = Column(String, nullable=False)  # RAINFALL_TRIGGER | LANDSLIDE | RIVER_BLOCKAGE | FLOOD
    occurred_at = Column(DateTime(timezone=True))
    is_historical = Column(Boolean, default=False)
    is_synthetic = Column(Boolean, default=False)
    confidence = Column(Float)
    severity = Column(Float)  # 0–1 normalized severity
    description = Column(Text)
    location = Column(Geometry("POINT", srid=4326))


class CascadePrediction(Base):
    __tablename__ = "cascade_predictions"

    id = Column(Integer, primary_key=True)
    region_id = Column(Integer, ForeignKey("regions.id"))
    source_hazard_id = Column(Integer, ForeignKey("hazard_events.id"))
    target_hazard_type = Column(String, nullable=False)
    probability = Column(Float, nullable=False)
    time_lag_min_hours = Column(Float)
    time_lag_max_hours = Column(Float)
    causal_path = Column(JSON)   # ordered list of {node, probability, evidence} dicts
    impact_zone = Column(Geometry("POLYGON", srid=4326))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_replay = Column(Boolean, default=False)
    replay_timestamp = Column(DateTime(timezone=True))  # simulation time for replay mode


class ImpactScore(Base):
    __tablename__ = "impact_scores"

    id = Column(Integer, primary_key=True)
    prediction_id = Column(Integer, ForeignKey("cascade_predictions.id"))
    population_exposed = Column(Integer)
    hospitals_exposed = Column(Integer)
    roads_affected_km = Column(Float)
    shelters_available = Column(Integer)
    impact_score = Column(Float)   # 0–100 normalized
    vulnerability_index = Column(Float)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True)
    prediction_id = Column(Integer, ForeignKey("cascade_predictions.id"))
    tier = Column(String, nullable=False)   # GREEN | YELLOW | ORANGE | RED
    recommended_action = Column(Text)
    status = Column(String, default="PENDING_VERIFICATION")  # PENDING_VERIFICATION | VERIFIED | DISMISSED | DOWNGRADED
    verified_by = Column(String)
    verified_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    notes = Column(Text)


# ---------------------------------------------------------------------------
# DB session dependency + initialisation
# ---------------------------------------------------------------------------

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    """Create all tables (idempotent — use Alembic for production migrations)."""
    async with engine.begin() as conn:
        # Ensure PostGIS extension exists
        await conn.execute(__import__("sqlalchemy").text("CREATE EXTENSION IF NOT EXISTS postgis"))
        await conn.run_sync(Base.metadata.create_all)

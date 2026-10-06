"""
Database seeding script — loads the pilot region, historical events,
and synthetic sensor readings into PostgreSQL/PostGIS.

Run once after `docker-compose up` has created the tables:
    docker-compose exec backend python -m scripts.seed_db

Or directly:
    python scripts/seed_db.py
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Allow running from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text
from app.config import settings
from app.db import Base, Region, HazardEvent, SensorReading


engine = create_async_engine(settings.database_url, echo=False)
Session = async_sessionmaker(engine, expire_on_commit=False)


async def seed():
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        await conn.run_sync(Base.metadata.create_all)

    async with Session() as db:
        # ── 1. Pilot region — Sikkim / Teesta Valley ───────────────────────
        existing = await db.execute(
            text("SELECT id FROM regions WHERE name = 'Sikkim — Teesta Valley'")
        )
        if existing.scalar_one_or_none() is None:
            region = Region(
                name="Sikkim — Teesta Valley",
                description=(
                    "Pilot region for CascadeIQ MVP. "
                    "Covers the Teesta river basin from South Lhonak glacial lake "
                    "to Rangpo. Primary hazard pair: GLOF → River Blockage → Flood."
                ),
                pilot=True,
                # PostGIS polygon: rough bounding box of the Teesta corridor
                boundary=text(
                    "ST_GeomFromText('POLYGON((88.3 27.0, 88.9 27.0, 88.9 28.0, 88.3 28.0, 88.3 27.0))', 4326)"
                ),
            )
            db.add(region)
            await db.flush()
            region_id = region.id
            print(f"✅ Created region: Sikkim — Teesta Valley (id={region_id})")
        else:
            region_id = existing.scalar_one_or_none()
            # refetch properly
            res = await db.execute(
                text("SELECT id FROM regions WHERE name = 'Sikkim — Teesta Valley'")
            )
            region_id = res.scalar_one()
            print(f"ℹ️  Region already exists (id={region_id})")

        # ── 2. Kedarnath / Mandakini Valley ────────────────────────────────
        existing2 = await db.execute(
            text("SELECT id FROM regions WHERE name = 'Kedarnath — Mandakini Valley'")
        )
        if existing2.scalar_one_or_none() is None:
            r2 = Region(
                name="Kedarnath — Mandakini Valley",
                description=(
                    "Secondary pilot region. Kedarnath 2013 backtest. "
                    "Hazard pair: Cloudburst → Debris Flow → Flash Flood."
                ),
                pilot=True,
            )
            db.add(r2)
            print("✅ Created region: Kedarnath — Mandakini Valley")

        # ── 3. Historical hazard events — Sikkim 2023 ──────────────────────
        # South Lhonak GLOF, 4 October 2023
        real_event_time = datetime(2023, 10, 4, 4, 0, 0, tzinfo=timezone.utc)
        events = [
            HazardEvent(
                region_id=region_id,
                hazard_type="RAINFALL_TRIGGER",
                occurred_at=real_event_time - timedelta(hours=48),
                is_historical=True,
                is_synthetic=False,
                confidence=0.95,
                severity=0.85,
                description="Cyclone Hamoon-associated extreme rainfall, 165–205mm/24h over Sikkim",
            ),
            HazardEvent(
                region_id=region_id,
                hazard_type="LANDSLIDE",
                occurred_at=real_event_time - timedelta(hours=6),
                is_historical=True,
                is_synthetic=False,
                confidence=0.90,
                severity=0.95,
                description="South Lhonak glacial lake moraine dam failure — GLOF initiated",
            ),
            HazardEvent(
                region_id=region_id,
                hazard_type="RIVER_BLOCKAGE",
                occurred_at=real_event_time - timedelta(hours=5),
                is_historical=True,
                is_synthetic=False,
                confidence=0.85,
                severity=0.90,
                description="Temporary blockage of Teesta at Dikchu by debris from GLOF",
            ),
            HazardEvent(
                region_id=region_id,
                hazard_type="FLOOD",
                occurred_at=real_event_time,
                is_historical=True,
                is_synthetic=False,
                confidence=1.0,
                severity=1.0,
                description=(
                    "CONFIRMED: South Lhonak GLOF reached Singtam ~07:00 IST 4 Oct 2023. "
                    "~40 fatalities. Bridges, roads, buildings destroyed. Peak discharge ~40,000 m³/s."
                ),
            ),
        ]
        for ev in events:
            db.add(ev)
        print(f"✅ Inserted {len(events)} historical hazard events (Sikkim 2023 GLOF)")

        # ── 4. Synthetic sensor readings (replay data as DB rows) ──────────
        # Pre-event rainfall readings T-72h to T=0
        base_time = real_event_time - timedelta(hours=72)
        rainfall_series = [
            (0,  45.0, 120.0, 0.55, 0.40),   # T-72h
            (24, 110.0, 195.0, 0.68, 0.52),  # T-48h
            (36, 165.0, 310.0, 0.78, 0.61),  # T-36h
            (48, 190.0, 420.0, 0.85, 0.70),  # T-24h
            (60, 205.0, 490.0, 0.92, 0.82),  # T-12h
            (66, 180.0, 520.0, 0.95, 0.90),  # T-6h
            (72, 175.0, 520.0, 0.95, 1.00),  # T=0
        ]

        reading_count = 0
        for hours_offset, rain_24h, rain_72h, soil_sat, river_lvl in rainfall_series:
            ts = base_time + timedelta(hours=hours_offset)
            readings = [
                SensorReading(
                    region_id=region_id,
                    source="SYNTHETIC",
                    metric="rainfall_mm_24h",
                    value=rain_24h,
                    recorded_at=ts,
                ),
                SensorReading(
                    region_id=region_id,
                    source="SYNTHETIC",
                    metric="rainfall_mm_72h",
                    value=rain_72h,
                    recorded_at=ts,
                ),
                SensorReading(
                    region_id=region_id,
                    source="SYNTHETIC",
                    metric="soil_saturation_index",
                    value=soil_sat,
                    recorded_at=ts,
                ),
                SensorReading(
                    region_id=region_id,
                    source="SYNTHETIC",
                    metric="river_level_normalised",
                    value=river_lvl,
                    recorded_at=ts,
                ),
            ]
            for r in readings:
                db.add(r)
            reading_count += len(readings)

        print(f"✅ Inserted {reading_count} synthetic sensor readings (Sikkim 2023 lead-up)")

        await db.commit()
        print("\n🌊 Database seeding complete!")
        print("   Next: POST /api/v1/predictions/trigger?region_id=1 to run inference")


if __name__ == "__main__":
    asyncio.run(seed())

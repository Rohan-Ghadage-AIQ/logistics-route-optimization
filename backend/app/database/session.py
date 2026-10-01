"""
Database Connection & Session Management
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.config import settings
from app.models.entities import Base, VehicleFleet

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for obtaining async DB session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables, apply column migrations and seed/sync shift fleet"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # Automatic SQLite column migration
        for col_name, col_type in [
            ("waiting_time_minutes", "INTEGER DEFAULT 0"),
            ("service_start_minutes", "INTEGER"),
            ("departure_minutes", "INTEGER")
        ]:
            try:
                await conn.exec_driver_sql(f"ALTER TABLE orders ADD COLUMN {col_name} {col_type};")
            except Exception:
                pass

        for col_name, col_type in [
            ("capacity_kg", "FLOAT DEFAULT 500.0"),
            ("driving_duration_minutes", "FLOAT DEFAULT 0.0"),
            ("service_duration_minutes", "FLOAT DEFAULT 0.0"),
            ("waiting_duration_minutes", "FLOAT DEFAULT 0.0"),
            ("start_time_minutes", "INTEGER DEFAULT 480"),
            ("end_time_minutes", "INTEGER DEFAULT 480"),
            ("legs", "JSON"),
            ("timeline", "JSON"),
            ("validation_data", "JSON")
        ]:
            try:
                await conn.exec_driver_sql(f"ALTER TABLE routes ADD COLUMN {col_name} {col_type};")
            except Exception:
                pass

    # Exact Fleet Shift Configuration:
    # Vehicles 1, 2, 3: 07:00 - 09:00 (Morning Shift)
    # Vehicles 4, 5, 6: 09:00 - 18:00 (Day Shift)
    # Vehicles 7, 8, 9, 10: 18:00 - 21:00 (Evening Shift)
    default_fleet_configs = [
        # Shift 1 (07:00 - 09:00, 420m - 540m)
        {"id": 1, "name": "Vehicle 1 (07:00-09:00)", "capacity_kg": 200.0, "cost_per_km": 12.0, "shift_start_minutes": 420, "shift_end_minutes": 540},
        {"id": 2, "name": "Vehicle 2 (07:00-09:00)", "capacity_kg": 250.0, "cost_per_km": 14.0, "shift_start_minutes": 420, "shift_end_minutes": 540},
        {"id": 3, "name": "Vehicle 3 (07:00-09:00)", "capacity_kg": 300.0, "cost_per_km": 15.0, "shift_start_minutes": 420, "shift_end_minutes": 540},
        
        # Shift 2 (09:00 - 18:00, 540m - 1080m)
        {"id": 4, "name": "Vehicle 4 (09:00-18:00)", "capacity_kg": 200.0, "cost_per_km": 12.0, "shift_start_minutes": 540, "shift_end_minutes": 1080},
        {"id": 5, "name": "Vehicle 5 (09:00-18:00)", "capacity_kg": 250.0, "cost_per_km": 14.0, "shift_start_minutes": 540, "shift_end_minutes": 1080},
        {"id": 6, "name": "Vehicle 6 (09:00-18:00)", "capacity_kg": 250.0, "cost_per_km": 14.0, "shift_start_minutes": 540, "shift_end_minutes": 1080},
        
        # Shift 3 (18:00 - 21:00, 1080m - 1260m)
        {"id": 7, "name": "Vehicle 7 (18:00-21:00)", "capacity_kg": 180.0, "cost_per_km": 10.0, "shift_start_minutes": 1080, "shift_end_minutes": 1260},
        {"id": 8, "name": "Vehicle 8 (18:00-21:00)", "capacity_kg": 200.0, "cost_per_km": 12.0, "shift_start_minutes": 1080, "shift_end_minutes": 1260},
        {"id": 9, "name": "Vehicle 9 (18:00-21:00)", "capacity_kg": 220.0, "cost_per_km": 12.0, "shift_start_minutes": 1080, "shift_end_minutes": 1260},
        {"id": 10, "name": "Vehicle 10 (18:00-21:00)", "capacity_kg": 250.0, "cost_per_km": 14.0, "shift_start_minutes": 1080, "shift_end_minutes": 1260},
    ]

    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        result = await session.execute(select(VehicleFleet))
        existing_vehicles = {v.id: v for v in result.scalars().all()}

        for cfg in default_fleet_configs:
            v_id = cfg["id"]
            if v_id in existing_vehicles:
                v = existing_vehicles[v_id]
                v.name = cfg["name"]
                v.capacity_kg = cfg["capacity_kg"]
                v.cost_per_km = cfg["cost_per_km"]
                v.shift_start_minutes = cfg["shift_start_minutes"]
                v.shift_end_minutes = cfg["shift_end_minutes"]
                v.is_active = True
            else:
                new_v = VehicleFleet(
                    id=v_id,
                    name=cfg["name"],
                    capacity_kg=cfg["capacity_kg"],
                    cost_per_km=cfg["cost_per_km"],
                    shift_start_minutes=cfg["shift_start_minutes"],
                    shift_end_minutes=cfg["shift_end_minutes"],
                    is_active=True
                )
                session.add(new_v)
        await session.commit()

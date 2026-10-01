"""
Fleet Management API Router
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.entities import VehicleFleet
from app.schemas.fleet import VehicleFleetRead, VehicleFleetCreate, VehicleFleetUpdate
from app.utils.time_utils import minutes_to_clock_str

router = APIRouter(prefix="/fleet", tags=["Fleet Management"])


@router.get("", response_model=List[VehicleFleetRead])
async def list_fleet(db: AsyncSession = Depends(get_db)):
    """Retrieve all configurable fleet vehicles."""
    result = await db.execute(select(VehicleFleet).order_by(VehicleFleet.id))
    vehicles = result.scalars().all()
    return [
        VehicleFleetRead(
            id=v.id,
            name=v.name,
            capacity_kg=v.capacity_kg,
            cost_per_km=v.cost_per_km,
            shift_start_minutes=v.shift_start_minutes,
            shift_end_minutes=v.shift_end_minutes,
            is_active=v.is_active,
            shift_start_str=minutes_to_clock_str(v.shift_start_minutes),
            shift_end_str=minutes_to_clock_str(v.shift_end_minutes)
        )
        for v in vehicles
    ]


@router.post("", response_model=VehicleFleetRead)
async def create_fleet_vehicle(payload: VehicleFleetCreate, db: AsyncSession = Depends(get_db)):
    """Add a new vehicle to the fleet."""
    new_v = VehicleFleet(
        name=payload.name,
        capacity_kg=payload.capacity_kg,
        cost_per_km=payload.cost_per_km,
        shift_start_minutes=payload.shift_start_minutes,
        shift_end_minutes=payload.shift_end_minutes,
        is_active=payload.is_active
    )
    db.add(new_v)
    await db.commit()
    await db.refresh(new_v)

    return VehicleFleetRead(
        id=new_v.id,
        name=new_v.name,
        capacity_kg=new_v.capacity_kg,
        cost_per_km=new_v.cost_per_km,
        shift_start_minutes=new_v.shift_start_minutes,
        shift_end_minutes=new_v.shift_end_minutes,
        is_active=new_v.is_active,
        shift_start_str=minutes_to_clock_str(new_v.shift_start_minutes),
        shift_end_str=minutes_to_clock_str(new_v.shift_end_minutes)
    )


@router.put("/{vehicle_id}", response_model=VehicleFleetRead)
async def update_fleet_vehicle(vehicle_id: int, payload: VehicleFleetUpdate, db: AsyncSession = Depends(get_db)):
    """Update vehicle specifications."""
    vehicle = await db.get(VehicleFleet, vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found.")

    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(vehicle, field, val)

    await db.commit()
    await db.refresh(vehicle)

    return VehicleFleetRead(
        id=vehicle.id,
        name=vehicle.name,
        capacity_kg=vehicle.capacity_kg,
        cost_per_km=vehicle.cost_per_km,
        shift_start_minutes=vehicle.shift_start_minutes,
        shift_end_minutes=vehicle.shift_end_minutes,
        is_active=vehicle.is_active,
        shift_start_str=minutes_to_clock_str(vehicle.shift_start_minutes),
        shift_end_str=minutes_to_clock_str(vehicle.shift_end_minutes)
    )


@router.delete("/{vehicle_id}")
async def delete_fleet_vehicle(vehicle_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a vehicle from the fleet."""
    vehicle = await db.get(VehicleFleet, vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found.")

    await db.delete(vehicle)
    await db.commit()
    return {"success": True, "message": f"Vehicle {vehicle_id} removed from fleet."}

"""
Fleet Vehicle Schemas
"""
from typing import Optional
from pydantic import BaseModel, Field


class VehicleFleetBase(BaseModel):
    name: str = Field(..., description="Vehicle name or license identifier")
    capacity_kg: float = Field(..., gt=0, description="Maximum payload weight capacity in kg")
    cost_per_km: float = Field(default=15.0, ge=0, description="Operating fuel & vehicle cost per kilometer (₹)")
    shift_start_minutes: int = Field(default=480, ge=0, description="Shift start in minutes from midnight (e.g. 480 = 08:00)")
    shift_end_minutes: int = Field(default=1080, ge=0, description="Shift end in minutes from midnight (e.g. 1080 = 18:00)")
    is_active: bool = Field(default=True, description="Whether vehicle is available for assignment")


class VehicleFleetCreate(VehicleFleetBase):
    pass


class VehicleFleetUpdate(BaseModel):
    name: Optional[str] = None
    capacity_kg: Optional[float] = None
    cost_per_km: Optional[float] = None
    shift_start_minutes: Optional[int] = None
    shift_end_minutes: Optional[int] = None
    is_active: Optional[bool] = None


class VehicleFleetRead(VehicleFleetBase):
    id: int
    shift_start_str: Optional[str] = None
    shift_end_str: Optional[str] = None

    class Config:
        from_attributes = True

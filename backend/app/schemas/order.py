"""
Order and Delivery Location Schemas
"""
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class OrderBase(BaseModel):
    external_order_id: str = Field(..., description="Unique Order or Station ID from manifest")
    raw_address: str = Field(..., description="Delivery address text")
    parcel_weight_kg: float = Field(default=10.0, ge=0.1, description="Weight of parcel in kg")
    service_time_minutes: int = Field(default=10, ge=1, description="Delivery handover service duration in minutes")
    window_start_minutes: int = Field(default=0, ge=0, description="Opening delivery window in minutes from midnight")
    window_end_minutes: int = Field(default=1440, ge=0, description="Deadline delivery window in minutes from midnight")
    latitude: Optional[float] = Field(default=None, description="Optional pre-geocoded latitude")
    longitude: Optional[float] = Field(default=None, description="Optional pre-geocoded longitude")


class OrderCreate(OrderBase):
    pass


class OrderRead(OrderBase):
    id: str
    job_id: str
    resolved_address: Optional[str] = None
    geocoding_status: str
    geocoding_error: Optional[str] = None
    is_assigned: bool = False
    unassigned_reason: Optional[str] = None
    assigned_vehicle_id: Optional[int] = None
    stop_sequence: Optional[int] = None
    estimated_arrival_minutes: Optional[int] = None
    estimated_arrival_time_str: Optional[str] = None

    class Config:
        from_attributes = True


class OrderValidationResult(BaseModel):
    is_valid: bool
    total_rows: int
    valid_rows: int
    errors: list[str] = []
    warnings: list[str] = []

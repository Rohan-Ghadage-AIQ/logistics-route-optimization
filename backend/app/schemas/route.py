"""
Canonical Route and Stop Schemas with Single Source of Truth
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class RouteStopDetail(BaseModel):
    sequence: int
    stop_type: str  # 'DEPOT_START', 'DELIVERY', 'DEPOT_RETURN'
    order_id: Optional[str] = None
    external_order_id: Optional[str] = None
    address: str
    latitude: float
    longitude: float
    parcel_weight_kg: float = 0.0
    
    # Precise ETA & Chronological Progression
    estimated_arrival_minutes: int
    estimated_arrival_time_str: str
    waiting_time_minutes: int = 0
    service_start_minutes: int = 0
    service_start_time_str: str = ""
    service_time_minutes: int = 0
    departure_minutes: int = 0
    departure_time_str: str = ""
    
    # Time Window Validation
    window_start_minutes: int = 0
    window_end_minutes: int = 1440
    window_start_str: Optional[str] = None
    window_end_str: Optional[str] = None
    is_late: bool = False
    lateness_minutes: int = 0
    time_window_status: str = "ON_TIME"  # 'ON_TIME', 'EARLY_WAITING', 'LATE_VIOLATION'


class RouteLegDetail(BaseModel):
    leg_index: int
    from_name: str
    to_name: str
    from_type: str  # 'DEPOT', 'DELIVERY'
    to_type: str    # 'DEPOT', 'DELIVERY'
    distance_km: float
    driving_duration_minutes: float
    departure_time_str: str = ""
    arrival_time_str: str = ""
    geometry: Optional[Dict[str, Any]] = None
    maneuvers: List[Dict[str, Any]] = []


class RouteRead(BaseModel):
    id: str
    vehicle_id: int
    vehicle_name: str
    capacity_kg: float = 500.0
    total_payload_kg: float = 0.0
    capacity_utilization_pct: float = 0.0
    is_over_capacity: bool = False
    total_stops: int = 0
    
    # Duration Breakdown (Single Source of Truth)
    total_distance_km: float
    driving_duration_minutes: float
    service_duration_minutes: float
    waiting_duration_minutes: float
    total_duration_minutes: float  # driving + service + waiting
    
    # Schedule Start & End
    start_time_minutes: int
    start_time_str: str
    end_time_minutes: int
    end_time_str: str
    
    operational_cost: float
    warehouse_start: Dict[str, Any] = {}
    warehouse_end: Dict[str, Any] = {}
    
    geometry: Optional[Dict[str, Any]] = None  # GeoJSON LineString
    maneuvers: Optional[List[Dict[str, Any]]] = None
    legs: List[RouteLegDetail] = []
    stops: List[RouteStopDetail] = []
    timeline: List[Dict[str, Any]] = []
    validation: Dict[str, Any] = {}

    class Config:
        from_attributes = True


class OptimizationSummary(BaseModel):
    total_orders: int
    assigned_orders: int
    unassigned_orders: int
    vehicles_available: int
    vehicles_used: int
    total_distance_km: float
    total_driving_minutes: float = 0.0
    total_service_minutes: float = 0.0
    total_waiting_minutes: float = 0.0
    total_duration_minutes: float
    total_cost: float
    average_capacity_utilization_pct: float
    unassigned_details: List[Dict[str, Any]] = []

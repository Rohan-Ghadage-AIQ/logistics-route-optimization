"""
Abstract Route Optimization Solver Interface & Data Structures
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class LocationPoint(BaseModel):
    id: str
    name: str
    latitude: float
    longitude: float
    demand_kg: float = 0.0
    service_time_minutes: int = 10
    window_start_minutes: int = 0
    window_end_minutes: int = 1440


class VehicleEntity(BaseModel):
    id: int
    name: str
    capacity_kg: float
    cost_per_km: float = 15.0
    shift_start_minutes: int = 480  # 08:00
    shift_end_minutes: int = 1080   # 18:00
    is_active: bool = True


class VehicleRoutePlan(BaseModel):
    vehicle_id: int
    vehicle_name: str
    ordered_stop_indices: List[int]  # Indices into LocationPoint list
    ordered_stop_ids: List[str]
    arrival_times_minutes: List[int]
    total_payload_kg: float
    capacity_utilization_pct: float
    total_distance_km: float = 0.0
    total_duration_minutes: float = 0.0
    operational_cost: float = 0.0
    is_feasible: bool = True
    constraint_violations: List[str] = []


class SolverOutput(BaseModel):
    success: bool
    status: str
    routes: List[VehicleRoutePlan] = []
    unassigned_order_ids: List[str] = []
    unassigned_reasons: Dict[str, str] = {}
    total_distance_km: float = 0.0
    total_duration_minutes: float = 0.0
    total_cost: float = 0.0
    solver_time_seconds: float = 0.0
    error_message: Optional[str] = None


class BaseRouteOptimizer(ABC):
    """Abstract interface for all VRP / Route Optimization Solvers."""

    @abstractmethod
    async def solve(
        self,
        depot: LocationPoint,
        orders: List[LocationPoint],
        fleet: List[VehicleEntity],
        time_matrix_seconds: List[List[int]],
        dist_matrix_meters: List[List[int]]
    ) -> SolverOutput:
        """Solves the multi-vehicle routing problem."""
        pass

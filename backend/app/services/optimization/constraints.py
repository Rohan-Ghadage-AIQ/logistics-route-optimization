"""
Explicit Optimization Constraint Definitions
Encapsulates hard bounds, soft upper bounds, penalty coefficients, and validation checks.
"""
from typing import List, Tuple
from app.config import settings


class VehicleCapacityConstraint:
    """
    Capacity Constraint:
    - Hard relaxed limit: 2x nominal capacity to prevent infeasibility crash.
    - Soft upper bound: Nominal capacity with heavy penalty (1,000,000 / kg overweight).
    """
    def __init__(self, penalty_per_kg: int = settings.OVERCAPACITY_PENALTY_PER_KG):
        self.penalty_per_kg = penalty_per_kg

    def get_relaxed_capacity(self, nominal_capacity: float) -> int:
        return max(500, int(nominal_capacity * 2))


class TimeWindowConstraint:
    """
    Customer Time Window Constraint:
    - Hard lower bound: Customer opening time (cannot deliver before window_start).
    - Soft upper bound: Customer deadline (100,000 penalty points / min late).
    """
    def __init__(self, penalty_per_minute_late: int = settings.TIME_WINDOW_PENALTY_PER_MINUTE):
        self.penalty_per_minute_late = penalty_per_minute_late


class DriverShiftConstraint:
    """
    Driver Shift Window & Overtime Constraint:
    - Hard departure window: Driver shift start to shift end.
    - Soft return deadline: Driver shift end (50,000 penalty points / min overtime).
    - Hard overtime ceiling: Shift end + 60 minutes overtime limit.
    """
    def __init__(
        self,
        overtime_buffer_minutes: int = settings.OVERTIME_BUFFER_MINUTES,
        overtime_penalty_per_minute: int = settings.SHIFT_OVERTIME_PENALTY_PER_MINUTE
    ):
        self.overtime_buffer_minutes = overtime_buffer_minutes
        self.overtime_penalty_per_minute = overtime_penalty_per_minute


class DropDisjunctionConstraint:
    """
    Zero-Drop Guarantee Disjunction:
    - Massive penalty (1,000,000,000 points) for leaving an order unassigned.
    """
    def __init__(self, penalty: int = settings.DROP_PENALTY_MULTIPLIER):
        self.penalty = penalty


class FleetActivationConstraint:
    """
    Fixed Vehicle Dispatch Cost:
    - Flat fee for dispatching an active vehicle to avoid unnecessary fleet dispersion.
    """
    def __init__(self, fixed_cost: int = settings.FIXED_VEHICLE_DISPATCH_COST):
        self.fixed_cost = fixed_cost

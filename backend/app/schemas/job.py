"""
Optimization Job Schemas
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.schemas.order import OrderRead
from app.schemas.route import RouteRead, OptimizationSummary


class JobCreateResponse(BaseModel):
    job_id: str
    filename: str
    status: str
    message: str
    created_at: datetime


class JobStatusRead(BaseModel):
    job_id: str
    filename: str
    status: str  # PENDING, VALIDATING, GEOCODING, MATRIX_GENERATION, OPTIMIZING, ROUTE_GENERATION, COMPLETED, FAILED
    current_step: str
    progress_percentage: int
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    # High-level counters
    total_orders: int = 0
    assigned_orders: int = 0
    unassigned_orders: int = 0
    vehicles_used: int = 0
    total_distance_km: float = 0.0
    total_duration_minutes: float = 0.0
    total_cost: float = 0.0


class JobDetailRead(JobStatusRead):
    summary: Optional[OptimizationSummary] = None
    routes: List[RouteRead] = []
    orders: List[OrderRead] = []

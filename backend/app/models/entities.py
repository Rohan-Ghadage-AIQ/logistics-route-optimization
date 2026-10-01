"""
SQLAlchemy Database Models for Auditable Logistics Optimization
"""
from datetime import datetime
import json
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, JSON
)
from sqlalchemy.orm import declarative_base, relationship
from app.utils.time_utils import minutes_to_clock_str

Base = declarative_base()


class OptimizationJob(Base):
    __tablename__ = "optimization_jobs"

    id = Column(String(36), primary_key=True)
    filename = Column(String(255), nullable=False)
    status = Column(String(50), default="PENDING", nullable=False)
    current_step = Column(String(100), default="Initialized")
    progress_percentage = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)

    # Summary Metrics (Stored as JSON & Columns)
    total_orders = Column(Integer, default=0)
    assigned_orders = Column(Integer, default=0)
    unassigned_orders = Column(Integer, default=0)
    vehicles_used = Column(Integer, default=0)
    total_distance_km = Column(Float, default=0.0)
    total_duration_minutes = Column(Float, default=0.0)
    total_cost = Column(Float, default=0.0)

    summary_data = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    orders = relationship("Order", back_populates="job", cascade="all, delete-orphan")
    routes = relationship("Route", back_populates="job", cascade="all, delete-orphan")


class Order(Base):
    __tablename__ = "orders"

    id = Column(String(36), primary_key=True)
    job_id = Column(String(36), ForeignKey("optimization_jobs.id"), nullable=False)
    external_order_id = Column(String(100), nullable=False)

    # Address & Coordinates
    raw_address = Column(Text, nullable=False)
    resolved_address = Column(Text, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    # Cargo & Time Window Constraints
    parcel_weight_kg = Column(Float, nullable=False, default=0.0)
    service_time_minutes = Column(Integer, nullable=False, default=5)
    window_start_minutes = Column(Integer, nullable=False, default=0)
    window_end_minutes = Column(Integer, nullable=False, default=1440)

    # Audit & Status Tracking
    geocoding_status = Column(String(50), default="PENDING")
    geocoding_error = Column(Text, nullable=True)

    is_assigned = Column(Boolean, default=False)
    unassigned_reason = Column(String(255), nullable=True)
    assigned_vehicle_id = Column(Integer, nullable=True)
    stop_sequence = Column(Integer, nullable=True)
    estimated_arrival_minutes = Column(Integer, nullable=True)
    waiting_time_minutes = Column(Integer, default=0)
    service_start_minutes = Column(Integer, nullable=True)
    departure_minutes = Column(Integer, nullable=True)

    job = relationship("OptimizationJob", back_populates="orders")


class VehicleFleet(Base):
    __tablename__ = "fleet_vehicles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    capacity_kg = Column(Float, nullable=False, default=200.0)
    cost_per_km = Column(Float, nullable=False, default=15.0)
    shift_start_minutes = Column(Integer, default=480, nullable=False)  # 08:00 default
    shift_end_minutes = Column(Integer, default=1080, nullable=False)   # 18:00 default
    is_active = Column(Boolean, default=True)


class Route(Base):
    __tablename__ = "routes"

    id = Column(String(36), primary_key=True)
    job_id = Column(String(36), ForeignKey("optimization_jobs.id"), nullable=False)
    vehicle_id = Column(Integer, nullable=False)
    vehicle_name = Column(String(100), nullable=False)
    capacity_kg = Column(Float, default=500.0)

    # Metrics
    total_stops = Column(Integer, default=0)
    total_distance_km = Column(Float, default=0.0)
    driving_duration_minutes = Column(Float, default=0.0)
    service_duration_minutes = Column(Float, default=0.0)
    waiting_duration_minutes = Column(Float, default=0.0)
    total_duration_minutes = Column(Float, default=0.0)
    
    start_time_minutes = Column(Integer, default=480)
    end_time_minutes = Column(Integer, default=480)
    
    total_payload_kg = Column(Float, default=0.0)
    capacity_utilization_pct = Column(Float, default=0.0)
    operational_cost = Column(Float, default=0.0)

    # Geometry, Legs & Maneuvers
    geometry = Column(JSON, nullable=True)
    maneuvers = Column(JSON, nullable=True)
    ordered_stop_ids = Column(JSON, nullable=True)
    legs = Column(JSON, nullable=True)
    timeline = Column(JSON, nullable=True)
    validation_data = Column(JSON, nullable=True)

    job = relationship("OptimizationJob", back_populates="routes")

    @property
    def start_time_str(self) -> str:
        return minutes_to_clock_str(self.start_time_minutes or 480)

    @property
    def end_time_str(self) -> str:
        return minutes_to_clock_str(self.end_time_minutes or 480)

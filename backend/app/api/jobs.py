"""
Optimization Jobs API Router
Provides endpoints for manifest upload, polling status, canonical route retrieval, and Excel export.
"""
import io
import uuid
import asyncio
from datetime import datetime
from typing import List, Optional
import pandas as pd
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database.session import get_db, AsyncSessionLocal
from app.models.entities import OptimizationJob, Order, Route, VehicleFleet
from app.schemas.job import JobCreateResponse, JobStatusRead, JobDetailRead
from app.schemas.order import OrderRead
from app.schemas.route import RouteRead, RouteStopDetail, RouteLegDetail, OptimizationSummary
from app.services.pipeline import pipeline_orchestrator
from app.utils.time_utils import minutes_to_clock_str
from app.utils.logger import logger

router = APIRouter(prefix="/jobs", tags=["Optimization Jobs"])


async def run_pipeline_task(job_id: str, file_bytes: bytes, filename: str) -> None:
    """Background task runner with dedicated DB session."""
    async with AsyncSessionLocal() as session:
        await pipeline_orchestrator.execute_job(job_id, file_bytes, filename, session)


@router.post("/upload", response_model=JobCreateResponse)
async def upload_manifest_job(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload Excel/CSV manifest to create and trigger an asynchronous route optimization job.
    """
    if not file.filename.endswith((".xlsx", ".xls", ".csv")):
        raise HTTPException(
            status_code=400,
            detail="Invalid file extension. Please upload an Excel (.xlsx, .xls) or CSV (.csv) file."
        )

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    job_id = str(uuid.uuid4())
    job = OptimizationJob(
        id=job_id,
        filename=file.filename,
        status="PENDING",
        current_step="Manifest received, queuing optimization job",
        progress_percentage=0
    )
    db.add(job)
    await db.commit()

    background_tasks.add_task(run_pipeline_task, job_id, file_bytes, file.filename)

    logger.info(f"Accepted upload for job {job_id} ({file.filename})")
    return JobCreateResponse(
        job_id=job_id,
        filename=file.filename,
        status="PENDING",
        message="Manifest accepted. Optimization job started in background.",
        created_at=job.created_at
    )


@router.get("/{job_id}/status", response_model=JobStatusRead)
async def get_job_status(job_id: str, db: AsyncSession = Depends(get_db)):
    """
    Lightweight polling endpoint to track job progress through the pipeline stages.
    """
    job = await db.get(OptimizationJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Optimization job not found.")

    return JobStatusRead(
        job_id=job.id,
        filename=job.filename,
        status=job.status,
        current_step=job.current_step,
        progress_percentage=job.progress_percentage,
        error_message=job.error_message,
        created_at=job.created_at,
        completed_at=job.completed_at,
        total_orders=job.total_orders,
        assigned_orders=job.assigned_orders,
        unassigned_orders=job.unassigned_orders,
        vehicles_used=job.vehicles_used,
        total_distance_km=job.total_distance_km,
        total_duration_minutes=job.total_duration_minutes,
        total_cost=job.total_cost
    )


@router.get("/{job_id}", response_model=JobDetailRead)
async def get_job_details(job_id: str, db: AsyncSession = Depends(get_db)):
    """
    Returns full canonical job details, per-leg geometries, maneuvers, ETAs, and summary.
    """
    query = (
        select(OptimizationJob)
        .where(OptimizationJob.id == job_id)
        .options(selectinload(OptimizationJob.orders), selectinload(OptimizationJob.routes))
    )
    result = await db.execute(query)
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Optimization job not found.")

    # Format orders
    orders_read: List[OrderRead] = []
    order_dict = {}
    for o in job.orders:
        ord_read = OrderRead(
            id=o.id,
            job_id=o.job_id,
            external_order_id=o.external_order_id,
            raw_address=o.raw_address,
            resolved_address=o.resolved_address,
            latitude=o.latitude,
            longitude=o.longitude,
            parcel_weight_kg=o.parcel_weight_kg,
            service_time_minutes=o.service_time_minutes,
            window_start_minutes=o.window_start_minutes,
            window_end_minutes=o.window_end_minutes,
            geocoding_status=o.geocoding_status,
            geocoding_error=o.geocoding_error,
            is_assigned=o.is_assigned,
            unassigned_reason=o.unassigned_reason,
            assigned_vehicle_id=o.assigned_vehicle_id,
            stop_sequence=o.stop_sequence,
            estimated_arrival_minutes=o.estimated_arrival_minutes,
            estimated_arrival_time_str=minutes_to_clock_str(o.estimated_arrival_minutes) if o.estimated_arrival_minutes is not None else None
        )
        orders_read.append(ord_read)
        order_dict[o.id] = ord_read

    # Format routes with canonical legs and stops
    routes_read: List[RouteRead] = []
    for r in job.routes:
        stop_details: List[RouteStopDetail] = []
        ordered_ids = r.ordered_stop_ids or []

        for seq, oid in enumerate(ordered_ids, start=1):
            if oid in order_dict:
                o_obj = order_dict[oid]
                arr_min = o_obj.estimated_arrival_minutes or 0
                win_start = o_obj.window_start_minutes or 0
                win_end = o_obj.window_end_minutes or 1440

                waiting_mins = getattr(o_obj, "waiting_time_minutes", max(0, win_start - arr_min))
                service_mins = o_obj.service_time_minutes or 0
                service_start_mins = arr_min + waiting_mins
                departure_mins = service_start_mins + service_mins

                is_late = arr_min > win_end
                lateness = max(0, arr_min - win_end) if is_late else 0

                tw_status = "LATE_VIOLATION" if is_late else ("EARLY_WAITING" if waiting_mins > 0 else "ON_TIME")

                stop_details.append(RouteStopDetail(
                    sequence=seq,
                    stop_type="DELIVERY",
                    order_id=o_obj.id,
                    external_order_id=o_obj.external_order_id,
                    address=o_obj.resolved_address or o_obj.raw_address,
                    latitude=o_obj.latitude,
                    longitude=o_obj.longitude,
                    parcel_weight_kg=o_obj.parcel_weight_kg,
                    estimated_arrival_minutes=arr_min,
                    estimated_arrival_time_str=minutes_to_clock_str(arr_min),
                    waiting_time_minutes=waiting_mins,
                    service_start_minutes=service_start_mins,
                    service_start_time_str=minutes_to_clock_str(service_start_mins),
                    service_time_minutes=service_mins,
                    departure_minutes=departure_mins,
                    departure_time_str=minutes_to_clock_str(departure_mins),
                    window_start_minutes=win_start,
                    window_end_minutes=win_end,
                    window_start_str=minutes_to_clock_str(win_start),
                    window_end_str=minutes_to_clock_str(win_end),
                    is_late=is_late,
                    lateness_minutes=lateness,
                    time_window_status=tw_status
                ))

        # Parse stored legs
        legs_read: List[RouteLegDetail] = []
        if r.legs:
            for l_data in r.legs:
                legs_read.append(RouteLegDetail(**l_data))

        # Start and end time
        start_min = r.start_time_minutes or 420
        end_min = r.end_time_minutes or (start_min + round(r.total_duration_minutes))

        routes_read.append(RouteRead(
            id=r.id,
            vehicle_id=r.vehicle_id,
            vehicle_name=r.vehicle_name,
            capacity_kg=r.capacity_kg or 500.0,
            total_payload_kg=r.total_payload_kg or 0.0,
            capacity_utilization_pct=r.capacity_utilization_pct or 0.0,
            is_over_capacity=(r.total_payload_kg or 0.0) > (r.capacity_kg or 500.0),
            total_stops=r.total_stops or len(stop_details),
            total_distance_km=r.total_distance_km or 0.0,
            driving_duration_minutes=r.driving_duration_minutes or 0.0,
            service_duration_minutes=r.service_duration_minutes or 0.0,
            waiting_duration_minutes=r.waiting_duration_minutes or 0.0,
            total_duration_minutes=r.total_duration_minutes or 0.0,
            start_time_minutes=start_min,
            start_time_str=minutes_to_clock_str(start_min),
            end_time_minutes=end_min,
            end_time_str=minutes_to_clock_str(end_min),
            operational_cost=r.operational_cost or 0.0,
            warehouse_start={
                "name": settings.DEPOT_NAME,
                "latitude": settings.DEPOT_LATITUDE,
                "longitude": settings.DEPOT_LONGITUDE,
                "departure_time_str": minutes_to_clock_str(start_min)
            },
            warehouse_end={
                "name": settings.DEPOT_NAME,
                "latitude": settings.DEPOT_LATITUDE,
                "longitude": settings.DEPOT_LONGITUDE,
                "arrival_time_str": minutes_to_clock_str(end_min)
            },
            geometry=r.geometry,
            maneuvers=r.maneuvers,
            legs=legs_read,
            stops=stop_details,
            timeline=r.timeline or [],
            validation=r.validation_data or {}
        ))

    # Summary
    unassigned_list = [
        {"order_id": o.external_order_id, "address": o.raw_address, "reason": o.unassigned_reason or "Unknown"}
        for o in orders_read if not o.is_assigned
    ]

    avg_util = 0.0
    if routes_read:
        avg_util = round(sum(r.capacity_utilization_pct for r in routes_read) / len(routes_read), 1)

    summary = OptimizationSummary(
        total_orders=job.total_orders,
        assigned_orders=job.assigned_orders,
        unassigned_orders=job.unassigned_orders,
        vehicles_available=len(routes_read),
        vehicles_used=job.vehicles_used,
        total_distance_km=job.total_distance_km,
        total_driving_minutes=round(sum(r.driving_duration_minutes for r in routes_read), 1),
        total_service_minutes=round(sum(r.service_duration_minutes for r in routes_read), 1),
        total_waiting_minutes=round(sum(r.waiting_duration_minutes for r in routes_read), 1),
        total_duration_minutes=job.total_duration_minutes,
        total_cost=job.total_cost,
        average_capacity_utilization_pct=avg_util,
        unassigned_details=unassigned_list
    )

    return JobDetailRead(
        job_id=job.id,
        filename=job.filename,
        status=job.status,
        current_step=job.current_step,
        progress_percentage=job.progress_percentage,
        error_message=job.error_message,
        created_at=job.created_at,
        completed_at=job.completed_at,
        total_orders=job.total_orders,
        assigned_orders=job.assigned_orders,
        unassigned_orders=job.unassigned_orders,
        vehicles_used=job.vehicles_used,
        total_distance_km=job.total_distance_km,
        total_duration_minutes=job.total_duration_minutes,
        total_cost=job.total_cost,
        orders=orders_read,
        routes=routes_read,
        summary=summary
    )


@router.get("", response_model=List[JobStatusRead])
async def list_jobs(limit: int = 10, db: AsyncSession = Depends(get_db)):
    """Lists recent optimization jobs."""
    query = select(OptimizationJob).order_by(desc(OptimizationJob.created_at)).limit(limit)
    result = await db.execute(query)
    jobs = result.scalars().all()
    return [
        JobStatusRead(
            job_id=j.id,
            filename=j.filename,
            status=j.status,
            current_step=j.current_step,
            progress_percentage=j.progress_percentage,
            error_message=j.error_message,
            created_at=j.created_at,
            completed_at=j.completed_at,
            total_orders=j.total_orders,
            assigned_orders=j.assigned_orders,
            unassigned_orders=j.unassigned_orders,
            vehicles_used=j.vehicles_used,
            total_distance_km=j.total_distance_km,
            total_duration_minutes=j.total_duration_minutes,
            total_cost=j.total_cost
        )
        for j in jobs
    ]


@router.get("/{job_id}/export")
async def export_job_schedule(job_id: str, db: AsyncSession = Depends(get_db)):
    """
    Generates and downloads detailed multi-sheet Excel route schedule.
    """
    query = (
        select(OptimizationJob)
        .where(OptimizationJob.id == job_id)
        .options(selectinload(OptimizationJob.orders), selectinload(OptimizationJob.routes))
    )
    result = await db.execute(query)
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Optimization job not found.")

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        # Sheet 1: Master Schedule
        schedule_rows = []
        for r in job.routes:
            for t in (r.timeline or []):
                schedule_rows.append({
                    "Vehicle ID": r.vehicle_id,
                    "Vehicle Name": r.vehicle_name,
                    "Stop Sequence": t.get("sequence", 0),
                    "Stop Type": t.get("type", "DELIVERY"),
                    "Order ID": t.get("external_order_id", "N/A"),
                    "Address / Location": t.get("address", ""),
                    "Arrival Time (ETA)": t.get("arrival_time_str", ""),
                    "Waiting Duration (mins)": t.get("waiting_minutes", 0),
                    "Service Duration (mins)": t.get("service_minutes", 0),
                    "Departure Time": t.get("departure_time_str", ""),
                    "Time Window Start": t.get("window_start_str", ""),
                    "Time Window End": t.get("window_end_str", ""),
                    "Time Window Status": t.get("time_window_status", "ON_TIME"),
                    "Parcel Weight (kg)": t.get("weight_kg", 0.0)
                })

        if schedule_rows:
            pd.DataFrame(schedule_rows).to_excel(writer, sheet_name="Master Delivery Schedule", index=False)

        # Sheet 2: Vehicle Fleet Summary
        fleet_rows = []
        for r in job.routes:
            fleet_rows.append({
                "Vehicle ID": r.vehicle_id,
                "Vehicle Name": r.vehicle_name,
                "Capacity (kg)": r.capacity_kg,
                "Total Payload (kg)": r.total_payload_kg,
                "Capacity Utilization (%)": f"{r.capacity_utilization_pct}%",
                "Total Stops": r.total_stops,
                "Total Distance (km)": r.total_distance_km,
                "Driving Time (hours)": round(r.driving_duration_minutes / 60.0, 2),
                "Service Time (hours)": round(r.service_duration_minutes / 60.0, 2),
                "Waiting Time (hours)": round(r.waiting_duration_minutes / 60.0, 2),
                "Total Route Time (hours)": round(r.total_duration_minutes / 60.0, 2),
                "Shift Start Time": minutes_to_clock_str(r.start_time_minutes or 420),
                "Warehouse Return Time": minutes_to_clock_str(r.end_time_minutes or 420),
                "Operational Cost (INR)": r.operational_cost
            })
        if fleet_rows:
            pd.DataFrame(fleet_rows).to_excel(writer, sheet_name="Fleet Route Summary", index=False)

    output.seek(0)
    filename = f"Optimized_Delivery_Schedule_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

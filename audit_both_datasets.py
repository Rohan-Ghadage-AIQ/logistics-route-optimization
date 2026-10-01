import asyncio
import os
import sys
import uuid

sys.path.insert(0, os.path.abspath("backend"))

from app.database.session import AsyncSessionLocal, init_db
from app.models.entities import OptimizationJob
from app.services.pipeline import pipeline_orchestrator
from sqlalchemy import select
from sqlalchemy.orm import selectinload

async def run_audit(file_path, filename):
    print(f"\n========================================================")
    print(f"RUNNING AUDIT ON: {filename} ({file_path})")
    print(f"========================================================")
    
    await init_db()
    job_id = str(uuid.uuid4())
    with open(file_path, "rb") as f:
        file_bytes = f.read()
        
    async with AsyncSessionLocal() as db:
        job = OptimizationJob(id=job_id, filename=filename, status="PENDING")
        db.add(job)
        await db.commit()
        await pipeline_orchestrator.execute_job(job_id, file_bytes, filename, db)
    
    async with AsyncSessionLocal() as db:
        stmt = select(OptimizationJob).where(OptimizationJob.id == job_id).options(
            selectinload(OptimizationJob.routes), 
            selectinload(OptimizationJob.orders)
        )
        res = await db.execute(stmt)
        finished_job = res.scalar_one_or_none()
        
        print(f"Job Status: {finished_job.status}")
        print(f"Total Orders: {finished_job.total_orders} | Assigned: {finished_job.assigned_orders} | Unassigned: {finished_job.unassigned_orders}")
        print(f"Fleet Used: {finished_job.vehicles_used} vehicles | Total Distance: {finished_job.total_distance_km} km | Total Cost: Rs {finished_job.total_cost}")
        print(f"Total Schedule Duration: {finished_job.total_duration_minutes} min ({(finished_job.total_duration_minutes/60):.2f} hrs)")
        
        bugs_found = []
        for r in finished_job.routes:
            # 1. Math equation check: Driving + Service + Waiting == Total
            expected_total = round(r.driving_duration_minutes + r.service_duration_minutes + r.waiting_duration_minutes, 1)
            actual_total = round(r.total_duration_minutes, 1)
            if abs(expected_total - actual_total) > 0.5:
                bugs_found.append(f"Math discrepancy in {r.vehicle_name}: Driving({r.driving_duration_minutes}) + Svc({r.service_duration_minutes}) + Wait({r.waiting_duration_minutes}) = {expected_total} != Total({actual_total})")
            
            # 2. Shift bounds check
            if r.start_time_minutes > r.end_time_minutes:
                bugs_found.append(f"Inverted timeline in {r.vehicle_name}: Start({r.start_time_minutes}) > End({r.end_time_minutes})")
                
            # 3. Payload capacity check
            if r.total_payload_kg > r.capacity_kg:
                bugs_found.append(f"Overcapacity in {r.vehicle_name}: Payload({r.total_payload_kg}kg) > Capacity({r.capacity_kg}kg)")
                
            print(f"\n  [{r.vehicle_name}]")
            print(f"    Stops: {r.total_stops} deliveries | Payload: {r.total_payload_kg}/{r.capacity_kg} kg ({r.capacity_utilization_pct}%)")
            print(f"    Timeline: {r.start_time_str} -> {r.end_time_str}")
            print(f"    Distance: {r.total_distance_km} km")
            print(f"    Durations: Driving={r.driving_duration_minutes}m, Service={r.service_duration_minutes}m, Waiting={r.waiting_duration_minutes}m, Total={r.total_duration_minutes}m")
            print(f"    Legs count: {len(r.legs or [])} | Maneuvers count: {len(r.maneuvers or [])}")
        
        if bugs_found:
            print(f"\n  [!] BUGS FOUND ({len(bugs_found)}):")
            for b in bugs_found:
                print(f"    - {b}")
        else:
            print(f"\n  [✓] ZERO INCONSISTENCY BUGS FOUND. ALL EQUATIONS BALANCED.")

async def main():
    if os.path.exists("data/sample_orders.xlsx"):
        await run_audit("data/sample_orders.xlsx", "sample_orders.xlsx")
    if os.path.exists("converted_stations_addresses_new.csv"):
        await run_audit("converted_stations_addresses_new.csv", "converted_stations_addresses_new.csv")

if __name__ == "__main__":
    asyncio.run(main())

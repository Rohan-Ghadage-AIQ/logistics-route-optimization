import asyncio
import os
import sys
import uuid

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath("backend"))

from app.database.session import AsyncSessionLocal, init_db
from app.models.entities import OptimizationJob
from app.services.pipeline import pipeline_orchestrator
from sqlalchemy import select
from sqlalchemy.orm import selectinload

async def main():
    await init_db()
    job_id = str(uuid.uuid4())
    excel_path = os.path.abspath("data/sample_orders.xlsx")
    with open(excel_path, "rb") as f:
        file_bytes = f.read()
        
    async with AsyncSessionLocal() as db:
        job = OptimizationJob(id=job_id, filename="sample_orders.xlsx", status="PENDING")
        db.add(job)
        await db.commit()
    
        print(f"Starting pipeline test for job {job_id} on {excel_path}...")
        await pipeline_orchestrator.execute_job(job_id, file_bytes, "sample_orders.xlsx", db)
    
    async with AsyncSessionLocal() as db:
        stmt = select(OptimizationJob).where(OptimizationJob.id == job_id).options(selectinload(OptimizationJob.routes), selectinload(OptimizationJob.orders))
        res = await db.execute(stmt)
        finished_job = res.scalar_one_or_none()
        
        print(f"\n================ PIPELINE EXECUTION SUMMARY ================")
        print(f"Pipeline Result Status: {finished_job.status}")
        print(f"Total Distance: {finished_job.total_distance_km} km")
        print(f"Total Duration: {finished_job.total_duration_minutes} min ({(finished_job.total_duration_minutes/60):.2f} hrs)")
        print(f"Total Orders: {finished_job.total_orders}, Assigned: {finished_job.assigned_orders}, Unassigned: {finished_job.unassigned_orders}")
        print(f"Routes count: {len(finished_job.routes)}")
        
        for r in finished_job.routes:
            print(f"\n------------------------------------------------------------")
            print(f"VEHICLE: {r.vehicle_name} (Capacity: {r.capacity_kg} kg, Payload: {r.total_payload_kg} kg, Util: {r.capacity_utilization_pct}%)")
            print(f"  Stops Assigned: {r.total_stops}")
            print(f"  Total Distance: {r.total_distance_km} km")
            print(f"  Driving Duration: {r.driving_duration_minutes} mins ({(r.driving_duration_minutes/60):.2f} hrs)")
            print(f"  Service Duration: {r.service_duration_minutes} mins ({(r.service_duration_minutes/60):.2f} hrs)")
            print(f"  Waiting Duration: {r.waiting_duration_minutes} mins ({(r.waiting_duration_minutes/60):.2f} hrs)")
            print(f"  Total Route Duration: {r.total_duration_minutes} mins ({(r.total_duration_minutes/60):.2f} hrs)")
            print(f"  Schedule Span: {r.start_time_str} -> {r.end_time_str}")
            print(f"  Legs count: {len(r.legs or [])}, Maneuvers: {len(r.maneuvers or [])}")
            
            # Check duration math consistency
            expected_total = round(r.driving_duration_minutes + r.service_duration_minutes + r.waiting_duration_minutes, 1)
            actual_total = round(r.total_duration_minutes, 1)
            math_check = "PASS" if abs(expected_total - actual_total) < 0.2 else "FAIL"
            print(f"  Mathematical Consistency Check (Driving + Service + Waiting == Total): {math_check} ({expected_total} vs {actual_total})")
            
            if r.validation_data:
                val = r.validation_data
                print(f"  Validation status: is_valid = {val.get('is_valid')}")
                if val.get('errors'):
                    print(f"    Errors: {val.get('errors')}")
                if val.get('warnings'):
                    print(f"    Warnings: {val.get('warnings')}")

if __name__ == "__main__":
    asyncio.run(main())

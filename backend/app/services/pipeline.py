"""
End-to-End Route Optimization Pipeline Orchestrator
Coordinates: Validation -> Geocoding -> Valhalla Matrix -> Optimization -> Canonical Route Building -> Persistence
"""
import uuid
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.entities import OptimizationJob, Order, VehicleFleet, Route
from app.services.excel_parser import ManifestParser
from app.services.geocoding.factory import geocoding_service
from app.services.valhalla.client import valhalla_client
from app.services.optimization.ortools_solver import OrToolsRouteOptimizer
from app.services.optimization.base import LocationPoint, VehicleEntity
from app.services.route_builder import route_builder
from app.utils.time_utils import minutes_to_clock_str
from app.utils.logger import logger


class OptimizationPipeline:
    """Manages asynchronous job lifecycle and executes the optimization pipeline."""

    def __init__(self):
        self.geocoder = geocoding_service
        self.valhalla = valhalla_client
        self.solver = OrToolsRouteOptimizer()

    async def execute_job(self, job_id: str, file_bytes: bytes, filename: str, session: AsyncSession) -> None:
        """Executes full multi-stage optimization pipeline for a job."""
        job = await session.get(OptimizationJob, job_id)
        if not job:
            logger.error(f"Job {job_id} not found in database.")
            return

        try:
            # =========================================================
            # STAGE 1: VALIDATION & PARSING
            # =========================================================
            job.status = "VALIDATING"
            job.current_step = "Validating and parsing Excel manifest"
            job.progress_percentage = 10
            await session.commit()

            parsed_orders, errors, warnings = ManifestParser.parse_file(file_bytes, filename)
            if errors and not parsed_orders:
                raise ValueError("; ".join(errors))

            # Persist parsed orders to DB
            db_orders: List[Order] = []
            for item in parsed_orders:
                order_id = str(uuid.uuid4())
                db_order = Order(
                    id=order_id,
                    job_id=job_id,
                    external_order_id=item["external_order_id"],
                    raw_address=item["raw_address"],
                    latitude=item["latitude"],
                    longitude=item["longitude"],
                    parcel_weight_kg=item["parcel_weight_kg"],
                    service_time_minutes=item["service_time_minutes"],
                    window_start_minutes=item["window_start_minutes"],
                    window_end_minutes=item["window_end_minutes"],
                    geocoding_status="PROVIDED" if item["latitude"] and item["longitude"] else "PENDING"
                )
                session.add(db_order)
                db_orders.append(db_order)

            job.total_orders = len(db_orders)
            await session.commit()

            # =========================================================
            # STAGE 2: GEOCODING
            # =========================================================
            job.status = "GEOCODING"
            job.current_step = "Resolving delivery addresses to geographic coordinates"
            job.progress_percentage = 30
            await session.commit()

            orders_to_geocode = [o for o in db_orders if o.latitude is None or o.longitude is None]
            if orders_to_geocode:
                addresses = [o.raw_address for o in orders_to_geocode]
                geocode_results = await self.geocoder.geocode_batch(addresses)

                for db_order, res in zip(orders_to_geocode, geocode_results):
                    if res.success and res.latitude and res.longitude:
                        db_order.latitude = res.latitude
                        db_order.longitude = res.longitude
                        db_order.resolved_address = res.resolved_address
                        db_order.geocoding_status = "CACHED" if res.is_cached else "RESOLVED"
                    else:
                        db_order.geocoding_status = "FAILED"
                        db_order.geocoding_error = res.error or "Could not resolve address to coordinates"

                await session.commit()

            valid_orders = [o for o in db_orders if o.latitude is not None and o.longitude is not None]
            if not valid_orders:
                raise ValueError("All addresses failed geocoding. Please verify address validity in manifest.")

            # =========================================================
            # STAGE 3: LOGISTICS DEPOT DETERMINATION & MATRIX COMPUTATION
            # =========================================================
            job.status = "MATRIX_GENERATION"
            job.progress_percentage = 50
            
            # Check if any uploaded order is explicitly marked as a depot
            depot_order = next((o for o in valid_orders if "depot" in (o.raw_address or "").lower() or "warehouse" in (o.raw_address or "").lower() or o.external_order_id in ["0", "DEPOT", "HUB"]), None)

            if depot_order:
                depot_coords = (depot_order.latitude, depot_order.longitude)
                depot_name = depot_order.resolved_address or depot_order.raw_address or "Central Fulfillment Depot"
                valid_orders = [o for o in valid_orders if o.id != depot_order.id]
            else:
                mean_lat = sum(o.latitude for o in valid_orders) / len(valid_orders)
                mean_lon = sum(o.longitude for o in valid_orders) / len(valid_orders)
                dist_to_cfg = ((mean_lat - settings.DEPOT_LATITUDE)**2 + (mean_lon - settings.DEPOT_LONGITUDE)**2)**0.5
                if dist_to_cfg < 0.15:
                    depot_coords = (settings.DEPOT_LATITUDE, settings.DEPOT_LONGITUDE)
                    depot_name = settings.DEPOT_NAME
                else:
                    depot_coords = (round(mean_lat, 4), round(mean_lon, 4))
                    depot_name = f"Logistics Dispatch Hub ({round(mean_lat, 3)}N, {round(mean_lon, 3)}E)"

            job.current_step = f"Computing road network travel matrix for {len(valid_orders) + 1} locations from {depot_name}"
            await session.commit()

            all_coords = [depot_coords] + [(o.latitude, o.longitude) for o in valid_orders]

            matrix_result = await self.valhalla.compute_matrix(all_coords)
            time_matrix = matrix_result["time_matrix_seconds"]
            dist_matrix = matrix_result["dist_matrix_meters"]

            # =========================================================
            # STAGE 4: ROUTE OPTIMIZATION (OR-TOOLS CVRPTW)
            # =========================================================
            job.status = "OPTIMIZING"
            job.current_step = "Solving CVRPTW with fleet capacities, driver shifts & time windows"
            job.progress_percentage = 70
            await session.commit()

            fleet_result = await session.execute(
                select(VehicleFleet).where(VehicleFleet.is_active == True)
            )
            fleet_list = fleet_result.scalars().all()
            fleet_map = {v.id: v for v in fleet_list}

            fleet_entities = [
                VehicleEntity(
                    id=v.id,
                    name=v.name,
                    capacity_kg=v.capacity_kg,
                    cost_per_km=v.cost_per_km,
                    shift_start_minutes=v.shift_start_minutes,
                    shift_end_minutes=v.shift_end_minutes,
                    is_active=v.is_active
                )
                for v in fleet_list
            ]

            depot_location = LocationPoint(
                id="DEPOT",
                name=depot_name,
                latitude=depot_coords[0],
                longitude=depot_coords[1],
                demand_kg=0.0,
                service_time_minutes=settings.DEPOT_LOADING_DURATION_MINUTES
            )

            order_locations = [
                LocationPoint(
                    id=o.id,
                    name=o.external_order_id,
                    latitude=o.latitude,
                    longitude=o.longitude,
                    demand_kg=o.parcel_weight_kg,
                    service_time_minutes=o.service_time_minutes,
                    window_start_minutes=o.window_start_minutes,
                    window_end_minutes=o.window_end_minutes
                )
                for o in valid_orders
            ]

            solver_output = await self.solver.solve(
                depot=depot_location,
                orders=order_locations,
                fleet=fleet_entities,
                time_matrix_seconds=time_matrix,
                dist_matrix_meters=dist_matrix
            )

            if not solver_output.success:
                raise ValueError(solver_output.error_message or "Solver could not find a feasible solution.")

            # =========================================================
            # STAGE 5: CANONICAL ROUTE BUILDING & VALIDATION
            # =========================================================
            job.status = "ROUTE_GENERATION"
            job.current_step = "Constructing canonical route objects, leg breakdowns & ETAs"
            job.progress_percentage = 85
            await session.commit()

            order_map = {o.id: o for o in db_orders}
            total_global_km = 0.0
            total_global_driving_mins = 0.0
            total_global_service_mins = 0.0
            total_global_waiting_mins = 0.0
            total_global_dur_mins = 0.0
            total_global_cost = 0.0
            assigned_order_count = 0
            built_routes: List[Route] = []

            for route_plan in solver_output.routes:
                v_obj = fleet_map.get(route_plan.vehicle_id)
                if not v_obj:
                    continue

                assigned_orders_for_vehicle: List[Order] = []
                for stop_id in route_plan.ordered_stop_ids:
                    if stop_id != "DEPOT" and stop_id in order_map:
                        db_order = order_map[stop_id]
                        db_order.is_assigned = True
                        db_order.assigned_vehicle_id = route_plan.vehicle_id
                        assigned_orders_for_vehicle.append(db_order)

                if not assigned_orders_for_vehicle:
                    continue

                canonical_res = await route_builder.build_route(
                    job_id=job_id,
                    vehicle=v_obj,
                    assigned_orders=assigned_orders_for_vehicle,
                    depot_coords=depot_coords,
                    depot_name=depot_name
                )

                if not canonical_res:
                    continue

                db_route: Route = canonical_res["db_route"]
                stops_detail = canonical_res["stops_detail"]

                # Fixed dispatch + (Distance * cost_per_km)
                fixed_cost = settings.FIXED_VEHICLE_DISPATCH_COST
                km_cost = db_route.total_distance_km * (v_obj.cost_per_km or 12.0)
                vehicle_cost = round(fixed_cost + km_cost, 2)
                db_route.operational_cost = vehicle_cost

                for s_item in stops_detail:
                    if s_item.order_id and s_item.order_id in order_map:
                        ord_obj = order_map[s_item.order_id]
                        ord_obj.stop_sequence = s_item.sequence
                        ord_obj.estimated_arrival_minutes = s_item.estimated_arrival_minutes
                        ord_obj.waiting_time_minutes = s_item.waiting_time_minutes
                        ord_obj.service_start_minutes = s_item.service_start_minutes
                        ord_obj.departure_minutes = s_item.departure_minutes

                session.add(db_route)
                built_routes.append(db_route)

                total_global_km += db_route.total_distance_km
                total_global_driving_mins += db_route.driving_duration_minutes
                total_global_service_mins += db_route.service_duration_minutes
                total_global_waiting_mins += db_route.waiting_duration_minutes
                total_global_dur_mins += db_route.total_duration_minutes
                total_global_cost += vehicle_cost
                assigned_order_count += len(assigned_orders_for_vehicle)

            unassigned_details = []
            for o in db_orders:
                if not o.is_assigned:
                    o.unassigned_reason = o.geocoding_error or "Time window or fleet capacity constraint exceeded"
                    unassigned_details.append({
                        "order_id": o.external_order_id,
                        "address": o.raw_address,
                        "reason": o.unassigned_reason
                    })

            avg_util = 0.0
            if built_routes:
                avg_util = round(sum(r.capacity_utilization_pct for r in built_routes) / len(built_routes), 1)

            # =========================================================
            # STAGE 6: FINAL PERSISTENCE & AUDIT SUMMARY
            # =========================================================
            job.status = "COMPLETED"
            job.current_step = "Optimization and route generation complete"
            job.progress_percentage = 100
            job.completed_at = datetime.utcnow()
            job.assigned_orders = assigned_order_count
            job.unassigned_orders = len(unassigned_details)
            job.vehicles_used = len(built_routes)
            job.total_distance_km = round(total_global_km, 2)
            job.total_duration_minutes = round(total_global_dur_mins, 1)
            job.total_cost = round(total_global_cost, 2)

            job.summary_data = {
                "total_orders": job.total_orders,
                "assigned_orders": job.assigned_orders,
                "unassigned_orders": job.unassigned_orders,
                "vehicles_available": len(fleet_list),
                "vehicles_used": job.vehicles_used,
                "total_distance_km": job.total_distance_km,
                "total_driving_minutes": round(total_global_driving_mins, 1),
                "total_service_minutes": round(total_global_service_mins, 1),
                "total_waiting_minutes": round(total_global_waiting_mins, 1),
                "total_duration_minutes": job.total_duration_minutes,
                "total_cost": job.total_cost,
                "average_capacity_utilization_pct": avg_util,
                "depot_name": depot_name,
                "depot_coords": depot_coords,
                "unassigned_details": unassigned_details
            }

            await session.commit()
            logger.info(
                f"Job {job_id} successfully completed: {assigned_order_count} assigned, "
                f"{len(unassigned_details)} unassigned, {len(built_routes)} vehicles used, "
                f"{job.total_distance_km} km total distance."
            )

        except Exception as e:
            logger.error(f"Pipeline error for Job {job_id}: {e}", exc_info=True)
            job.status = "FAILED"
            job.current_step = "Pipeline Execution Failed"
            job.error_message = str(e)
            await session.commit()
            raise


pipeline_orchestrator = OptimizationPipeline()

"""
Google OR-Tools CVRPTW Solver Implementation
Applies constraint programming and Guided Local Search to the Valhalla distance/duration matrix.
Optimizes vehicle shifts, minimizes idle waiting time, and enforces time-window adherence.
"""
import time
from typing import List, Dict, Any, Tuple
from ortools.constraint_solver import routing_enums_pb2, pywrapcp

from app.config import settings
from app.services.optimization.base import (
    BaseRouteOptimizer, LocationPoint, VehicleEntity, VehicleRoutePlan, SolverOutput
)
from app.services.optimization.constraints import (
    VehicleCapacityConstraint, TimeWindowConstraint, DriverShiftConstraint,
    DropDisjunctionConstraint, FleetActivationConstraint
)
from app.utils.time_utils import normalize_shift
from app.utils.logger import logger


class OrToolsRouteOptimizer(BaseRouteOptimizer):
    """Production-grade CVRPTW Optimizer using Google OR-Tools."""

    def __init__(self):
        self.capacity_constraint = VehicleCapacityConstraint()
        self.time_window_constraint = TimeWindowConstraint()
        self.driver_shift_constraint = DriverShiftConstraint()
        self.drop_constraint = DropDisjunctionConstraint()
        self.fleet_activation_constraint = FleetActivationConstraint()

    async def solve(
        self,
        depot: LocationPoint,
        orders: List[LocationPoint],
        fleet: List[VehicleEntity],
        time_matrix_seconds: List[List[int]],
        dist_matrix_meters: List[List[int]]
    ) -> SolverOutput:
        start_time = time.perf_counter()

        active_fleet = [v for v in fleet if v.is_active]
        if not active_fleet:
            return SolverOutput(
                success=False,
                status="NO_ACTIVE_VEHICLES",
                error_message="No active fleet vehicles available for dispatch."
            )

        if not orders:
            return SolverOutput(
                success=True,
                status="EMPTY_ORDERS",
                solver_time_seconds=0.0
            )

        all_locations = [depot] + orders
        num_locations = len(all_locations)
        num_vehicles = len(active_fleet)

        # 1. Routing Index Manager & Model Setup
        manager = pywrapcp.RoutingIndexManager(num_locations, num_vehicles, 0)
        routing = pywrapcp.RoutingModel(manager)

        # 2. Time Transit Callback (Discretized minutes + service duration)
        node_service_times = [loc.service_time_minutes for loc in all_locations]
        node_service_times[0] = settings.DEPOT_LOADING_DURATION_MINUTES

        def time_callback(from_idx: int, to_idx: int) -> int:
            from_node = manager.IndexToNode(from_idx)
            to_node = manager.IndexToNode(to_idx)
            raw_seconds = time_matrix_seconds[from_node][to_node]
            if from_node != to_node:
                travel_mins = max(1, round(raw_seconds / 60.0))
            else:
                travel_mins = 0
            return travel_mins + node_service_times[from_node]

        time_callback_idx = routing.RegisterTransitCallback(time_callback)

        # Calculate time dimension horizon
        normalized_shifts = [
            normalize_shift(v.shift_start_minutes, v.shift_end_minutes)
            for v in active_fleet
        ]
        max_shift_end = max(end for _, end in normalized_shifts) if normalized_shifts else 1440
        max_window_end = max(loc.window_end_minutes for loc in orders) if orders else 1440
        horizon = max(max_shift_end + 120, max_window_end) + 120

        # Maximum slack waiting allowed between successive stops
        routing.AddDimension(
            time_callback_idx,
            settings.OPTIMIZATION_WAITING_SLACK_MINUTES,
            horizon,
            False,
            "Time"
        )
        time_dimension = routing.GetDimensionOrDie("Time")

        # Heavily penalize route span (driving + waiting + service) to eliminate unnecessary waiting
        time_dimension.SetSpanCostCoefficientForAllVehicles(settings.WAITING_SPAN_PENALTY_WEIGHT)

        # 3. Apply Customer Time Windows & Restrict to Compatible Vehicle Shifts
        for i, order in enumerate(orders, start=1):
            index = manager.NodeToIndex(i)
            # Hard lower bound: Customer opening time
            time_dimension.CumulVar(index).SetRange(order.window_start_minutes, horizon)
            # Soft upper bound: Customer deadline penalty
            time_dimension.SetCumulVarSoftUpperBound(
                index,
                order.window_end_minutes,
                self.time_window_constraint.penalty_per_minute_late
            )

            # Match order to vehicle shifts overlapping with delivery window (eliminates cross-shift waiting)
            allowed_vehicles = []
            for v_idx, (s_start, s_end) in enumerate(normalized_shifts):
                if s_start <= (order.window_end_minutes + 60) and s_end >= (order.window_start_minutes - 60):
                    allowed_vehicles.append(v_idx)

            if allowed_vehicles and len(allowed_vehicles) < num_vehicles:
                routing.VehicleVar(index).SetValues(allowed_vehicles)

        # 4. Vehicle Departure / Return / Shifts & Overtime Constraints
        for v_idx, vehicle in enumerate(active_fleet):
            shift_start, shift_end = normalized_shifts[v_idx]

            start_idx = routing.Start(v_idx)
            end_idx = routing.End(v_idx)

            # Departure window: driver starts during shift
            time_dimension.CumulVar(start_idx).SetRange(shift_start, shift_end)

            # Hard return ceiling: shift_end + overtime buffer
            overtime_limit = min(shift_end + self.driver_shift_constraint.overtime_buffer_minutes, horizon)
            time_dimension.CumulVar(end_idx).SetRange(shift_start, overtime_limit)

            # Soft penalty: penalize returning past normal shift_end
            time_dimension.SetCumulVarSoftUpperBound(
                end_idx,
                shift_end,
                self.driver_shift_constraint.overtime_penalty_per_minute
            )

            # Minimize start and end variables for compact schedule
            routing.AddVariableMinimizedByFinalizer(time_dimension.CumulVar(start_idx))
            routing.AddVariableMinimizedByFinalizer(time_dimension.CumulVar(end_idx))

            # Fixed vehicle dispatch fee
            routing.SetFixedCostOfVehicle(self.fleet_activation_constraint.fixed_cost, v_idx)

        # 5. Disjunction Drop Penalty (Ensure all parcels are assigned)
        for i in range(1, num_locations):
            routing.AddDisjunction([manager.NodeToIndex(i)], self.drop_constraint.penalty)

        # 6. Cost Transit Callback per Vehicle
        vehicle_rates = [v.cost_per_km for v in active_fleet]

        def create_cost_evaluator(v_index: int):
            cost_per_m = vehicle_rates[v_index] / 1000.0
            def cost_cb(from_idx: int, to_idx: int) -> int:
                from_node = manager.IndexToNode(from_idx)
                to_node = manager.IndexToNode(to_idx)
                dist_m = dist_matrix_meters[from_node][to_node]
                return int(dist_m * cost_per_m * 100)
            return cost_cb

        for v_idx in range(num_vehicles):
            cb = create_cost_evaluator(v_idx)
            cb_idx = routing.RegisterTransitCallback(cb)
            routing.SetArcCostEvaluatorOfVehicle(cb_idx, v_idx)

        # 7. Capacity Dimension
        node_demands = [0] + [int(loc.demand_kg) for loc in orders]

        def demand_cb(from_idx: int) -> int:
            return node_demands[manager.IndexToNode(from_idx)]

        demand_cb_idx = routing.RegisterUnaryTransitCallback(demand_cb)
        relaxed_caps = [
            self.capacity_constraint.get_relaxed_capacity(v.capacity_kg)
            for v in active_fleet
        ]

        routing.AddDimensionWithVehicleCapacity(
            demand_cb_idx,
            0,
            relaxed_caps,
            True,
            "Capacity"
        )
        cap_dimension = routing.GetDimensionOrDie("Capacity")

        for v_idx, vehicle in enumerate(active_fleet):
            nom_cap = int(vehicle.capacity_kg)
            for i in range(1, num_locations):
                index = manager.NodeToIndex(i)
                cap_dimension.SetCumulVarSoftUpperBound(
                    index,
                    nom_cap,
                    self.capacity_constraint.penalty_per_kg
                )

        # 8. Solver Search Parameters
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION
        )
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        search_parameters.time_limit.seconds = settings.OPTIMIZATION_SOLVER_TIME_LIMIT_SECONDS
        search_parameters.log_search = False

        # 9. Solve
        solution = routing.SolveWithParameters(search_parameters)
        elapsed_seconds = round(time.perf_counter() - start_time, 2)

        if not solution:
            return SolverOutput(
                success=False,
                status="INFEASIBLE",
                error_message="OR-Tools solver could not find a feasible solution within time/capacity constraints.",
                solver_time_seconds=elapsed_seconds
            )

        # 10. Extract Routes & Timelines
        routes: List[VehicleRoutePlan] = []
        unassigned_node_indices: List[int] = []

        for i in range(1, num_locations):
            index = manager.NodeToIndex(i)
            if solution.Value(routing.NextVar(index)) == index:
                unassigned_node_indices.append(i)

        for v_idx, vehicle in enumerate(active_fleet):
            if not routing.IsVehicleUsed(solution, v_idx):
                continue

            index = routing.Start(v_idx)
            ordered_nodes = []
            arrival_times = []
            service_times = []
            waiting_times = []

            route_dist_m = 0
            route_demand = 0.0

            prev_departure = solution.Min(time_dimension.CumulVar(index))
            start_time_min = prev_departure

            while not routing.IsEnd(index):
                node_idx = manager.IndexToNode(index)
                ordered_nodes.append(node_idx)

                arrival_min = solution.Min(time_dimension.CumulVar(index))
                arrival_times.append(arrival_min)
                svc_time = node_service_times[node_idx]
                service_times.append(svc_time)

                wait_min = max(0, arrival_min - prev_departure)
                waiting_times.append(wait_min)

                prev_departure = arrival_min + svc_time
                route_demand += node_demands[node_idx]

                next_index = solution.Value(routing.NextVar(index))
                next_node = manager.IndexToNode(next_index)
                route_dist_m += dist_matrix_meters[node_idx][next_node]
                index = next_index

            end_time_min = solution.Min(time_dimension.CumulVar(index))

            ordered_stop_ids = [
                all_locations[n].id if n != 0 else "DEPOT"
                for n in ordered_nodes
            ]

            if len(ordered_nodes) > 1:
                util_pct = round((route_demand / max(1.0, vehicle.capacity_kg)) * 100.0, 1)

                route_plan = VehicleRoutePlan(
                    vehicle_id=vehicle.id,
                    vehicle_name=vehicle.name,
                    ordered_stop_indices=ordered_nodes,
                    ordered_stop_ids=ordered_stop_ids,
                    arrival_times_minutes=arrival_times,
                    total_payload_kg=round(route_demand, 1),
                    capacity_utilization_pct=util_pct,
                    total_distance_km=round(route_dist_m / 1000.0, 2),
                    total_duration_minutes=float(max(1, end_time_min - start_time_min))
                )
                routes.append(route_plan)

        unassigned_ids = [all_locations[n].id for n in unassigned_node_indices]

        logger.info(
            f"Optimization finished in {elapsed_seconds}s: "
            f"{len(routes)} vehicles used, {num_locations - 1 - len(unassigned_ids)}/{num_locations - 1} orders assigned."
        )

        return SolverOutput(
            success=True,
            status="SUCCESS" if len(unassigned_ids) == 0 else "PARTIAL",
            routes=routes,
            unassigned_order_ids=unassigned_ids,
            solver_time_seconds=elapsed_seconds
        )

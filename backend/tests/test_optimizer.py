"""
Unit Tests for OR-Tools CVRPTW Route Optimizer
"""
from app.services.optimization.ortools_solver import OrToolsRouteOptimizer
from app.services.optimization.base import LocationPoint, VehicleEntity


async def test_ortools_solver_basic_assignment():
    solver = OrToolsRouteOptimizer()

    depot = LocationPoint(
        id="DEPOT", name="Central Depot", latitude=19.055, longitude=72.875
    )

    orders = [
        LocationPoint(id="ORD-1", name="Stop 1", latitude=19.119, longitude=72.845, demand_kg=20.0, window_start_minutes=480, window_end_minutes=720),
        LocationPoint(id="ORD-2", name="Stop 2", latitude=19.061, longitude=72.836, demand_kg=15.0, window_start_minutes=480, window_end_minutes=720),
        LocationPoint(id="ORD-3", name="Stop 3", latitude=19.118, longitude=72.911, demand_kg=25.0, window_start_minutes=600, window_end_minutes=900),
    ]

    fleet = [
        VehicleEntity(id=1, name="Van 1", capacity_kg=100.0, cost_per_km=15.0, shift_start_minutes=480, shift_end_minutes=1080),
        VehicleEntity(id=2, name="Van 2", capacity_kg=100.0, cost_per_km=15.0, shift_start_minutes=480, shift_end_minutes=1080),
    ]

    # Simplified 4x4 mock matrices (depot + 3 orders)
    time_matrix = [
        [0, 900, 600, 1200],
        [900, 0, 800, 1100],
        [600, 800, 0, 1400],
        [1200, 1100, 1400, 0]
    ]

    dist_matrix = [
        [0, 10000, 7000, 15000],
        [10000, 0, 9000, 12000],
        [7000, 9000, 0, 16000],
        [15000, 12000, 16000, 0]
    ]

    result = await solver.solve(depot, orders, fleet, time_matrix, dist_matrix)

    assert result.success is True
    assert len(result.routes) > 0
    assert len(result.unassigned_order_ids) == 0
    assert result.total_distance_km > 0

"""
Unit Tests for Valhalla Matrix & Fallback Generator
"""
from app.services.valhalla.client import ValhallaClient


async def test_valhalla_fallback_matrix_generation():
    client = ValhallaClient(base_url="http://invalid-host:9999")
    locations = [
        (19.0550, 72.8750),  # Depot
        (19.1193, 72.8450),  # Andheri
        (19.0616, 72.8360),  # Bandra
    ]

    matrix_res = await client.compute_matrix(locations)
    assert "time_matrix_seconds" in matrix_res
    assert "dist_matrix_meters" in matrix_res

    time_mat = matrix_res["time_matrix_seconds"]
    dist_mat = matrix_res["dist_matrix_meters"]

    assert len(time_mat) == 3
    assert len(dist_mat) == 3
    assert time_mat[0][0] == 0
    assert dist_mat[0][0] == 0

    # Ensure distances are positive and non-zero between different stops
    assert dist_mat[0][1] > 0
    assert time_mat[0][1] > 0

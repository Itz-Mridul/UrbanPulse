"""
Pytest configuration and fixtures shared across tests.
"""
import pytest


@pytest.fixture
def sikkim_terrain():
    """Standard Sikkim/Teesta Valley terrain parameters for test reuse."""
    from app.physics.constraints import TerrainParams
    return TerrainParams(
        slope_degrees=32.0,
        channel_width_m=120.0,
        valley_length_km=45.0,
        debris_volume_m3=1_500_000,
        upstream_lake_area_km2=1.65,
    )

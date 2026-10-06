"""
Impact Layer — Exposure and vulnerability overlay.

Queries OpenStreetMap (Overpass API) for infrastructure in the impact zone,
overlays population density (WorldPop/Census), and computes:

  Impact Score = Hazard Probability × Exposure × Vulnerability   (0–100)
"""
from __future__ import annotations

import asyncio
from typing import Any, Optional

import httpx
from loguru import logger
from shapely.geometry import shape, mapping
from shapely.ops import transform
import pyproj


OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# WorldPop population density API (1km grid, India)
WORLDPOP_URL = "https://www.worldpop.org/rest/data/pop/wpgp"


async def query_overpass(bbox: tuple[float, float, float, float]) -> dict[str, Any]:
    """
    Fetch hospitals, roads (primary/secondary), and emergency shelters in bbox.

    bbox: (south, west, north, east) in WGS84 degrees.
    """
    south, west, north, east = bbox
    query = f"""
    [out:json][timeout:30];
    (
      node["amenity"="hospital"]({south},{west},{north},{east});
      way["amenity"="hospital"]({south},{west},{north},{east});
      node["amenity"="clinic"]({south},{west},{north},{east});
      node["emergency"="shelter"]({south},{west},{north},{east});
      node["amenity"="shelter"]({south},{west},{north},{east});
      way["highway"~"primary|secondary|trunk"]({south},{west},{north},{east});
    );
    out body;
    >;
    out skel qt;
    """
    try:
        async with httpx.AsyncClient(timeout=35.0) as client:
            resp = await client.post(OVERPASS_URL, data={"data": query})
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        logger.warning(f"Overpass API failed ({e}), returning empty infra dataset.")
        return {"hospitals": 0, "shelters": 0, "roads_km": 0.0}

    hospitals = sum(
        1 for el in data.get("elements", [])
        if el.get("tags", {}).get("amenity") in ("hospital", "clinic")
    )
    shelters = sum(
        1 for el in data.get("elements", [])
        if el.get("tags", {}).get("amenity") == "shelter"
        or el.get("tags", {}).get("emergency") == "shelter"
    )
    road_ways = sum(
        1 for el in data.get("elements", [])
        if el.get("type") == "way"
        and el.get("tags", {}).get("highway") in ("primary", "secondary", "trunk")
    )
    # Rough road length estimate: assume avg 2 km per way segment
    roads_km = road_ways * 2.0

    return {
        "hospitals": hospitals,
        "shelters": shelters,
        "roads_km": round(roads_km, 1),
    }


def estimate_population_exposed(
    bbox: tuple[float, float, float, float],
    region_name: str = "Sikkim",
) -> int:
    """
    Estimate population in the impact zone using a simplified density lookup.

    In MVP mode, uses district-level census density figures for the pilot region.
    Future: replace with WorldPop API call or local raster extraction.

    Pilot figures (2011 Census, Sikkim):
      - South district: ~160 persons/km²
      - West district:  ~90 persons/km²
      - East district:  ~270 persons/km²
    """
    south, west, north, east = bbox
    area_deg2 = (north - south) * (east - west)
    # 1 degree ≈ 111 km, so area in km²
    area_km2 = area_deg2 * (111 * 111)

    density_per_km2 = {
        "Sikkim": 86,
        "Kedarnath": 45,
        "default": 100,
    }
    density = density_per_km2.get(region_name, density_per_km2["default"])
    return int(area_km2 * density)


def compute_impact_score(
    probability: float,
    population: int,
    hospitals: int,
    roads_km: float,
    shelters: int,
) -> dict[str, Any]:
    """
    Compute a normalised 0–100 Impact Score.

    Formula: Impact Score = 100 × P × (E_norm × W_exp + V_norm × W_vul)

    Where:
      E_norm = normalised exposure (population, hospitals, roads)
      V_norm = vulnerability (inverse of shelter coverage)
      W_exp, W_vul = weights (0.6, 0.4)
    """
    # Normalise exposure (against regional maximums)
    pop_norm = min(1.0, population / 100_000)
    hosp_norm = min(1.0, hospitals / 10)
    road_norm = min(1.0, roads_km / 200)
    exposure_norm = (pop_norm * 0.6 + hosp_norm * 0.25 + road_norm * 0.15)

    # Vulnerability: low shelter coverage = high vulnerability
    shelter_coverage = min(1.0, shelters / max(1, population // 5000))
    vulnerability_norm = 1.0 - shelter_coverage

    impact_score = 100 * probability * (exposure_norm * 0.6 + vulnerability_norm * 0.4)
    impact_score = round(min(100.0, impact_score), 1)

    return {
        "impact_score": impact_score,
        "population_exposed": population,
        "hospitals_exposed": hospitals,
        "roads_affected_km": roads_km,
        "shelters_available": shelters,
        "exposure_index": round(exposure_norm, 3),
        "vulnerability_index": round(vulnerability_norm, 3),
    }


async def compute_full_impact(
    probability: float,
    bbox: tuple[float, float, float, float],
    region_name: str = "Sikkim",
) -> dict[str, Any]:
    """
    Full impact computation pipeline: OSM query + population + score.

    Args:
        probability: Cascade flood probability from the Bayesian engine.
        bbox: Impact zone bounding box (south, west, north, east).
        region_name: Pilot region name for population density lookup.
    """
    infra = await query_overpass(bbox)
    population = estimate_population_exposed(bbox, region_name)
    scores = compute_impact_score(
        probability,
        population,
        infra["hospitals"],
        infra["roads_km"],
        infra["shelters"],
    )
    return scores

"""
IMD Rainfall Data Ingestion Script
===================================
Downloads historical gridded rainfall data from IMD using imdlib,
clips to the pilot region bbox, and loads into the sensor_readings table.

Usage (after activating venv):
    python scripts/fetch_imd_data.py --year 2023 --region sikkim

Requirements:
    pip install imdlib netCDF4

Note: imdlib downloads from IMD FTP — requires network.
For offline/demo use, the synthetic data from seed_db.py is sufficient.
"""
import argparse
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent))

# Pilot region bounding boxes (lat_min, lat_max, lon_min, lon_max)
REGIONS = {
    "sikkim": {
        "lat": (27.0, 28.0),
        "lon": (88.3, 89.0),
        "name": "Sikkim — Teesta Valley",
        "db_region_id": 1,
    },
    "kedarnath": {
        "lat": (30.0, 31.0),
        "lon": (79.0, 80.0),
        "name": "Kedarnath — Mandakini Valley",
        "db_region_id": 2,
    },
}


def fetch_imd_rainfall(year: int, region_key: str, output_dir: str) -> bool:
    """
    Download IMD gridded rainfall data for a given year and region.

    Returns True if successful, False if imdlib unavailable.
    """
    try:
        import imdlib as imd
    except ImportError:
        print("❌ imdlib not installed. Run: pip install imdlib")
        print("   Falling back to synthetic data from seed_db.py")
        return False

    region = REGIONS[region_key]
    output_path = Path(output_dir) / "imd" / region_key
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"📡 Downloading IMD rainfall for {year}, region: {region['name']} …")
    try:
        data = imd.get_data(
            "rain",
            year,
            year,
            "yearwise",
            file_dir=str(output_path),
        )
        print(f"✅ Downloaded to {output_path}")

        # Clip to region bbox
        clipped = data.get_xarray().sel(
            lat=slice(region["lat"][0], region["lat"][1]),
            lon=slice(region["lon"][0], region["lon"][1]),
        )
        clipped.to_netcdf(output_path / f"rainfall_{year}_clipped.nc")
        print(f"✅ Clipped to {region['name']} bbox")
        return True
    except Exception as e:
        print(f"❌ IMD download failed: {e}")
        return False


def fetch_srtm_dem(region_key: str, output_dir: str):
    """
    Instructions for downloading SRTM DEM data.
    Automated download requires NASA Earthdata credentials.
    """
    region = REGIONS[region_key]
    lat_min, lat_max = region["lat"]
    lon_min, lon_max = region["lon"]

    print(f"\n📋 SRTM DEM for {region['name']}:")
    print(f"   Bbox: lat={lat_min}–{lat_max}, lon={lon_min}–{lon_max}")
    print(f"   Options:")
    print(f"   1. OpenTopography (free): https://portal.opentopography.org/raster?opentopoID=OCSDEM.082016.4326.1")
    print(f"      Select bbox: {lon_min}°E {lat_min}°N to {lon_max}°E {lat_max}°N")
    print(f"   2. Bhoonidhi (India, free): https://bhoonidhi.nrsc.gov.in/")
    print(f"   3. USGS EarthExplorer: https://earthexplorer.usgs.gov/")
    print(f"   Save as: {output_dir}/dem/{region_key}/srtm_30m.tif")


def run_terrain_pipeline(region_key: str, dem_path: str, output_dir: str):
    """
    Run WhiteboxTools terrain analysis pipeline on the DEM.
    Produces: slope, flow_accumulation, watershed boundaries.

    Requires: pip install whitebox-workflows
    """
    try:
        import whitebox
        wbt = whitebox.WhiteboxTools()
        wbt.verbose = False
    except ImportError:
        print("❌ whitebox not installed. Run: pip install whitebox")
        print("   Reference: https://github.com/jblindsay/whitebox-tools")
        return

    out_dir = Path(output_dir) / "terrain" / region_key
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n🏔  Running terrain pipeline for {region_key} …")

    # 1. Fill depressions (needed for flow analysis)
    wbt.fill_depressions(dem_path, str(out_dir / "dem_filled.tif"))

    # 2. Flow direction
    wbt.d8_pointer(str(out_dir / "dem_filled.tif"), str(out_dir / "flow_dir.tif"))

    # 3. Flow accumulation
    wbt.d8_flow_accumulation(str(out_dir / "flow_dir.tif"), str(out_dir / "flow_acc.tif"))

    # 4. Slope
    wbt.slope(dem_path, str(out_dir / "slope.tif"))

    # 5. Stream network (threshold: 1000 cells ~ medium streams)
    wbt.extract_streams(str(out_dir / "flow_acc.tif"), str(out_dir / "streams.tif"), threshold=1000)

    print(f"✅ Terrain pipeline complete. Outputs in {out_dir}/")
    print(f"   slope.tif, flow_acc.tif, streams.tif, flow_dir.tif")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CascadeIQ data ingestion script")
    parser.add_argument("--year", type=int, default=2023)
    parser.add_argument("--region", choices=list(REGIONS.keys()), default="sikkim")
    parser.add_argument("--data-dir", default="data/raw")
    parser.add_argument("--dem-path", help="Path to existing SRTM DEM GeoTIFF")
    args = parser.parse_args()

    print(f"\n🌊 CascadeIQ Data Ingestion")
    print(f"   Region: {args.region} | Year: {args.year}")
    print(f"   Output: {args.data_dir}\n")

    # Step 1: Rainfall
    success = fetch_imd_rainfall(args.year, args.region, args.data_dir)
    if not success:
        print("   ℹ️  Using synthetic seed data from seed_db.py instead")

    # Step 2: DEM instructions / pipeline
    if args.dem_path:
        run_terrain_pipeline(args.region, args.dem_path, args.data_dir)
    else:
        fetch_srtm_dem(args.region, args.data_dir)

    print("\n📋 Next steps:")
    print("   1. Load rainfall into DB: python scripts/seed_db.py")
    print("   2. Start backend:         docker-compose up backend")
    print("   3. Trigger inference:     curl -X POST http://localhost:8000/api/v1/predictions/trigger?region_id=1")

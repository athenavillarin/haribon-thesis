"""
==============================================================================
HARIBON Red Tide Validation Study — Task 1: Baseline Data Extraction
==============================================================================
Purpose:
    Extract Level-4 Gap-Free Marine Data from the Copernicus Marine Service
    (CMS) for coastal sites in Capiz, Philippines (2019–2022).

Strategy — "Server-Side Subset & Local Mean":
    1. For each polygon site, compute the geographic Bounding Box.
    2. Call copernicusmarine.subset() to request the Copernicus servers to
       cut a tiny NetCDF file covering only our box, time range, depth, and
       variables.  The server does the heavy lifting — we download kilobytes
       instead of megabytes.
    3. Open the small local NetCDF with xarray.
    4. Average spatially with .mean(dim=[lat, lon], skipna=True).
       This automatically ignores land pixels (NaN) and averages only water.
    5. Delete the temp file; merge all variables into a Master CSV.

Output:
    task1_data/Task1_Marine_Baseline_Daily.csv
==============================================================================
"""

import copernicusmarine
import xarray as xr
import pandas as pd
import numpy as np
import os
import sys
import traceback
import shutil
from shapely.geometry import shape

# =============================================================================
# CONFIGURATION
# =============================================================================

TIME_START = "2019-01-01"
TIME_END = "2022-12-31"
OUTPUT_DIR = "task1_data"
OUTPUT_FILE = "Task1_Marine_Baseline_Daily.csv"
TEMP_DIR = "temp_nc_files"  # server-side subsets land here temporarily

# When computing the bounding box for biogeochem datasets, add a buffer:
# The biogeochem grid is 0.25° — polygons smaller than one grid cell may
# contain zero grid-point centres, returning empty data. A half-cell buffer
# guarantees the nearest ocean point is captured.
BIOGEOCHEM_BUFFER = 0.125  # half of 0.25° grid

# ---------------------------------------------------------------------------
# Target Datasets — Level-4 / Reanalysis ("Gold Standard" gap-free grids)
# ---------------------------------------------------------------------------
DATASETS = {
    "ocean_colour": {
        "dataset_id": "cmems_obs-oc_glo_bgc-plankton_my_l4-gapfree-multi-4km_P1D",
        "variables": ["CHL"],
        "name": "Chlorophyll-a (L4 Gap-Free)",
        "has_depth": False,  # Ocean-colour L4 has no depth dimension
    },
    "physics": {
        "dataset_id": "cmems_mod_glo_phy_my_0.083deg_P1D-m",
        "variables": ["thetao", "so", "uo", "vo", "mlotst"],
        "name": "Physics — GLORYS12 (SST, Salinity, Currents, MLD)",
        "has_depth": True,
    },
    "biogeochem": {
        "dataset_id": "cmems_mod_glo_bgc_my_0.25deg_P1D-m",
        "variables": ["no3", "po4", "o2"],
        "name": "Biogeochemistry (Nitrate, Phosphate, Oxygen)",
        "has_depth": True,
    },
}

# ---------------------------------------------------------------------------
# GeoJSON Input — Coastal sites in Capiz Province
# ---------------------------------------------------------------------------
LOCATIONS_GEOJSON = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {"Name": "Gigantes Polygon"},
            "geometry": {
                "coordinates": [
                    [
                        [123.2316, 11.6632],
                        [123.2316, 11.5188],
                        [123.3871, 11.5188],
                        [123.3871, 11.6632],
                        [123.2316, 11.6632],
                    ]
                ],
                "type": "Polygon",
            },
            "id": 0,
        },
        {
            "type": "Feature",
            "properties": {"Name": "Roxas Polygon"},
            "geometry": {
                "coordinates": [
                    [
                        [122.7027, 11.5404],
                        [122.7761, 11.5400],
                        [122.8065, 11.6067],
                        [122.8063, 11.6647],
                        [122.6280, 11.6527],
                        [122.6867, 11.5436],
                        [122.7027, 11.5404],
                    ]
                ],
                "type": "Polygon",
            },
            "id": 1,
        },
    ],
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def get_bounding_box(feature):
    """
    Return [min_lon, min_lat, max_lon, max_lat] for a GeoJSON Polygon Feature.

    Uses the polygon's natural bounding box via shapely .bounds.
    """
    geom = shape(feature["geometry"])
    # shapely .bounds → (minx, miny, maxx, maxy)
    return list(geom.bounds)


def _resolve_spatial_dims(ds):
    """
    Detect whether the dataset uses 'latitude'/'longitude' or 'lat'/'lon'
    and return the pair as (lat_dim, lon_dim).
    """
    dims = set(ds.dims)
    coords = set(ds.coords)
    all_names = dims | coords

    if "latitude" in all_names and "longitude" in all_names:
        return "latitude", "longitude"
    if "lat" in all_names and "lon" in all_names:
        return "lat", "lon"

    # Fallback — try common aliases
    for lat_candidate in ["latitude", "lat", "nav_lat", "y"]:
        for lon_candidate in ["longitude", "lon", "nav_lon", "x"]:
            if lat_candidate in all_names and lon_candidate in all_names:
                return lat_candidate, lon_candidate

    raise KeyError(
        f"Cannot find lat/lon dimensions in dataset. "
        f"Available dims: {list(ds.dims)}, coords: {list(ds.coords)}"
    )


def _resolve_depth_dim(ds):
    """Return the name of the depth dimension/coordinate, or None."""
    for name in ("depth", "deptho", "lev", "z"):
        if name in ds.dims or name in ds.coords:
            return name
    return None


def extract_dataset(dataset_cfg, bbox, site_name, dataset_key=None):
    """
    Use copernicusmarine.subset() to request a server-side cut of data,
    download a small NetCDF file, compute the spatial mean locally, and
    return a tidy DataFrame with columns = [Date, var1, var2, ...].

    Steps:
        1. SERVER-SIDE SUBSET — Copernicus cuts our box + time + depth.
        2. Download a tiny .nc file (KB, not MB).
        3. Open locally with xarray, compute spatial mean (skipna=True).
        4. Convert to DataFrame & clean up the temp file.
    """
    dataset_id = dataset_cfg["dataset_id"]
    variables = dataset_cfg["variables"]
    has_depth = dataset_cfg["has_depth"]
    min_lon, min_lat, max_lon, max_lat = bbox

    # Apply buffer for biogeochem datasets (0.25° grid may miss small polygons)
    if dataset_key == "biogeochem":
        min_lon = min_lon - BIOGEOCHEM_BUFFER
        min_lat = min_lat - BIOGEOCHEM_BUFFER
        max_lon = max_lon + BIOGEOCHEM_BUFFER
        max_lat = max_lat + BIOGEOCHEM_BUFFER

    # Build a unique temp filename for this site + dataset
    safe_name = site_name.replace(" ", "_")
    nc_filename = f"{safe_name}_{dataset_key}.nc"
    nc_filepath = os.path.join(TEMP_DIR, nc_filename)

    print(f"    Requesting server-side subset: {dataset_id} ...")
    print(f"    Box: lon [{min_lon:.4f}, {max_lon:.4f}]  "
          f"lat [{min_lat:.4f}, {max_lat:.4f}]")

    # ------------------------------------------------------------------
    # 1. SERVER-SIDE SUBSET — the server cuts only our tiny piece
    # ------------------------------------------------------------------
    subset_kwargs = dict(
        dataset_id=dataset_id,
        variables=variables,
        minimum_longitude=min_lon,
        maximum_longitude=max_lon,
        minimum_latitude=min_lat,
        maximum_latitude=max_lat,
        start_datetime=f"{TIME_START}T00:00:00",
        end_datetime=f"{TIME_END}T23:59:59",
        output_filename=nc_filename,
        output_directory=TEMP_DIR,
    )

    # Only request depth for datasets that have a depth axis
    # Physics shallowest = ~0.494m, Biogeochem shallowest = ~0.506m
    if has_depth:
        subset_kwargs["minimum_depth"] = 0.49
        subset_kwargs["maximum_depth"] = 1.0  # captures shallowest level of all datasets

    copernicusmarine.subset(**subset_kwargs)

    # ------------------------------------------------------------------
    # 2. VERIFY the file arrived
    # ------------------------------------------------------------------
    if not os.path.exists(nc_filepath):
        print(f"    ! File not found after subset: {nc_filepath}")
        return pd.DataFrame()

    file_kb = os.path.getsize(nc_filepath) / 1024
    print(f"    Downloaded: {nc_filename} ({file_kb:.1f} KB)")

    # ------------------------------------------------------------------
    # 3. OPEN LOCALLY & COMPUTE SPATIAL MEAN
    # ------------------------------------------------------------------
    ds = xr.open_dataset(nc_filepath)

    # Select only our variables (intersection with what's in the file)
    available_vars = [v for v in variables if v in ds]
    if not available_vars:
        print(f"    ! Warning: Variables {variables} not found in file.")
        ds.close()
        os.remove(nc_filepath)
        return pd.DataFrame()

    ds = ds[available_vars]

    # Depth: if present, pick shallowest level (surface)
    if has_depth:
        depth_dim = _resolve_depth_dim(ds)
        if depth_dim is not None:
            ds = ds.isel({depth_dim: 0})
            if depth_dim in ds.coords:
                ds = ds.drop_vars(depth_dim)

    # Spatial Mean — the "Box & Filter" core
    # skipna=True → land pixels (NaN) are automatically excluded
    lat_dim, lon_dim = _resolve_spatial_dims(ds)
    print(f"    Averaging over: {lat_dim}, {lon_dim} ...")
    daily_mean = ds.mean(dim=[lat_dim, lon_dim], skipna=True)

    # ------------------------------------------------------------------
    # 4. CONVERT TO DATAFRAME
    # ------------------------------------------------------------------
    df = daily_mean.to_dataframe().reset_index()
    ds.close()

    # Normalise the time column
    time_col = "time" if "time" in df.columns else df.columns[0]
    df[time_col] = pd.to_datetime(df[time_col]).dt.date
    df.rename(columns={time_col: "Date"}, inplace=True)

    # Keep only Date + variable columns
    keep_cols = ["Date"] + [v for v in available_vars if v in df.columns]
    df = df[keep_cols]
    df = df.dropna(subset=["Date"])
    df = df.drop_duplicates(subset="Date")

    # ------------------------------------------------------------------
    # 5. CLEANUP — delete the temp NetCDF to save disk space
    # ------------------------------------------------------------------
    try:
        os.remove(nc_filepath)
    except OSError:
        pass

    return df


# =============================================================================
# MAIN PIPELINE
# =============================================================================


def run_pipeline():
    """
    Master control loop:
        For each site → for each dataset → subset → process → merge → master CSV.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)

    print("=" * 60)
    print("  HARIBON Data Extraction Agent — Task 1")
    print(f"  Method : Server-Side Subset (fast)")
    print(f"  Period : {TIME_START}  →  {TIME_END}")
    print(f"  Sites  : {len(LOCATIONS_GEOJSON['features'])}")
    print(f"  Output : {OUTPUT_DIR}/{OUTPUT_FILE}")
    print("=" * 60)

    all_site_frames = []  # collect every site's merged DataFrame here

    # ------------------------------------------------------------------
    # GEOMETRY LOOP — one iteration per GeoJSON Feature
    # ------------------------------------------------------------------
    for idx, feature in enumerate(LOCATIONS_GEOJSON["features"], start=1):
        site_name = feature["properties"]["Name"]
        bbox = get_bounding_box(feature)

        print(f"\n[{idx}/{len(LOCATIONS_GEOJSON['features'])}] "
              f"SITE: {site_name}")
        print(f"  Geometry : {feature['geometry']['type']}")
        print(f"  Bbox     : lon [{bbox[0]:.4f}, {bbox[2]:.4f}]  "
              f"lat [{bbox[1]:.4f}, {bbox[3]:.4f}]")

        site_dfs = []  # one DataFrame per dataset category

        # --------------------------------------------------------------
        # EXTRACTION LOOP — one iteration per dataset (CHL, Physics, Bio)
        # --------------------------------------------------------------
        for key, config in DATASETS.items():
            print(f"\n  >> {config['name']}")

            try:
                df_chunk = extract_dataset(config, bbox, site_name, dataset_key=key)

                if df_chunk.empty:
                    print(f"    !  Empty result for {key}")
                    continue

                df_chunk.set_index("Date", inplace=True)
                site_dfs.append(df_chunk)
                print(f"    OK  {len(df_chunk)} daily records extracted.")

            except Exception as e:
                # Catch timeouts, HTTP errors, missing datasets, etc.
                print(f"    ERROR extracting {key}: {e}")
                traceback.print_exc()

        # --------------------------------------------------------------
        # MERGE all variable groups for this site on Date
        # --------------------------------------------------------------
        if site_dfs:
            merged = pd.concat(site_dfs, axis=1, join="outer")
            merged.reset_index(inplace=True)
            merged.insert(0, "Location_Name", site_name)

            all_site_frames.append(merged)
            print(f"\n  OK  Merged {len(merged)} days for {site_name}")
        else:
            print(f"\n  FAIL  No data returned for {site_name}")

    # ------------------------------------------------------------------
    # CLEANUP temp directory
    # ------------------------------------------------------------------
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR, ignore_errors=True)

    # ------------------------------------------------------------------
    # SAVE MASTER CSV — one file with all sites stacked
    # ------------------------------------------------------------------
    if all_site_frames:
        master_df = pd.concat(all_site_frames, ignore_index=True)

        # Friendly column order
        leading = ["Location_Name", "Date"]
        other = [c for c in master_df.columns if c not in leading]
        master_df = master_df[leading + sorted(other)]

        output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
        master_df.to_csv(output_path, index=False)

        print("\n" + "=" * 60)
        print(f"  PIPELINE COMPLETE")
        print(f"  Rows   : {len(master_df):,}")
        print(f"  Columns: {list(master_df.columns)}")
        print(f"  Saved  : {output_path}")
        print("=" * 60)
    else:
        print("\n!  No data was extracted for any site. Check errors above.")
        sys.exit(1)


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    run_pipeline()
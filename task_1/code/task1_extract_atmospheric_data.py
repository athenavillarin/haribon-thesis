"""
==============================================================================
HARIBON Red Tide Validation Study — Task 2: Atmospheric & Land Context Data
==============================================================================
Purpose:
    Extract Rainfall, Wind, and Vegetation (NDVI) data from Google Earth Engine
    for the same coastal polygon sites (2019–2022).

Key Design Decisions:
    1. SEAMLESS INTEGRATION: Output CSV has the exact same structure as Part 1
       (Location_Name, Date, var1, var2, ...) so a simple pd.merge() combines
       marine + atmospheric data.

    2. DIRECT DOWNLOAD via getInfo(): No Google Drive export needed. Data is
       pulled directly into Python as dictionaries, converted to DataFrames,
       and saved locally. Faster iteration, no Drive dependency.

    3. GIGANTES WIND SOLVED: ERA5-Land only covers land grid cells, so for
       ocean-heavy sites (e.g., Gigantes) the geometry is buffered by 35 km
       before querying. This captures nearby coastal / land ERA5-Land pixels
       and avoids the all-NaN issue that a tight ocean-only box would produce.

    4. SMART NDVI: Sentinel-2 revisits every 5–10 days (and clouds remove more).
       After extracting available observations, the script uses LINEAR
       INTERPOLATION (.interpolate()) to fill gaps, producing a daily
       "Regional Greenness Index" aligned with the other daily variables.

    5. YEARLY CHUNKING: GEE getInfo() has limits (~5000 elements). We process
       one year at a time to stay well within bounds.

Strategy — "Regional Box Averaging":
    - Rainfall: CHIRPS Daily → precipitation (mm/day) averaged over box.
    - Wind:     ERA5-Land Daily Aggregates (buffered 35 km for ocean sites) → u, v, speed.
    - NDVI:     Sentinel-2 SR cloud-masked → box average, then linearly
               interpolated to daily. Edges left as NaN (no ffill).

Prerequisites:
    pip install earthengine-api pandas shapely numpy
    earthengine authenticate

Output:
    task1_data/Task1_Atmospheric_Baseline_Daily.csv
==============================================================================
"""

import ee
import pandas as pd
import numpy as np
import os
import sys
import traceback
from shapely.geometry import shape as shapely_shape

# =============================================================================
# INITIALIZE EARTH ENGINE
# =============================================================================

PROJECT_ID = "haribon-487510"

try:
    ee.Initialize(project=PROJECT_ID)
    print("OK  Earth Engine initialized.")
except Exception:
    ee.Authenticate()
    ee.Initialize(project=PROJECT_ID)
    print("OK  Earth Engine authenticated and initialized.")

# =============================================================================
# CONFIGURATION
# =============================================================================

TIME_START = "2019-01-01"
TIME_END = "2022-12-31"
OUTPUT_DIR = "task1_data"
OUTPUT_FILE = "Task1_Atmospheric_Baseline_Daily.csv"

# Years to process individually (GEE getInfo() works better in yearly chunks)
YEARS = [2019, 2020, 2021, 2022]

# ---------------------------------------------------------------------------
# GeoJSON Input — Polygon sites only (matches Task 1)
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
        },
    ],
}


# =============================================================================
# HELPER — Bounding Box from Polygon
# =============================================================================
def get_bounding_box(feature):
    """Extract (min_lon, min_lat, max_lon, max_lat) from a Polygon feature."""
    geom = shapely_shape(feature["geometry"])
    return geom.bounds  # (minx, miny, maxx, maxy)


def fc_to_dataframe(fc):
    """
    Convert an ee.FeatureCollection to a Pandas DataFrame via getInfo().
    This downloads the data directly — no Drive export needed.
    """
    info = fc.getInfo()
    rows = []
    for feat in info["features"]:
        rows.append(feat["properties"])
    return pd.DataFrame(rows)


# =============================================================================
# 1. RAINFALL — CHIRPS Daily
# =============================================================================
def extract_rainfall_year(geometry, year):
    """
    CHIRPS Daily — Climate Hazards Group InfraRed Precipitation with Station.
    Dataset: UCSB-CHG/CHIRPS/DAILY
    Band: 'precipitation' (mm/day) — already daily totals, no aggregation needed.

    More reliable via getInfo() than GPM (which requires day-by-day mapping
    of ~48 half-hourly images and often hits GEE computation limits).

    reduceRegion(mean) over the box → single daily value (land + sea avg).
    Processed one year at a time to stay within GEE getInfo() limits.
    """
    start = f"{year}-01-01"
    end = f"{year}-12-31"

    chirps = (
        ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY")
        .filterDate(start, end)
        .filterBounds(geometry)
        .select(["precipitation"])
    )

    def process_day(img):
        mean_val = img.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=geometry,
            scale=5566,  # CHIRPS native ~0.05 deg
            maxPixels=1e8,
        )
        return ee.Feature(None, {
            "date": img.date().format("YYYY-MM-dd"),
            "precip_mm_day": mean_val.get("precipitation"),
        })

    return ee.FeatureCollection(chirps.map(process_day))


# =============================================================================
# 2. WIND — ERA5 Daily Aggregates
# =============================================================================
WIND_BUFFER_M = 35_000  # 35 km buffer so ocean sites still capture ERA5-Land pixels


def extract_wind_year(geometry, year):
    """
    ERA5-Land Daily Aggregates — land-only reanalysis.
    Dataset: ECMWF/ERA5_LAND/DAILY_AGGR
    Bands: u_component_of_wind_10m, v_component_of_wind_10m (m/s)

    Because ERA5-Land only covers land pixels, ocean-heavy sites like
    Gigantes would return empty results with a tight bounding box.
    Solution: the geometry is buffered by WIND_BUFFER_M (35 km) so the
    reduceRegion captures nearby coastal / island pixels from ERA5-Land.

    Wind speed = sqrt(u^2 + v^2).
    Processed one year at a time.
    """
    start = f"{year}-01-01"
    end = f"{year}-12-31"

    # Expand geometry so we always capture some ERA5-Land grid cells
    buffered_geom = geometry.buffer(WIND_BUFFER_M)

    era5 = (
        ee.ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR")
        .filterDate(start, end)
        .filterBounds(buffered_geom)
        .select([
            "u_component_of_wind_10m",
            "v_component_of_wind_10m",
        ])
    )

    def process_image(img):
        u = img.select("u_component_of_wind_10m")
        v = img.select("v_component_of_wind_10m")
        speed = u.pow(2).add(v.pow(2)).sqrt().rename("wind_speed_ms")
        combined = img.addBands(speed)

        mean_val = combined.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=buffered_geom,
            scale=11132,  # ERA5-Land ~0.1 deg ~ 11 km
            maxPixels=1e8,
        )

        return ee.Feature(None, {
            "date": img.date().format("YYYY-MM-dd"),
            "wind_u_ms": mean_val.get("u_component_of_wind_10m"),
            "wind_v_ms": mean_val.get("v_component_of_wind_10m"),
            "wind_speed_ms": mean_val.get("wind_speed_ms"),
        })

    return ee.FeatureCollection(era5.map(process_image))


# =============================================================================
# 3. NDVI — Sentinel-2 (Cloud-Masked, then Interpolated)
# =============================================================================
def mask_s2_clouds(image):
    """
    Cloud masking using QA60 band.
    Bit 10 = opaque clouds, Bit 11 = cirrus.
    """
    qa = image.select("QA60")
    cloud_bit = 1 << 10
    cirrus_bit = 1 << 11
    mask = qa.bitwiseAnd(cloud_bit).eq(0).And(qa.bitwiseAnd(cirrus_bit).eq(0))
    return image.updateMask(mask)


def extract_ndvi_year(geometry, year):
    """
    Sentinel-2 Surface Reflectance — NDVI.
    Dataset: COPERNICUS/S2_SR_HARMONIZED
    NDVI = (B8 - B4) / (B8 + B4)

    Cloud mask with QA60, filter < 50% cloudy.
    reduceRegion(mean) -> box average = "Regional Greenness Index."

    Returns SPARSE data (every 5-10 days). Interpolation happens later
    in the main pipeline after all years are collected.
    """
    start = f"{year}-01-01"
    end = f"{year}-12-31"

    s2 = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterDate(start, end)
        .filterBounds(geometry)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 30))  # stricter filter
        .map(mask_s2_clouds)
    )

    def calc_ndvi(img):
        ndvi = img.normalizedDifference(["B8", "B4"]).rename("NDVI")

        mean_val = ndvi.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=geometry,
            scale=10,  # Sentinel-2 native 10 m
            maxPixels=1e9,
        )

        return ee.Feature(None, {
            "date": img.date().format("YYYY-MM-dd"),
            "NDVI_raw": mean_val.get("NDVI"),
        })

    return ee.FeatureCollection(s2.map(calc_ndvi))


# =============================================================================
# MAIN PIPELINE
# =============================================================================
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=" * 70)
    print("  HARIBON Task 2 — Atmospheric & Land Context Extraction")
    print(f"  Method : Direct Download via getInfo() (no Drive export)")
    print(f"  Period : {TIME_START} -> {TIME_END}")
    print(f"  Sites  : {len(LOCATIONS_GEOJSON['features'])}")
    print(f"  Output : {OUTPUT_DIR}/{OUTPUT_FILE}")
    print("=" * 70)

    all_site_frames = []

    for feature in LOCATIONS_GEOJSON["features"]:
        site_name = feature["properties"]["Name"]

        print(f"\n{'=' * 60}")
        print(f"SITE: {site_name}")
        print(f"{'=' * 60}")

        # --- Bounding Box ---
        min_lon, min_lat, max_lon, max_lat = get_bounding_box(feature)
        print(f"  Box: lon [{min_lon:.4f}, {max_lon:.4f}]  "
              f"lat [{min_lat:.4f}, {max_lat:.4f}]")
        roi = ee.Geometry.Rectangle([min_lon, min_lat, max_lon, max_lat])

        # Collect yearly chunks for each variable
        rain_frames = []
        wind_frames = []
        ndvi_frames = []

        for year in YEARS:
            print(f"\n  --- Year {year} ---")

            # --- 1. Rainfall ---
            print(f"    >> Rainfall (CHIRPS) ...", end=" ", flush=True)
            try:
                rain_fc = extract_rainfall_year(roi, year)
                df_rain = fc_to_dataframe(rain_fc)
                rain_frames.append(df_rain)
                print(f"OK ({len(df_rain)} days)")
            except Exception as e:
                print(f"ERROR: {e}")
                traceback.print_exc()

            # --- 2. Wind ---
            print(f"    >> Wind (ERA5) ...", end=" ", flush=True)
            try:
                wind_fc = extract_wind_year(roi, year)
                df_wind = fc_to_dataframe(wind_fc)
                wind_frames.append(df_wind)
                print(f"OK ({len(df_wind)} days)")
            except Exception as e:
                print(f"ERROR: {e}")
                traceback.print_exc()

            # --- 3. NDVI ---
            print(f"    >> NDVI (Sentinel-2) ...", end=" ", flush=True)
            try:
                ndvi_fc = extract_ndvi_year(roi, year)
                df_ndvi = fc_to_dataframe(ndvi_fc)
                ndvi_frames.append(df_ndvi)
                print(f"OK ({len(df_ndvi)} observations)")
            except Exception as e:
                print(f"ERROR: {e}")
                traceback.print_exc()

        # ==================================================================
        # MERGE all years for this site
        # ==================================================================
        print(f"\n  Merging all years for {site_name} ...")

        # --- Rainfall ---
        if rain_frames:
            df_rain_all = pd.concat(rain_frames, ignore_index=True)
            df_rain_all["date"] = pd.to_datetime(df_rain_all["date"])
            df_rain_all = df_rain_all.drop_duplicates(subset="date")
            df_rain_all = df_rain_all.set_index("date").sort_index()
        else:
            df_rain_all = pd.DataFrame()

        # --- Wind ---
        if wind_frames:
            df_wind_all = pd.concat(wind_frames, ignore_index=True)
            df_wind_all["date"] = pd.to_datetime(df_wind_all["date"])
            df_wind_all = df_wind_all.drop_duplicates(subset="date")
            df_wind_all = df_wind_all.set_index("date").sort_index()
        else:
            df_wind_all = pd.DataFrame()

        # --- NDVI (sparse → interpolated to daily) ---
        if ndvi_frames:
            df_ndvi_all = pd.concat(ndvi_frames, ignore_index=True)
            df_ndvi_all["date"] = pd.to_datetime(df_ndvi_all["date"])
            df_ndvi_all = df_ndvi_all.drop_duplicates(subset="date")
            df_ndvi_all = df_ndvi_all.set_index("date").sort_index()

            # Create a full daily date range and reindex
            full_index = pd.date_range(TIME_START, TIME_END, freq="D")
            df_ndvi_all = df_ndvi_all.reindex(full_index)
            df_ndvi_all.index.name = "date"

            # Linear interpolation to fill gaps BETWEEN observations only.
            # Edges (before first obs / after last obs) are left as NaN —
            # no ffill/bfill extrapolation that would create flat tails.
            df_ndvi_all["NDVI_daily"] = (
                df_ndvi_all["NDVI_raw"]
                .interpolate(method="linear")
            )
            print(f"    NDVI: {df_ndvi_all['NDVI_raw'].notna().sum()} raw obs "
                  f"-> {len(df_ndvi_all)} daily (interpolated)")
        else:
            df_ndvi_all = pd.DataFrame()

        # --- Combine all into one DataFrame ---
        dfs_to_merge = [df for df in [df_rain_all, df_wind_all, df_ndvi_all]
                        if not df.empty]

        if dfs_to_merge:
            site_df = pd.concat(dfs_to_merge, axis=1, join="outer")
            site_df.index.name = "date"
            site_df.reset_index(inplace=True)
            site_df.rename(columns={"date": "Date"}, inplace=True)
            site_df["Date"] = site_df["Date"].dt.date
            site_df.insert(0, "Location_Name", site_name)

            all_site_frames.append(site_df)
            print(f"  OK  {len(site_df)} rows merged for {site_name}")
        else:
            print(f"  FAIL  No data for {site_name}")

    # ======================================================================
    # SAVE MASTER CSV — matches Task 1 structure for easy merge
    # ======================================================================
    if all_site_frames:
        master_df = pd.concat(all_site_frames, ignore_index=True)

        # Friendly column order
        leading = ["Location_Name", "Date"]
        other = [c for c in master_df.columns if c not in leading]
        master_df = master_df[leading + sorted(other)]

        output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
        master_df.to_csv(output_path, index=False)

        print(f"\n{'=' * 70}")
        print(f"  PIPELINE COMPLETE")
        print(f"  Rows   : {len(master_df):,}")
        print(f"  Columns: {list(master_df.columns)}")
        print(f"  Saved  : {output_path}")
        print(f"{'=' * 70}")
        print(f"\n  To merge with Part 1:")
        print(f"    df1 = pd.read_csv('haribon_data_task1/Task1_Validation_Baseline_Daily.csv')")
        print(f"    df2 = pd.read_csv('{output_path}')")
        print(f"    merged = pd.merge(df1, df2, on=['Location_Name', 'Date'], how='outer')")
    else:
        print("\n  ERROR: No data extracted. Check errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()

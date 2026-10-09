"""
fetch_site_environment.py
=========================
Pulls the 11 daily environmental variables of Combined_Labeled.csv for a site
point, sampled the same way as the existing sites (matched against
Combined_Labeled_fixed.csv for Matarinao Bay, 2020):

  thetao, so, uo, vo, mlotst  GLORYS 1/12 deg, nearest water cell to the point
                              (exact match for the existing sites)
  CHL                         CMEMS L4 gap-free 4 km, mean of a +-0.1 deg box (corr 1.00)
  precip_mm_day               CHIRPS daily, mean within 5 km of the point (corr 0.99)
  wind_u_ms, wind_v_ms        ERA5-Land daily, mean within 35 km of the point (corr 1.00)
  wind_speed_ms               sqrt(u^2 + v^2) of the daily means
  NDVI_raw                    Sentinel-2 SR, SCL cloud/shadow mask, scenes < 60% cloud,
                              mean within 10 km (corr 0.93; the original box shape is unknown)
  NDVI_daily                  NDVI_raw linearly interpolated between scenes, edges left NaN

Credentials are read from product/haribon_system/backend/.env.

Usage:
    cd final_compiled_dataset
    python fetch_site_environment.py --site "Milagros (Masbate)" 12.2182 123.5094
    python fetch_site_environment.py --validate     # Matarinao Bay 2020 against the fixed dataset
"""

from __future__ import annotations

import argparse
import functools
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

_THIS_DIR = Path(__file__).resolve().parent
ENV_FILE = _THIS_DIR.parents[1] / "product" / "haribon_system" / "backend" / ".env"
OUTPUT_DIR = _THIS_DIR / "new_sites"

START, END = "2015-01-01", "2026-09-07"
GLORYS_MY = "cmems_mod_glo_phy_my_0.083deg_P1D-m"
GLORYS_ANFC = {
    "thetao": "cmems_mod_glo_phy-thetao_anfc_0.083deg_P1D-m",
    "so": "cmems_mod_glo_phy-so_anfc_0.083deg_P1D-m",
    "uo": "cmems_mod_glo_phy-cur_anfc_0.083deg_P1D-m",
    "vo": "cmems_mod_glo_phy-cur_anfc_0.083deg_P1D-m",
    "mlotst": "cmems_mod_glo_phy_anfc_0.083deg_P1D-m",
}
CHL_MY = "cmems_obs-oc_glo_bgc-plankton_my_l4-gapfree-multi-4km_P1D"
GLORYS_VARS = ["thetao", "so", "uo", "vo", "mlotst"]
CELL_SEARCH_DEG = 0.3
CHL_HALF_WIDTH_DEG = 0.1
SURFACE_DEPTH = (0.49, 1.0)

PRECIP_BUFFER_M, WIND_BUFFER_M, NDVI_BUFFER_M = 5_000, 35_000, 10_000


CREDENTIAL_KEYS = ["COPERNICUSMARINE_SERVICE_USERNAME", "COPERNICUSMARINE_SERVICE_PASSWORD", "GCP_CREDENTIALS_JSON"]


@functools.lru_cache(maxsize=1)
def _credentials() -> dict:
    """Environment variables (as in GitHub Actions), falling back to the backend .env file."""
    values = {}
    if ENV_FILE.exists():
        from dotenv import dotenv_values
        values.update(dotenv_values(ENV_FILE))
    values.update({k: os.environ[k] for k in CREDENTIAL_KEYS if os.environ.get(k)})
    return values


def _open(dataset_id: str, variables: list[str], lat: float, lon: float, half: float,
          start: str, end: str, depth: bool):
    import copernicusmarine as cm
    env = _credentials()
    kwargs = dict(
        dataset_id=dataset_id, variables=variables,
        minimum_longitude=lon - half, maximum_longitude=lon + half,
        minimum_latitude=lat - half, maximum_latitude=lat + half,
        start_datetime=start, end_datetime=end,
        username=env["COPERNICUSMARINE_SERVICE_USERNAME"], password=env["COPERNICUSMARINE_SERVICE_PASSWORD"],
    )
    if depth:
        kwargs.update(minimum_depth=SURFACE_DEPTH[0], maximum_depth=SURFACE_DEPTH[1])
    ds = cm.open_dataset(**kwargs)
    return ds.isel(depth=0) if "depth" in ds.dims else ds


def nearest_water_cell(lat: float, lon: float) -> tuple[float, float, float]:
    """GLORYS cell closest to the point that is water; returns (lat, lon, distance_km)."""
    ds = _open(GLORYS_MY, ["thetao"], lat, lon, CELL_SEARCH_DEG, "2020-01-01", "2020-01-01", depth=True)
    grid = ds["thetao"].isel(time=0).load()
    la, lo = np.meshgrid(grid.latitude.values, grid.longitude.values, indexing="ij")
    dist = np.hypot((la - lat) * 111.0, (lo - lon) * 111.0 * np.cos(np.radians(lat)))
    dist[~np.isfinite(grid.values)] = np.inf
    i = np.unravel_index(np.argmin(dist), dist.shape)
    return float(la[i]), float(lo[i]), float(dist[i])


def fetch_glorys(lat: float, lon: float, start: str, end: str) -> pd.DataFrame:
    cell_lat, cell_lon, dist = nearest_water_cell(lat, lon)
    print(f"  GLORYS water cell ({cell_lat:.4f}, {cell_lon:.4f}), {dist:.1f} km from the point")
    ds = _open(GLORYS_MY, GLORYS_VARS, cell_lat, cell_lon, 0.05, start, end, depth=True)
    my = ds.sel(latitude=cell_lat, longitude=cell_lon, method="nearest")[GLORYS_VARS].load().to_dataframe()[GLORYS_VARS]
    frames = [my]

    tail_start = (pd.to_datetime(my.index).max() + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    if tail_start <= end:
        tail = {}
        by_dataset: dict[str, list[str]] = {}
        for var, dataset_id in GLORYS_ANFC.items():
            by_dataset.setdefault(dataset_id, []).append(var)
        for dataset_id, variables in by_dataset.items():
            t = _open(dataset_id, variables, cell_lat, cell_lon, 0.05, tail_start, end, depth="mlotst" not in variables)
            cell = t.sel(latitude=cell_lat, longitude=cell_lon, method="nearest")
            for var in variables:
                tail[var] = cell[var].load().to_series()
        frames.append(pd.DataFrame(tail))
    out = pd.concat(frames)
    out.index = pd.to_datetime(out.index).normalize()
    return out[~out.index.duplicated()]


def fetch_chl(lat: float, lon: float, start: str, end: str) -> pd.Series:
    ds = _open(CHL_MY, ["CHL"], lat, lon, CHL_HALF_WIDTH_DEG, start, end, depth=False)
    s = ds["CHL"].mean(["latitude", "longitude"]).load().to_series()
    s.index = pd.to_datetime(s.index).normalize()
    return s.rename("CHL")


def _init_ee() -> None:
    import ee
    env = _credentials()
    info = json.loads(env["GCP_CREDENTIALS_JSON"])
    ee.Initialize(ee.ServiceAccountCredentials(info["client_email"], key_data=env["GCP_CREDENTIALS_JSON"]),
                  project=info["project_id"])


def _reduce_daily(collection, bands: list[str], geometry, scale: float) -> pd.DataFrame:
    import ee

    def to_feature(img):
        values = img.select(bands).reduceRegion(ee.Reducer.mean(), geometry, scale, maxPixels=1e9)
        return ee.Feature(None, values.set("date", img.date().format("YYYY-MM-dd")))

    rows = [f["properties"] for f in collection.map(to_feature).getInfo()["features"]]
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(columns=bands, dtype=float)
    df.index = pd.to_datetime(df.pop("date"))
    return df.reindex(columns=bands).astype(float).groupby(level=0).mean()


def fetch_gee(lat: float, lon: float, start: str, end: str) -> pd.DataFrame:
    import ee
    _init_ee()
    point = ee.Geometry.Point([lon, lat])
    years = range(pd.Timestamp(start).year, pd.Timestamp(end).year + 1)
    precip, wind, ndvi = [], [], []
    for year in years:
        y0 = max(pd.Timestamp(start), pd.Timestamp(f"{year}-01-01")).strftime("%Y-%m-%d")
        y1 = (min(pd.Timestamp(end), pd.Timestamp(f"{year}-12-31")) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        print(f"  GEE {year}")
        precip.append(_reduce_daily(
            ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY").filterDate(y0, y1),
            ["precipitation"], point.buffer(PRECIP_BUFFER_M), 5566))
        wind.append(_reduce_daily(
            ee.ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR").filterDate(y0, y1),
            ["u_component_of_wind_10m", "v_component_of_wind_10m"], point.buffer(WIND_BUFFER_M), 11132))

        def add_ndvi(img):
            # QA60 is empty in S2_SR_HARMONIZED from 2022-01 to 2024-02, so use the scene classification
            scl = img.select("SCL")
            clear = scl.neq(3).And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10))
            return img.normalizedDifference(["B8", "B4"]).rename("ndvi").updateMask(clear) \
                .copyProperties(img, ["system:time_start"])

        s2 = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
              .filterBounds(point.buffer(NDVI_BUFFER_M)).filterDate(y0, y1)
              .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 60)).map(add_ndvi))
        ndvi.append(_reduce_daily(s2, ["ndvi"], point.buffer(NDVI_BUFFER_M), 20))

    out = pd.concat([pd.concat(precip), pd.concat(wind), pd.concat(ndvi)], axis=1)
    out.columns = ["precip_mm_day", "wind_u_ms", "wind_v_ms", "NDVI_raw"]
    out["wind_speed_ms"] = np.hypot(out["wind_u_ms"], out["wind_v_ms"])
    return out


def environment_path(site: str) -> Path:
    """Output file for a site, e.g. 'Milagros (Masbate)' -> new_sites/milagros_environment.csv."""
    return OUTPUT_DIR / f"{site.split(' (')[0].replace(' ', '_').lower()}_environment.csv"


def imerg_daily(area, start: str, end: str) -> pd.Series:
    """Daily rainfall (mm/day) from half-hourly GPM IMERG, averaged per day on the Earth Engine side."""
    import ee
    first = ee.Date(start)
    n_days = (pd.Timestamp(end) - pd.Timestamp(start)).days + 1
    half_hourly = ee.ImageCollection("NASA/GPM_L3/IMERG_V07").select("precipitation")

    def day_mean(offset):
        day = first.advance(offset, "day")
        images = half_hourly.filterDate(day, day.advance(1, "day"))
        # Days with no IMERG images yet become a fully masked image, which reduces to NaN
        empty = ee.Image.constant(0).rename("precipitation").updateMask(0)
        mean = ee.Image(ee.Algorithms.If(images.size().gt(0), images.mean().multiply(24), empty))
        return mean.set("system:time_start", day.millis())

    daily = ee.ImageCollection(ee.List.sequence(0, n_days - 1).map(day_mean))
    return _reduce_daily(daily, ["precipitation"], area, 11132)["precipitation"]


def fetch_recent_drivers(lat: float, lon: float, start: str, end: str) -> pd.DataFrame:
    """
    Daily thetao and precip_mm_day for the live forecast, sampled as in training.

    thetao comes from the GLORYS forecast product at the nearest water cell.
    precip_mm_day comes from CHIRPS within 5 km; days CHIRPS has not published
    yet are filled from GPM IMERG over the same area and marked in precip_source.
    """
    import ee
    cell_lat, cell_lon, _ = nearest_water_cell(lat, lon)
    ds = _open(GLORYS_ANFC["thetao"], ["thetao"], cell_lat, cell_lon, 0.05, start, end, depth=True)
    thetao = ds.sel(latitude=cell_lat, longitude=cell_lon, method="nearest")["thetao"].load().to_series()
    thetao.index = pd.to_datetime(thetao.index).normalize()

    _init_ee()
    area = ee.Geometry.Point([lon, lat]).buffer(PRECIP_BUFFER_M)
    stop = (pd.Timestamp(end) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    chirps = _reduce_daily(ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY").filterDate(start, stop),
                           ["precipitation"], area, 5566)["precipitation"]

    dates = pd.date_range(start, end, freq="D")
    out = pd.DataFrame(index=dates)
    out["thetao"] = thetao.groupby(level=0).mean().reindex(dates)
    out["precip_mm_day"] = chirps.reindex(dates)
    out["precip_source"] = np.where(out["precip_mm_day"].notna(), "chirps", None)
    fill = out["precip_mm_day"].isna()
    if fill.any():
        imerg = imerg_daily(area, out.index[fill].min().strftime("%Y-%m-%d"), end)
        out.loc[fill, "precip_mm_day"] = imerg.reindex(dates)[fill]
        out.loc[fill & out["precip_mm_day"].notna(), "precip_source"] = "imerg"
    out.index.name = "Date"
    return out


def fetch_site(name: str, lat: float, lon: float, start: str = START, end: str = END) -> pd.DataFrame:
    print(f"{name} ({lat}, {lon})")
    dates = pd.date_range(start, end, freq="D")
    df = pd.concat([fetch_glorys(lat, lon, start, end), fetch_chl(lat, lon, start, end),
                    fetch_gee(lat, lon, start, end)], axis=1).reindex(dates)
    df = df.apply(pd.to_numeric)
    df["NDVI_daily"] = df["NDVI_raw"].interpolate(limit_area="inside")
    df.index.name = "Date"
    df.insert(0, "Location_Name", name)
    return df.reset_index()


def validate() -> None:
    fetched = fetch_site("Matarinao Bay", 11.23, 125.55, "2020-01-01", "2020-12-31").set_index("Date")
    ref = pd.read_csv(_THIS_DIR / "Combined_Labeled_fixed.csv", parse_dates=["Date"])
    ref = ref[ref["Location_Name"] == "Matarinao Bay"].set_index("Date").loc["2020"]
    print("\nVariable          corr    mean abs diff")
    for col in ["thetao", "so", "uo", "vo", "mlotst", "CHL", "precip_mm_day",
                "wind_u_ms", "wind_v_ms", "wind_speed_ms", "NDVI_daily"]:
        a, b = fetched[col], ref[col]
        print(f"{col:16s} {a.corr(b):6.3f}   {(a - b).abs().mean():.4f}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch environmental variables for a site point.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--site", nargs=3, metavar=("NAME", "LAT", "LON"))
    mode.add_argument("--validate", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.validate:
        validate()
        return
    name, lat, lon = args.site[0], float(args.site[1]), float(args.site[2])
    OUTPUT_DIR.mkdir(exist_ok=True)
    df = fetch_site(name, lat, lon)
    path = environment_path(name)
    df.to_csv(path, index=False)
    print(f"Wrote {path.name}: {len(df):,} rows; missing share per column:")
    print(df.drop(columns=["Location_Name", "Date"]).isna().mean().round(3).to_string())


if __name__ == "__main__":
    main()

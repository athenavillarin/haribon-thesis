"""
Copernicus Marine Environment Monitoring Service (CMEMS) integration.

Fetches live marine data (SST, salinity, chlorophyll, MLD, currents) for all
monitored sites. Each product is opened once over a box covering every site,
then averaged per site, matching the surface-level box means used in training.
"""
from typing import Dict, Any, Optional
from datetime import timedelta

import numpy as np
import pandas as pd

from app.core.config import settings

CMEMS_PRODUCTS_CONFIG = {
    "thetao": {
        "dataset_id": "cmems_mod_glo_phy-thetao_anfc_0.083deg_P1D-m",
        "variables": ["thetao"],
        "has_depth": True,
    },
    "so": {
        "dataset_id": "cmems_mod_glo_phy-so_anfc_0.083deg_P1D-m",
        "variables": ["so"],
        "has_depth": True,
    },
    "currents": {
        "dataset_id": "cmems_mod_glo_phy-cur_anfc_0.083deg_P1D-m",
        "variables": ["uo", "vo"],
        "has_depth": True,
    },
    "mixed_layer": {
        "dataset_id": "cmems_mod_glo_phy_anfc_0.083deg_P1D-m",
        "variables": ["mlotst"],
        "has_depth": False,
    },
    "chlorophyll": {
        "dataset_id": "cmems_obs-oc_glo_bgc-plankton_nrt_l4-gapfree-multi-4km_P1D",
        "variables": ["CHL"],
        "has_depth": False,
    },
}

SITE_BOX_HALF_WIDTH_DEG = 0.5
SURFACE_DEPTH_RANGE = (0.49, 1.0)
MAX_DATE_RETRY_DAYS = 7


def _spatial_dims(ds) -> tuple[str, str]:
    names = set(ds.dims) | set(ds.coords)
    if "latitude" in names and "longitude" in names:
        return "latitude", "longitude"
    return "lat", "lon"


def _open_product(product_cfg: dict, bbox: tuple, day: pd.Timestamp):
    import copernicusmarine

    lon_min, lon_max, lat_min, lat_max = bbox
    kwargs = dict(
        dataset_id=product_cfg["dataset_id"],
        username=settings.COPERNICUSMARINE_SERVICE_USERNAME,
        password=settings.COPERNICUSMARINE_SERVICE_PASSWORD,
        start_datetime=day.isoformat(),
        end_datetime=(day + timedelta(hours=23, minutes=59)).isoformat(),
        minimum_longitude=lon_min,
        maximum_longitude=lon_max,
        minimum_latitude=lat_min,
        maximum_latitude=lat_max,
    )
    if product_cfg["has_depth"]:
        kwargs["minimum_depth"], kwargs["maximum_depth"] = SURFACE_DEPTH_RANGE

    ds = copernicusmarine.open_dataset(**kwargs)
    lowered = {v.lower(): v for v in ds.data_vars}
    variables = {req: lowered[req.lower()] for req in product_cfg["variables"] if req.lower() in lowered}
    if not variables:
        return None, {}

    ds = ds[list(variables.values())]
    for depth_dim in ("depth", "deptho", "lev", "z"):
        if depth_dim in ds.dims:
            ds = ds.isel({depth_dim: 0})
            break
    return ds.load(), variables


def _site_means(ds, variables: dict, lon: float, lat: float) -> Dict[str, float]:
    lat_dim, lon_dim = _spatial_dims(ds)
    half = SITE_BOX_HALF_WIDTH_DEG
    lat_slice = slice(lat - half, lat + half)
    if ds[lat_dim].size > 1 and ds[lat_dim][0] > ds[lat_dim][-1]:
        lat_slice = slice(lat + half, lat - half)
    box = ds.sel({lat_dim: lat_slice, lon_dim: slice(lon - half, lon + half)})
    out = {}
    for key, var in variables.items():
        values = np.asarray(box[var].values, dtype=float).ravel()
        if values.size and not np.all(np.isnan(values)):
            out[key] = float(np.nanmean(values))
    return out


def fetch_cmems_for_sites(sites: Dict[str, tuple], date_str: str) -> Dict[str, Dict[str, Any]]:
    """
    Fetch CMEMS marine data for all sites on a date.

    Args:
        sites: {location_name: (lon, lat)}
        date_str: Date string (YYYY-MM-DD)

    Returns:
        {location_name: {variable: value, "_source": ..., "_source_dates": {...}}}
        Sites with no data from any product are omitted.
    """
    if not sites:
        return {}
    if not settings.COPERNICUSMARINE_SERVICE_USERNAME or not settings.COPERNICUSMARINE_SERVICE_PASSWORD:
        print("[CMEMS] Credentials not configured; skipping.")
        return {}

    half = SITE_BOX_HALF_WIDTH_DEG
    lons = [lon for lon, _ in sites.values()]
    lats = [lat for _, lat in sites.values()]
    bbox = (min(lons) - half, max(lons) + half, min(lats) - half, max(lats) + half)
    target = pd.to_datetime(date_str).normalize()

    results: Dict[str, Dict[str, Any]] = {name: {} for name in sites}
    source_dates: Dict[str, Dict[str, str]] = {name: {} for name in sites}

    for product_key, product_cfg in CMEMS_PRODUCTS_CONFIG.items():
        for retry in range(MAX_DATE_RETRY_DAYS + 1):
            day = target - timedelta(days=retry)
            try:
                ds, variables = _open_product(product_cfg, bbox, day)
            except Exception as exc:
                print(f"  [CMEMS] {product_cfg['dataset_id']} {day.date()}: {type(exc).__name__}")
                continue
            if ds is None:
                continue

            found = 0
            for name, (lon, lat) in sites.items():
                means = _site_means(ds, variables, lon, lat)
                if means:
                    found += 1
                    results[name].update(means)
                    source_dates[name][product_key] = str(day.date())
            if found:
                print(f"  [CMEMS] {product_key}: {day.date()} ({found}/{len(sites)} sites)")
                break

    out = {}
    for name, values in results.items():
        if not values:
            continue
        out[name] = {
            **values,
            "_source": "cmems_live",
            "_source_date": date_str,
            "_source_dates": source_dates[name],
            "_fetch_status": "OK",
        }
    return out

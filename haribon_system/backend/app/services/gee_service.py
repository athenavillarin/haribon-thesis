import json
from datetime import datetime
from typing import Dict, Any

import ee

from app.core.config import settings

_ee_initialized = False


def _initialize_ee() -> None:
    """Initialize the Earth Engine client once.

    Try project init first, then configured service-account auth, then default auth.
    """
    global _ee_initialized
    if _ee_initialized:
        return

    try:
        ee.Initialize(project="haribon-datasets")
        print("✅ Google Earth Engine initialized (haribon-datasets).")
        _ee_initialized = True
        return
    except Exception:
        print("Authenticating to Google Earth Engine...")

    try:
        if settings.GCP_CREDENTIALS_JSON:
            print("🚀 Authenticating with GCP_CREDENTIALS_JSON environment variable...")
            creds_json = json.loads(settings.GCP_CREDENTIALS_JSON)
            credentials = ee.ServiceAccountCredentials(
                settings.GCP_SERVICE_ACCOUNT_EMAIL,
                key_data=json.dumps(creds_json),
            )
            ee.Initialize(credentials=credentials)
            print("✅ GEE initialized using JSON content (Production Mode).")
            _ee_initialized = True
            return
    except Exception as exc:
        print(f"⚠️ Failed JSON-based GEE auth: {exc}")

    try:
        if settings.GCP_PRIVATE_KEY_PATH and settings.GCP_PRIVATE_KEY_PATH.exists():
            print(f"🚀 Authenticating with key file from: {settings.GCP_PRIVATE_KEY_PATH}...")
            credentials = ee.ServiceAccountCredentials(
                settings.GCP_SERVICE_ACCOUNT_EMAIL,
                str(settings.GCP_PRIVATE_KEY_PATH),
            )
            ee.Initialize(credentials=credentials)
            print("✅ GEE initialized using key file (Local Mode).")
            _ee_initialized = True
            return
    except Exception as exc:
        print(f"⚠️ Failed file-based GEE auth: {exc}")

    try:
        print("⚠️ No service account credentials found. Attempting default authentication...")
        ee.Initialize()
        print("✅ GEE initialized with default credentials.")
        _ee_initialized = True
    except Exception as exc:
        print(f"❌ FATAL GEE AUTHENTICATION ERROR: {exc}")

def _get_value(image, geometry, reducer=None, scale=1000, max_pixels=1e9) -> Dict[str, Any]:
    """Reduce an EE image over a geometry with basic error handling."""
    try:
        if image is None:
            return {}
        if reducer is None:
            reducer = ee.Reducer.mean()

        stats = image.reduceRegion(
            reducer=reducer,
            geometry=geometry,
            scale=scale,
            maxPixels=max_pixels,
            bestEffort=True,
            tileScale=2,
        )
        return stats.getInfo() or {}
    except Exception as exc:
        print(f"    ⚠️ Reduction error: {exc}")
        return {}

def get_environmental_data_for_feature(feature: Dict[str, Any], date_str: str) -> Dict[str, Any]:
    """Fetch SST, Salinity, CHL-proxy, Rainfall, and Agriculture for one location.

    Differences from the Hackathon version:
    - Supports Point geometries (locations.json in haribon_system uses points).
      We create a small buffer around the point to get an area-mean.
    - Returns the same key names as in the Hackathon service so that
      downstream mapping is straightforward.
    """
    _initialize_ee()
    loc_name = feature.get("properties", {}).get("Name", "Unknown")

    if not _ee_initialized:
        print(f"🌊 [GEE] Fetching data for {loc_name} on {date_str}")
        print("  ❌ GEE unavailable: authentication/initialization failed")
        print("  [GEE] Parameter fetch status:")
        for param in ["SST", "Salinity", "Chlorophyll", "Rainfall", "Agriculture", "NDVI", "Wind"]:
            print(f"    - {param}: FAIL")
        return {}

    try:
        geom = feature.get("geometry", {})
        gtype = geom.get("type")
        coords = geom.get("coordinates")

        if not coords:
            raise ValueError("Feature has no coordinates")

        if gtype == "Point":
            point = ee.Geometry.Point(coords)
            aoi = point.buffer(5000).bounds()
        else:
            aoi = ee.Geometry.Polygon(coords)

        target_date = ee.Date(date_str)
        year = target_date.get("year").getInfo()

        start_date_short = target_date.advance(-3, "day")
        start_date_medium = target_date.advance(-15, "day")
        start_date_long = target_date.advance(-30, "day")

        print(f"🌊 [GEE] Fetching data for {loc_name} on {date_str}")

        status = {
            "SST": False,
            "Salinity": False,
            "Chlorophyll": False,
            "Rainfall": False,
            "Agriculture": False,
            "NDVI": False,
            "Wind": False,
        }

        sst_data = None
        try:
            oisst = ee.ImageCollection("NOAA/CDR/OISST/V2_1").filterDate(
                start_date_short, target_date
            ).filterBounds(aoi)
            if oisst.size().getInfo() > 0:
                sst_image = oisst.mean().select("sst")
                sst_stats = _get_value(sst_image, aoi, scale=25000)
                if sst_stats.get("sst") is not None:
                    sst_data = sst_stats["sst"] * 0.01
                    status["SST"] = True
                    print(f"  ✅ SST from OISST: {sst_data:.2f} °C")

            if sst_data is None:
                hycom = ee.ImageCollection("HYCOM/sea_temp_salinity").filterDate(
                    start_date_medium, target_date
                )
                if hycom.size().getInfo() > 0:
                    hycom_img = hycom.mean().select("water_temp_0")
                    hycom_stats = _get_value(hycom_img, aoi, scale=50000)
                    if hycom_stats.get("water_temp_0") is not None:
                        sst_data = hycom_stats["water_temp_0"] * 0.001
                        status["SST"] = True
                        print(f"  ✅ SST from HYCOM: {sst_data:.2f} °C")
        except Exception as exc:
            print(f"  ⚠️ SST error: {exc}")

        salinity_data = None
        try:
            if year >= 2015:
                smap = ee.ImageCollection("NASA/SMAP/SPL3SMP_E/005").filterDate(
                    start_date_long, target_date
                ).filterBounds(aoi)
                if smap.size().getInfo() > 0:
                    smap_img = smap.mean().select("sss_smap")
                    smap_stats = _get_value(smap_img, aoi, scale=40000)
                    if smap_stats.get("sss_smap") is not None:
                        salinity_data = smap_stats["sss_smap"]
                        status["Salinity"] = True
                        print(f"  ✅ Salinity from SMAP: {salinity_data:.2f} PSU")

            if salinity_data is None:
                hycom = ee.ImageCollection("HYCOM/sea_temp_salinity").filterDate(
                    start_date_medium, target_date
                )
                if hycom.size().getInfo() > 0:
                    hycom_img = hycom.mean().select("salinity_0")
                    hycom_stats = _get_value(hycom_img, aoi, scale=50000)
                    if hycom_stats.get("salinity_0") is not None:
                        salinity_data = hycom_stats["salinity_0"] * 0.001
                        status["Salinity"] = True
                        print(f"  ✅ Salinity from HYCOM: {salinity_data:.2f} PSU")
        except Exception as exc:
            print(f"  ⚠️ Salinity error: {exc}")

        chloro_data = None
        try:
            olci = ee.ImageCollection("COPERNICUS/S3/OLCI").filterDate(
                start_date_medium, target_date
            ).filterBounds(aoi)
            if olci.size().getInfo() > 0:
                def mask_olci(image):
                    qa = image.select("quality_flags")
                    mask = qa.bitwiseAnd(1 << 1).eq(0).And(
                        qa.bitwiseAnd(1 << 31).eq(0)
                    )
                    return image.updateMask(mask)

                olci_masked = olci.map(mask_olci)
                olci_img = olci_masked.mean()

                oa08 = olci_img.select("Oa08_radiance")
                oa06 = olci_img.select("Oa06_radiance")
                ratio = oa08.divide(oa06.add(1e-10))
                ratio = ratio.updateMask(ratio.gt(0.01).And(ratio.lt(100)))
                chloro_proxy = ratio.log10()

                chl_stats = _get_value(chloro_proxy, aoi, scale=300)
                for key, val in chl_stats.items():
                    if val is not None:
                        chloro_data = val
                        break
                if chloro_data is not None:
                    status["Chlorophyll"] = True
                    print(
                        f"  ✅ Chlorophyll-a proxy from Sentinel-3 OLCI: {chloro_data:.4f} (log10 ratio)"
                    )
        except Exception as exc:
            print(f"  ⚠️ Chlorophyll-a proxy error: {exc}")

        rainfall_data = None
        try:
            chirps = ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY").filterDate(
                start_date_short, target_date
            ).filterBounds(aoi)
            if chirps.size().getInfo() > 0:
                rain_img = chirps.sum().select("precipitation")
                rain_stats = _get_value(rain_img, aoi, scale=5500)
                if rain_stats.get("precipitation") is not None:
                    rainfall_data = rain_stats["precipitation"]
                    status["Rainfall"] = True
                    print(f"  ✅ Rainfall from CHIRPS: {rainfall_data:.2f} mm")
        except Exception as exc:
            print(f"  ⚠️ Rainfall error: {exc}")

        agri_data = None
        try:
            if year == 2015:
                landcover = ee.Image("GCEP/GCEP30").select("b1")
                agri_mask = landcover.eq(2)
                agri_stats = _get_value(agri_mask, aoi, reducer=ee.Reducer.mean(), scale=1000)
                if agri_stats.get("b1") is not None:
                    agri_data = agri_stats["b1"] * 100
            elif 2016 <= year <= 2021:
                lc_coll = ee.ImageCollection("MODIS/006/MCD12Q1").filterDate(
                    f"{year}-01-01", f"{year}-12-31"
                )
                if lc_coll.size().getInfo() > 0:
                    lc_img = lc_coll.first().select("LC_Type1")
                    agri_mask = lc_img.eq(12).Or(lc_img.eq(14))
                    agri_stats = _get_value(agri_mask, aoi, reducer=ee.Reducer.mean(), scale=500)
                    if agri_stats.get("LC_Type1") is not None:
                        agri_data = agri_stats["LC_Type1"] * 100
            else:
                dw_start = target_date.advance(-90, "day")
                dw_coll = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1").filterBounds(aoi).filterDate(
                    dw_start, target_date
                ).select("label")
                if dw_coll.size().getInfo() > 0:
                    lc_img = dw_coll.mode()
                    agri_mask = lc_img.eq(4)
                    agri_stats = _get_value(agri_mask, aoi, reducer=ee.Reducer.mean(), scale=100)
                    if agri_stats.get("label") is not None:
                        agri_data = agri_stats["label"] * 100

            if agri_data is not None:
                status["Agriculture"] = True
                print(f"  ✅ Agriculture coverage: {agri_data:.2f}%")
        except Exception as exc:
            print(f"  ⚠️ Agriculture error: {exc}")

        ndvi_data = None
        try:
            ndvi_coll = ee.ImageCollection("MODIS/061/MOD13Q1").filterDate(
                start_date_medium, target_date
            ).filterBounds(aoi)
            if ndvi_coll.size().getInfo() > 0:
                ndvi_img = ndvi_coll.mean().select("NDVI")
                ndvi_stats = _get_value(ndvi_img, aoi, scale=500)
                if ndvi_stats.get("NDVI") is not None:
                    ndvi_data = ndvi_stats["NDVI"] * 0.0001
                    status["NDVI"] = True
                    print(f"  ✅ NDVI from MODIS: {ndvi_data:.3f}")
        except Exception as exc:
            print(f"  ⚠️ NDVI error: {exc}")

        wind_u = None
        wind_v = None
        wind_speed = None
        try:
            era5 = ee.ImageCollection("ECMWF/ERA5/DAILY").filterDate(
                start_date_short, target_date
            ).filterBounds(aoi)
            if era5.size().getInfo() > 0:
                wind_img = era5.mean().select([
                    "u_component_of_wind_10m",
                    "v_component_of_wind_10m",
                ])
                wind_stats = _get_value(wind_img, aoi, scale=11000)
                u_val = wind_stats.get("u_component_of_wind_10m")
                v_val = wind_stats.get("v_component_of_wind_10m")
                if u_val is not None and v_val is not None:
                    wind_u = float(u_val)
                    wind_v = float(v_val)
                    wind_speed = (wind_u ** 2 + wind_v ** 2) ** 0.5
                    status["Wind"] = True
                    print(
                        f"  ✅ Wind from ERA5: speed={wind_speed:.2f} m/s, "
                        f"u={wind_u:.2f}, v={wind_v:.2f}"
                    )
        except Exception as exc:
            print(f"  ⚠️ Wind error: {exc}")

        data = {
            "SST": round(sst_data, 3) if sst_data is not None else None,
            "Salinity": round(salinity_data, 3) if salinity_data is not None else None,
            "Chlorophyll_a_proxy": round(chloro_data, 6) if chloro_data is not None else None,
            "Rainfall_mm": round(rainfall_data, 2) if rainfall_data is not None else None,
            "Agriculture_pct": round(agri_data, 2) if agri_data is not None else None,
                "NDVI": round(ndvi_data, 4) if ndvi_data is not None else None,
                "Wind_u_ms": round(wind_u, 3) if wind_u is not None else None,
                "Wind_v_ms": round(wind_v, 3) if wind_v is not None else None,
                "Wind_speed_ms": round(wind_speed, 3) if wind_speed is not None else None,
            "data_sources": {
                "sst": "OISST/HYCOM",
                "salinity": "SMAP/HYCOM/WOA13",
                "chlorophyll": "Sentinel-3 OLCI (proxy)",
                "rainfall": "CHIRPS",
                "agriculture": f"GCEP30/MODIS/DynamicWorld (year: {year})",
                "ndvi": "MODIS MOD13Q1",
                "wind": "ECMWF ERA5 DAILY",
            },
        }

        print("  [GEE] Parameter fetch status:")
        for param, ok in status.items():
            print(f"    - {param}: {'OK' if ok else 'FAIL'}")

        print(f"  🎯 [GEE] Data collection complete for {loc_name}")
        return data

    except Exception as exc:
        loc_name = feature.get("properties", {}).get("Name", "Unknown")
        print(f"❌ ERROR fetching GEE data for {loc_name}: {exc}")
        return {}

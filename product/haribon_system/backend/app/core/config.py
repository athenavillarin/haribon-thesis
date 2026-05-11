from pydantic_settings import BaseSettings
from pathlib import Path
import json
from functools import lru_cache
from typing import Optional


def _discover_repo_root(start_path: Path) -> Path:
    """Find repository root by walking up until thesis manifest is found."""
    current = start_path.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "artifacts" / "THESIS_WINNERS.json").exists():
            return candidate
    # Fallback to prior behavior if manifest is not present yet.
    return Path(__file__).resolve().parent.parent.parent.parent.parent


def _discover_system_base(repo_root: Path) -> Path:
    """Resolve backend system root across old and reorganized layouts."""
    candidates = [
        repo_root / "product" / "haribon_system",
        repo_root / "haribon_system",
    ]
    for path in candidates:
        if path.exists():
            return path
    return candidates[-1]


def _discover_ml_dir(repo_root: Path) -> Path:
    candidates = [
        repo_root / "thesis" / "ml_xgboost",
        repo_root / "ml_xgboost",
    ]
    for path in candidates:
        if path.exists():
            return path
    return candidates[0]


def _discover_training_data(repo_root: Path) -> Path:
    candidates = [
        repo_root / "thesis" / "final_compiled_dataset" / "Combined_Labeled.csv",
        repo_root / "final_compiled_dataset" / "Combined_Labeled.csv",
    ]
    for path in candidates:
        if path.exists():
            return path
    return candidates[0]


class Settings(BaseSettings):
    PROJECT_NAME: str = "HARIBON v2.0"
    API_V1_STR: str = "/api/v1"

    # GCP / Google Earth Engine Configuration (optional)
    GCP_SERVICE_ACCOUNT_EMAIL: str = "placeholder@example.com"
    # Optional JSON string with service account credentials (for production use)
    GCP_CREDENTIALS_JSON: Optional[str] = None
    # Optional path to a local service account key file (for local dev)
    GCP_PRIVATE_KEY_PATH: Optional[Path] = None

    # Copernicus Marine (CMEMS) Configuration (optional)
    COPERNICUSMARINE_SERVICE_USERNAME: Optional[str] = None
    COPERNICUSMARINE_SERVICE_PASSWORD: Optional[str] = None

    # Data directories
    REPO_ROOT: Path = _discover_repo_root(Path(__file__).resolve().parent)
    BASE_DIR: Path = _discover_system_base(REPO_ROOT)
    DATA_DIR: Path = BASE_DIR / "data"
    PROCESSED_DATA_DIR: Path = DATA_DIR / "processed"
    HISTORICAL_DATA_DIR: Path = DATA_DIR / "historical"

    # Location geometry file (GeoJSON FeatureCollection)
    LOCATIONS_FILE_PATH: Path = DATA_DIR / "locations.json"

    # ML model directory
    ML_DIR: Path = _discover_ml_dir(REPO_ROOT)

    # Dataset path
    TRAINING_DATA_PATH: Path = _discover_training_data(REPO_ROOT)

    # Thesis winners manifest (single source of truth for production model + imputation)
    THESIS_WINNERS_PATH: Path = REPO_ROOT / "artifacts" / "THESIS_WINNERS.json"

    # Database configuration (optional)
    # Example: postgresql://user:password@localhost:5432/haribon
    DATABASE_URL: Optional[str] = None

    class Config:
        env_file = str(Path(__file__).resolve().parent.parent.parent / ".env")
        case_sensitive = True


settings = Settings()


@lru_cache(maxsize=1)
def get_thesis_winners_manifest() -> dict:
    """Load and cache thesis winners manifest used by production services."""
    manifest_path = settings.THESIS_WINNERS_PATH
    if not manifest_path.exists():
        raise FileNotFoundError(f"Thesis winners manifest not found: {manifest_path}")

    with manifest_path.open("r", encoding="utf-8") as f:
        return json.load(f)
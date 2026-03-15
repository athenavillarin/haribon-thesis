from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "HARIBON v2.0"
    API_V1_STR: str = "/api/v1"

    # GCP / Google Earth Engine Configuration (optional)
    GCP_SERVICE_ACCOUNT_EMAIL: str = "placeholder@example.com"
    # Optional JSON string with service account credentials (for production use)
    GCP_CREDENTIALS_JSON: Optional[str] = None
    # Optional path to a local service account key file (for local dev)
    GCP_PRIVATE_KEY_PATH: Optional[Path] = None

    # Data directories
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    PROCESSED_DATA_DIR: Path = DATA_DIR / "processed"
    HISTORICAL_DATA_DIR: Path = DATA_DIR / "historical"

    # Location geometry file (GeoJSON FeatureCollection)
    LOCATIONS_FILE_PATH: Path = DATA_DIR / "locations.json"

    # ML model directory
    ML_DIR: Path = BASE_DIR.parent / "ml_xgboost"

    # Dataset path
    TRAINING_DATA_PATH: Path = BASE_DIR.parent.parent / "final_compiled_dataset" / "Combined_Labeled.csv"

    # Database configuration (optional)
    # Example: postgresql://user:password@localhost:5432/haribon
    DATABASE_URL: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
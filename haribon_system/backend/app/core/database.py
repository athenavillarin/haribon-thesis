from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

# Optional PostgreSQL engine; if DATABASE_URL is not set, database
# features are effectively disabled but the app can still run.
DATABASE_URL = settings.DATABASE_URL

engine = create_engine(DATABASE_URL) if DATABASE_URL else None
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) if engine else None

Base = declarative_base()

# Create tables on startup when a database URL is configured.
if engine is not None:
    try:
        from app import models  # noqa: F401  # ensure models are imported
        Base.metadata.create_all(bind=engine)
    except Exception as exc:  # pragma: no cover
        # Fail quietly so a missing DB does not break the API.
        print(f"[WARN] Failed to initialize database: {exc}")

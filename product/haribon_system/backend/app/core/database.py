from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

import asyncio
import threading
from sqlalchemy import text

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

def start_db_keep_alive():
    """Keep Neon database awake by pinging it every 4 minutes."""
    def keep_alive():
        while True:
            try:
                with SessionLocal() as session:
                    session.execute(text("SELECT 1"))
                    session.commit()
                    print("[DB Keep-Alive] Database pinged successfully")
            except Exception as e:
                print(f"[DB Keep-Alive] Ping failed (database may be waking up): {e}")
            
            threading.Event().wait(240)  # 4 minutes
    
    thread = threading.Thread(target=keep_alive, daemon=True)
    thread.start()

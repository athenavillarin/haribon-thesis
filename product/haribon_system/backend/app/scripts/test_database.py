#!/usr/bin/env python3
"""
Test database connection script for HARIBON system.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from app.core.database import engine, SessionLocal
    from app.models.forecast import DailyForecast, Location, HistoricalData, PredictionLog
    from sqlalchemy import text

    if engine is None:
        print("❌ Database not configured. Please set DATABASE_URL in .env file.")
        sys.exit(1)

    # Test connection
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        version = result.fetchone()[0]
        print(f"✅ Connected to PostgreSQL: {version[:50]}...")

    # Test session and tables
    session = SessionLocal()

    # Check locations
    location_count = session.query(Location).count()
    print(f"✅ Locations table: {location_count} locations")

    # Check historical data
    historical_count = session.query(HistoricalData).count()
    print(f"✅ Historical data table: {historical_count} records")

    # Check prediction logs
    prediction_count = session.query(PredictionLog).count()
    print(f"✅ Prediction logs table: {prediction_count} records")

    # Check daily forecasts
    forecast_count = session.query(DailyForecast).count()
    print(f"✅ Daily forecasts table: {forecast_count} records")

    session.close()

    print("\n🎉 Database setup is working correctly!")

except Exception as e:
    print(f"❌ Database connection failed: {e}")
    print("\nTroubleshooting:")
    print("1. Make sure PostgreSQL is running")
    print("2. Check DATABASE_URL in .env file")
    print("3. Verify database 'haribon' exists")
    print("4. Ensure PostgreSQL user has permissions")
    sys.exit(1)
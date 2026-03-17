#!/usr/bin/env python3
"""
Script to populate historical data from CSV into PostgreSQL database.
"""

import sys
import pandas as pd
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.forecast import Location, HistoricalData

def populate_historical_data():
    """Populate historical_data table from Combined_Labeled.csv."""
    if not settings.DATABASE_URL:
        print("ERROR: DATABASE_URL not configured in .env file")
        return False

    try:
        # Load CSV data
        csv_path = settings.TRAINING_DATA_PATH
        if not csv_path.exists():
            print(f"ERROR: Training data file not found at {csv_path}")
            return False

        print(f"Loading data from {csv_path}...")
        df = pd.read_csv(csv_path)

        # Convert Date column to datetime
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date'])

        # Get location mapping
        session = SessionLocal()
        locations = session.query(Location).all()
        location_map = {loc.location_name: loc.location_id for loc in locations}

        if not location_map:
            print("ERROR: No locations found in database. Run setup_database.py first.")
            session.close()
            return False

        print(f"Found {len(location_map)} locations in database")

        # Check existing records
        existing_count = session.query(HistoricalData).count()
        if existing_count > 0:
            print(f"Historical data already populated ({existing_count} records)")
            session.close()
            return True

        records_added = 0
        batch_size = 1000

        for _, row in df.iterrows():
            location_name = row['Location_Name']
            if location_name not in location_map:
                print(f"WARNING: Location '{location_name}' not found in database, skipping")
                continue

            # Map CSV columns to database fields
            historical_record = HistoricalData(
                location_id=location_map[location_name],
                date=row['Date'].date(),
                redtide_present=bool(row.get('red_tide_label', 0) > 0),  # Convert to boolean
                sst=row.get('thetao'),  # Sea Surface Temperature
                chlorophyll_a_proxy=row.get('CHL'),  # Chlorophyll-a
                rainfall_mm=row.get('precip_mm_day'),  # Precipitation
                salinity=row.get('so'),  # Salinity
                agriculture_pct=None  # Not available in current dataset
            )

            session.add(historical_record)
            records_added += 1

            # Commit in batches
            if records_added % batch_size == 0:
                session.commit()
                print(f"Processed {records_added} records...")

        # Final commit
        session.commit()
        session.close()

        print(f"✓ Successfully added {records_added} historical data records")
        return True

    except Exception as e:
        print(f"ERROR: Failed to populate historical data: {e}")
        return False

if __name__ == "__main__":
    print("Populating historical data...")
    success = populate_historical_data()
    if success:
        print("Historical data population complete!")
    else:
        print("Historical data population failed.")
        sys.exit(1)
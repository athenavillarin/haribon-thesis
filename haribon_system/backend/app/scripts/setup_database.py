#!/usr/bin/env python3
"""
Database setup script for HARIBON system.

This script creates the PostgreSQL database and tables for storing predicted data.
Run this after installing PostgreSQL and updating the DATABASE_URL in .env.
"""

import os
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from app.core.config import settings

def setup_database():
    """Create database and tables."""
    if not settings.DATABASE_URL:
        print("ERROR: DATABASE_URL not configured in .env file")
        return False

    # Extract database name from URL
    from urllib.parse import urlparse
    parsed = urlparse(settings.DATABASE_URL)
    db_name = parsed.path.lstrip('/')

    # Create connection URL without database name for initial connection
    admin_url = settings.DATABASE_URL.replace(f"/{db_name}", "/postgres")

    try:
        # Connect to postgres database to create our database
        engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
        with engine.connect() as conn:
            # Check if database already exists
            result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'"))
            if result.fetchone():
                print(f"✓ Database '{db_name}' already exists")
            else:
                # Create database if it doesn't exist
                conn.execute(text(f"CREATE DATABASE {db_name}"))
                print(f"✓ Database '{db_name}' created successfully")

        # Now connect to our database and create tables
        engine = create_engine(settings.DATABASE_URL)
        from app.core.database import Base
        Base.metadata.create_all(bind=engine)
        print("✓ Tables created successfully")

        # Populate locations table
        populate_locations(engine)
        print("✓ Locations populated successfully")

        return True

    except Exception as e:
        print(f"ERROR: Failed to setup database: {e}")
        return False

def populate_locations(engine):
    """Populate the location table with data from locations.json."""
    try:
        from app.models.forecast import Location
        from sqlalchemy.orm import sessionmaker

        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()

        # Check if locations already exist
        existing_count = session.query(Location).count()
        if existing_count > 0:
            print(f"Locations already populated ({existing_count} locations)")
            session.close()
            return

        # Load locations from JSON file
        locations_file = settings.LOCATIONS_FILE_PATH
        if not locations_file.exists():
            print(f"WARNING: Locations file not found at {locations_file}")
            session.close()
            return

        with open(locations_file, 'r') as f:
            data = json.load(f)

        locations_added = 0
        for feature in data.get('features', []):
            location_name = feature.get('properties', {}).get('Name')
            if location_name:
                # Check if location already exists
                existing = session.query(Location).filter_by(location_name=location_name).first()
                if not existing:
                    location = Location(location_name=location_name)
                    session.add(location)
                    locations_added += 1

        session.commit()
        session.close()
        print(f"Added {locations_added} locations to database")

    except Exception as e:
        print(f"ERROR: Failed to populate locations: {e}")

if __name__ == "__main__":
    print("Setting up HARIBON database...")
    success = setup_database()
    if success:
        print("\nDatabase setup complete! You can now run the FastAPI server.")
    else:
        print("\nDatabase setup failed. Please check your PostgreSQL installation and .env configuration.")
        sys.exit(1)
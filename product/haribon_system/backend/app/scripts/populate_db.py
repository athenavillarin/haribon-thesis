import sys
from pathlib import Path

def _discover_repo_root(start_path: Path) -> Path:
    current = start_path.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "artifacts" / "THESIS_WINNERS.json").exists():
            return candidate
    return current.parents[4]

backend_dir = Path(__file__).resolve().parent.parent.parent
system_dir = backend_dir.parent
repo_root = _discover_repo_root(Path(__file__).resolve().parent)
project_root = repo_root

sys.path.append(str(backend_dir))
sys.path.append(str(system_dir))
sys.path.append(str(repo_root / "product" / "haribon_system"))

# Now the imports will work
import pandas as pd
from app.core.database import engine, SessionLocal
from app.models.forecast import Location, HistoricalData

# Path to the CSV (adjust if needed)
csv_path = Path(__file__).resolve().parent.parent.parent.parent.parent / "thesis" / "final_compiled_dataset" / "Combined_Labeled.csv"
print(f"CSV path: {csv_path}")
print(f"Exists: {csv_path.exists()}")

def populate_database():
    if not engine:
        print("Database not configured. Check DATABASE_URL.")
        return

    # Load CSV
    df = pd.read_csv(csv_path)
    df['Date'] = pd.to_datetime(df['Date']).dt.date  # Convert to date objects

    # Create session
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Insert unique locations
        unique_locations = df['Location_Name'].unique()
        for loc_name in unique_locations:
            if not session.query(Location).filter_by(location_name=loc_name).first():
                location = Location(location_name=loc_name)
                session.add(location)
        session.commit()
        print(f"Inserted {len(unique_locations)} locations.")

        # Insert historical data
        location_map = {loc.location_name: loc.location_id for loc in session.query(Location).all()}
        for _, row in df.iterrows():
            loc_id = location_map.get(row['Location_Name'])
            if loc_id:
                historical = HistoricalData(
                    location_id=loc_id,
                    date=row['Date'],
                    redtide_present=bool(row['red_tide_label'] >= 1.0) if pd.notna(row['red_tide_label']) else None,
                    sst=row['thetao'] if pd.notna(row['thetao']) else None,
                    chlorophyll_a_proxy=row['CHL'] if pd.notna(row['CHL']) else None,
                    rainfall_mm=row['precip_mm_day'] if pd.notna(row['precip_mm_day']) else None,
                    salinity=row['so'] if pd.notna(row['so']) else None,
                    agriculture_pct=row['NDVI_daily'] if pd.notna(row['NDVI_daily']) else None,  # Mapped to NDVI
                )
                session.add(historical)
        session.commit()
        print(f"Inserted {len(df)} historical data records.")
    except Exception as e:
        session.rollback()
        print(f"Error populating database: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    populate_database()
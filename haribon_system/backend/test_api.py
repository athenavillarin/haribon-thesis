import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from app.api.forecast import _load_latest_forecast_data, _simplify_forecast_for_frontend

# Load the raw data
raw_data = _load_latest_forecast_data()
print('Raw data keys:', list(raw_data.keys()))

# Get simplified data
simplified = _simplify_forecast_for_frontend(raw_data)
print('Locations count:', len(simplified.get('locations', [])))

if simplified.get('locations'):
    first_loc = simplified['locations'][0]
    print('First location:', first_loc.get('name'))
    print('Five day outlook dates:')
    for i, day in enumerate(first_loc.get('five_day_outlook', [])):
        print(f'  {i}: {day.get("date")} - {day.get("label")} - {day.get("day")}')
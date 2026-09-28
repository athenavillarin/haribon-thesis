"""
Remove duplicate daily_forecasts rows (keeping the newest per forecast_date)
and add a unique index on forecast_date.
"""

import sys
from pathlib import Path

from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.core.database import engine


def dedupe_daily_forecasts() -> bool:
    if engine is None:
        print("ERROR: Database not configured. Set DATABASE_URL environment variable.")
        return False

    with engine.begin() as conn:
        deleted = conn.execute(text("""
            DELETE FROM daily_forecasts
            WHERE id IN (
                SELECT id FROM (
                    SELECT id, ROW_NUMBER() OVER (
                        PARTITION BY forecast_date
                        ORDER BY created_at DESC, id DESC
                    ) AS rn
                    FROM daily_forecasts
                ) ranked
                WHERE rn > 1
            )
        """)).rowcount
        print(f"Removed {deleted} duplicate rows.")

        conn.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS uq_daily_forecasts_forecast_date
            ON daily_forecasts (forecast_date)
        """))
        print("Unique index on daily_forecasts.forecast_date is in place.")

    return True


if __name__ == "__main__":
    sys.exit(0 if dedupe_daily_forecasts() else 1)

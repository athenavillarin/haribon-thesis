"""
Script to remove unused/legacy columns from prediction_logs table:
- agriculture_pct (no data source)
- chlorophyll_a_proxy (replaced by chlorophyll_a)
- rainfall_mm (replaced by precipitation_mm)
"""

import sys
from sqlalchemy import text

# Add parent directory to path
sys.path.insert(0, "/".join(__file__.split("/")[:-3]))

from app.core.database import SessionLocal, engine


def remove_unused_columns():
    """Remove deprecated columns from prediction_logs table."""
    
    if SessionLocal is None or engine is None:
        print("ERROR: Database not configured. Set DATABASE_URL environment variable.")
        return False
    
    try:
        session = SessionLocal()
        
        columns_to_remove = ["agriculture_pct", "chlorophyll_a_proxy", "rainfall_mm"]
        
        print("🔍 Checking which columns exist...")
        
        # Get existing columns
        result = session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'prediction_logs'
        """))
        existing_columns = {row[0] for row in result}
        
        # Filter to only those that exist
        cols_to_remove = [col for col in columns_to_remove if col in existing_columns]
        
        if not cols_to_remove:
            print("✅ No deprecated columns found. Clean!")
            session.close()
            return True
        
        print(f"⏳ Removing deprecated columns: {cols_to_remove}")
        
        for col_name in cols_to_remove:
            alter_query = f"ALTER TABLE prediction_logs DROP COLUMN {col_name}"
            try:
                session.execute(text(alter_query))
                session.commit()
                print(f"  ✅ Removed {col_name}")
            except Exception as e:
                print(f"  ⚠️  Could not remove {col_name}: {e}")
        
        print("\n✨ Cleanup complete!")
        
        # Verify final columns
        print("\n📊 Final prediction_logs columns:")
        result = session.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'prediction_logs'
            ORDER BY ordinal_position
        """))
        for col_name, data_type in result:
            print(f"  • {col_name}: {data_type}")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"❌ Error removing columns: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = remove_unused_columns()
    sys.exit(0 if success else 1)

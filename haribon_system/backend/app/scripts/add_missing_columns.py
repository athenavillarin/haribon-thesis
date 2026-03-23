"""
Script to add missing environmental parameter columns to prediction_logs table.
Runs ALTER TABLE commands to migrate the existing table schema.
"""

import sys
from sqlalchemy import text

# Add parent directory to path
sys.path.insert(0, "/".join(__file__.split("/")[:-3]))

from app.core.database import SessionLocal, engine


def add_missing_columns():
    """Add the 10 environmental parameter columns to prediction_logs table."""
    
    if SessionLocal is None or engine is None:
        print("ERROR: Database not configured. Set DATABASE_URL environment variable.")
        return False
    
    try:
        session = SessionLocal()
        
        # List of columns to add with their definitions
        columns_to_add = [
            ("chlorophyll_a", "FLOAT"),
            ("ndvi_daily", "FLOAT"),
            ("ndvi_raw", "FLOAT"),
            ("mixed_layer_depth", "FLOAT"),
            ("precipitation_mm", "FLOAT"),
            ("salinity", "FLOAT"),
            ("sst", "FLOAT"),
            ("eastward_current_velocity", "FLOAT"),
            ("northward_current_velocity", "FLOAT"),
            ("wind_speed_ms", "FLOAT"),
            ("wind_u_component", "FLOAT"),
            ("wind_v_component", "FLOAT"),
        ]
        
        print("🔍 Checking which columns already exist...")
        
        # Get existing columns
        result = session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'prediction_logs'
        """))
        existing_columns = {row[0] for row in result}
        print(f"✅ Existing columns: {existing_columns}")
        
        # Add missing columns
        missing_columns = [col for col, dtype in columns_to_add if col not in existing_columns]
        
        if not missing_columns:
            print("✅ All columns already exist! Nothing to add.")
            session.close()
            return True
        
        print(f"\n📋 Missing columns to add: {missing_columns}")
        print("⏳ Adding columns...")
        
        for col_name, col_type in columns_to_add:
            if col_name in existing_columns:
                print(f"  ⏭️  {col_name} already exists, skipping")
                continue
            
            alter_query = f"ALTER TABLE prediction_logs ADD COLUMN {col_name} {col_type}"
            try:
                session.execute(text(alter_query))
                session.commit()
                print(f"  ✅ Added {col_name} ({col_type})")
            except Exception as e:
                print(f"  ⚠️  Could not add {col_name}: {e}")
        
        # Also update risk_level to VARCHAR(20) if it's still TEXT
        print("\n🔄 Checking risk_level column...")
        result = session.execute(text("""
            SELECT data_type, character_maximum_length
            FROM information_schema.columns 
            WHERE table_name = 'prediction_logs' AND column_name = 'risk_level'
        """))
        risk_col_info = result.fetchone()
        if risk_col_info:
            data_type, char_max = risk_col_info
            print(f"   Current risk_level type: {data_type}({char_max if char_max else 'unlimited'})")
            
            if data_type.upper() == 'TEXT' or (data_type.upper() == 'CHARACTER VARYING' and char_max != 20):
                print("   ⏳ Updating risk_level to VARCHAR(20)...")
                try:
                    session.execute(text("ALTER TABLE prediction_logs ALTER COLUMN risk_level TYPE VARCHAR(20)"))
                    session.commit()
                    print("   ✅ Updated risk_level to VARCHAR(20)")
                except Exception as e:
                    print(f"   ⚠️  Could not update risk_level: {e}")
        
        print("\n✨ Column migration complete!")
        
        # Verify all columns
        print("\n📊 Final column list:")
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
        print(f"❌ Error adding columns: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = add_missing_columns()
    sys.exit(0 if success else 1)

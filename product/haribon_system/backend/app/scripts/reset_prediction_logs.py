"""
Script to reset prediction_logs table sequence to 1 and clear all existing records.
Run this after updating the model schema with new environmental parameter columns.
"""

import sys
from sqlalchemy import text

# Add parent directory to path
sys.path.insert(0, "/".join(__file__.split("/")[:-3]))

from app.core.database import SessionLocal, engine


def reset_prediction_logs():
    """Clear all prediction logs and reset the sequence to 1."""
    
    if SessionLocal is None or engine is None:
        print("ERROR: Database not configured. Set DATABASE_URL environment variable.")
        return False
    
    try:
        session = SessionLocal()
        
        # Delete all records from prediction_logs table
        print("🗑️  Deleting all records from prediction_logs table...")
        session.execute(text("DELETE FROM prediction_logs"))
        session.commit()
        print("✅ Successfully deleted all prediction log records")
        
        # Reset the sequence to 1
        print("🔄 Resetting prediction_id sequence to 1...")
        session.execute(text("ALTER SEQUENCE prediction_logs_prediction_id_seq RESTART WITH 1"))
        session.commit()
        print("✅ Successfully reset prediction_id sequence to 1")
        
        # Verify
        result = session.execute(text("SELECT COUNT(*) FROM prediction_logs"))
        count = result.scalar()
        print(f"✅ Current record count in prediction_logs: {count}")
        
        session.close()
        print("\n✨ Reset complete! Next prediction will have prediction_id = 1")
        return True
        
    except Exception as e:
        print(f"❌ Error resetting prediction logs: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = reset_prediction_logs()
    sys.exit(0 if success else 1)

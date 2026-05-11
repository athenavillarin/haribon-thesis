#!/usr/bin/env python3
"""
HARIBON v2.0 Setup Script
Handles initial model training and data generation.
"""

import sys
import os
from pathlib import Path
import subprocess

def run_command(command, description):
    """Run a shell command and report status."""
    print(f"\n🔧 {description}...")
    try:
        # Changed: Added check=True and removed capture_output 
        # so you can see the progress of training in real-time.
        subprocess.run(command, shell=True, check=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Error: {e}")
        return False

def main():
    """Run the complete setup process."""
    print("🌊 HARIBON v2.0 Setup Script")
    print("=" * 50)

    # Get the project root as an absolute path
    project_root = Path(__file__).parent.resolve()
    backend_dir = project_root / "backend"
    ml_dir = project_root / "ml_xgboost"

    # Step 1: Train the ML model
    # Note: We use absolute path for the script to avoid chdir issues
    success_count = 0
    training_script = ml_dir / "training_script.py"
    
    if run_command(f"python \"{training_script}\"", "Training XGBoost model"):
        success_count += 1
    else:
        print("⚠️  Model training failed, but continuing with setup...")

    # Step 2: Generate initial forecast data
    # Change to backend directory so python -m app works correctly
    os.chdir(backend_dir)
    
    if run_command("python -m app.scripts.daily_updater", "Generating initial forecast data"):
        success_count += 1
    else:
        print("❌ Failed to generate forecast data. Setup cannot continue.")
        return 1

    # Step 3: API Instructions
    print("\n🧪 Note: To test the API, run the following commands in separate terminals:")    
    print("   Terminal 1: cd backend && python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000")
    print("   Terminal 2: python test_api.py")

    # Step 4: Verify setup (Fixed Syntax Errors here)
    print("\n📋 Setup Summary:")
    print(f"   ✅ Model training: {'Completed' if success_count >= 1 else 'Failed'}")
    print(f"   ✅ Forecast generation: {'Completed' if success_count >= 2 else 'Failed'}")
    print(f"   📁 Data directory: {project_root / 'data' / 'processed'}")
    print(f"   🤖 ML artifacts: {ml_dir}")

    if success_count >= 2:
        print("\n🎉 HARIBON v2.0 setup completed successfully!")
        print("\n🚀 To start the system:")
        print("   1. cd backend")
        print("   2. python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000")
        print("   3. Open http://127.0.0.1:8000/docs")
        return 0
    else:
        print("\n❌ Setup failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
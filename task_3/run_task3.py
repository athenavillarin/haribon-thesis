"""
==============================================================================
HARIBON Red Tide Validation Study — Task 3: Run All Spatial Imputation
==============================================================================
Purpose:
    Execute the complete Task 3 workflow: spatial imputation analysis,
    hybrid methods, and validation plot generation.

Usage:
    python run_task3.py

This script will:
    1. Run spatial imputation methods on all masked datasets
    2. Run hybrid temporal-spatial methods
    3. Generate validation plots and summaries
    4. Compare results with Task 2 temporal methods

Output:
    All results saved in task3_results/ directory
==============================================================================
"""

import os
import sys
import subprocess
import time

def run_command(command, description):
    """Run a command and return success status."""
    print(f"\n{'='*70}")
    print(f"Running: {description}")
    print('='*70)
    
    start_time = time.time()
    
    # Get the directory where this script is located (task_3/)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    try:
        result = subprocess.run(command, shell=True, check=True,
                              capture_output=True, text=True, cwd=script_dir)
        print(result.stdout)
        elapsed = time.time() - start_time
        print(f"\n[OK] Completed in {elapsed:.1f} seconds")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Error running {description}:")
        print(e.stderr)
        elapsed = time.time() - start_time
        print(f"\n[FAILED] Failed after {elapsed:.1f} seconds")
        return False

def main():
    """Main execution function."""
    print("\n" + "="*70)
    print("HARIBON Red Tide Validation Study - Task 3")
    print("Spatial & Hybrid Imputation Methods")
    print("="*70)
    
    # Check if we're in the right directory
    if not os.path.exists("code/task3_spatial_imputation.py"):
        print("\n[ERROR] Error: Please run this script from the task_3 directory")
        print("  Current directory:", os.getcwd())
        print("  Expected files: code/task3_spatial_imputation.py")
        sys.exit(1)
    
    # Check if Task 1 data exists
    if not os.path.exists("../task_1/task1_data/Task1_Combined_Baseline_Daily.csv"):
        print("\n[ERROR] Error: Task 1 baseline data not found")
        print("  Expected: ../task_1/task1_data/Task1_Combined_Baseline_Daily.csv")
        print("  Please ensure Task 1 has been completed first")
        sys.exit(1)
    
    # Create results directory
    os.makedirs("task3_results", exist_ok=True)
    os.makedirs("task3_results/validation_plots", exist_ok=True)
    
    total_start = time.time()
    success_count = 0
    total_steps = 2
    
    # Step 1: Run spatial imputation analysis
    print("\n" + "-"*70)
    print("STEP 1/2: Spatial Imputation Analysis")
    print("-"*70)
    print("This will:")
    print("  - Load baseline and masked datasets")
    print("  - Apply 8 spatial imputation methods")
    print("  - Apply 3 hybrid temporal-spatial methods")
    print("  - Validate against ground truth")
    print("  - Generate detailed results CSV")
    print("\nEstimated time: 10-20 minutes")
    
    if run_command("python code/task3_spatial_imputation.py", "Spatial Imputation Analysis"):
        success_count += 1
    else:
        print("\n[FAILED] Spatial imputation analysis failed")
        print("  Continuing to next step...")
    
    # Step 2: Generate validation plots
    print("\n" + "-"*70)
    print("STEP 2/2: Validation Plots Generation")
    print("-"*70)
    print("This will:")
    print("  - Create method comparison heatmaps")
    print("  - Generate variable performance plots")
    print("  - Compare spatial vs temporal methods")
    print("  - Visualize hybrid method performance")
    print("  - Create time series examples")
    print("\nEstimated time: 2-5 minutes")
    
    if run_command("python code/task3_validation_plots.py", "Validation Plots"):
        success_count += 1
    else:
        print("\n[FAILED] Validation plot generation failed")
    
    # Summary
    total_elapsed = time.time() - total_start
    print("\n" + "="*70)
    print("TASK 3 EXECUTION SUMMARY")
    print("="*70)
    print(f"Steps completed: {success_count}/{total_steps}")
    print(f"Total time: {total_elapsed/60:.1f} minutes")
    
    if success_count == total_steps:
        print("\n[SUCCESS] All steps completed successfully!")
        print("\nResults saved in:")
        print("  - task3_results/spatial_imputation_results.csv")
        print("  - task3_results/method_comparison_metrics.csv")
        print("  - task3_results/summary_table.csv")
        print("  - task3_results/validation_plots/")
        
        print("\nNext Steps:")
        print("  1. Review validation plots in task3_results/validation_plots/")
        print("  2. Examine summary_table.csv for best performing methods")
        print("  3. Compare with Task 2 results for temporal vs spatial insights")
        print("  4. Use findings for Task 4 XGBoost feature engineering")
    else:
        print(f"\n[WARNING] Warning: {total_steps - success_count} step(s) failed")
        print("  Check error messages above for details")
        sys.exit(1)
    
    print("="*70)

if __name__ == "__main__":
    main()

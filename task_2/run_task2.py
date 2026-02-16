"""
==============================================================================
HARIBON Red Tide Validation Study — Task 2: Run All Temporal Imputation
==============================================================================
Purpose:
    Execute the complete Task 2 workflow: temporal imputation analysis and
    validation plot generation.

Usage:
    python run_task2.py

This script will:
    1. Run temporal imputation methods on all masked datasets
    2. Generate validation plots and summaries
    3. Display key findings

Output:
    All results saved in task2_results/ directory
==============================================================================
"""

import os
import sys
import subprocess

def run_command(command, description):
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print('='*60)

    try:
        result = subprocess.run(command, shell=True, check=True,
                              capture_output=True, text=True, cwd=os.path.dirname(__file__))
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running {description}:")
        print(e.stderr)
        return False

def main():
    """Main execution function."""
    print("HARIBON Red Tide Validation Study - Task 2")
    print("Temporal Imputation Methods")
    print("=" * 60)

    # Check if we're in the right directory
    if not os.path.exists("code/task2_temporal_imputation.py"):
        print("Error: Please run this script from the task_2 directory")
        sys.exit(1)

    # Step 1: Run temporal imputation analysis
    success1 = run_command(
        "cd code && python task2_temporal_imputation.py",
        "Temporal Imputation Analysis"
    )

    if not success1:
        print("Task 2 failed at imputation step")
        sys.exit(1)

    # Step 2: Generate validation plots
    success2 = run_command(
        "cd code && python task2_validation_plots.py",
        "Validation Plot Generation"
    )

    if not success2:
        print("Task 2 failed at plotting step")
        sys.exit(1)

    # Display summary
    print("\n" + "=" * 60)
    print("TASK 2 COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("Results saved in: task2_results/")
    print("\nKey outputs:")
    print("- temporal_imputation_results.csv: Detailed results for each variable/method/mask combination")
    print("- method_comparison_metrics.csv: Summary metrics by method and mask type")
    print("- validation_plots/: Performance comparison plots")
    print("- summary_table.csv: Overall method comparison")

    # Quick summary of findings
    print("\n" + "=" * 60)
    print("QUICK SUMMARY OF FINDINGS")
    print("=" * 60)

    try:
        import pandas as pd
        summary_df = pd.read_csv("task2_results/summary_table.csv")

        print("Overall Performance (averaged across all variables and gap patterns):")
        for _, row in summary_df.iterrows():
            method = row['method_name']
            rmse = row['rmse_mean']
            mae = row['mae_mean']
            r2 = row['r2_mean']
            print(f"\n{method}:")
            print(".4f")
            print(".4f")
            print(".4f")

        # Best performing method
        best_method = summary_df.loc[summary_df['rmse_mean'].idxmin(), 'method_name']
        print(f"\nBest overall method: {best_method}")

    except Exception as e:
        print(f"Could not load summary for quick analysis: {e}")

    print("\nNext steps:")
    print("- Review detailed results in task2_results/")
    print("- Compare with Task 3 (spatial imputation methods)")
    print("- Use best methods in Task 4 (XGBoost baseline)")

if __name__ == "__main__":
    main()
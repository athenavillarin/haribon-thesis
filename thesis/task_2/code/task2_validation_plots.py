"""
==============================================================================
HARIBON Red Tide Validation Study — Task 2: Validation Plots
==============================================================================
Purpose:
    Generate visualization plots for temporal imputation method validation.
    Creates comparison plots showing imputation accuracy across different
    methods and gap patterns.

Plots Generated:
    1. Method comparison by mask type (RMSE, MAE, R²)
    2. Variable-wise performance comparison
    3. Time series plots showing original vs imputed values
    4. Error distribution plots

Input:
    task2_results/temporal_imputation_results.csv
    task2_results/method_comparison_metrics.csv

Output:
    task2_results/validation_plots/*.png
==============================================================================
"""

import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Set style
plt.style.use('default')
sns.set_palette("husl")

# =============================================================================
# CONFIGURATION
# =============================================================================

RESULTS_DIR = "../task2_results"
RESULTS_FILE = "temporal_imputation_results.csv"
METRICS_FILE = "method_comparison_metrics.csv"
PLOTS_DIR = "validation_plots"

# Color scheme for methods
METHOD_COLORS = {
    'Linear Interpolation': '#1f77b4',
    'Climatological Substitution': '#ff7f0e'
}

# =============================================================================
# PLOTTING FUNCTIONS
# =============================================================================

def plot_method_comparison_by_mask_type(results_df):
    """Plot comparison of methods across different mask types."""
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    metrics = ['rmse', 'mae', 'r2']
    metric_labels = ['RMSE', 'MAE', 'R²']
    metric_limits = [(0, None), (0, None), (None, 1)]

    for i, (metric, label, limits) in enumerate(zip(metrics, metric_labels, metric_limits)):
        ax = axes[i]

        # Group by method and mask type
        plot_data = results_df.groupby(['method_name', 'mask_type'])[metric].mean().reset_index()

        # Create bar plot
        sns.barplot(data=plot_data, x='mask_type', y=metric, hue='method_name',
                   palette=METHOD_COLORS, ax=ax)

        ax.set_title(f'{label} by Mask Type', fontsize=12, fontweight='bold')
        ax.set_xlabel('Mask Type')
        ax.set_ylabel(label)
        ax.tick_params(axis='x', rotation=45)
        ax.legend(title='Method', bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.grid(True, alpha=0.3)

        # Set y-axis limits if specified
        if limits[0] is not None or limits[1] is not None:
            ax.set_ylim(limits[0], limits[1])

    plt.tight_layout()
    return fig

def plot_variable_performance(results_df):
    """Plot performance comparison across variables."""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    methods = results_df['method_name'].unique()

    for i, method in enumerate(methods):
        ax = axes[i // 2, i % 2]
        method_data = results_df[results_df['method_name'] == method]

        # Calculate mean metrics per variable
        var_metrics = method_data.groupby('variable')[['rmse', 'mae', 'r2']].mean().reset_index()

        # Plot RMSE and MAE as bars, R² as line
        x = np.arange(len(var_metrics))
        width = 0.35

        rmse_bars = ax.bar(x - width/2, var_metrics['rmse'], width,
                          label='RMSE', alpha=0.7, color='#d62728')
        mae_bars = ax.bar(x + width/2, var_metrics['mae'], width,
                         label='MAE', alpha=0.7, color='#ff7f0e')

        ax2 = ax.twinx()
        r2_line = ax2.plot(x, var_metrics['r2'], 'o-', color='#1f77b4',
                          linewidth=2, label='R²')

        ax.set_title(f'{method} - Variable Performance', fontsize=12, fontweight='bold')
        ax.set_xlabel('Variable')
        ax.set_ylabel('Error Metrics')
        ax2.set_ylabel('R² Score')
        ax.set_xticks(x)
        ax.set_xticklabels(var_metrics['variable'], rotation=45, ha='right')

        # Combine legends
        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines1 + lines2, labels1 + labels2, loc='upper right')

        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig

def plot_error_distributions(results_df):
    """Plot error distribution histograms."""
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))

    methods = results_df['method_name'].unique()

    for i, method in enumerate(methods):
        ax = axes[i]
        method_data = results_df[results_df['method_name'] == method]

        # Plot RMSE distribution
        sns.histplot(data=method_data, x='rmse', hue='mask_type',
                    multiple='stack', ax=ax, alpha=0.7)

        ax.set_title(f'{method} - RMSE Distribution', fontsize=12, fontweight='bold')
        ax.set_xlabel('RMSE')
        ax.set_ylabel('Count')
        ax.legend(title='Mask Type', bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig

def plot_method_comparison_heatmap(results_df):
    """Create heatmap showing method performance across variables and mask types."""
    # Pivot data for heatmap
    pivot_rmse = results_df.pivot_table(
        values='rmse', index='variable', columns=['method_name', 'mask_type'],
        aggfunc='mean'
    )

    # Simplify column names
    pivot_rmse.columns = [f"{method[:4]} - {mask}"
                         for method, mask in pivot_rmse.columns]

    fig, ax = plt.subplots(figsize=(12, 10))

    # Create heatmap
    sns.heatmap(pivot_rmse, annot=True, fmt='.3f', cmap='RdYlBu_r',
               ax=ax, cbar_kws={'label': 'RMSE'})

    ax.set_title('RMSE Heatmap: Methods vs Variables vs Mask Types',
                fontsize=14, fontweight='bold')
    ax.set_xlabel('Method - Mask Type')
    ax.set_ylabel('Variable')

    plt.tight_layout()
    return fig

def create_summary_table(results_df):
    """Create a summary table of results."""
    # Calculate overall performance by method
    summary = results_df.groupby('method_name').agg({
        'rmse': ['mean', 'std', 'min', 'max'],
        'mae': ['mean', 'std', 'min', 'max'],
        'r2': ['mean', 'std', 'min', 'max']
    }).round(4)

    # Flatten column names
    summary.columns = ['_'.join(col).strip() for col in summary.columns]

    return summary

# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main execution function."""
    print("Generating Task 2 validation plots...")
    print("=" * 50)

    # Load results
    results_path = os.path.join(RESULTS_DIR, RESULTS_FILE)
    if not os.path.exists(results_path):
        print(f"Error: Results file not found: {results_path}")
        print("Please run task2_temporal_imputation.py first.")
        return

    results_df = pd.read_csv(results_path)
    print(f"Loaded {len(results_df)} result records")

    # Create plots directory
    plots_dir = os.path.join(RESULTS_DIR, PLOTS_DIR)
    os.makedirs(plots_dir, exist_ok=True)

    # Generate plots
    plots = [
        ('method_comparison', plot_method_comparison_by_mask_type),
        ('variable_performance', plot_variable_performance),
        ('error_distributions', plot_error_distributions),
        ('performance_heatmap', plot_method_comparison_heatmap)
    ]

    for plot_name, plot_func in plots:
        print(f"Generating {plot_name} plot...")
        try:
            fig = plot_func(results_df)
            plot_path = os.path.join(plots_dir, f'{plot_name}.png')
            fig.savefig(plot_path, dpi=300, bbox_inches='tight')
            plt.close(fig)
            print(f"  Saved: {plot_path}")
        except Exception as e:
            print(f"  Error generating {plot_name}: {e}")

    # Create and save summary table
    print("Creating summary table...")
    summary = create_summary_table(results_df)
    summary_path = os.path.join(RESULTS_DIR, 'summary_table.csv')
    summary.to_csv(summary_path)
    print(f"Summary table saved: {summary_path}")

    # Print summary to console
    print("\n" + "=" * 60)
    print("TEMPORAL IMPUTATION SUMMARY")
    print("=" * 60)
    print(summary)

    print(f"\nPlots saved in: {plots_dir}")
    print("Task 2 visualization completed!")

if __name__ == "__main__":
    main()
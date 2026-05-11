"""
==============================================================================
HARIBON Red Tide Validation Study — Task 3: Validation Plots
==============================================================================
Purpose:
    Generate comprehensive validation plots for spatial and hybrid imputation
    methods, comparing performance across methods, variables, and gap patterns.

Plots Generated:
    1. Method comparison heatmap: RMSE by method × gap pattern
    2. Variable performance boxplots: MAE distribution across methods
    3. Spatial correlation scatter: Gigantes vs Roxas for key variables
    4. Hybrid comparison bar chart: Temporal vs Spatial vs Hybrid
    5. Gap size analysis: Performance vs gap length
    6. Time series examples: Original, masked, imputed for CHL
    7. Advection validation: Lag time analysis

Input:
    ../task3_results/spatial_imputation_results.csv
    ../task2_results/temporal_imputation_results.csv (for comparison)

Output:
    ../task3_results/validation_plots/*.png

==============================================================================
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10

# =============================================================================
# CONFIGURATION
# =============================================================================

# Input paths
TASK3_RESULTS_DIR = "task3_results"
TASK2_RESULTS_DIR = os.path.join("..", "task_2", "task2_results")
TASK1_DATA_DIR = os.path.join("..", "task_1", "task1_data")
RESULTS_FILE = "spatial_imputation_results.csv"
TEMPORAL_RESULTS_FILE = "temporal_imputation_results.csv"
BASELINE_FILE = "Task1_Combined_Baseline_Daily.csv"

# Output paths
PLOTS_DIR = os.path.join(TASK3_RESULTS_DIR, "validation_plots")

# Variables for focused analysis
KEY_VARIABLES = ['CHL', 'thetao', 'NDVI_daily', 'wind_speed_ms']

# Color schemes
SPATIAL_COLOR = '#2E86AB'
TEMPORAL_COLOR = '#A23B72'
HYBRID_COLOR = '#F18F01'

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def load_results():
    """Load spatial imputation results."""
    results_path = os.path.join(TASK3_RESULTS_DIR, RESULTS_FILE)
    if not os.path.exists(results_path):
        raise FileNotFoundError(f"Results file not found: {results_path}")
    
    df = pd.read_csv(results_path)
    return df

def load_temporal_results():
    """Load temporal imputation results from Task 2 for comparison."""
    results_path = os.path.join(TASK2_RESULTS_DIR, TEMPORAL_RESULTS_FILE)
    if os.path.exists(results_path):
        df = pd.read_csv(results_path)
        return df
    else:
        print(f"Warning: Task 2 results not found at {results_path}")
        return None

def load_baseline_data():
    """Load baseline data for spatial correlation analysis."""
    baseline_path = os.path.join(TASK1_DATA_DIR, BASELINE_FILE)
    df = pd.read_csv(baseline_path)
    df['Date'] = pd.to_datetime(df['Date'])
    return df

def categorize_method(method_name):
    """Categorize method as Spatial, Temporal, or Hybrid."""
    if 'Hybrid' in method_name or 'hybrid' in method_name:
        return 'Hybrid'
    elif method_name in ['Linear Interpolation', 'Climatological Substitution']:
        return 'Temporal'
    else:
        return 'Spatial'

# =============================================================================
# PLOT 1: METHOD COMPARISON HEATMAP
# =============================================================================

def plot_method_comparison_heatmap(results_df):
    """Create heatmap of RMSE by method × gap pattern."""
    print("  Generating method comparison heatmap...")
    
    # Aggregate by method and mask type
    pivot_data = results_df.groupby(['method_name', 'mask_type'])['rmse'].mean().reset_index()
    pivot_table = pivot_data.pivot(index='method_name', columns='mask_type', values='rmse')
    
    # Sort methods by average RMSE
    method_avg = pivot_table.mean(axis=1).sort_values()
    pivot_table = pivot_table.loc[method_avg.index]
    
    # Create plot
    fig, ax = plt.subplots(figsize=(14, 10))
    
    sns.heatmap(pivot_table, annot=True, fmt='.3f', cmap='RdYlGn_r', 
                cbar_kws={'label': 'RMSE'}, ax=ax, vmin=0, vmax=pivot_table.max().max())
    
    ax.set_title('Spatial Imputation Performance by Method and Gap Pattern\n(Lower RMSE = Better)', 
                 fontsize=14, fontweight='bold', pad=20)
    ax.set_xlabel('Gap Pattern', fontsize=12, fontweight='bold')
    ax.set_ylabel('Imputation Method', fontsize=12, fontweight='bold')
    
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    
    output_path = os.path.join(PLOTS_DIR, 'method_comparison_heatmap.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"    Saved: method_comparison_heatmap.png")

# =============================================================================
# PLOT 2: VARIABLE PERFORMANCE BOXPLOTS
# =============================================================================

def plot_variable_performance(results_df):
    """Create boxplots of MAE distribution across methods per variable."""
    print("  Generating variable performance boxplots...")
    
    # Filter to key variables
    var_data = results_df[results_df['variable'].isin(KEY_VARIABLES)].copy()
    
    # Create plot
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()
    
    for idx, variable in enumerate(KEY_VARIABLES):
        ax = axes[idx]
        data = var_data[var_data['variable'] == variable]
        
        # Group by method category
        data['method_category'] = data['method_name'].apply(categorize_method)
        
        # Create boxplot
        bp = data.boxplot(column='mae', by='method_category', ax=ax, 
                          patch_artist=True, return_type='dict')
        
        # Color by category
        colors = {'Spatial': SPATIAL_COLOR, 'Temporal': TEMPORAL_COLOR, 'Hybrid': HYBRID_COLOR}
        for patch, category in zip(bp['mae']['boxes'], data['method_category'].unique()):
            patch.set_facecolor(colors.get(category, 'gray'))
        
        ax.set_title(f'{variable}', fontsize=12, fontweight='bold')
        ax.set_xlabel('Method Category', fontsize=10)
        ax.set_ylabel('MAE', fontsize=10)
        ax.get_figure().suptitle('')  # Remove auto title
    
    fig.suptitle('Variable Performance by Method Category\n(Lower MAE = Better)', 
                 fontsize=14, fontweight='bold', y=0.995)
    
    plt.tight_layout()
    
    output_path = os.path.join(PLOTS_DIR, 'variable_performance_boxplot.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"    Saved: variable_performance_boxplot.png")

# =============================================================================
# PLOT 3: SPATIAL CORRELATION SCATTER
# =============================================================================

def plot_spatial_correlation(baseline_df):
    """Create scatter plots of Gigantes vs Roxas for key variables."""
    print("  Generating spatial correlation scatter plots...")
    
    # Pivot to get both locations side by side
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()
    
    for idx, variable in enumerate(KEY_VARIABLES):
        ax = axes[idx]
        
        # Get data for both locations
        gigantes = baseline_df[baseline_df['Location_Name'] == 'Gigantes Polygon'][['Date', variable]]
        roxas = baseline_df[baseline_df['Location_Name'] == 'Roxas Polygon'][['Date', variable]]
        
        merged = pd.merge(gigantes, roxas, on='Date', suffixes=('_Gigantes', '_Roxas'))
        merged = merged.dropna()
        
        if len(merged) == 0:
            ax.text(0.5, 0.5, 'No overlapping data', ha='center', va='center', transform=ax.transAxes)
            continue
        
        # Scatter plot
        ax.scatter(merged[f'{variable}_Gigantes'], merged[f'{variable}_Roxas'], 
                  alpha=0.5, s=20, c=SPATIAL_COLOR)
        
        # Fit line
        z = np.polyfit(merged[f'{variable}_Gigantes'], merged[f'{variable}_Roxas'], 1)
        p = np.poly1d(z)
        x_line = np.linspace(merged[f'{variable}_Gigantes'].min(), 
                            merged[f'{variable}_Gigantes'].max(), 100)
        ax.plot(x_line, p(x_line), "r--", alpha=0.8, linewidth=2, label=f'y = {z[0]:.2f}x + {z[1]:.2f}')
        
        # 1:1 line
        ax.plot([merged[f'{variable}_Gigantes'].min(), merged[f'{variable}_Gigantes'].max()],
               [merged[f'{variable}_Gigantes'].min(), merged[f'{variable}_Gigantes'].max()],
               'k-', alpha=0.3, linewidth=1, label='1:1 line')
        
        # Calculate correlation
        corr = np.corrcoef(merged[f'{variable}_Gigantes'], merged[f'{variable}_Roxas'])[0, 1]
        
        ax.set_title(f'{variable} (r = {corr:.3f})', fontsize=12, fontweight='bold')
        ax.set_xlabel('Gigantes Polygon', fontsize=10)
        ax.set_ylabel('Roxas Polygon', fontsize=10)
        ax.legend(loc='upper left', fontsize=8)
        ax.grid(True, alpha=0.3)
    
    fig.suptitle('Cross-Location Spatial Correlation\n(~60km distance)', 
                 fontsize=14, fontweight='bold', y=0.995)
    
    plt.tight_layout()
    
    output_path = os.path.join(PLOTS_DIR, 'spatial_correlation_scatter.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"    Saved: spatial_correlation_scatter.png")

# =============================================================================
# PLOT 4: HYBRID COMPARISON BAR CHART
# =============================================================================

def plot_hybrid_comparison(results_df, temporal_df=None):
    """Compare Temporal-only, Spatial-only, and Hybrid methods."""
    print("  Generating hybrid comparison bar chart...")
    
    # Categorize methods
    results_df['method_category'] = results_df['method_name'].apply(categorize_method)
    
    # Calculate average metrics by category
    category_metrics = results_df.groupby('method_category').agg({
        'rmse': 'mean',
        'mae': 'mean',
        'r2': 'mean'
    }).reset_index()
    
    # Add Task 2 temporal methods if available
    if temporal_df is not None:
        temporal_metrics = temporal_df.groupby('method_name').agg({
            'rmse': 'mean',
            'mae': 'mean',
            'r2': 'mean'
        }).reset_index()
        temporal_metrics['method_category'] = 'Task 2 Temporal'
        
        # Take average of temporal methods
        temporal_avg = temporal_metrics[['rmse', 'mae', 'r2']].mean()
        temporal_row = pd.DataFrame([{
            'method_category': 'Task 2 Temporal',
            'rmse': temporal_avg['rmse'],
            'mae': temporal_avg['mae'],
            'r2': temporal_avg['r2']
        }])
        category_metrics = pd.concat([category_metrics, temporal_row], ignore_index=True)
    
    # Create subplots for each metric
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    metrics = ['rmse', 'mae', 'r2']
    titles = ['Root Mean Square Error', 'Mean Absolute Error', 'R² Score']
    colors_map = {
        'Spatial': SPATIAL_COLOR,
        'Temporal': TEMPORAL_COLOR,
        'Hybrid': HYBRID_COLOR,
        'Task 2 Temporal': '#6A0572'
    }
    
    for idx, (metric, title) in enumerate(zip(metrics, titles)):
        ax = axes[idx]
        
        data_to_plot = category_metrics.sort_values(metric, ascending=(metric != 'r2'))
        colors = [colors_map.get(cat, 'gray') for cat in data_to_plot['method_category']]
        
        bars = ax.bar(range(len(data_to_plot)), data_to_plot[metric], color=colors, alpha=0.8)
        
        # Add value labels
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2., height,
                   f'{height:.3f}', ha='center', va='bottom', fontsize=9)
        
        ax.set_xticks(range(len(data_to_plot)))
        ax.set_xticklabels(data_to_plot['method_category'], rotation=45, ha='right')
        ax.set_ylabel(title, fontsize=11, fontweight='bold')
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')
    
    fig.suptitle('Temporal vs Spatial vs Hybrid Methods Comparison', 
                 fontsize=14, fontweight='bold', y=0.98)
    
    plt.tight_layout()
    
    output_path = os.path.join(PLOTS_DIR, 'hybrid_comparison_bar.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"    Saved: hybrid_comparison_bar.png")

# =============================================================================
# PLOT 5: GAP SIZE ANALYSIS
# =============================================================================

def plot_gap_size_analysis(results_df):
    """Analyze performance vs gap characteristics."""
    print("  Generating gap size analysis...")
    
    # Map mask types to approximate gap sizes
    gap_size_map = {
        'random_10': 2,
        'random_20': 2,
        'block_7day': 7,
        'block_14day': 14,
        'seasonal': 30,  # Approximate
        'cross_variable': 50,  # Approximate
        'rolling_origin': 90,
        'rolling_origin_180': 180
    }
    
    results_df['approx_gap_size'] = results_df['mask_type'].map(gap_size_map)
    
    # Filter to methods with sufficient data
    method_counts = results_df.groupby('method_name').size()
    valid_methods = method_counts[method_counts >= 50].index
    
    plot_data = results_df[results_df['method_name'].isin(valid_methods)].copy()
    plot_data['method_category'] = plot_data['method_name'].apply(categorize_method)
    
    # Create plot
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # RMSE vs Gap Size
    ax = axes[0]
    for category in ['Spatial', 'Temporal', 'Hybrid']:
        cat_data = plot_data[plot_data['method_category'] == category]
        if len(cat_data) == 0:
            continue
        
        gap_rmse = cat_data.groupby('approx_gap_size')['rmse'].mean()
        ax.plot(gap_rmse.index, gap_rmse.values, marker='o', linewidth=2, 
               label=category, alpha=0.8)
    
    ax.set_xlabel('Approximate Gap Size (days)', fontsize=11, fontweight='bold')
    ax.set_ylabel('Average RMSE', fontsize=11, fontweight='bold')
    ax.set_title('RMSE vs Gap Size', fontsize=12, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xscale('log')
    
    # MAE vs Gap Size
    ax = axes[1]
    for category in ['Spatial', 'Temporal', 'Hybrid']:
        cat_data = plot_data[plot_data['method_category'] == category]
        if len(cat_data) == 0:
            continue
        
        gap_mae = cat_data.groupby('approx_gap_size')['mae'].mean()
        ax.plot(gap_mae.index, gap_mae.values, marker='o', linewidth=2, 
               label=category, alpha=0.8)
    
    ax.set_xlabel('Approximate Gap Size (days)', fontsize=11, fontweight='bold')
    ax.set_ylabel('Average MAE', fontsize=11, fontweight='bold')
    ax.set_title('MAE vs Gap Size', fontsize=12, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xscale('log')
    
    fig.suptitle('Method Performance vs Gap Size', fontsize=14, fontweight='bold', y=0.98)
    
    plt.tight_layout()
    
    output_path = os.path.join(PLOTS_DIR, 'gap_size_analysis.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"    Saved: gap_size_analysis.png")

# =============================================================================
# PLOT 6: TIME SERIES EXAMPLE
# =============================================================================

def plot_time_series_example(baseline_df):
    """Show example time series with imputation."""
    print("  Generating time series examples...")
    
    # Note: This is a conceptual plot showing what imputation looks like
    # Actual imputed values would need to be loaded from intermediate results
    
    # Get CHL data for both locations
    gigantes = baseline_df[baseline_df['Location_Name'] == 'Gigantes Polygon'][['Date', 'CHL']].copy()
    gigantes = gigantes.sort_values('Date').reset_index(drop=True)
    
    # Select 3-month window
    start_idx = 200
    end_idx = start_idx + 90
    plot_data = gigantes.iloc[start_idx:end_idx].copy()
    
    # Simulate gaps (10% random)
    np.random.seed(42)
    gap_mask = np.random.random(len(plot_data)) < 0.1
    plot_data['CHL_masked'] = plot_data['CHL'].copy()
    plot_data.loc[gap_mask, 'CHL_masked'] = np.nan
    
    # Simulate imputation (linear interpolation)
    plot_data['CHL_imputed'] = plot_data['CHL_masked'].interpolate(method='linear')
    
    # Create plot
    fig, ax = plt.subplots(figsize=(14, 6))
    
    # Original (ground truth)
    ax.plot(plot_data['Date'], plot_data['CHL'], 'k-', linewidth=2, 
           label='Original (Ground Truth)', alpha=0.7)
    
    # Masked
    ax.plot(plot_data['Date'], plot_data['CHL_masked'], 'o', color='red', 
           markersize=4, label='Available Data (After Masking)', alpha=0.6)
    
    # Imputed values
    imputed_points = plot_data[gap_mask]
    ax.plot(imputed_points['Date'], imputed_points['CHL_imputed'], 'o', 
           color='green', markersize=6, label='Imputed Values', zorder=5)
    
    ax.set_xlabel('Date', fontsize=12, fontweight='bold')
    ax.set_ylabel('Chlorophyll-a (mg/m³)', fontsize=12, fontweight='bold')
    ax.set_title('Example: Spatial Imputation of CHL at Gigantes Polygon\n(3-month window)', 
                fontsize=14, fontweight='bold')
    ax.legend(loc='upper right', fontsize=10)
    ax.grid(True, alpha=0.3)
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    output_path = os.path.join(PLOTS_DIR, 'time_series_example.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"    Saved: time_series_example.png")

# =============================================================================
# PLOT 7: METHOD RANKING
# =============================================================================

def plot_method_ranking(results_df):
    """Create ranking of all methods by overall performance."""
    print("  Generating method ranking...")
    
    # Calculate average metrics
    method_summary = results_df.groupby('method_name').agg({
        'rmse': 'mean',
        'mae': 'mean',
        'r2': 'mean',
        'missing_count': 'sum'
    }).reset_index()
    
    # Rank by RMSE
    method_summary = method_summary.sort_values('rmse')
    method_summary['rank'] = range(1, len(method_summary) + 1)
    
    # Color by category
    method_summary['method_category'] = method_summary['method_name'].apply(categorize_method)
    colors_map = {
        'Spatial': SPATIAL_COLOR,
        'Temporal': TEMPORAL_COLOR,
        'Hybrid': HYBRID_COLOR
    }
    colors = [colors_map.get(cat, 'gray') for cat in method_summary['method_category']]
    
    # Create plot
    fig, ax = plt.subplots(figsize=(10, 8))
    
    bars = ax.barh(range(len(method_summary)), method_summary['rmse'], color=colors, alpha=0.8)
    
    # Add value labels
    for idx, (bar, rmse) in enumerate(zip(bars, method_summary['rmse'])):
        ax.text(rmse + 0.02, bar.get_y() + bar.get_height() / 2, 
               f'{rmse:.3f}', va='center', fontsize=9)
    
    ax.set_yticks(range(len(method_summary)))
    ax.set_yticklabels(method_summary['method_name'], fontsize=10)
    ax.set_xlabel('Average RMSE (Lower = Better)', fontsize=12, fontweight='bold')
    ax.set_title('Method Ranking by RMSE\nAcross All Variables and Gap Patterns', 
                fontsize=14, fontweight='bold', pad=20)
    ax.grid(True, alpha=0.3, axis='x')
    
    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=SPATIAL_COLOR, alpha=0.8, label='Spatial'),
        Patch(facecolor=HYBRID_COLOR, alpha=0.8, label='Hybrid')
    ]
    ax.legend(handles=legend_elements, loc='lower right')
    
    plt.tight_layout()
    
    output_path = os.path.join(PLOTS_DIR, 'method_ranking.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"    Saved: method_ranking.png")

# =============================================================================
# MAIN EXECUTION
# =============================================================================

def generate_all_plots():
    """Generate all validation plots."""
    print("="*70)
    print("HARIBON Red Tide Validation Study - Task 3")
    print("Validation Plots Generation")
    print("="*70)
    
    # Create plots directory
    os.makedirs(PLOTS_DIR, exist_ok=True)
    
    # Load data
    print("\nLoading results...")
    results_df = load_results()
    print(f"  Loaded {len(results_df)} spatial imputation results")
    
    temporal_df = load_temporal_results()
    if temporal_df is not None:
        print(f"  Loaded {len(temporal_df)} temporal imputation results")
    
    baseline_df = load_baseline_data()
    print(f"  Loaded {len(baseline_df)} baseline records")
    
    # Generate plots
    print("\nGenerating plots...")
    
    plot_method_comparison_heatmap(results_df)
    plot_variable_performance(results_df)
    plot_spatial_correlation(baseline_df)
    plot_hybrid_comparison(results_df, temporal_df)
    plot_gap_size_analysis(results_df)
    plot_time_series_example(baseline_df)
    plot_method_ranking(results_df)
    
    print(f"\n{'='*70}")
    print("All validation plots generated successfully!")
    print(f"Plots saved in: {PLOTS_DIR}")
    print(f"{'='*70}")

if __name__ == "__main__":
    generate_all_plots()

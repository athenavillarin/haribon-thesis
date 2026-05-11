#!/usr/bin/env python3
"""
Standalone SHAP Report Generator for HARIBON XGBoost Model

This script loads the trained XGBoost model, computes SHAP values on the full training dataset,
and generates comprehensive explainability reports including plots and CSV data.

Outputs:
- shap_summary_bar.png: Bar plot of mean absolute SHAP values by feature importance
- shap_summary_beeswarm.png: Beeswarm summary plot showing SHAP value distributions
- shap_values.csv: CSV file with mean absolute SHAP values per feature
"""

import pandas as pd
import numpy as np
import xgboost as xgb
import shap
import matplotlib.pyplot as plt
from pathlib import Path
import os

# Define the 11 environmental features used in the model
FEATURES = [
    'CHL', 'NDVI_daily', 'mlotst', 'precip_mm_day', 'so', 'thetao',
    'uo', 'vo', 'wind_speed_ms', 'wind_u_ms', 'wind_v_ms'
]

def load_xgboost_model(model_path):
    """Load the trained XGBoost model."""
    print(f"Loading XGBoost model from {model_path}...")
    model = xgb.XGBClassifier()
    model.load_model(str(model_path))
    return model

def load_training_data(data_path):
    """Load and preprocess the training dataset."""
    print(f"Loading training data from {data_path}...")
    df = pd.read_csv(data_path)

    # Filter to the 11 features + target (if available)
    available_features = [f for f in FEATURES if f in df.columns]
    if len(available_features) != len(FEATURES):
        missing = set(FEATURES) - set(available_features)
        print(f"Warning: Missing features in dataset: {missing}")

    # Select features and drop rows with NaN values
    X = df[available_features].dropna()

    print(f"Loaded {len(X)} samples with {len(available_features)} features")
    print(f"Features: {available_features}")

    return X

def compute_shap_values(model, X):
    """Compute SHAP values for the dataset."""
    print("Computing SHAP values using TreeExplainer...")

    # Create SHAP explainer
    explainer = shap.TreeExplainer(model)

    # Compute SHAP values (this may take some time for large datasets)
    shap_values = explainer.shap_values(X)

    print(f"SHAP values computed with shape: {shap_values.shape}")
    return shap_values, explainer

def generate_shap_plots(shap_values, X, output_dir):
    """Generate SHAP summary plots."""
    print("Generating SHAP summary plots...")

    # Set matplotlib backend to avoid display issues
    plt.switch_backend('Agg')

    # 1. Bar plot of mean absolute SHAP values
    plt.figure(figsize=(10, 6))
    shap.summary_plot(shap_values, X, plot_type="bar", show=False)
    plt.title("SHAP Feature Importance (Mean Absolute Values)")
    plt.tight_layout()
    bar_plot_path = output_dir / "shap_summary_bar.png"
    plt.savefig(bar_plot_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved bar plot to {bar_plot_path}")

    # 2. Beeswarm summary plot
    plt.figure(figsize=(10, 8))
    shap.summary_plot(shap_values, X, show=False)
    plt.title("SHAP Value Distribution (Beeswarm Plot)")
    plt.tight_layout()
    beeswarm_plot_path = output_dir / "shap_summary_beeswarm.png"
    plt.savefig(beeswarm_plot_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved beeswarm plot to {beeswarm_plot_path}")

def generate_shap_csv(shap_values, X, output_dir):
    """Generate CSV file with mean absolute SHAP values per feature."""
    print("Generating SHAP values CSV...")

    # Calculate mean absolute SHAP values for each feature
    mean_abs_shap = np.abs(shap_values).mean(axis=0)

    # Create DataFrame with feature names and SHAP values
    shap_df = pd.DataFrame({
        'feature': X.columns,
        'mean_absolute_shap': mean_abs_shap
    })

    # Sort by importance (descending)
    shap_df = shap_df.sort_values('mean_absolute_shap', ascending=False)

    # Save to CSV
    csv_path = output_dir / "shap_values.csv"
    shap_df.to_csv(csv_path, index=False)
    print(f"Saved SHAP values to {csv_path}")

    # Print top 5 features
    print("\nTop 5 most important features by mean absolute SHAP value:")
    for i, row in shap_df.head(5).iterrows():
        print(".4f")

def main():
    """Main function to run the SHAP report generation."""
    print("HARIBON XGBoost SHAP Report Generator")
    print("=" * 50)

    # Determine project paths
    script_dir = Path(__file__).resolve().parent
    backend_dir = script_dir.parent.parent
    project_root = backend_dir.parent.parent

    # Define paths
    model_path = project_root / "xgboost_model" / "saved_model" / "best_xgboost_model.json"
    data_path = project_root / "final_compiled_dataset" / "Combined_Labeled.csv"
    output_dir = script_dir  # Save outputs in the scripts directory

    # Verify paths exist
    if not model_path.exists():
        raise FileNotFoundError(f"XGBoost model not found at {model_path}")
    if not data_path.exists():
        raise FileNotFoundError(f"Training data not found at {data_path}")

    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Load model and data
        model = load_xgboost_model(model_path)
        X = load_training_data(data_path)

        # Compute SHAP values
        shap_values, explainer = compute_shap_values(model, X)

        # Generate outputs
        generate_shap_plots(shap_values, X, output_dir)
        generate_shap_csv(shap_values, X, output_dir)

        print("\nSHAP report generation completed successfully!")
        print(f"Output files saved in: {output_dir}")

    except Exception as e:
        print(f"Error during SHAP report generation: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
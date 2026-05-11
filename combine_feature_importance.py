import pandas as pd
from pathlib import Path

# Directory with all feature importance files
feature_importance_dir = Path(r'c:\Users\meagie\Desktop\haribon-thesis\task_4\task4_results\feature_importance')
output_file = Path(r'c:\Users\meagie\Desktop\haribon-thesis\ensemble_model\results\feature_importance_combined.csv')

# Read all feature importance CSVs
all_files = list(feature_importance_dir.glob('feature_importance_*.csv'))
dfs = []

for file in sorted(all_files):
    df = pd.read_csv(file)
    dfs.append(df)
    print(f"Read {file.name}: {len(df)} rows")

# Combine all dataframes
combined_df = pd.concat(dfs, ignore_index=True)

# Sort by method, then by importance (descending)
combined_df = combined_df.sort_values(['method', 'mean_abs_importance'], ascending=[True, False])

# Save to CSV
output_file.parent.mkdir(parents=True, exist_ok=True)
combined_df.to_csv(output_file, index=False)

print(f"\n✓ Combined {len(dfs)} files with {len(combined_df)} total rows")
print(f"✓ Output saved to: {output_file}")

# Show top features per method
print("\n=== Top 3 Features per Imputation Method ===\n")
for method in sorted(combined_df['method'].unique()):
    top_3 = combined_df[combined_df['method'] == method].head(3)
    print(f"{method}:")
    for idx, row in top_3.iterrows():
        print(f"  {row['feature']:<40} {row['mean_abs_importance']:.6f}")
    print()

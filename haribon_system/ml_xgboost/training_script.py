import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from sklearn.preprocessing import StandardScaler
import joblib
from datetime import datetime
from pathlib import Path
import json

def load_and_preprocess_data(data_path):
    """Load and preprocess the enhanced HARIBON dataset"""
    print("Loading HARIBON v2.0 dataset...")

    df = pd.read_csv(data_path)
    df['Date'] = pd.to_datetime(df['Date'])

    # Filter out rows with missing target
    df = df.dropna(subset=['red_tide_label'])

    print(f"Dataset loaded: {len(df)} samples")
    print(f"Features available: {list(df.columns)}")
    print(f"Target distribution: {df['red_tide_label'].value_counts()}")

    return df

def create_training_features(df):
    """Create comprehensive training features"""
    print("Creating enhanced training features...")

    df = df.sort_values(['Location_Name', 'Date'])

    # Lag features (7 days)
    lag_features = ['CHL', 'NDVI_daily', 'NDVI_raw', 'mlotst', 'precip_mm_day',
                   'so', 'thetao', 'uo', 'vo', 'wind_speed_ms', 'wind_u_ms', 'wind_v_ms']

    for lag in range(1, 8):
        for feature in lag_features:
            df[f'{feature}_lag_{lag}'] = df.groupby('Location_Name')[feature].shift(lag)

    # Rolling statistics (30-day windows)
    rolling_features = ['CHL', 'so', 'thetao', 'mlotst', 'precip_mm_day']
    for feature in rolling_features:
        df[f'{feature}_rolling30_mean'] = df.groupby('Location_Name')[feature].transform(
            lambda x: x.rolling(window=30, min_periods=1).mean())
        df[f'{feature}_rolling30_std'] = df.groupby('Location_Name')[feature].transform(
            lambda x: x.rolling(window=30, min_periods=1).std())

    # Anomaly features
    anomaly_features = ['CHL', 'so', 'thetao', 'mlotst']
    for feature in anomaly_features:
        df[f'{feature}_anomaly'] = df[feature] - df[f'{feature}_rolling30_mean']

    # Temporal features
    df['Day_of_year'] = df['Date'].dt.dayofyear
    df['Week_of_year'] = df['Date'].dt.isocalendar().week.astype(int)
    df['Month'] = df['Date'].dt.month
    df['Quarter'] = df['Date'].dt.quarter

    # Interaction features
    df['thetao_x_so'] = df['thetao'] * df['so']
    df['CHL_x_thetao'] = df['CHL'] * df['thetao']
    df['CHL_per_precip'] = df['CHL'] / (df['precip_mm_day'] + 1e-6)
    df['wind_stress'] = df['wind_speed_ms'] * df['wind_speed_ms']
    df['current_magnitude'] = np.sqrt(df['uo']**2 + df['vo']**2)
    df['NDVI_x_precip'] = df['NDVI_daily'] * df['precip_mm_day']

    # Fill missing values
    df = df.fillna(method='ffill').fillna(method='bfill').fillna(0)

    return df

def train_enhanced_model(X_train, y_train, X_test, y_test):
    """Train the enhanced XGBoost model"""
    print("Training enhanced HARIBON XGBoost model...")

    # Enhanced hyperparameters for better performance
    params = {
        'objective': 'binary:logistic',
        'eval_metric': 'auc',
        'max_depth': 6,
        'learning_rate': 0.1,
        'n_estimators': 200,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'min_child_weight': 1,
        'gamma': 0.1,
        'reg_alpha': 0.1,
        'reg_lambda': 0.1,
        'scale_pos_weight': len(y_train[y_train == 0]) / len(y_train[y_train == 1])  # Handle class imbalance
    }

    model = xgb.XGBClassifier(**params)

    # Train with early stopping
    eval_set = [(X_train, y_train), (X_test, y_test)]
    model.fit(
        X_train, y_train,
        eval_set=eval_set,
        verbose=True
    )

    return model

def evaluate_model(model, X_test, y_test, feature_names):
    """Evaluate model performance"""
    print("Evaluating model performance...")

    y_pred_proba = model.predict_proba(X_test)[:, 1]
    y_pred = (y_pred_proba > 0.5).astype(int)

    # Calculate metrics
    auc_score = roc_auc_score(y_test, y_pred_proba)

    print(f"AUC Score: {auc_score:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))

    print("\nConfusion Matrix:")
    cm = confusion_matrix(y_test, y_pred)
    print(cm)

    # Feature importance
    feature_importance = model.feature_importances_
    top_features = sorted(zip(feature_names, feature_importance),
                         key=lambda x: x[1], reverse=True)[:20]

    print("\nTop 20 Feature Importances:")
    for feature, importance in top_features:
        print(f"{feature}: {importance:.4f}")

    return {
        'auc_score': auc_score,
        'feature_importance': dict(top_features)
    }

def save_model_artifacts(model, scaler, feature_names, model_dir):
    """Save model and related artifacts"""
    print("Saving model artifacts...")

    model_dir = Path(model_dir)
    model_dir.mkdir(exist_ok=True)

    # Save model and scaler
    joblib.dump(model, model_dir / 'haribon_model_v2.joblib')
    joblib.dump(scaler, model_dir / 'haribon_scaler_v2.joblib')

    # Save feature names
    with open(model_dir / 'haribon_feature_names_v2.txt', 'w') as f:
        f.write('\n'.join(feature_names))

    # Save feature importance
    feature_importance = model.feature_importances_
    importance_dict = dict(zip(feature_names, feature_importance))
    with open(model_dir / 'haribon_feature_importance_v2.json', 'w') as f:
        json.dump(importance_dict, f, indent=2)

    print(f"Model artifacts saved to {model_dir}")

def main():
    """Main training pipeline"""
    print("=== HARIBON v2.0 Model Training Pipeline ===")

    # Configuration
    data_path = Path(__file__).parent.parent.parent / "final_compiled_dataset" / "Combined_Labeled.csv"
    model_dir = Path(__file__).parent

    # Load and preprocess data
    df = load_and_preprocess_data(data_path)

    # Create features
    df_featured = create_training_features(df)

    # Prepare training data
    feature_cols = [col for col in df_featured.columns
                   if col not in ['Location_Name', 'Date', 'red_tide', 'red_tide_label']]
    X = df_featured[feature_cols]
    y = df_featured['red_tide_label']

    # Convert continuous labels to binary (threshold = 0.5)
    y = (y >= 0.5).astype(int)

    print(f"Training with {len(feature_cols)} features")
    print(f"Converted target to binary: {y.value_counts().to_dict()}")

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Train model
    model = train_enhanced_model(X_train_scaled, y_train, X_test_scaled, y_test)

    # Evaluate
    metrics = evaluate_model(model, X_test_scaled, y_test, feature_cols)

    # Save artifacts
    save_model_artifacts(model, scaler, feature_cols, model_dir)

    print("=== Training Complete ===")
    print(f"Model saved with AUC: {metrics['auc_score']:.4f}")

if __name__ == "__main__":
    main()
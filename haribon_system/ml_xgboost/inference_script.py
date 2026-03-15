import pandas as pd
import numpy as np
import joblib
from datetime import datetime
from pathlib import Path

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================
def create_inference_features(df):
    """Create comprehensive features for the enhanced HARIBON model"""
    df = df.sort_values(['Location_Name', 'Date'])

    # Lag features for time series (7 days)
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
    df['thetao_x_so'] = df['thetao'] * df['so']  # SST x Salinity
    df['CHL_x_thetao'] = df['CHL'] * df['thetao']  # Chlorophyll x SST
    df['CHL_per_precip'] = df['CHL'] / (df['precip_mm_day'] + 1e-6)  # Chlorophyll per precipitation
    df['wind_stress'] = df['wind_speed_ms'] * df['wind_speed_ms']  # Wind stress approximation
    df['current_magnitude'] = np.sqrt(df['uo']**2 + df['vo']**2)  # Current speed

    # Land-sea interaction features
    df['NDVI_x_precip'] = df['NDVI_daily'] * df['precip_mm_day']  # Vegetation x rainfall (runoff potential)

    # Fill missing values
    df = df.fillna(method='ffill').fillna(method='bfill').fillna(0)

    return df

def generate_explanation(input_data_row):
    """Generate human-readable explanation for high-risk predictions"""
    reasons = []

    # Environmental thresholds for explanation
    thresholds = {
        'CHL_anomaly': 0.5,
        'thetao_anomaly': 0.8,
        'precip_mm_day': 15.0,
        'mlotst_anomaly': 5.0,
        'so_anomaly': 0.5
    }

    if input_data_row.get('CHL_anomaly', 0) > thresholds['CHL_anomaly']:
        reasons.append(f"elevated chlorophyll-a levels (anomaly of +{input_data_row['CHL_anomaly']:.2f})")
    if input_data_row.get('thetao_anomaly', 0) > thresholds['thetao_anomaly']:
        reasons.append(f"unusually warm sea surface temperatures (anomaly of +{input_data_row['thetao_anomaly']:.2f}°C)")
    if input_data_row.get('precip_mm_day', 0) > thresholds['precip_mm_day']:
        reasons.append(f"heavy recent rainfall ({input_data_row['precip_mm_day']:.1f} mm/day)")
    if input_data_row.get('mlotst_anomaly', 0) > thresholds['mlotst_anomaly']:
        reasons.append(f"unusual mixed layer depth (anomaly of {input_data_row['mlotst_anomaly']:.1f} m)")
    if input_data_row.get('so_anomaly', 0) > thresholds['so_anomaly']:
        reasons.append(f"salinity anomalies (change of {input_data_row['so_anomaly']:.2f} PSU)")

    if not reasons:
        return "Multiple environmental factors indicate potential bloom conditions."

    if len(reasons) == 1:
        return f"High risk primarily due to {reasons[0]}."
    return f"High risk due to a combination of: {', '.join(reasons[:-1])} and {reasons[-1]}."

def map_risk_with_explanation(probability):
    """Map probability to risk level with explanation"""
    if probability < 0.20:
        return "Green: Very Low Risk (<20%)"
    elif probability < 0.40:
        return "Yellow: Low Risk (20-40%)"
    elif probability < 0.70:
        return "Orange: Moderate Risk (40-70%)"
    else:
        return "Red: High Risk (>70%)"

# ==============================================================================
# CORE INFERENCE FUNCTION
# ==============================================================================
def predict_risk(new_data_point, historical_df, model, scaler, feature_names):
    """Enhanced inference function for HARIBON v2.0"""
    print("--- Starting Enhanced HARIBON Inference ---")

    # Ensure required columns exist
    if 'red_tide_label' not in historical_df.columns:
        historical_df['red_tide_label'] = 0
    if 'red_tide_label' not in new_data_point:
        new_data_point['red_tide_label'] = 0

    # Prepare new data
    df_new = pd.DataFrame([new_data_point])
    df_new['Date'] = pd.to_datetime(df_new['Date'])

    required_cols = ['Date', 'Location_Name', 'CHL', 'NDVI_daily', 'NDVI_raw', 'mlotst',
                    'precip_mm_day', 'so', 'thetao', 'uo', 'vo', 'wind_speed_ms',
                    'wind_u_ms', 'wind_v_ms', 'red_tide_label']

    df_combined = pd.concat([historical_df[required_cols], df_new], ignore_index=True)

    # Feature engineering
    df_featured = create_inference_features(df_combined)
    latest_features_df = df_featured.iloc[-1:]

    print("1. Enhanced features engineered for the new data point.")

    # Align with model's training features
    X_pred = latest_features_df.reindex(columns=feature_names, fill_value=0)
    print(f"2. Data aligned to {len(X_pred.columns)} model features.")

    # Scale data safely
    try:
        data_scaled = scaler.transform(X_pred)
    except ValueError as e:
        print(f"WARNING: Feature mismatch detected: {e}")
        print("Attempting automatic fix...")
        if hasattr(scaler, 'feature_names_in_'):
            X_pred = X_pred.reindex(columns=scaler.feature_names_in_, fill_value=0)
            data_scaled = scaler.transform(X_pred)
        else:
            raise

    print("3. Input data scaled.")

    # Predict
    probability = model.predict_proba(data_scaled)[0, 1]
    risk_level = map_risk_with_explanation(probability)

    explanation = ""
    if "Red: High Risk" in risk_level:
        explanation = generate_explanation(X_pred.iloc[0])

    print("--- Enhanced HARIBON Inference Complete ---")
    
    # Calculate confidence based on how extreme the probability is (0 or 1 is high confidence, 0.5 is low)
    # distance_from_uncertainty = abs(probability - 0.5) * 2  # 0 to 1 scale
    # Raw probability isn't confidence, but for this display we'll use a derived metric or just show probability
    # If the user asks for "confidence", usually in ML it means probability of the predicted class.
    # Here, "red tide probability" is what we have.
    # Let's map it: if prob is very low (<0.1) -> high confidence it's safe.
    # if prob is high (>0.8) -> high confidence it's risky.
    # if prob is 0.5 -> low confidence.
    dist = abs(probability - 0.5)
    conf_score = 0.5 + dist # Range [0.5, 1.0] -> 50% to 100% confidence
    
    return {
        "risk_level": risk_level,
        "probability": probability,
        "explanation": explanation,
        "confidence": f"{conf_score * 100:.1f}%"
    }
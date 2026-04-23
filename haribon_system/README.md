# 🌊 HARIBON v2.0: Harmful Algal Bloom Intelligent Observer Network

An enhanced AI-powered early warning system for proactive red tide risk forecasting in Western Visayas, Philippines.

---

## 📜 Project Overview

The Harmful Algal Bloom Intelligent Observer Network (HARIBON) v2.0 is an advanced predictive monitoring platform that leverages state-of-the-art machine learning, comprehensive satellite remote sensing, and multi-modal environmental data analytics to provide superior forecasting of Harmful Algal Blooms (HABs), commonly known as red tide.

### 🚀 What's New in v2.0

- **Enhanced Feature Set**: 15+ environmental variables including chlorophyll-a, SST, salinity, ocean currents, wind patterns, NDVI, and mixed layer depth
- **Advanced ML Pipeline**: XGBoost with comprehensive feature engineering including lag features, rolling statistics, and interaction terms
- **Expanded Coverage**: 7 key locations across Western Visayas with precise coordinates
- **Real-time Predictions**: Live prediction API endpoint for immediate risk assessment
- **Improved Data Quality**: Enhanced preprocessing and feature validation

### 🌟 Key Differentiators

- **Comprehensive Environmental Monitoring**: Integrates marine, atmospheric, and terrestrial data sources
- **Advanced Feature Engineering**: Time-series analysis with lag features and rolling statistics
- **Location-Specific Models**: Tailored predictions for aquaculture and fishing zones
- **Open Data Integration**: Compatible with Copernicus Marine, NASA Earthdata, and local monitoring networks

---

## 🎯 Core Objectives

1. **Enhanced Prediction Accuracy**: Utilize comprehensive environmental datasets for superior HAB forecasting
2. **Multi-Temporal Analysis**: Incorporate historical patterns and real-time environmental conditions
3. **Stakeholder Empowerment**: Provide actionable intelligence for fisheries and coastal management
4. **Scientific Advancement**: Contribute to HAB research through open-source predictive modeling

---

## 🤖 AI Solution Architecture

### Core Technology Stack
- **Algorithm**: XGBoost Classifier with advanced feature engineering
- **Data Sources**: Enhanced HARIBON dataset with 15+ environmental variables
- **Feature Engineering**:
  - Time-series lags (7-day windows)
  - Rolling statistics (30-day means and standard deviations)
  - Anomaly detection features
  - Interaction terms (SST × salinity, chlorophyll × precipitation)
  - Ocean current magnitude and wind stress calculations

### Predictor Variables

**Marine Variables**:
- Chlorophyll-a Concentration (CHL)
- Sea Surface Temperature (thetao)
- Sea Surface Salinity (so)
- Mixed Layer Thickness (mlotst)
- Ocean Currents (uo, vo)
- Nitrate, Phosphate, Oxygen levels

**Atmospheric Variables**:
- Precipitation (precip_mm_day)
- Wind Speed and Direction (wind_speed_ms, wind_u_ms, wind_v_ms)

**Terrestrial Variables**:
- NDVI (Normalized Difference Vegetation Index)
- Land use indicators

### Enhanced Risk Levels
- 🟢 **Green: Very Low Risk** (<20% probability)
- 🟡 **Yellow: Low Risk** (20-40% probability)
- 🟠 **Orange: Moderate Risk** (40-70% probability)
- 🔴 **Red: High Risk** (>70% probability)

---

## 🗂️ Repository Layout

```
haribon_system/
├── backend/                    # FastAPI application
│   ├── app/
│   │   ├── api/               # API endpoints (forecast, summary)
│   │   ├── core/              # Configuration and schemas
│   │   ├── models/            # SQLAlchemy database models
│   │   ├── scripts/           # Data processing scripts
│   │   └── services/          # Business logic services
│   ├── main.py               # FastAPI entry point
│   └── requirements.txt      # Python dependencies
├── data/
│   ├── locations.json        # Geographic coordinates
│   ├── historical/           # Training data archives
│   └── processed/            # Generated forecast JSONs
├── ml_xgboost/               # ML model and training
│   ├── training_script.py    # Model training pipeline
│   ├── inference_script.py   # Prediction logic
│   └── [model artifacts]     # Trained models and scalers
└── frontend/                 # React dashboard (to be created)
```

## 🗄️ Database Schema

The system uses PostgreSQL with the following tables:

### Core Tables
- **`daily_forecasts`**: Stores complete forecast data as JSON payloads
- **`location`**: Master list of monitored locations
- **`historical_data`**: Historical environmental data and red tide occurrences
- **`prediction_logs`**: Individual prediction records with environmental parameters

### Table Relationships
```
location (1) ──── (many) historical_data
location (1) ──── (many) prediction_logs
```

### Key Features
- **Automatic Logging**: Predictions are automatically logged to `prediction_logs` during daily updates
- **Historical Analysis**: `historical_data` enables trend analysis and model validation
- **Data Integrity**: Foreign key constraints ensure referential integrity
- **JSON Storage**: `daily_forecasts` preserves complete forecast context

---

## ▶️ Setup and Run

### Prerequisites
- Python 3.10+
- Node.js 18+ (for frontend)
- PostgreSQL 15+ (for data persistence)
- Git

### Database Setup (Optional but Recommended)

1. **Install PostgreSQL**:
   - Download from: https://www.postgresql.org/download/windows/
   - Run the installer and set password for postgres user (remember this password)
   - Keep default port (5432)

2. **Configure Database Connection**:
   ```bash
   cd haribon_system/backend
   # Edit .env file and update DATABASE_URL
   # DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/haribon
   ```

3. **Create Database and Tables**:
   ```bash
   python -m app.scripts.setup_database
   ```

4. **Populate Historical Data (Optional)**:
   ```bash
   python -m app.scripts.populate_historical_data
   ```

### 1) Backend Setup

```bash
cd haribon_system/backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2) Train the ML Model

```bash
cd ../ml_xgboost
python training_script.py
```

### 3) Generate Initial Forecast Data

```bash
cd ../backend
python -m app.scripts.daily_updater
```

### 4) Run the API

```bash
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Visit http://127.0.0.1:8000/docs for API documentation.

### 5) Frontend (Coming Soon)

```bash
cd ../frontend/haribon
npm install
npm run dev
```

---

## 📊 API Endpoints

### Forecast Endpoints
- `GET /api/forecast/today` - Full forecast data
- `GET /api/forecast/today/simple` - Frontend-friendly format
- `GET /api/forecast/locations` - Location summaries
- `GET /api/forecast/location/{name}` - Specific location details
- `GET /api/forecast/latest` - Most recent forecast
- `GET /api/forecast/predict/{location}` - Live prediction
- `POST /api/forecast/update` - Trigger forecast update

### Summary Endpoints
- `GET /api/summary/risk-summary` - Risk distribution overview
- `GET /api/summary/environmental-overview` - Environmental conditions

---

## 🔧 Configuration

Key settings in `backend/app/core/config.py`:
- `TRAINING_DATA_PATH`: Path to final compiled dataset
- `ML_DIR`: ML model artifacts directory
- `PROCESSED_DATA_DIR`: Forecast output directory

---

## 📈 Model Performance

The enhanced XGBoost model includes:
- **Feature Engineering**: 100+ engineered features from 15 base variables
- **Cross-Validation**: Robust evaluation with stratified sampling
- **Feature Importance**: Analysis of key environmental predictors
- **Real-time Inference**: Optimized for low-latency predictions

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Train and validate model improvements
4. Submit a pull request

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙏 Acknowledgments

- Western Visayas fishing communities
- Philippine Bureau of Fisheries and Aquatic Resources (BFAR)
- Copernicus Marine Environment Monitoring Service
- NASA Earth Science Data Systems
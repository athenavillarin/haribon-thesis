/**
 * Mock data for frontend development and offline previews.
 * Reconstructed from actual validated forecast and historical datasets.
 */

export const MOCK_LATEST_FORECAST = {
  "metadata": {
    "last_updated": "2026-10-11T04:03:49.268531+08:00",
    "system_version": "v2.2 (ensemble)",
    "total_locations": 9,
    "forecast_date": "2026-10-11"
  },
  "locations": [
    {
      "id": "cancabato_bay",
      "name": "Cancabato Bay",
      "coordinates": {
        "lat": 11.2249,
        "lng": 125.0131
      },
      "risk_level": "Very Low Risk",
      "risk_color": "green",
      "confidence": "78.0%",
      "current_status": {
        "risk_level": "Very Low Risk",
        "risk_color": "green",
        "confidence": "78.0%",
        "safe_to_harvest": true
      },
      "today_forecast": {
        "probability": "Very Low",
        "recommendations": [
          "Conditions are favorable.",
          "Shellfish harvesting is permitted.",
          "Continue regular monitoring."
        ],
        "contributing_factors": {
          "chl-a": 0.371,
          "sst": 30.87,
          "salinity": 33.86,
          "rainfall": 0.3
        }
      },
      "five_day_outlook": [
        {
          "day": "Today",
          "date": "2026-10-11",
          "label": "Today",
          "risk_level": "Very Low Risk",
          "risk_color": "green",
          "confidence": "78.0%",
          "probability": "Very Low"
        },
        {
          "day": 1,
          "date": "2026-10-12",
          "label": "Mon",
          "risk_level": "Very Low Risk",
          "risk_color": "green",
          "confidence": "74.1%",
          "probability": "Very Low"
        },
        {
          "day": 2,
          "date": "2026-10-13",
          "label": "Tue",
          "risk_level": "Very Low Risk",
          "risk_color": "green",
          "confidence": "70.4%",
          "probability": "Very Low"
        },
        {
          "day": 3,
          "date": "2026-10-14",
          "label": "Wed",
          "risk_level": "Very Low Risk",
          "risk_color": "green",
          "confidence": "66.9%",
          "probability": "Very Low"
        },
        {
          "day": 4,
          "date": "2026-10-15",
          "label": "Thu",
          "risk_level": "Very Low Risk",
          "risk_color": "green",
          "confidence": "63.5%",
          "probability": "Very Low"
        },
        {
          "day": 5,
          "date": "2026-10-16",
          "label": "Fri",
          "risk_level": "Very Low Risk",
          "risk_color": "green",
          "confidence": "60.3%",
          "probability": "Very Low"
        },
        {
          "day": 6,
          "date": "2026-10-17",
          "label": "Sat",
          "risk_level": "Very Low Risk",
          "risk_color": "green",
          "confidence": "57.3%",
          "probability": "Very Low"
        }
      ],
      "data_quality": {
        "score": 0.91,
        "confidence_level": "High",
        "warnings": []
      },
      "environmental_data": {
        "Chlorophyll-a": "0.37 mg/m3",
        "Temperature": "30.87 °C",
        "Salinity (PSU)": "33.86 PSU",
        "MLD (m)": "13.08 m",
        "Precipitation": "0.29 mm",
        "NDVI": "0.2528",
        "U-Wind Speed (m/s)": "0.28 m/s",
        "V-Wind Speed (m/s)": "-0.49 m/s",
        "U-VEL (m/s)": "-0.011 m/s",
        "V-VEL (m/s)": "0.03 m/s"
      }
    },
    {
      "id": "dumanquillas_bay",
      "name": "Dumanquillas Bay",
      "coordinates": {
        "lat": 7.697,
        "lng": 123.018
      },
      "risk_level": "High Risk",
      "risk_color": "red",
      "confidence": "87.2%",
      "current_status": {
        "risk_level": "High Risk",
        "risk_color": "red",
        "confidence": "87.2%",
        "safe_to_harvest": false
      },
      "today_forecast": {
        "probability": "High",
        "recommendations": [
          "HARMFUL ALGAL BLOOM DETECTED",
          "Do not harvest, buy, or eat shellfish from this area.",
          "Wait for official BFAR advisory before resuming activities."
        ],
        "contributing_factors": {
          "chl-a": 0.7,
          "sst": 30.19,
          "salinity": 33.15,
          "rainfall": 1.6
        }
      },
      "five_day_outlook": [
        {
          "day": "Today",
          "date": "2026-10-11",
          "label": "Today",
          "risk_level": "High Risk",
          "risk_color": "red",
          "confidence": "87.2%",
          "probability": "High"
        },
        {
          "day": 1,
          "date": "2026-10-12",
          "label": "Mon",
          "risk_level": "High Risk",
          "risk_color": "red",
          "confidence": "82.8%",
          "probability": "High"
        },
        {
          "day": 2,
          "date": "2026-10-13",
          "label": "Tue",
          "risk_level": "High Risk",
          "risk_color": "red",
          "confidence": "78.7%",
          "probability": "High"
        },
        {
          "day": 3,
          "date": "2026-10-14",
          "label": "Wed",
          "risk_level": "High Risk",
          "risk_color": "red",
          "confidence": "74.7%",
          "probability": "High"
        },
        {
          "day": 4,
          "date": "2026-10-15",
          "label": "Thu",
          "risk_level": "Moderate Risk",
          "risk_color": "orange",
          "confidence": "71.0%",
          "probability": "Moderate"
        },
        {
          "day": 5,
          "date": "2026-10-16",
          "label": "Fri",
          "risk_level": "Moderate Risk",
          "risk_color": "orange",
          "confidence": "67.5%",
          "probability": "Moderate"
        },
        {
          "day": 6,
          "date": "2026-10-17",
          "label": "Sat",
          "risk_level": "Moderate Risk",
          "risk_color": "orange",
          "confidence": "64.1%",
          "probability": "Moderate"
        }
      ],
      "data_quality": {
        "score": 1,
        "confidence_level": "High",
        "warnings": []
      },
      "environmental_data": {
        "Chlorophyll-a": "0.7 mg/m3",
        "Temperature": "30.19 °C",
        "Salinity (PSU)": "33.15 PSU",
        "MLD (m)": "11.14 m",
        "Precipitation": "1.59 mm",
        "NDVI": "0.7828",
        "U-Wind Speed (m/s)": "0.3 m/s",
        "V-Wind Speed (m/s)": "0.4 m/s",
        "U-VEL (m/s)": "-0.009 m/s",
        "V-VEL (m/s)": "0.053 m/s"
      }
    },
    {
      "id": "gigantes_islands",
      "name": "Gigantes Islands",
      "coordinates": {
        "lat": 11.5975,
        "lng": 123.3364
      },
      "risk_level": "Very Low Risk",
      "risk_color": "green",
      "confidence": "76.9%",
      "current_status": {
        "risk_level": "Very Low Risk",
        "risk_color": "green",
        "confidence": "76.9%",
        "safe_to_harvest": true
      },
      "today_forecast": {
        "probability": "Very Low",
        "recommendations": [
          "Conditions are favorable.",
          "Shellfish harvesting is permitted.",
          "Continue regular monitoring."
        ],
        "contributing_factors": {
          "chl-a": 0.619,
          "sst": 30.7,
          "salinity": 33.58,
          "rainfall": 0.4
        }
      },
      "five_day_outlook": [
        {
          "day": "Today",
          "date": "2026-10-11",
          "label": "Today",
          "risk_level": "Very Low Risk",
          "risk_color": "green",
          "confidence": "76.9%",
          "probability": "Very Low"
        },
        {
          "day": 1,
          "date": "2026-10-12",
          "label": "Mon",
          "risk_level": "Very Low Risk",
          "risk_color": "green",
          "confidence": "73.1%",
          "probability": "Very Low"
        },
        {
          "day": 2,
          "date": "2026-10-13",
          "label": "Tue",
          "risk_level": "Very Low Risk",
          "risk_color": "green",
          "confidence": "69.4%",
          "probability": "Very Low"
        },
        {
          "day": 3,
          "date": "2026-10-14",
          "label": "Wed",
          "risk_level": "Very Low Risk",
          "risk_color": "green",
          "confidence": "65.9%",
          "probability": "Very Low"
        },
        {
          "day": 4,
          "date": "2026-10-15",
          "label": "Thu",
          "risk_level": "Very Low Risk",
          "risk_color": "green",
          "confidence": "62.7%",
          "probability": "Very Low"
        },
        {
          "day": 5,
          "date": "2026-10-16",
          "label": "Fri",
          "risk_level": "Very Low Risk",
          "risk_color": "green",
          "confidence": "59.5%",
          "probability": "Very Low"
        },
        {
          "day": 6,
          "date": "2026-10-17",
          "label": "Sat",
          "risk_level": "Very Low Risk",
          "risk_color": "green",
          "confidence": "56.5%",
          "probability": "Very Low"
        }
      ],
      "data_quality": {
        "score": 1,
        "confidence_level": "High",
        "warnings": []
      },
      "environmental_data": {
        "Chlorophyll-a": "0.62 mg/m3",
        "Temperature": "30.7 °C",
        "Salinity (PSU)": "33.58 PSU",
        "MLD (m)": "11.89 m",
        "Precipitation": "0.38 mm",
        "NDVI": "-0.4736",
        "U-Wind Speed (m/s)": "0.04 m/s",
        "V-Wind Speed (m/s)": "-1.78 m/s",
        "U-VEL (m/s)": "0.031 m/s",
        "V-VEL (m/s)": "0.065 m/s"
      }
    },
    {
      "id": "matarinao_bay",
      "name": "Matarinao Bay",
      "coordinates": {
        "lat": 11.23,
        "lng": 125.55
      },
      "risk_level": "High Risk",
      "risk_color": "red",
      "confidence": "73.2%",
      "current_status": {
        "risk_level": "High Risk",
        "risk_color": "red",
        "confidence": "73.2%",
        "safe_to_harvest": false
      },
      "today_forecast": {
        "probability": "High",
        "recommendations": [
          "HARMFUL ALGAL BLOOM DETECTED",
          "Do not harvest, buy, or eat shellfish from this area.",
          "Wait for official BFAR advisory before resuming activities."
        ],
        "contributing_factors": {
          "chl-a": 0.198,
          "sst": 30.84,
          "salinity": 33.42,
          "rainfall": 0.5
        }
      },
      "five_day_outlook": [
        {
          "day": "Today",
          "date": "2026-10-11",
          "label": "Today",
          "risk_level": "High Risk",
          "risk_color": "red",
          "confidence": "73.2%",
          "probability": "High"
        },
        {
          "day": 1,
          "date": "2026-10-12",
          "label": "Mon",
          "risk_level": "High Risk",
          "risk_color": "red",
          "confidence": "69.5%",
          "probability": "High"
        },
        {
          "day": 2,
          "date": "2026-10-13",
          "label": "Tue",
          "risk_level": "Moderate Risk",
          "risk_color": "orange",
          "confidence": "66.0%",
          "probability": "Moderate"
        },
        {
          "day": 3,
          "date": "2026-10-14",
          "label": "Wed",
          "risk_level": "Moderate Risk",
          "risk_color": "orange",
          "confidence": "62.7%",
          "probability": "Moderate"
        },
        {
          "day": 4,
          "date": "2026-10-15",
          "label": "Thu",
          "risk_level": "Moderate Risk",
          "risk_color": "orange",
          "confidence": "59.6%",
          "probability": "Moderate"
        },
        {
          "day": 5,
          "date": "2026-10-16",
          "label": "Fri",
          "risk_level": "Low Risk",
          "risk_color": "yellow",
          "confidence": "56.6%",
          "probability": "Low"
        },
        {
          "day": 6,
          "date": "2026-10-17",
          "label": "Sat",
          "risk_level": "Low Risk",
          "risk_color": "yellow",
          "confidence": "53.8%",
          "probability": "Low"
        }
      ],
      "data_quality": {
        "score": 1,
        "confidence_level": "High",
        "warnings": []
      },
      "environmental_data": {
        "Chlorophyll-a": "0.2 mg/m3",
        "Temperature": "30.84 °C",
        "Salinity (PSU)": "33.42 PSU",
        "MLD (m)": "12.57 m",
        "Precipitation": "0.46 mm",
        "NDVI": "0.6535",
        "U-Wind Speed (m/s)": "0.43 m/s",
        "V-Wind Speed (m/s)": "-1.32 m/s",
        "U-VEL (m/s)": "0.04 m/s",
        "V-VEL (m/s)": "-0.118 m/s"
      }
    },
    {
      "id": "milagros_masbate",
      "name": "Milagros (Masbate)",
      "coordinates": {
        "lat": 12.2182,
        "lng": 123.5094
      },
      "risk_level": "Low Risk",
      "risk_color": "yellow",
      "confidence": "60.2%",
      "current_status": {
        "risk_level": "Low Risk",
        "risk_color": "yellow",
        "confidence": "60.2%",
        "safe_to_harvest": true
      },
      "today_forecast": {
        "probability": "Low",
        "recommendations": [
          "Conditions are favorable.",
          "Shellfish harvesting is permitted.",
          "Continue regular monitoring."
        ],
        "contributing_factors": {
          "chl-a": 0.572,
          "sst": 30.66,
          "salinity": 33.88,
          "rainfall": 0.5
        }
      },
      "five_day_outlook": [
        {
          "day": "Today",
          "date": "2026-10-11",
          "label": "Today",
          "risk_level": "Low Risk",
          "risk_color": "yellow",
          "confidence": "60.2%",
          "probability": "Low"
        },
        {
          "day": 1,
          "date": "2026-10-12",
          "label": "Mon",
          "risk_level": "Low Risk",
          "risk_color": "yellow",
          "confidence": "57.2%",
          "probability": "Low"
        },
        {
          "day": 2,
          "date": "2026-10-13",
          "label": "Tue",
          "risk_level": "Low Risk",
          "risk_color": "yellow",
          "confidence": "54.3%",
          "probability": "Low"
        },
        {
          "day": 3,
          "date": "2026-10-14",
          "label": "Wed",
          "risk_level": "Very Low Risk",
          "risk_color": "green",
          "confidence": "51.6%",
          "probability": "Very Low"
        },
        {
          "day": 4,
          "date": "2026-10-15",
          "label": "Thu",
          "risk_level": "Very Low Risk",
          "risk_color": "green",
          "confidence": "49.0%",
          "probability": "Very Low"
        },
        {
          "day": 5,
          "date": "2026-10-16",
          "label": "Fri",
          "risk_level": "Very Low Risk",
          "risk_color": "green",
          "confidence": "46.6%",
          "probability": "Very Low"
        },
        {
          "day": 6,
          "date": "2026-10-17",
          "label": "Sat",
          "risk_level": "Very Low Risk",
          "risk_color": "green",
          "confidence": "44.3%",
          "probability": "Very Low"
        }
      ],
      "data_quality": {
        "score": 1,
        "confidence_level": "High",
        "warnings": []
      },
      "environmental_data": {
        "Chlorophyll-a": "0.57 mg/m3",
        "Temperature": "30.66 °C",
        "Salinity (PSU)": "33.88 PSU",
        "MLD (m)": "12.55 m",
        "Precipitation": "0.45 mm",
        "NDVI": "0.6876",
        "U-Wind Speed (m/s)": "-0.51 m/s",
        "V-Wind Speed (m/s)": "-1.12 m/s",
        "U-VEL (m/s)": "-0.066 m/s",
        "V-VEL (m/s)": "0.065 m/s"
      }
    },
    {
      "id": "pilar",
      "name": "Pilar",
      "coordinates": {
        "lat": 11.504,
        "lng": 122.941
      },
      "risk_level": "Very Low Risk",
      "risk_color": "green",
      "confidence": "76.3%",
      "current_status": {
        "risk_level": "Very Low Risk",
        "risk_color": "green",
        "confidence": "76.3%",
        "safe_to_harvest": true
      },
      "today_forecast": {
        "probability": "Very Low",
        "recommendations": [
          "Conditions are favorable.",
          "Shellfish harvesting is permitted.",
          "Continue regular monitoring."
        ],
        "contributing_factors": {
          "chl-a": 0.509,
          "sst": 30.66,
          "salinity": 33.3,
          "rainfall": 0
        }
      },
      "five_day_outlook": [
        {
          "day": "Today",
          "date": "2026-10-11",
          "label": "Today",
          "risk_level": "Very Low Risk",
          "risk_color": "green",
          "confidence": "76.3%",
          "probability": "Very Low"
        },
        {
          "day": 1,
          "date": "2026-10-12",
          "label": "Mon",
          "risk_level": "Very Low Risk",
          "risk_color": "green",
          "confidence": "72.5%",
          "probability": "Very Low"
        },
        {
          "day": 2,
          "date": "2026-10-13",
          "label": "Tue",
          "risk_level": "Very Low Risk",
          "risk_color": "green",
          "confidence": "68.9%",
          "probability": "Very Low"
        },
        {
          "day": 3,
          "date": "2026-10-14",
          "label": "Wed",
          "risk_level": "Very Low Risk",
          "risk_color": "green",
          "confidence": "65.5%",
          "probability": "Very Low"
        },
        {
          "day": 4,
          "date": "2026-10-15",
          "label": "Thu",
          "risk_level": "Very Low Risk",
          "risk_color": "green",
          "confidence": "62.2%",
          "probability": "Very Low"
        },
        {
          "day": 5,
          "date": "2026-10-16",
          "label": "Fri",
          "risk_level": "Very Low Risk",
          "risk_color": "green",
          "confidence": "59.1%",
          "probability": "Very Low"
        },
        {
          "day": 6,
          "date": "2026-10-17",
          "label": "Sat",
          "risk_level": "Very Low Risk",
          "risk_color": "green",
          "confidence": "56.1%",
          "probability": "Very Low"
        }
      ],
      "data_quality": {
        "score": 1,
        "confidence_level": "High",
        "warnings": []
      },
      "environmental_data": {
        "Chlorophyll-a": "0.51 mg/m3",
        "Temperature": "30.66 °C",
        "Salinity (PSU)": "33.3 PSU",
        "MLD (m)": "11.41 m",
        "Precipitation": "0.0 mm",
        "NDVI": "0.198",
        "U-Wind Speed (m/s)": "0.3 m/s",
        "V-Wind Speed (m/s)": "-0.77 m/s",
        "U-VEL (m/s)": "0.047 m/s",
        "V-VEL (m/s)": "0.065 m/s"
      }
    },
    {
      "id": "president_roxas",
      "name": "President Roxas",
      "coordinates": {
        "lat": 11.496,
        "lng": 122.914
      },
      "risk_level": "Very Low Risk",
      "risk_color": "green",
      "confidence": "75.8%",
      "current_status": {
        "risk_level": "Very Low Risk",
        "risk_color": "green",
        "confidence": "75.8%",
        "safe_to_harvest": true
      },
      "today_forecast": {
        "probability": "Very Low",
        "recommendations": [
          "Conditions are favorable.",
          "Shellfish harvesting is permitted.",
          "Continue regular monitoring."
        ],
        "contributing_factors": {
          "chl-a": 0.498,
          "sst": 30.68,
          "salinity": 33.14,
          "rainfall": 0
        }
      },
      "five_day_outlook": [
        {
          "day": "Today",
          "date": "2026-10-11",
          "label": "Today",
          "risk_level": "Very Low Risk",
          "risk_color": "green",
          "confidence": "75.8%",
          "probability": "Very Low"
        },
        {
          "day": 1,
          "date": "2026-10-12",
          "label": "Mon",
          "risk_level": "Very Low Risk",
          "risk_color": "green",
          "confidence": "72.0%",
          "probability": "Very Low"
        },
        {
          "day": 2,
          "date": "2026-10-13",
          "label": "Tue",
          "risk_level": "Very Low Risk",
          "risk_color": "green",
          "confidence": "68.4%",
          "probability": "Very Low"
        },
        {
          "day": 3,
          "date": "2026-10-14",
          "label": "Wed",
          "risk_level": "Very Low Risk",
          "risk_color": "green",
          "confidence": "65.0%",
          "probability": "Very Low"
        },
        {
          "day": 4,
          "date": "2026-10-15",
          "label": "Thu",
          "risk_level": "Very Low Risk",
          "risk_color": "green",
          "confidence": "61.7%",
          "probability": "Very Low"
        },
        {
          "day": 5,
          "date": "2026-10-16",
          "label": "Fri",
          "risk_level": "Very Low Risk",
          "risk_color": "green",
          "confidence": "58.6%",
          "probability": "Very Low"
        },
        {
          "day": 6,
          "date": "2026-10-17",
          "label": "Sat",
          "risk_level": "Very Low Risk",
          "risk_color": "green",
          "confidence": "55.7%",
          "probability": "Very Low"
        }
      ],
      "data_quality": {
        "score": 1,
        "confidence_level": "High",
        "warnings": []
      },
      "environmental_data": {
        "Chlorophyll-a": "0.5 mg/m3",
        "Temperature": "30.68 °C",
        "Salinity (PSU)": "33.14 PSU",
        "MLD (m)": "11.04 m",
        "Precipitation": "0.01 mm",
        "NDVI": "0.2249",
        "U-Wind Speed (m/s)": "0.23 m/s",
        "V-Wind Speed (m/s)": "-0.72 m/s",
        "U-VEL (m/s)": "0.041 m/s",
        "V-VEL (m/s)": "0.065 m/s"
      }
    },
    {
      "id": "roxas_city",
      "name": "Roxas City",
      "coordinates": {
        "lat": 11.5853,
        "lng": 122.7511
      },
      "risk_level": "Very Low Risk",
      "risk_color": "green",
      "confidence": "76.0%",
      "current_status": {
        "risk_level": "Very Low Risk",
        "risk_color": "green",
        "confidence": "76.0%",
        "safe_to_harvest": true
      },
      "today_forecast": {
        "probability": "Very Low",
        "recommendations": [
          "Conditions are favorable.",
          "Shellfish harvesting is permitted.",
          "Continue regular monitoring."
        ],
        "contributing_factors": {
          "chl-a": 0.442,
          "sst": 30.7,
          "salinity": 33.21,
          "rainfall": 0
        }
      },
      "five_day_outlook": [
        {
          "day": "Today",
          "date": "2026-10-11",
          "label": "Today",
          "risk_level": "Very Low Risk",
          "risk_color": "green",
          "confidence": "76.0%",
          "probability": "Very Low"
        },
        {
          "day": 1,
          "date": "2026-10-12",
          "label": "Mon",
          "risk_level": "Very Low Risk",
          "risk_color": "green",
          "confidence": "72.2%",
          "probability": "Very Low"
        },
        {
          "day": 2,
          "date": "2026-10-13",
          "label": "Tue",
          "risk_level": "Very Low Risk",
          "risk_color": "green",
          "confidence": "68.6%",
          "probability": "Very Low"
        },
        {
          "day": 3,
          "date": "2026-10-14",
          "label": "Wed",
          "risk_level": "Very Low Risk",
          "risk_color": "green",
          "confidence": "65.2%",
          "probability": "Very Low"
        },
        {
          "day": 4,
          "date": "2026-10-15",
          "label": "Thu",
          "risk_level": "Very Low Risk",
          "risk_color": "green",
          "confidence": "61.9%",
          "probability": "Very Low"
        },
        {
          "day": 5,
          "date": "2026-10-16",
          "label": "Fri",
          "risk_level": "Very Low Risk",
          "risk_color": "green",
          "confidence": "58.8%",
          "probability": "Very Low"
        },
        {
          "day": 6,
          "date": "2026-10-17",
          "label": "Sat",
          "risk_level": "Very Low Risk",
          "risk_color": "green",
          "confidence": "55.9%",
          "probability": "Very Low"
        }
      ],
      "data_quality": {
        "score": 1,
        "confidence_level": "High",
        "warnings": []
      },
      "environmental_data": {
        "Chlorophyll-a": "0.44 mg/m3",
        "Temperature": "30.7 °C",
        "Salinity (PSU)": "33.21 PSU",
        "MLD (m)": "10.92 m",
        "Precipitation": "0.0 mm",
        "NDVI": "0.7735",
        "U-Wind Speed (m/s)": "0.2 m/s",
        "V-Wind Speed (m/s)": "-0.76 m/s",
        "U-VEL (m/s)": "0.033 m/s",
        "V-VEL (m/s)": "0.068 m/s"
      }
    },
    {
      "id": "sapian_bay",
      "name": "Sapian Bay",
      "coordinates": {
        "lat": 11.4936,
        "lng": 122.6186
      },
      "risk_level": "Very Low Risk",
      "risk_color": "green",
      "confidence": "77.6%",
      "current_status": {
        "risk_level": "Very Low Risk",
        "risk_color": "green",
        "confidence": "77.6%",
        "safe_to_harvest": true
      },
      "today_forecast": {
        "probability": "Very Low",
        "recommendations": [
          "Conditions are favorable.",
          "Shellfish harvesting is permitted.",
          "Continue regular monitoring."
        ],
        "contributing_factors": {
          "chl-a": 0.283,
          "sst": 30.64,
          "salinity": 33.61,
          "rainfall": 0.1
        }
      },
      "five_day_outlook": [
        {
          "day": "Today",
          "date": "2026-10-11",
          "label": "Today",
          "risk_level": "Very Low Risk",
          "risk_color": "green",
          "confidence": "77.6%",
          "probability": "Very Low"
        },
        {
          "day": 1,
          "date": "2026-10-12",
          "label": "Mon",
          "risk_level": "Very Low Risk",
          "risk_color": "green",
          "confidence": "73.7%",
          "probability": "Very Low"
        },
        {
          "day": 2,
          "date": "2026-10-13",
          "label": "Tue",
          "risk_level": "Very Low Risk",
          "risk_color": "green",
          "confidence": "70.1%",
          "probability": "Very Low"
        },
        {
          "day": 3,
          "date": "2026-10-14",
          "label": "Wed",
          "risk_level": "Very Low Risk",
          "risk_color": "green",
          "confidence": "66.6%",
          "probability": "Very Low"
        },
        {
          "day": 4,
          "date": "2026-10-15",
          "label": "Thu",
          "risk_level": "Very Low Risk",
          "risk_color": "green",
          "confidence": "63.2%",
          "probability": "Very Low"
        },
        {
          "day": 5,
          "date": "2026-10-16",
          "label": "Fri",
          "risk_level": "Very Low Risk",
          "risk_color": "green",
          "confidence": "60.1%",
          "probability": "Very Low"
        },
        {
          "day": 6,
          "date": "2026-10-17",
          "label": "Sat",
          "risk_level": "Very Low Risk",
          "risk_color": "green",
          "confidence": "57.1%",
          "probability": "Very Low"
        }
      ],
      "data_quality": {
        "score": 1,
        "confidence_level": "High",
        "warnings": []
      },
      "environmental_data": {
        "Chlorophyll-a": "0.28 mg/m3",
        "Temperature": "30.64 °C",
        "Salinity (PSU)": "33.61 PSU",
        "MLD (m)": "11.48 m",
        "Precipitation": "0.06 mm",
        "NDVI": "0.793",
        "U-Wind Speed (m/s)": "0.18 m/s",
        "V-Wind Speed (m/s)": "-0.75 m/s",
        "U-VEL (m/s)": "0.025 m/s",
        "V-VEL (m/s)": "0.073 m/s"
      }
    }
  ],
  "summary": {
    "risk_distribution": {
      "green": 6,
      "yellow": 1,
      "orange": 0,
      "red": 2
    },
    "average_confidence": 75.7,
    "high_risk_locations": [
      "Dumanquillas Bay",
      "Matarinao Bay"
    ],
    "data_quality_avg": 0.99
  }
};

export const MOCK_HISTORICAL_DATA = {
  "available_range": {
    "start": "2015-01-05",
    "end": "2026-10-01"
  },
  "all": [
    {
      "label": "2015-01",
      "value": 0
    },
    {
      "label": "2015-02",
      "value": 0
    },
    {
      "label": "2015-03",
      "value": 0
    },
    {
      "label": "2015-04",
      "value": 0
    },
    {
      "label": "2015-05",
      "value": 0
    },
    {
      "label": "2015-06",
      "value": 0
    },
    {
      "label": "2015-07",
      "value": 0
    },
    {
      "label": "2015-08",
      "value": 3
    },
    {
      "label": "2015-09",
      "value": 30
    },
    {
      "label": "2015-10",
      "value": 16
    },
    {
      "label": "2015-11",
      "value": 55
    },
    {
      "label": "2015-12",
      "value": 107
    },
    {
      "label": "2016-01",
      "value": 99
    },
    {
      "label": "2016-02",
      "value": 57
    },
    {
      "label": "2016-03",
      "value": 34
    },
    {
      "label": "2016-04",
      "value": 0
    },
    {
      "label": "2016-05",
      "value": 0
    },
    {
      "label": "2016-06",
      "value": 0
    },
    {
      "label": "2016-07",
      "value": 10
    },
    {
      "label": "2016-08",
      "value": 38
    },
    {
      "label": "2016-09",
      "value": 55
    },
    {
      "label": "2016-10",
      "value": 42
    },
    {
      "label": "2016-11",
      "value": 81
    },
    {
      "label": "2016-12",
      "value": 62
    },
    {
      "label": "2017-01",
      "value": 62
    },
    {
      "label": "2017-02",
      "value": 56
    },
    {
      "label": "2017-03",
      "value": 72
    },
    {
      "label": "2017-04",
      "value": 14
    },
    {
      "label": "2017-05",
      "value": 0
    },
    {
      "label": "2017-06",
      "value": 0
    },
    {
      "label": "2017-07",
      "value": 0
    },
    {
      "label": "2017-08",
      "value": 36
    },
    {
      "label": "2017-09",
      "value": 90
    },
    {
      "label": "2017-10",
      "value": 71
    },
    {
      "label": "2017-11",
      "value": 30
    },
    {
      "label": "2017-12",
      "value": 31
    },
    {
      "label": "2018-01",
      "value": 33
    },
    {
      "label": "2018-02",
      "value": 28
    },
    {
      "label": "2018-03",
      "value": 6
    },
    {
      "label": "2018-04",
      "value": 0
    },
    {
      "label": "2018-05",
      "value": 0
    },
    {
      "label": "2018-06",
      "value": 0
    },
    {
      "label": "2018-07",
      "value": 0
    },
    {
      "label": "2018-08",
      "value": 22
    },
    {
      "label": "2018-09",
      "value": 40
    },
    {
      "label": "2018-10",
      "value": 62
    },
    {
      "label": "2018-11",
      "value": 60
    },
    {
      "label": "2018-12",
      "value": 44
    },
    {
      "label": "2019-01",
      "value": 49
    },
    {
      "label": "2019-02",
      "value": 55
    },
    {
      "label": "2019-03",
      "value": 4
    },
    {
      "label": "2019-04",
      "value": 0
    },
    {
      "label": "2019-05",
      "value": 0
    },
    {
      "label": "2019-06",
      "value": 0
    },
    {
      "label": "2019-07",
      "value": 0
    },
    {
      "label": "2019-08",
      "value": 3
    },
    {
      "label": "2019-09",
      "value": 30
    },
    {
      "label": "2019-10",
      "value": 29
    },
    {
      "label": "2019-11",
      "value": 16
    },
    {
      "label": "2019-12",
      "value": 50
    },
    {
      "label": "2020-01",
      "value": 52
    },
    {
      "label": "2020-02",
      "value": 29
    },
    {
      "label": "2020-03",
      "value": 12
    },
    {
      "label": "2020-04",
      "value": 0
    },
    {
      "label": "2020-05",
      "value": 0
    },
    {
      "label": "2020-06",
      "value": 0
    },
    {
      "label": "2020-07",
      "value": 12
    },
    {
      "label": "2020-08",
      "value": 31
    },
    {
      "label": "2020-09",
      "value": 64
    },
    {
      "label": "2020-10",
      "value": 93
    },
    {
      "label": "2020-11",
      "value": 90
    },
    {
      "label": "2020-12",
      "value": 12
    },
    {
      "label": "2021-01",
      "value": 40
    },
    {
      "label": "2021-02",
      "value": 56
    },
    {
      "label": "2021-03",
      "value": 40
    },
    {
      "label": "2021-04",
      "value": 19
    },
    {
      "label": "2021-05",
      "value": 24
    },
    {
      "label": "2021-06",
      "value": 36
    },
    {
      "label": "2021-07",
      "value": 93
    },
    {
      "label": "2021-08",
      "value": 93
    },
    {
      "label": "2021-09",
      "value": 62
    },
    {
      "label": "2021-10",
      "value": 42
    },
    {
      "label": "2021-11",
      "value": 81
    },
    {
      "label": "2021-12",
      "value": 68
    },
    {
      "label": "2022-01",
      "value": 124
    },
    {
      "label": "2022-02",
      "value": 68
    },
    {
      "label": "2022-03",
      "value": 62
    },
    {
      "label": "2022-04",
      "value": 60
    },
    {
      "label": "2022-05",
      "value": 62
    },
    {
      "label": "2022-06",
      "value": 60
    },
    {
      "label": "2022-07",
      "value": 52
    },
    {
      "label": "2022-08",
      "value": 31
    },
    {
      "label": "2022-09",
      "value": 63
    },
    {
      "label": "2022-10",
      "value": 192
    },
    {
      "label": "2022-11",
      "value": 180
    },
    {
      "label": "2022-12",
      "value": 186
    },
    {
      "label": "2023-01",
      "value": 149
    },
    {
      "label": "2023-02",
      "value": 118
    },
    {
      "label": "2023-03",
      "value": 62
    },
    {
      "label": "2023-04",
      "value": 49
    },
    {
      "label": "2023-05",
      "value": 31
    },
    {
      "label": "2023-06",
      "value": 30
    },
    {
      "label": "2023-07",
      "value": 31
    },
    {
      "label": "2023-08",
      "value": 61
    },
    {
      "label": "2023-09",
      "value": 180
    },
    {
      "label": "2023-10",
      "value": 186
    },
    {
      "label": "2023-11",
      "value": 180
    },
    {
      "label": "2023-12",
      "value": 91
    },
    {
      "label": "2024-01",
      "value": 45
    },
    {
      "label": "2024-02",
      "value": 87
    },
    {
      "label": "2024-03",
      "value": 93
    },
    {
      "label": "2024-04",
      "value": 90
    },
    {
      "label": "2024-05",
      "value": 64
    },
    {
      "label": "2024-06",
      "value": 39
    },
    {
      "label": "2024-07",
      "value": 33
    },
    {
      "label": "2024-08",
      "value": 91
    },
    {
      "label": "2024-09",
      "value": 60
    },
    {
      "label": "2024-10",
      "value": 46
    },
    {
      "label": "2024-11",
      "value": 30
    },
    {
      "label": "2024-12",
      "value": 54
    },
    {
      "label": "2025-01",
      "value": 62
    },
    {
      "label": "2025-02",
      "value": 78
    },
    {
      "label": "2025-03",
      "value": 81
    },
    {
      "label": "2025-04",
      "value": 60
    },
    {
      "label": "2025-05",
      "value": 62
    },
    {
      "label": "2025-06",
      "value": 38
    },
    {
      "label": "2025-07",
      "value": 49
    },
    {
      "label": "2025-08",
      "value": 62
    },
    {
      "label": "2025-09",
      "value": 60
    },
    {
      "label": "2025-10",
      "value": 62
    },
    {
      "label": "2025-11",
      "value": 60
    },
    {
      "label": "2025-12",
      "value": 62
    },
    {
      "label": "2026-01",
      "value": 56
    },
    {
      "label": "2026-02",
      "value": 50
    },
    {
      "label": "2026-03",
      "value": 56
    },
    {
      "label": "2026-04",
      "value": 54
    },
    {
      "label": "2026-05",
      "value": 56
    },
    {
      "label": "2026-06",
      "value": 54
    },
    {
      "label": "2026-07",
      "value": 62
    },
    {
      "label": "2026-08",
      "value": 62
    },
    {
      "label": "2026-09",
      "value": 60
    },
    {
      "label": "2026-10",
      "value": 2
    }
  ],
  "byLocation": {
    "cancabato_bay": [
      {
        "label": "2016-01",
        "value": 0
      },
      {
        "label": "2016-02",
        "value": 0
      },
      {
        "label": "2016-03",
        "value": 0
      },
      {
        "label": "2016-04",
        "value": 0
      },
      {
        "label": "2016-05",
        "value": 0
      },
      {
        "label": "2016-06",
        "value": 0
      },
      {
        "label": "2016-07",
        "value": 0
      },
      {
        "label": "2016-08",
        "value": 7
      },
      {
        "label": "2016-09",
        "value": 25
      },
      {
        "label": "2016-10",
        "value": 0
      },
      {
        "label": "2016-11",
        "value": 0
      },
      {
        "label": "2016-12",
        "value": 0
      },
      {
        "label": "2017-01",
        "value": 0
      },
      {
        "label": "2017-02",
        "value": 0
      },
      {
        "label": "2017-03",
        "value": 0
      },
      {
        "label": "2017-04",
        "value": 0
      },
      {
        "label": "2017-05",
        "value": 0
      },
      {
        "label": "2017-06",
        "value": 0
      },
      {
        "label": "2017-07",
        "value": 0
      },
      {
        "label": "2017-08",
        "value": 0
      },
      {
        "label": "2017-09",
        "value": 0
      },
      {
        "label": "2017-10",
        "value": 0
      },
      {
        "label": "2017-11",
        "value": 0
      },
      {
        "label": "2017-12",
        "value": 0
      },
      {
        "label": "2018-01",
        "value": 0
      },
      {
        "label": "2018-02",
        "value": 0
      },
      {
        "label": "2018-03",
        "value": 0
      },
      {
        "label": "2018-04",
        "value": 0
      },
      {
        "label": "2018-05",
        "value": 0
      },
      {
        "label": "2018-06",
        "value": 0
      },
      {
        "label": "2018-07",
        "value": 0
      },
      {
        "label": "2018-08",
        "value": 0
      },
      {
        "label": "2018-09",
        "value": 0
      },
      {
        "label": "2018-10",
        "value": 0
      },
      {
        "label": "2018-11",
        "value": 0
      },
      {
        "label": "2018-12",
        "value": 0
      },
      {
        "label": "2019-01",
        "value": 18
      },
      {
        "label": "2019-02",
        "value": 28
      },
      {
        "label": "2019-03",
        "value": 4
      },
      {
        "label": "2019-04",
        "value": 0
      },
      {
        "label": "2019-05",
        "value": 0
      },
      {
        "label": "2019-06",
        "value": 0
      },
      {
        "label": "2019-07",
        "value": 0
      },
      {
        "label": "2019-08",
        "value": 3
      },
      {
        "label": "2019-09",
        "value": 30
      },
      {
        "label": "2019-10",
        "value": 29
      },
      {
        "label": "2019-11",
        "value": 16
      },
      {
        "label": "2019-12",
        "value": 31
      },
      {
        "label": "2020-01",
        "value": 31
      },
      {
        "label": "2020-02",
        "value": 29
      },
      {
        "label": "2020-03",
        "value": 12
      },
      {
        "label": "2020-04",
        "value": 0
      },
      {
        "label": "2020-05",
        "value": 0
      },
      {
        "label": "2020-06",
        "value": 0
      },
      {
        "label": "2020-07",
        "value": 12
      },
      {
        "label": "2020-08",
        "value": 31
      },
      {
        "label": "2020-09",
        "value": 30
      },
      {
        "label": "2020-10",
        "value": 31
      },
      {
        "label": "2020-11",
        "value": 30
      },
      {
        "label": "2020-12",
        "value": 4
      },
      {
        "label": "2021-05",
        "value": 24
      },
      {
        "label": "2021-06",
        "value": 24
      },
      {
        "label": "2021-07",
        "value": 0
      },
      {
        "label": "2021-08",
        "value": 0
      },
      {
        "label": "2021-09",
        "value": 0
      },
      {
        "label": "2021-10",
        "value": 0
      },
      {
        "label": "2021-11",
        "value": 21
      },
      {
        "label": "2021-12",
        "value": 3
      },
      {
        "label": "2022-01",
        "value": 31
      },
      {
        "label": "2022-02",
        "value": 6
      },
      {
        "label": "2022-03",
        "value": 0
      },
      {
        "label": "2022-04",
        "value": 0
      },
      {
        "label": "2022-05",
        "value": 0
      },
      {
        "label": "2022-06",
        "value": 0
      },
      {
        "label": "2022-07",
        "value": 0
      },
      {
        "label": "2022-08",
        "value": 0
      },
      {
        "label": "2022-09",
        "value": 0
      },
      {
        "label": "2022-10",
        "value": 0
      },
      {
        "label": "2022-11",
        "value": 0
      },
      {
        "label": "2022-12",
        "value": 0
      },
      {
        "label": "2023-01",
        "value": 7
      },
      {
        "label": "2023-02",
        "value": 20
      },
      {
        "label": "2023-03",
        "value": 0
      },
      {
        "label": "2023-04",
        "value": 0
      },
      {
        "label": "2023-05",
        "value": 0
      },
      {
        "label": "2023-06",
        "value": 0
      },
      {
        "label": "2023-07",
        "value": 0
      },
      {
        "label": "2023-08",
        "value": 0
      },
      {
        "label": "2023-09",
        "value": 0
      },
      {
        "label": "2023-10",
        "value": 0
      },
      {
        "label": "2023-11",
        "value": 0
      },
      {
        "label": "2023-12",
        "value": 0
      },
      {
        "label": "2024-01",
        "value": 0
      },
      {
        "label": "2024-02",
        "value": 0
      },
      {
        "label": "2024-03",
        "value": 0
      },
      {
        "label": "2024-04",
        "value": 0
      },
      {
        "label": "2024-05",
        "value": 0
      },
      {
        "label": "2024-06",
        "value": 0
      },
      {
        "label": "2024-07",
        "value": 1
      },
      {
        "label": "2024-08",
        "value": 29
      },
      {
        "label": "2024-09",
        "value": 0
      },
      {
        "label": "2024-10",
        "value": 0
      },
      {
        "label": "2024-11",
        "value": 0
      },
      {
        "label": "2024-12",
        "value": 0
      },
      {
        "label": "2025-01",
        "value": 0
      },
      {
        "label": "2025-02",
        "value": 0
      },
      {
        "label": "2025-03",
        "value": 0
      },
      {
        "label": "2025-04",
        "value": 0
      },
      {
        "label": "2025-05",
        "value": 0
      },
      {
        "label": "2025-06",
        "value": 0
      },
      {
        "label": "2025-07",
        "value": 0
      },
      {
        "label": "2025-08",
        "value": 0
      },
      {
        "label": "2025-09",
        "value": 0
      },
      {
        "label": "2025-10",
        "value": 0
      },
      {
        "label": "2025-11",
        "value": 0
      },
      {
        "label": "2025-12",
        "value": 0
      },
      {
        "label": "2026-01",
        "value": 0
      },
      {
        "label": "2026-02",
        "value": 0
      },
      {
        "label": "2026-03",
        "value": 0
      },
      {
        "label": "2026-04",
        "value": 0
      },
      {
        "label": "2026-05",
        "value": 0
      },
      {
        "label": "2026-06",
        "value": 0
      },
      {
        "label": "2026-07",
        "value": 0
      },
      {
        "label": "2026-08",
        "value": 0
      },
      {
        "label": "2026-09",
        "value": 0
      },
      {
        "label": "2026-10",
        "value": 0
      }
    ],
    "dumanquillas_bay": [
      {
        "label": "2015-01",
        "value": 0
      },
      {
        "label": "2015-02",
        "value": 0
      },
      {
        "label": "2015-03",
        "value": 0
      },
      {
        "label": "2015-04",
        "value": 0
      },
      {
        "label": "2015-05",
        "value": 0
      },
      {
        "label": "2015-06",
        "value": 0
      },
      {
        "label": "2015-07",
        "value": 0
      },
      {
        "label": "2015-08",
        "value": 0
      },
      {
        "label": "2015-09",
        "value": 0
      },
      {
        "label": "2015-10",
        "value": 0
      },
      {
        "label": "2015-11",
        "value": 0
      },
      {
        "label": "2015-12",
        "value": 0
      },
      {
        "label": "2016-01",
        "value": 0
      },
      {
        "label": "2016-02",
        "value": 0
      },
      {
        "label": "2016-03",
        "value": 0
      },
      {
        "label": "2016-04",
        "value": 0
      },
      {
        "label": "2016-05",
        "value": 0
      },
      {
        "label": "2016-06",
        "value": 0
      },
      {
        "label": "2016-07",
        "value": 0
      },
      {
        "label": "2016-08",
        "value": 0
      },
      {
        "label": "2016-09",
        "value": 0
      },
      {
        "label": "2016-10",
        "value": 0
      },
      {
        "label": "2016-11",
        "value": 0
      },
      {
        "label": "2016-12",
        "value": 0
      },
      {
        "label": "2017-01",
        "value": 0
      },
      {
        "label": "2017-02",
        "value": 0
      },
      {
        "label": "2017-03",
        "value": 0
      },
      {
        "label": "2017-04",
        "value": 0
      },
      {
        "label": "2017-05",
        "value": 0
      },
      {
        "label": "2017-06",
        "value": 0
      },
      {
        "label": "2017-07",
        "value": 0
      },
      {
        "label": "2017-08",
        "value": 0
      },
      {
        "label": "2017-09",
        "value": 0
      },
      {
        "label": "2017-10",
        "value": 0
      },
      {
        "label": "2017-11",
        "value": 0
      },
      {
        "label": "2017-12",
        "value": 0
      },
      {
        "label": "2018-01",
        "value": 0
      },
      {
        "label": "2018-02",
        "value": 0
      },
      {
        "label": "2018-03",
        "value": 0
      },
      {
        "label": "2018-04",
        "value": 0
      },
      {
        "label": "2018-05",
        "value": 0
      },
      {
        "label": "2018-06",
        "value": 0
      },
      {
        "label": "2018-07",
        "value": 0
      },
      {
        "label": "2018-08",
        "value": 0
      },
      {
        "label": "2018-09",
        "value": 0
      },
      {
        "label": "2018-10",
        "value": 0
      },
      {
        "label": "2018-11",
        "value": 0
      },
      {
        "label": "2018-12",
        "value": 0
      },
      {
        "label": "2019-01",
        "value": 0
      },
      {
        "label": "2019-02",
        "value": 0
      },
      {
        "label": "2019-03",
        "value": 0
      },
      {
        "label": "2019-04",
        "value": 0
      },
      {
        "label": "2019-05",
        "value": 0
      },
      {
        "label": "2019-06",
        "value": 0
      },
      {
        "label": "2019-07",
        "value": 0
      },
      {
        "label": "2019-08",
        "value": 0
      },
      {
        "label": "2019-09",
        "value": 0
      },
      {
        "label": "2019-10",
        "value": 0
      },
      {
        "label": "2019-11",
        "value": 0
      },
      {
        "label": "2019-12",
        "value": 0
      },
      {
        "label": "2020-01",
        "value": 0
      },
      {
        "label": "2020-02",
        "value": 0
      },
      {
        "label": "2020-03",
        "value": 0
      },
      {
        "label": "2020-04",
        "value": 0
      },
      {
        "label": "2020-05",
        "value": 0
      },
      {
        "label": "2020-06",
        "value": 0
      },
      {
        "label": "2020-07",
        "value": 0
      },
      {
        "label": "2020-08",
        "value": 0
      },
      {
        "label": "2020-09",
        "value": 0
      },
      {
        "label": "2020-10",
        "value": 0
      },
      {
        "label": "2020-11",
        "value": 0
      },
      {
        "label": "2020-12",
        "value": 0
      },
      {
        "label": "2021-01",
        "value": 20
      },
      {
        "label": "2021-02",
        "value": 28
      },
      {
        "label": "2021-03",
        "value": 31
      },
      {
        "label": "2021-04",
        "value": 19
      },
      {
        "label": "2021-05",
        "value": 0
      },
      {
        "label": "2021-06",
        "value": 6
      },
      {
        "label": "2021-07",
        "value": 31
      },
      {
        "label": "2021-08",
        "value": 31
      },
      {
        "label": "2021-09",
        "value": 30
      },
      {
        "label": "2021-10",
        "value": 31
      },
      {
        "label": "2021-11",
        "value": 30
      },
      {
        "label": "2021-12",
        "value": 31
      },
      {
        "label": "2022-01",
        "value": 31
      },
      {
        "label": "2022-02",
        "value": 28
      },
      {
        "label": "2022-03",
        "value": 31
      },
      {
        "label": "2022-04",
        "value": 30
      },
      {
        "label": "2022-05",
        "value": 31
      },
      {
        "label": "2022-06",
        "value": 30
      },
      {
        "label": "2022-07",
        "value": 31
      },
      {
        "label": "2022-08",
        "value": 31
      },
      {
        "label": "2022-09",
        "value": 30
      },
      {
        "label": "2022-10",
        "value": 31
      },
      {
        "label": "2022-11",
        "value": 30
      },
      {
        "label": "2022-12",
        "value": 31
      },
      {
        "label": "2023-01",
        "value": 31
      },
      {
        "label": "2023-02",
        "value": 28
      },
      {
        "label": "2023-03",
        "value": 31
      },
      {
        "label": "2023-04",
        "value": 30
      },
      {
        "label": "2023-05",
        "value": 31
      },
      {
        "label": "2023-06",
        "value": 30
      },
      {
        "label": "2023-07",
        "value": 31
      },
      {
        "label": "2023-08",
        "value": 31
      },
      {
        "label": "2023-09",
        "value": 30
      },
      {
        "label": "2023-10",
        "value": 31
      },
      {
        "label": "2023-11",
        "value": 30
      },
      {
        "label": "2023-12",
        "value": 31
      },
      {
        "label": "2024-01",
        "value": 31
      },
      {
        "label": "2024-02",
        "value": 29
      },
      {
        "label": "2024-03",
        "value": 31
      },
      {
        "label": "2024-04",
        "value": 30
      },
      {
        "label": "2024-05",
        "value": 31
      },
      {
        "label": "2024-06",
        "value": 30
      },
      {
        "label": "2024-07",
        "value": 31
      },
      {
        "label": "2024-08",
        "value": 31
      },
      {
        "label": "2024-09",
        "value": 30
      },
      {
        "label": "2024-10",
        "value": 31
      },
      {
        "label": "2024-11",
        "value": 30
      },
      {
        "label": "2024-12",
        "value": 31
      },
      {
        "label": "2025-01",
        "value": 31
      },
      {
        "label": "2025-02",
        "value": 28
      },
      {
        "label": "2025-03",
        "value": 31
      },
      {
        "label": "2025-04",
        "value": 30
      },
      {
        "label": "2025-05",
        "value": 31
      },
      {
        "label": "2025-06",
        "value": 30
      },
      {
        "label": "2025-07",
        "value": 31
      },
      {
        "label": "2025-08",
        "value": 31
      },
      {
        "label": "2025-09",
        "value": 30
      },
      {
        "label": "2025-10",
        "value": 31
      },
      {
        "label": "2025-11",
        "value": 30
      },
      {
        "label": "2025-12",
        "value": 31
      },
      {
        "label": "2026-01",
        "value": 28
      },
      {
        "label": "2026-02",
        "value": 25
      },
      {
        "label": "2026-03",
        "value": 28
      },
      {
        "label": "2026-04",
        "value": 27
      },
      {
        "label": "2026-05",
        "value": 28
      },
      {
        "label": "2026-06",
        "value": 27
      },
      {
        "label": "2026-07",
        "value": 31
      },
      {
        "label": "2026-08",
        "value": 31
      },
      {
        "label": "2026-09",
        "value": 30
      },
      {
        "label": "2026-10",
        "value": 1
      }
    ],
    "gigantes_islands": [
      {
        "label": "2015-01",
        "value": 0
      },
      {
        "label": "2015-02",
        "value": 0
      },
      {
        "label": "2015-03",
        "value": 0
      },
      {
        "label": "2015-04",
        "value": 0
      },
      {
        "label": "2015-05",
        "value": 0
      },
      {
        "label": "2015-06",
        "value": 0
      },
      {
        "label": "2015-07",
        "value": 0
      },
      {
        "label": "2015-08",
        "value": 0
      },
      {
        "label": "2015-09",
        "value": 0
      },
      {
        "label": "2015-10",
        "value": 0
      },
      {
        "label": "2015-11",
        "value": 7
      },
      {
        "label": "2015-12",
        "value": 31
      },
      {
        "label": "2016-01",
        "value": 31
      },
      {
        "label": "2016-02",
        "value": 29
      },
      {
        "label": "2016-03",
        "value": 4
      },
      {
        "label": "2016-04",
        "value": 0
      },
      {
        "label": "2016-05",
        "value": 0
      },
      {
        "label": "2016-06",
        "value": 0
      },
      {
        "label": "2016-07",
        "value": 0
      },
      {
        "label": "2016-08",
        "value": 0
      },
      {
        "label": "2016-09",
        "value": 0
      },
      {
        "label": "2016-10",
        "value": 5
      },
      {
        "label": "2016-11",
        "value": 30
      },
      {
        "label": "2016-12",
        "value": 31
      },
      {
        "label": "2017-01",
        "value": 31
      },
      {
        "label": "2017-02",
        "value": 28
      },
      {
        "label": "2017-03",
        "value": 31
      },
      {
        "label": "2017-04",
        "value": 3
      },
      {
        "label": "2017-05",
        "value": 0
      },
      {
        "label": "2017-06",
        "value": 0
      },
      {
        "label": "2017-07",
        "value": 0
      },
      {
        "label": "2017-08",
        "value": 17
      },
      {
        "label": "2017-09",
        "value": 30
      },
      {
        "label": "2017-10",
        "value": 11
      },
      {
        "label": "2017-11",
        "value": 0
      },
      {
        "label": "2017-12",
        "value": 0
      },
      {
        "label": "2018-01",
        "value": 0
      },
      {
        "label": "2018-02",
        "value": 0
      },
      {
        "label": "2018-03",
        "value": 0
      },
      {
        "label": "2018-04",
        "value": 0
      },
      {
        "label": "2018-05",
        "value": 0
      },
      {
        "label": "2018-06",
        "value": 0
      },
      {
        "label": "2018-07",
        "value": 0
      },
      {
        "label": "2018-08",
        "value": 0
      },
      {
        "label": "2018-09",
        "value": 0
      },
      {
        "label": "2018-10",
        "value": 0
      },
      {
        "label": "2018-11",
        "value": 0
      },
      {
        "label": "2018-12",
        "value": 0
      },
      {
        "label": "2019-01",
        "value": 0
      },
      {
        "label": "2019-02",
        "value": 0
      },
      {
        "label": "2019-03",
        "value": 0
      },
      {
        "label": "2019-04",
        "value": 0
      },
      {
        "label": "2019-05",
        "value": 0
      },
      {
        "label": "2019-06",
        "value": 0
      },
      {
        "label": "2019-07",
        "value": 0
      },
      {
        "label": "2019-08",
        "value": 0
      },
      {
        "label": "2019-09",
        "value": 0
      },
      {
        "label": "2019-10",
        "value": 0
      },
      {
        "label": "2019-11",
        "value": 0
      },
      {
        "label": "2019-12",
        "value": 0
      },
      {
        "label": "2020-01",
        "value": 0
      },
      {
        "label": "2020-02",
        "value": 0
      },
      {
        "label": "2020-03",
        "value": 0
      },
      {
        "label": "2020-04",
        "value": 0
      },
      {
        "label": "2020-05",
        "value": 0
      },
      {
        "label": "2020-06",
        "value": 0
      },
      {
        "label": "2020-07",
        "value": 0
      },
      {
        "label": "2020-08",
        "value": 0
      },
      {
        "label": "2020-09",
        "value": 0
      },
      {
        "label": "2020-10",
        "value": 0
      },
      {
        "label": "2020-11",
        "value": 0
      },
      {
        "label": "2020-12",
        "value": 0
      },
      {
        "label": "2021-01",
        "value": 0
      },
      {
        "label": "2021-02",
        "value": 0
      },
      {
        "label": "2021-03",
        "value": 0
      },
      {
        "label": "2021-04",
        "value": 0
      },
      {
        "label": "2021-05",
        "value": 0
      },
      {
        "label": "2021-06",
        "value": 0
      },
      {
        "label": "2021-07",
        "value": 0
      },
      {
        "label": "2021-08",
        "value": 0
      },
      {
        "label": "2021-09",
        "value": 0
      },
      {
        "label": "2021-10",
        "value": 0
      },
      {
        "label": "2021-11",
        "value": 0
      },
      {
        "label": "2021-12",
        "value": 0
      },
      {
        "label": "2022-01",
        "value": 0
      },
      {
        "label": "2022-02",
        "value": 0
      },
      {
        "label": "2022-03",
        "value": 0
      },
      {
        "label": "2022-04",
        "value": 0
      },
      {
        "label": "2022-05",
        "value": 0
      },
      {
        "label": "2022-06",
        "value": 0
      },
      {
        "label": "2022-07",
        "value": 0
      },
      {
        "label": "2022-08",
        "value": 0
      },
      {
        "label": "2022-09",
        "value": 0
      },
      {
        "label": "2022-10",
        "value": 0
      },
      {
        "label": "2022-11",
        "value": 0
      },
      {
        "label": "2022-12",
        "value": 0
      },
      {
        "label": "2023-01",
        "value": 0
      },
      {
        "label": "2023-02",
        "value": 0
      },
      {
        "label": "2023-03",
        "value": 0
      },
      {
        "label": "2023-04",
        "value": 0
      },
      {
        "label": "2023-05",
        "value": 0
      },
      {
        "label": "2023-06",
        "value": 0
      },
      {
        "label": "2023-07",
        "value": 0
      },
      {
        "label": "2023-08",
        "value": 6
      },
      {
        "label": "2023-09",
        "value": 30
      },
      {
        "label": "2023-10",
        "value": 31
      },
      {
        "label": "2023-11",
        "value": 30
      },
      {
        "label": "2023-12",
        "value": 20
      },
      {
        "label": "2024-01",
        "value": 0
      },
      {
        "label": "2024-02",
        "value": 0
      },
      {
        "label": "2024-03",
        "value": 0
      },
      {
        "label": "2024-04",
        "value": 0
      },
      {
        "label": "2024-05",
        "value": 0
      },
      {
        "label": "2024-06",
        "value": 0
      },
      {
        "label": "2024-07",
        "value": 0
      },
      {
        "label": "2024-08",
        "value": 0
      },
      {
        "label": "2024-09",
        "value": 0
      },
      {
        "label": "2024-10",
        "value": 0
      },
      {
        "label": "2024-11",
        "value": 0
      },
      {
        "label": "2024-12",
        "value": 0
      },
      {
        "label": "2025-01",
        "value": 0
      },
      {
        "label": "2025-02",
        "value": 0
      },
      {
        "label": "2025-03",
        "value": 0
      },
      {
        "label": "2025-04",
        "value": 0
      },
      {
        "label": "2025-05",
        "value": 0
      },
      {
        "label": "2025-06",
        "value": 0
      },
      {
        "label": "2025-07",
        "value": 0
      },
      {
        "label": "2025-08",
        "value": 0
      },
      {
        "label": "2025-09",
        "value": 0
      },
      {
        "label": "2025-10",
        "value": 0
      },
      {
        "label": "2025-11",
        "value": 0
      },
      {
        "label": "2025-12",
        "value": 0
      },
      {
        "label": "2026-01",
        "value": 0
      },
      {
        "label": "2026-02",
        "value": 0
      },
      {
        "label": "2026-03",
        "value": 0
      },
      {
        "label": "2026-04",
        "value": 0
      },
      {
        "label": "2026-05",
        "value": 0
      },
      {
        "label": "2026-06",
        "value": 0
      },
      {
        "label": "2026-07",
        "value": 0
      },
      {
        "label": "2026-08",
        "value": 0
      },
      {
        "label": "2026-09",
        "value": 0
      },
      {
        "label": "2026-10",
        "value": 0
      }
    ],
    "matarinao_bay": [
      {
        "label": "2015-01",
        "value": 0
      },
      {
        "label": "2015-02",
        "value": 0
      },
      {
        "label": "2015-03",
        "value": 0
      },
      {
        "label": "2015-04",
        "value": 0
      },
      {
        "label": "2015-05",
        "value": 0
      },
      {
        "label": "2015-06",
        "value": 0
      },
      {
        "label": "2015-07",
        "value": 0
      },
      {
        "label": "2015-08",
        "value": 0
      },
      {
        "label": "2015-09",
        "value": 0
      },
      {
        "label": "2015-10",
        "value": 0
      },
      {
        "label": "2015-11",
        "value": 0
      },
      {
        "label": "2015-12",
        "value": 0
      },
      {
        "label": "2016-01",
        "value": 0
      },
      {
        "label": "2016-02",
        "value": 0
      },
      {
        "label": "2016-03",
        "value": 0
      },
      {
        "label": "2016-04",
        "value": 0
      },
      {
        "label": "2016-05",
        "value": 0
      },
      {
        "label": "2016-06",
        "value": 0
      },
      {
        "label": "2016-07",
        "value": 10
      },
      {
        "label": "2016-08",
        "value": 31
      },
      {
        "label": "2016-09",
        "value": 30
      },
      {
        "label": "2016-10",
        "value": 31
      },
      {
        "label": "2016-11",
        "value": 30
      },
      {
        "label": "2016-12",
        "value": 31
      },
      {
        "label": "2017-01",
        "value": 31
      },
      {
        "label": "2017-02",
        "value": 28
      },
      {
        "label": "2017-03",
        "value": 15
      },
      {
        "label": "2017-04",
        "value": 0
      },
      {
        "label": "2017-05",
        "value": 0
      },
      {
        "label": "2017-06",
        "value": 0
      },
      {
        "label": "2017-07",
        "value": 0
      },
      {
        "label": "2017-08",
        "value": 17
      },
      {
        "label": "2017-09",
        "value": 30
      },
      {
        "label": "2017-10",
        "value": 31
      },
      {
        "label": "2017-11",
        "value": 30
      },
      {
        "label": "2017-12",
        "value": 31
      },
      {
        "label": "2018-01",
        "value": 31
      },
      {
        "label": "2018-02",
        "value": 0
      },
      {
        "label": "2018-03",
        "value": 0
      },
      {
        "label": "2018-04",
        "value": 0
      },
      {
        "label": "2018-05",
        "value": 0
      },
      {
        "label": "2018-06",
        "value": 0
      },
      {
        "label": "2018-07",
        "value": 0
      },
      {
        "label": "2018-08",
        "value": 22
      },
      {
        "label": "2018-09",
        "value": 30
      },
      {
        "label": "2018-10",
        "value": 31
      },
      {
        "label": "2018-11",
        "value": 30
      },
      {
        "label": "2018-12",
        "value": 31
      },
      {
        "label": "2019-01",
        "value": 31
      },
      {
        "label": "2019-02",
        "value": 27
      },
      {
        "label": "2019-03",
        "value": 0
      },
      {
        "label": "2019-04",
        "value": 0
      },
      {
        "label": "2019-05",
        "value": 0
      },
      {
        "label": "2019-06",
        "value": 0
      },
      {
        "label": "2019-07",
        "value": 0
      },
      {
        "label": "2019-08",
        "value": 0
      },
      {
        "label": "2019-09",
        "value": 0
      },
      {
        "label": "2019-10",
        "value": 0
      },
      {
        "label": "2019-11",
        "value": 0
      },
      {
        "label": "2019-12",
        "value": 19
      },
      {
        "label": "2020-01",
        "value": 21
      },
      {
        "label": "2020-02",
        "value": 0
      },
      {
        "label": "2020-03",
        "value": 0
      },
      {
        "label": "2020-04",
        "value": 0
      },
      {
        "label": "2020-05",
        "value": 0
      },
      {
        "label": "2020-06",
        "value": 0
      },
      {
        "label": "2020-07",
        "value": 0
      },
      {
        "label": "2020-08",
        "value": 0
      },
      {
        "label": "2020-09",
        "value": 29
      },
      {
        "label": "2020-10",
        "value": 31
      },
      {
        "label": "2020-11",
        "value": 30
      },
      {
        "label": "2020-12",
        "value": 4
      },
      {
        "label": "2021-01",
        "value": 20
      },
      {
        "label": "2021-02",
        "value": 28
      },
      {
        "label": "2021-03",
        "value": 9
      },
      {
        "label": "2021-04",
        "value": 0
      },
      {
        "label": "2021-05",
        "value": 0
      },
      {
        "label": "2021-06",
        "value": 0
      },
      {
        "label": "2021-07",
        "value": 31
      },
      {
        "label": "2021-08",
        "value": 31
      },
      {
        "label": "2021-09",
        "value": 9
      },
      {
        "label": "2021-10",
        "value": 11
      },
      {
        "label": "2021-11",
        "value": 30
      },
      {
        "label": "2021-12",
        "value": 31
      },
      {
        "label": "2022-01",
        "value": 31
      },
      {
        "label": "2022-02",
        "value": 6
      },
      {
        "label": "2022-03",
        "value": 0
      },
      {
        "label": "2022-04",
        "value": 0
      },
      {
        "label": "2022-05",
        "value": 0
      },
      {
        "label": "2022-06",
        "value": 0
      },
      {
        "label": "2022-07",
        "value": 0
      },
      {
        "label": "2022-08",
        "value": 0
      },
      {
        "label": "2022-09",
        "value": 29
      },
      {
        "label": "2022-10",
        "value": 20
      },
      {
        "label": "2022-11",
        "value": 0
      },
      {
        "label": "2022-12",
        "value": 0
      },
      {
        "label": "2023-01",
        "value": 0
      },
      {
        "label": "2023-02",
        "value": 0
      },
      {
        "label": "2023-03",
        "value": 0
      },
      {
        "label": "2023-04",
        "value": 0
      },
      {
        "label": "2023-05",
        "value": 0
      },
      {
        "label": "2023-06",
        "value": 0
      },
      {
        "label": "2023-07",
        "value": 0
      },
      {
        "label": "2023-08",
        "value": 0
      },
      {
        "label": "2023-09",
        "value": 0
      },
      {
        "label": "2023-10",
        "value": 0
      },
      {
        "label": "2023-11",
        "value": 0
      },
      {
        "label": "2023-12",
        "value": 0
      },
      {
        "label": "2024-01",
        "value": 7
      },
      {
        "label": "2024-02",
        "value": 29
      },
      {
        "label": "2024-03",
        "value": 31
      },
      {
        "label": "2024-04",
        "value": 30
      },
      {
        "label": "2024-05",
        "value": 31
      },
      {
        "label": "2024-06",
        "value": 9
      },
      {
        "label": "2024-07",
        "value": 1
      },
      {
        "label": "2024-08",
        "value": 31
      },
      {
        "label": "2024-09",
        "value": 30
      },
      {
        "label": "2024-10",
        "value": 15
      },
      {
        "label": "2024-11",
        "value": 0
      },
      {
        "label": "2024-12",
        "value": 23
      },
      {
        "label": "2025-01",
        "value": 31
      },
      {
        "label": "2025-02",
        "value": 28
      },
      {
        "label": "2025-03",
        "value": 19
      },
      {
        "label": "2025-04",
        "value": 0
      },
      {
        "label": "2025-05",
        "value": 0
      },
      {
        "label": "2025-06",
        "value": 0
      },
      {
        "label": "2025-07",
        "value": 18
      },
      {
        "label": "2025-08",
        "value": 31
      },
      {
        "label": "2025-09",
        "value": 30
      },
      {
        "label": "2025-10",
        "value": 31
      },
      {
        "label": "2025-11",
        "value": 30
      },
      {
        "label": "2025-12",
        "value": 31
      },
      {
        "label": "2026-01",
        "value": 28
      },
      {
        "label": "2026-02",
        "value": 25
      },
      {
        "label": "2026-03",
        "value": 28
      },
      {
        "label": "2026-04",
        "value": 27
      },
      {
        "label": "2026-05",
        "value": 28
      },
      {
        "label": "2026-06",
        "value": 27
      },
      {
        "label": "2026-07",
        "value": 31
      },
      {
        "label": "2026-08",
        "value": 31
      },
      {
        "label": "2026-09",
        "value": 30
      },
      {
        "label": "2026-10",
        "value": 1
      }
    ],
    "milagros_masbate": [
      {
        "label": "2016-01",
        "value": 0
      },
      {
        "label": "2016-02",
        "value": 0
      },
      {
        "label": "2016-03",
        "value": 0
      },
      {
        "label": "2016-04",
        "value": 0
      },
      {
        "label": "2016-05",
        "value": 0
      },
      {
        "label": "2016-06",
        "value": 0
      },
      {
        "label": "2016-07",
        "value": 0
      },
      {
        "label": "2016-08",
        "value": 0
      },
      {
        "label": "2016-09",
        "value": 0
      },
      {
        "label": "2016-10",
        "value": 6
      },
      {
        "label": "2016-11",
        "value": 21
      },
      {
        "label": "2016-12",
        "value": 0
      },
      {
        "label": "2017-01",
        "value": 0
      },
      {
        "label": "2017-02",
        "value": 0
      },
      {
        "label": "2017-03",
        "value": 26
      },
      {
        "label": "2017-04",
        "value": 11
      },
      {
        "label": "2017-05",
        "value": 0
      },
      {
        "label": "2017-06",
        "value": 0
      },
      {
        "label": "2017-07",
        "value": 0
      },
      {
        "label": "2017-08",
        "value": 2
      },
      {
        "label": "2017-09",
        "value": 30
      },
      {
        "label": "2017-10",
        "value": 29
      },
      {
        "label": "2017-11",
        "value": 0
      },
      {
        "label": "2017-12",
        "value": 0
      },
      {
        "label": "2018-01",
        "value": 2
      },
      {
        "label": "2018-02",
        "value": 28
      },
      {
        "label": "2018-03",
        "value": 6
      },
      {
        "label": "2018-04",
        "value": 0
      },
      {
        "label": "2018-05",
        "value": 0
      },
      {
        "label": "2018-06",
        "value": 0
      },
      {
        "label": "2018-07",
        "value": 0
      },
      {
        "label": "2018-08",
        "value": 0
      },
      {
        "label": "2018-09",
        "value": 10
      },
      {
        "label": "2018-10",
        "value": 31
      },
      {
        "label": "2018-11",
        "value": 30
      },
      {
        "label": "2018-12",
        "value": 13
      },
      {
        "label": "2019-01",
        "value": 0
      },
      {
        "label": "2019-02",
        "value": 0
      },
      {
        "label": "2019-03",
        "value": 0
      },
      {
        "label": "2019-04",
        "value": 0
      },
      {
        "label": "2019-05",
        "value": 0
      },
      {
        "label": "2019-06",
        "value": 0
      },
      {
        "label": "2019-07",
        "value": 0
      },
      {
        "label": "2019-08",
        "value": 0
      },
      {
        "label": "2019-09",
        "value": 0
      },
      {
        "label": "2019-10",
        "value": 0
      },
      {
        "label": "2019-11",
        "value": 0
      },
      {
        "label": "2019-12",
        "value": 0
      },
      {
        "label": "2020-01",
        "value": 0
      },
      {
        "label": "2020-02",
        "value": 0
      },
      {
        "label": "2020-03",
        "value": 0
      },
      {
        "label": "2020-04",
        "value": 0
      },
      {
        "label": "2020-05",
        "value": 0
      },
      {
        "label": "2020-06",
        "value": 0
      },
      {
        "label": "2020-07",
        "value": 0
      },
      {
        "label": "2020-08",
        "value": 0
      },
      {
        "label": "2020-09",
        "value": 5
      },
      {
        "label": "2020-10",
        "value": 31
      },
      {
        "label": "2020-11",
        "value": 30
      },
      {
        "label": "2020-12",
        "value": 4
      },
      {
        "label": "2021-05",
        "value": 0
      },
      {
        "label": "2021-06",
        "value": 6
      },
      {
        "label": "2021-07",
        "value": 31
      },
      {
        "label": "2021-08",
        "value": 31
      },
      {
        "label": "2021-09",
        "value": 23
      },
      {
        "label": "2021-10",
        "value": 0
      },
      {
        "label": "2021-11",
        "value": 0
      },
      {
        "label": "2021-12",
        "value": 3
      },
      {
        "label": "2022-01",
        "value": 31
      },
      {
        "label": "2022-02",
        "value": 28
      },
      {
        "label": "2022-03",
        "value": 31
      },
      {
        "label": "2022-04",
        "value": 30
      },
      {
        "label": "2022-05",
        "value": 31
      },
      {
        "label": "2022-06",
        "value": 30
      },
      {
        "label": "2022-07",
        "value": 21
      },
      {
        "label": "2022-08",
        "value": 0
      },
      {
        "label": "2022-09",
        "value": 0
      },
      {
        "label": "2022-10",
        "value": 25
      },
      {
        "label": "2022-11",
        "value": 30
      },
      {
        "label": "2022-12",
        "value": 31
      },
      {
        "label": "2023-01",
        "value": 31
      },
      {
        "label": "2023-02",
        "value": 28
      },
      {
        "label": "2023-03",
        "value": 31
      },
      {
        "label": "2023-04",
        "value": 19
      },
      {
        "label": "2023-05",
        "value": 0
      },
      {
        "label": "2023-06",
        "value": 0
      },
      {
        "label": "2023-07",
        "value": 0
      },
      {
        "label": "2023-08",
        "value": 0
      },
      {
        "label": "2023-09",
        "value": 0
      },
      {
        "label": "2023-10",
        "value": 0
      },
      {
        "label": "2023-11",
        "value": 0
      },
      {
        "label": "2023-12",
        "value": 0
      },
      {
        "label": "2024-01",
        "value": 7
      },
      {
        "label": "2024-02",
        "value": 29
      },
      {
        "label": "2024-03",
        "value": 31
      },
      {
        "label": "2024-04",
        "value": 30
      },
      {
        "label": "2024-05",
        "value": 2
      },
      {
        "label": "2024-06",
        "value": 0
      },
      {
        "label": "2024-07",
        "value": 0
      },
      {
        "label": "2024-08",
        "value": 0
      },
      {
        "label": "2024-09",
        "value": 0
      },
      {
        "label": "2024-10",
        "value": 0
      },
      {
        "label": "2024-11",
        "value": 0
      },
      {
        "label": "2024-12",
        "value": 0
      },
      {
        "label": "2025-01",
        "value": 0
      },
      {
        "label": "2025-02",
        "value": 22
      },
      {
        "label": "2025-03",
        "value": 31
      },
      {
        "label": "2025-04",
        "value": 30
      },
      {
        "label": "2025-05",
        "value": 31
      },
      {
        "label": "2025-06",
        "value": 8
      },
      {
        "label": "2025-07",
        "value": 0
      },
      {
        "label": "2025-08",
        "value": 0
      },
      {
        "label": "2025-09",
        "value": 0
      },
      {
        "label": "2025-10",
        "value": 0
      },
      {
        "label": "2025-11",
        "value": 0
      },
      {
        "label": "2025-12",
        "value": 0
      },
      {
        "label": "2026-01",
        "value": 0
      },
      {
        "label": "2026-02",
        "value": 0
      },
      {
        "label": "2026-03",
        "value": 0
      },
      {
        "label": "2026-04",
        "value": 0
      },
      {
        "label": "2026-05",
        "value": 0
      },
      {
        "label": "2026-06",
        "value": 0
      },
      {
        "label": "2026-07",
        "value": 0
      },
      {
        "label": "2026-08",
        "value": 0
      },
      {
        "label": "2026-09",
        "value": 0
      },
      {
        "label": "2026-10",
        "value": 0
      }
    ],
    "pilar": [
      {
        "label": "2015-01",
        "value": 0
      },
      {
        "label": "2015-02",
        "value": 0
      },
      {
        "label": "2015-03",
        "value": 0
      },
      {
        "label": "2015-04",
        "value": 0
      },
      {
        "label": "2015-05",
        "value": 0
      },
      {
        "label": "2015-06",
        "value": 0
      },
      {
        "label": "2015-07",
        "value": 0
      },
      {
        "label": "2015-08",
        "value": 0
      },
      {
        "label": "2015-09",
        "value": 0
      },
      {
        "label": "2015-10",
        "value": 9
      },
      {
        "label": "2015-11",
        "value": 30
      },
      {
        "label": "2015-12",
        "value": 31
      },
      {
        "label": "2016-01",
        "value": 31
      },
      {
        "label": "2016-02",
        "value": 17
      },
      {
        "label": "2016-03",
        "value": 30
      },
      {
        "label": "2016-04",
        "value": 0
      },
      {
        "label": "2016-05",
        "value": 0
      },
      {
        "label": "2016-06",
        "value": 0
      },
      {
        "label": "2016-07",
        "value": 0
      },
      {
        "label": "2016-08",
        "value": 0
      },
      {
        "label": "2016-09",
        "value": 0
      },
      {
        "label": "2016-10",
        "value": 0
      },
      {
        "label": "2016-11",
        "value": 0
      },
      {
        "label": "2016-12",
        "value": 0
      },
      {
        "label": "2017-01",
        "value": 0
      },
      {
        "label": "2017-02",
        "value": 0
      },
      {
        "label": "2017-03",
        "value": 0
      },
      {
        "label": "2017-04",
        "value": 0
      },
      {
        "label": "2017-05",
        "value": 0
      },
      {
        "label": "2017-06",
        "value": 0
      },
      {
        "label": "2017-07",
        "value": 0
      },
      {
        "label": "2017-08",
        "value": 0
      },
      {
        "label": "2017-09",
        "value": 0
      },
      {
        "label": "2017-10",
        "value": 0
      },
      {
        "label": "2017-11",
        "value": 0
      },
      {
        "label": "2017-12",
        "value": 0
      },
      {
        "label": "2018-01",
        "value": 0
      },
      {
        "label": "2018-02",
        "value": 0
      },
      {
        "label": "2018-03",
        "value": 0
      },
      {
        "label": "2018-04",
        "value": 0
      },
      {
        "label": "2018-05",
        "value": 0
      },
      {
        "label": "2018-06",
        "value": 0
      },
      {
        "label": "2018-07",
        "value": 0
      },
      {
        "label": "2018-08",
        "value": 0
      },
      {
        "label": "2018-09",
        "value": 0
      },
      {
        "label": "2018-10",
        "value": 0
      },
      {
        "label": "2018-11",
        "value": 0
      },
      {
        "label": "2018-12",
        "value": 0
      },
      {
        "label": "2019-01",
        "value": 0
      },
      {
        "label": "2019-02",
        "value": 0
      },
      {
        "label": "2019-03",
        "value": 0
      },
      {
        "label": "2019-04",
        "value": 0
      },
      {
        "label": "2019-05",
        "value": 0
      },
      {
        "label": "2019-06",
        "value": 0
      },
      {
        "label": "2019-07",
        "value": 0
      },
      {
        "label": "2019-08",
        "value": 0
      },
      {
        "label": "2019-09",
        "value": 0
      },
      {
        "label": "2019-10",
        "value": 0
      },
      {
        "label": "2019-11",
        "value": 0
      },
      {
        "label": "2019-12",
        "value": 0
      },
      {
        "label": "2020-01",
        "value": 0
      },
      {
        "label": "2020-02",
        "value": 0
      },
      {
        "label": "2020-03",
        "value": 0
      },
      {
        "label": "2020-04",
        "value": 0
      },
      {
        "label": "2020-05",
        "value": 0
      },
      {
        "label": "2020-06",
        "value": 0
      },
      {
        "label": "2020-07",
        "value": 0
      },
      {
        "label": "2020-08",
        "value": 0
      },
      {
        "label": "2020-09",
        "value": 0
      },
      {
        "label": "2020-10",
        "value": 0
      },
      {
        "label": "2020-11",
        "value": 0
      },
      {
        "label": "2020-12",
        "value": 0
      },
      {
        "label": "2021-01",
        "value": 0
      },
      {
        "label": "2021-02",
        "value": 0
      },
      {
        "label": "2021-03",
        "value": 0
      },
      {
        "label": "2021-04",
        "value": 0
      },
      {
        "label": "2021-05",
        "value": 0
      },
      {
        "label": "2021-06",
        "value": 0
      },
      {
        "label": "2021-07",
        "value": 0
      },
      {
        "label": "2021-08",
        "value": 0
      },
      {
        "label": "2021-09",
        "value": 0
      },
      {
        "label": "2021-10",
        "value": 0
      },
      {
        "label": "2021-11",
        "value": 0
      },
      {
        "label": "2021-12",
        "value": 0
      },
      {
        "label": "2022-01",
        "value": 0
      },
      {
        "label": "2022-02",
        "value": 0
      },
      {
        "label": "2022-03",
        "value": 0
      },
      {
        "label": "2022-04",
        "value": 0
      },
      {
        "label": "2022-05",
        "value": 0
      },
      {
        "label": "2022-06",
        "value": 0
      },
      {
        "label": "2022-07",
        "value": 0
      },
      {
        "label": "2022-08",
        "value": 0
      },
      {
        "label": "2022-09",
        "value": 2
      },
      {
        "label": "2022-10",
        "value": 31
      },
      {
        "label": "2022-11",
        "value": 30
      },
      {
        "label": "2022-12",
        "value": 31
      },
      {
        "label": "2023-01",
        "value": 31
      },
      {
        "label": "2023-02",
        "value": 21
      },
      {
        "label": "2023-03",
        "value": 0
      },
      {
        "label": "2023-04",
        "value": 0
      },
      {
        "label": "2023-05",
        "value": 0
      },
      {
        "label": "2023-06",
        "value": 0
      },
      {
        "label": "2023-07",
        "value": 0
      },
      {
        "label": "2023-08",
        "value": 6
      },
      {
        "label": "2023-09",
        "value": 30
      },
      {
        "label": "2023-10",
        "value": 31
      },
      {
        "label": "2023-11",
        "value": 30
      },
      {
        "label": "2023-12",
        "value": 0
      },
      {
        "label": "2024-01",
        "value": 0
      },
      {
        "label": "2024-02",
        "value": 0
      },
      {
        "label": "2024-03",
        "value": 0
      },
      {
        "label": "2024-04",
        "value": 0
      },
      {
        "label": "2024-05",
        "value": 0
      },
      {
        "label": "2024-06",
        "value": 0
      },
      {
        "label": "2024-07",
        "value": 0
      },
      {
        "label": "2024-08",
        "value": 0
      },
      {
        "label": "2024-09",
        "value": 0
      },
      {
        "label": "2024-10",
        "value": 0
      },
      {
        "label": "2024-11",
        "value": 0
      },
      {
        "label": "2024-12",
        "value": 0
      },
      {
        "label": "2025-01",
        "value": 0
      },
      {
        "label": "2025-02",
        "value": 0
      },
      {
        "label": "2025-03",
        "value": 0
      },
      {
        "label": "2025-04",
        "value": 0
      },
      {
        "label": "2025-05",
        "value": 0
      },
      {
        "label": "2025-06",
        "value": 0
      },
      {
        "label": "2025-07",
        "value": 0
      },
      {
        "label": "2025-08",
        "value": 0
      },
      {
        "label": "2025-09",
        "value": 0
      },
      {
        "label": "2025-10",
        "value": 0
      },
      {
        "label": "2025-11",
        "value": 0
      },
      {
        "label": "2025-12",
        "value": 0
      },
      {
        "label": "2026-01",
        "value": 0
      },
      {
        "label": "2026-02",
        "value": 0
      },
      {
        "label": "2026-03",
        "value": 0
      },
      {
        "label": "2026-04",
        "value": 0
      },
      {
        "label": "2026-05",
        "value": 0
      },
      {
        "label": "2026-06",
        "value": 0
      },
      {
        "label": "2026-07",
        "value": 0
      },
      {
        "label": "2026-08",
        "value": 0
      },
      {
        "label": "2026-09",
        "value": 0
      },
      {
        "label": "2026-10",
        "value": 0
      }
    ],
    "president_roxas": [
      {
        "label": "2015-01",
        "value": 0
      },
      {
        "label": "2015-02",
        "value": 0
      },
      {
        "label": "2015-03",
        "value": 0
      },
      {
        "label": "2015-04",
        "value": 0
      },
      {
        "label": "2015-05",
        "value": 0
      },
      {
        "label": "2015-06",
        "value": 0
      },
      {
        "label": "2015-07",
        "value": 0
      },
      {
        "label": "2015-08",
        "value": 0
      },
      {
        "label": "2015-09",
        "value": 0
      },
      {
        "label": "2015-10",
        "value": 0
      },
      {
        "label": "2015-11",
        "value": 0
      },
      {
        "label": "2015-12",
        "value": 14
      },
      {
        "label": "2016-01",
        "value": 6
      },
      {
        "label": "2016-02",
        "value": 0
      },
      {
        "label": "2016-03",
        "value": 0
      },
      {
        "label": "2016-04",
        "value": 0
      },
      {
        "label": "2016-05",
        "value": 0
      },
      {
        "label": "2016-06",
        "value": 0
      },
      {
        "label": "2016-07",
        "value": 0
      },
      {
        "label": "2016-08",
        "value": 0
      },
      {
        "label": "2016-09",
        "value": 0
      },
      {
        "label": "2016-10",
        "value": 0
      },
      {
        "label": "2016-11",
        "value": 0
      },
      {
        "label": "2016-12",
        "value": 0
      },
      {
        "label": "2017-01",
        "value": 0
      },
      {
        "label": "2017-02",
        "value": 0
      },
      {
        "label": "2017-03",
        "value": 0
      },
      {
        "label": "2017-04",
        "value": 0
      },
      {
        "label": "2017-05",
        "value": 0
      },
      {
        "label": "2017-06",
        "value": 0
      },
      {
        "label": "2017-07",
        "value": 0
      },
      {
        "label": "2017-08",
        "value": 0
      },
      {
        "label": "2017-09",
        "value": 0
      },
      {
        "label": "2017-10",
        "value": 0
      },
      {
        "label": "2017-11",
        "value": 0
      },
      {
        "label": "2017-12",
        "value": 0
      },
      {
        "label": "2018-01",
        "value": 0
      },
      {
        "label": "2018-02",
        "value": 0
      },
      {
        "label": "2018-03",
        "value": 0
      },
      {
        "label": "2018-04",
        "value": 0
      },
      {
        "label": "2018-05",
        "value": 0
      },
      {
        "label": "2018-06",
        "value": 0
      },
      {
        "label": "2018-07",
        "value": 0
      },
      {
        "label": "2018-08",
        "value": 0
      },
      {
        "label": "2018-09",
        "value": 0
      },
      {
        "label": "2018-10",
        "value": 0
      },
      {
        "label": "2018-11",
        "value": 0
      },
      {
        "label": "2018-12",
        "value": 0
      },
      {
        "label": "2019-01",
        "value": 0
      },
      {
        "label": "2019-02",
        "value": 0
      },
      {
        "label": "2019-03",
        "value": 0
      },
      {
        "label": "2019-04",
        "value": 0
      },
      {
        "label": "2019-05",
        "value": 0
      },
      {
        "label": "2019-06",
        "value": 0
      },
      {
        "label": "2019-07",
        "value": 0
      },
      {
        "label": "2019-08",
        "value": 0
      },
      {
        "label": "2019-09",
        "value": 0
      },
      {
        "label": "2019-10",
        "value": 0
      },
      {
        "label": "2019-11",
        "value": 0
      },
      {
        "label": "2019-12",
        "value": 0
      },
      {
        "label": "2020-01",
        "value": 0
      },
      {
        "label": "2020-02",
        "value": 0
      },
      {
        "label": "2020-03",
        "value": 0
      },
      {
        "label": "2020-04",
        "value": 0
      },
      {
        "label": "2020-05",
        "value": 0
      },
      {
        "label": "2020-06",
        "value": 0
      },
      {
        "label": "2020-07",
        "value": 0
      },
      {
        "label": "2020-08",
        "value": 0
      },
      {
        "label": "2020-09",
        "value": 0
      },
      {
        "label": "2020-10",
        "value": 0
      },
      {
        "label": "2020-11",
        "value": 0
      },
      {
        "label": "2020-12",
        "value": 0
      },
      {
        "label": "2021-01",
        "value": 0
      },
      {
        "label": "2021-02",
        "value": 0
      },
      {
        "label": "2021-03",
        "value": 0
      },
      {
        "label": "2021-04",
        "value": 0
      },
      {
        "label": "2021-05",
        "value": 0
      },
      {
        "label": "2021-06",
        "value": 0
      },
      {
        "label": "2021-07",
        "value": 0
      },
      {
        "label": "2021-08",
        "value": 0
      },
      {
        "label": "2021-09",
        "value": 0
      },
      {
        "label": "2021-10",
        "value": 0
      },
      {
        "label": "2021-11",
        "value": 0
      },
      {
        "label": "2021-12",
        "value": 0
      },
      {
        "label": "2022-01",
        "value": 0
      },
      {
        "label": "2022-02",
        "value": 0
      },
      {
        "label": "2022-03",
        "value": 0
      },
      {
        "label": "2022-04",
        "value": 0
      },
      {
        "label": "2022-05",
        "value": 0
      },
      {
        "label": "2022-06",
        "value": 0
      },
      {
        "label": "2022-07",
        "value": 0
      },
      {
        "label": "2022-08",
        "value": 0
      },
      {
        "label": "2022-09",
        "value": 0
      },
      {
        "label": "2022-10",
        "value": 27
      },
      {
        "label": "2022-11",
        "value": 30
      },
      {
        "label": "2022-12",
        "value": 31
      },
      {
        "label": "2023-01",
        "value": 31
      },
      {
        "label": "2023-02",
        "value": 21
      },
      {
        "label": "2023-03",
        "value": 0
      },
      {
        "label": "2023-04",
        "value": 0
      },
      {
        "label": "2023-05",
        "value": 0
      },
      {
        "label": "2023-06",
        "value": 0
      },
      {
        "label": "2023-07",
        "value": 0
      },
      {
        "label": "2023-08",
        "value": 6
      },
      {
        "label": "2023-09",
        "value": 30
      },
      {
        "label": "2023-10",
        "value": 31
      },
      {
        "label": "2023-11",
        "value": 30
      },
      {
        "label": "2023-12",
        "value": 0
      },
      {
        "label": "2024-01",
        "value": 0
      },
      {
        "label": "2024-02",
        "value": 0
      },
      {
        "label": "2024-03",
        "value": 0
      },
      {
        "label": "2024-04",
        "value": 0
      },
      {
        "label": "2024-05",
        "value": 0
      },
      {
        "label": "2024-06",
        "value": 0
      },
      {
        "label": "2024-07",
        "value": 0
      },
      {
        "label": "2024-08",
        "value": 0
      },
      {
        "label": "2024-09",
        "value": 0
      },
      {
        "label": "2024-10",
        "value": 0
      },
      {
        "label": "2024-11",
        "value": 0
      },
      {
        "label": "2024-12",
        "value": 0
      },
      {
        "label": "2025-01",
        "value": 0
      },
      {
        "label": "2025-02",
        "value": 0
      },
      {
        "label": "2025-03",
        "value": 0
      },
      {
        "label": "2025-04",
        "value": 0
      },
      {
        "label": "2025-05",
        "value": 0
      },
      {
        "label": "2025-06",
        "value": 0
      },
      {
        "label": "2025-07",
        "value": 0
      },
      {
        "label": "2025-08",
        "value": 0
      },
      {
        "label": "2025-09",
        "value": 0
      },
      {
        "label": "2025-10",
        "value": 0
      },
      {
        "label": "2025-11",
        "value": 0
      },
      {
        "label": "2025-12",
        "value": 0
      },
      {
        "label": "2026-01",
        "value": 0
      },
      {
        "label": "2026-02",
        "value": 0
      },
      {
        "label": "2026-03",
        "value": 0
      },
      {
        "label": "2026-04",
        "value": 0
      },
      {
        "label": "2026-05",
        "value": 0
      },
      {
        "label": "2026-06",
        "value": 0
      },
      {
        "label": "2026-07",
        "value": 0
      },
      {
        "label": "2026-08",
        "value": 0
      },
      {
        "label": "2026-09",
        "value": 0
      },
      {
        "label": "2026-10",
        "value": 0
      }
    ],
    "roxas_city": [
      {
        "label": "2015-01",
        "value": 0
      },
      {
        "label": "2015-02",
        "value": 0
      },
      {
        "label": "2015-03",
        "value": 0
      },
      {
        "label": "2015-04",
        "value": 0
      },
      {
        "label": "2015-05",
        "value": 0
      },
      {
        "label": "2015-06",
        "value": 0
      },
      {
        "label": "2015-07",
        "value": 0
      },
      {
        "label": "2015-08",
        "value": 0
      },
      {
        "label": "2015-09",
        "value": 0
      },
      {
        "label": "2015-10",
        "value": 0
      },
      {
        "label": "2015-11",
        "value": 0
      },
      {
        "label": "2015-12",
        "value": 0
      },
      {
        "label": "2016-01",
        "value": 0
      },
      {
        "label": "2016-02",
        "value": 0
      },
      {
        "label": "2016-03",
        "value": 0
      },
      {
        "label": "2016-04",
        "value": 0
      },
      {
        "label": "2016-05",
        "value": 0
      },
      {
        "label": "2016-06",
        "value": 0
      },
      {
        "label": "2016-07",
        "value": 0
      },
      {
        "label": "2016-08",
        "value": 0
      },
      {
        "label": "2016-09",
        "value": 0
      },
      {
        "label": "2016-10",
        "value": 0
      },
      {
        "label": "2016-11",
        "value": 0
      },
      {
        "label": "2016-12",
        "value": 0
      },
      {
        "label": "2017-01",
        "value": 0
      },
      {
        "label": "2017-02",
        "value": 0
      },
      {
        "label": "2017-03",
        "value": 0
      },
      {
        "label": "2017-04",
        "value": 0
      },
      {
        "label": "2017-05",
        "value": 0
      },
      {
        "label": "2017-06",
        "value": 0
      },
      {
        "label": "2017-07",
        "value": 0
      },
      {
        "label": "2017-08",
        "value": 0
      },
      {
        "label": "2017-09",
        "value": 0
      },
      {
        "label": "2017-10",
        "value": 0
      },
      {
        "label": "2017-11",
        "value": 0
      },
      {
        "label": "2017-12",
        "value": 0
      },
      {
        "label": "2018-01",
        "value": 0
      },
      {
        "label": "2018-02",
        "value": 0
      },
      {
        "label": "2018-03",
        "value": 0
      },
      {
        "label": "2018-04",
        "value": 0
      },
      {
        "label": "2018-05",
        "value": 0
      },
      {
        "label": "2018-06",
        "value": 0
      },
      {
        "label": "2018-07",
        "value": 0
      },
      {
        "label": "2018-08",
        "value": 0
      },
      {
        "label": "2018-09",
        "value": 0
      },
      {
        "label": "2018-10",
        "value": 0
      },
      {
        "label": "2018-11",
        "value": 0
      },
      {
        "label": "2018-12",
        "value": 0
      },
      {
        "label": "2019-01",
        "value": 0
      },
      {
        "label": "2019-02",
        "value": 0
      },
      {
        "label": "2019-03",
        "value": 0
      },
      {
        "label": "2019-04",
        "value": 0
      },
      {
        "label": "2019-05",
        "value": 0
      },
      {
        "label": "2019-06",
        "value": 0
      },
      {
        "label": "2019-07",
        "value": 0
      },
      {
        "label": "2019-08",
        "value": 0
      },
      {
        "label": "2019-09",
        "value": 0
      },
      {
        "label": "2019-10",
        "value": 0
      },
      {
        "label": "2019-11",
        "value": 0
      },
      {
        "label": "2019-12",
        "value": 0
      },
      {
        "label": "2020-01",
        "value": 0
      },
      {
        "label": "2020-02",
        "value": 0
      },
      {
        "label": "2020-03",
        "value": 0
      },
      {
        "label": "2020-04",
        "value": 0
      },
      {
        "label": "2020-05",
        "value": 0
      },
      {
        "label": "2020-06",
        "value": 0
      },
      {
        "label": "2020-07",
        "value": 0
      },
      {
        "label": "2020-08",
        "value": 0
      },
      {
        "label": "2020-09",
        "value": 0
      },
      {
        "label": "2020-10",
        "value": 0
      },
      {
        "label": "2020-11",
        "value": 0
      },
      {
        "label": "2020-12",
        "value": 0
      },
      {
        "label": "2021-01",
        "value": 0
      },
      {
        "label": "2021-02",
        "value": 0
      },
      {
        "label": "2021-03",
        "value": 0
      },
      {
        "label": "2021-04",
        "value": 0
      },
      {
        "label": "2021-05",
        "value": 0
      },
      {
        "label": "2021-06",
        "value": 0
      },
      {
        "label": "2021-07",
        "value": 0
      },
      {
        "label": "2021-08",
        "value": 0
      },
      {
        "label": "2021-09",
        "value": 0
      },
      {
        "label": "2021-10",
        "value": 0
      },
      {
        "label": "2021-11",
        "value": 0
      },
      {
        "label": "2021-12",
        "value": 0
      },
      {
        "label": "2022-01",
        "value": 0
      },
      {
        "label": "2022-02",
        "value": 0
      },
      {
        "label": "2022-03",
        "value": 0
      },
      {
        "label": "2022-04",
        "value": 0
      },
      {
        "label": "2022-05",
        "value": 0
      },
      {
        "label": "2022-06",
        "value": 0
      },
      {
        "label": "2022-07",
        "value": 0
      },
      {
        "label": "2022-08",
        "value": 0
      },
      {
        "label": "2022-09",
        "value": 2
      },
      {
        "label": "2022-10",
        "value": 31
      },
      {
        "label": "2022-11",
        "value": 30
      },
      {
        "label": "2022-12",
        "value": 31
      },
      {
        "label": "2023-01",
        "value": 9
      },
      {
        "label": "2023-02",
        "value": 0
      },
      {
        "label": "2023-03",
        "value": 0
      },
      {
        "label": "2023-04",
        "value": 0
      },
      {
        "label": "2023-05",
        "value": 0
      },
      {
        "label": "2023-06",
        "value": 0
      },
      {
        "label": "2023-07",
        "value": 0
      },
      {
        "label": "2023-08",
        "value": 6
      },
      {
        "label": "2023-09",
        "value": 30
      },
      {
        "label": "2023-10",
        "value": 31
      },
      {
        "label": "2023-11",
        "value": 30
      },
      {
        "label": "2023-12",
        "value": 20
      },
      {
        "label": "2024-01",
        "value": 0
      },
      {
        "label": "2024-02",
        "value": 0
      },
      {
        "label": "2024-03",
        "value": 0
      },
      {
        "label": "2024-04",
        "value": 0
      },
      {
        "label": "2024-05",
        "value": 0
      },
      {
        "label": "2024-06",
        "value": 0
      },
      {
        "label": "2024-07",
        "value": 0
      },
      {
        "label": "2024-08",
        "value": 0
      },
      {
        "label": "2024-09",
        "value": 0
      },
      {
        "label": "2024-10",
        "value": 0
      },
      {
        "label": "2024-11",
        "value": 0
      },
      {
        "label": "2024-12",
        "value": 0
      },
      {
        "label": "2025-01",
        "value": 0
      },
      {
        "label": "2025-02",
        "value": 0
      },
      {
        "label": "2025-03",
        "value": 0
      },
      {
        "label": "2025-04",
        "value": 0
      },
      {
        "label": "2025-05",
        "value": 0
      },
      {
        "label": "2025-06",
        "value": 0
      },
      {
        "label": "2025-07",
        "value": 0
      },
      {
        "label": "2025-08",
        "value": 0
      },
      {
        "label": "2025-09",
        "value": 0
      },
      {
        "label": "2025-10",
        "value": 0
      },
      {
        "label": "2025-11",
        "value": 0
      },
      {
        "label": "2025-12",
        "value": 0
      },
      {
        "label": "2026-01",
        "value": 0
      },
      {
        "label": "2026-02",
        "value": 0
      },
      {
        "label": "2026-03",
        "value": 0
      },
      {
        "label": "2026-04",
        "value": 0
      },
      {
        "label": "2026-05",
        "value": 0
      },
      {
        "label": "2026-06",
        "value": 0
      },
      {
        "label": "2026-07",
        "value": 0
      },
      {
        "label": "2026-08",
        "value": 0
      },
      {
        "label": "2026-09",
        "value": 0
      },
      {
        "label": "2026-10",
        "value": 0
      }
    ],
    "sapian_bay": [
      {
        "label": "2015-01",
        "value": 0
      },
      {
        "label": "2015-02",
        "value": 0
      },
      {
        "label": "2015-03",
        "value": 0
      },
      {
        "label": "2015-04",
        "value": 0
      },
      {
        "label": "2015-05",
        "value": 0
      },
      {
        "label": "2015-06",
        "value": 0
      },
      {
        "label": "2015-07",
        "value": 0
      },
      {
        "label": "2015-08",
        "value": 3
      },
      {
        "label": "2015-09",
        "value": 30
      },
      {
        "label": "2015-10",
        "value": 7
      },
      {
        "label": "2015-11",
        "value": 18
      },
      {
        "label": "2015-12",
        "value": 31
      },
      {
        "label": "2016-01",
        "value": 31
      },
      {
        "label": "2016-02",
        "value": 11
      },
      {
        "label": "2016-03",
        "value": 0
      },
      {
        "label": "2016-04",
        "value": 0
      },
      {
        "label": "2016-05",
        "value": 0
      },
      {
        "label": "2016-06",
        "value": 0
      },
      {
        "label": "2016-07",
        "value": 0
      },
      {
        "label": "2016-08",
        "value": 0
      },
      {
        "label": "2016-09",
        "value": 0
      },
      {
        "label": "2016-10",
        "value": 0
      },
      {
        "label": "2016-11",
        "value": 0
      },
      {
        "label": "2016-12",
        "value": 0
      },
      {
        "label": "2017-01",
        "value": 0
      },
      {
        "label": "2017-02",
        "value": 0
      },
      {
        "label": "2017-03",
        "value": 0
      },
      {
        "label": "2017-04",
        "value": 0
      },
      {
        "label": "2017-05",
        "value": 0
      },
      {
        "label": "2017-06",
        "value": 0
      },
      {
        "label": "2017-07",
        "value": 0
      },
      {
        "label": "2017-08",
        "value": 0
      },
      {
        "label": "2017-09",
        "value": 0
      },
      {
        "label": "2017-10",
        "value": 0
      },
      {
        "label": "2017-11",
        "value": 0
      },
      {
        "label": "2017-12",
        "value": 0
      },
      {
        "label": "2018-01",
        "value": 0
      },
      {
        "label": "2018-02",
        "value": 0
      },
      {
        "label": "2018-03",
        "value": 0
      },
      {
        "label": "2018-04",
        "value": 0
      },
      {
        "label": "2018-05",
        "value": 0
      },
      {
        "label": "2018-06",
        "value": 0
      },
      {
        "label": "2018-07",
        "value": 0
      },
      {
        "label": "2018-08",
        "value": 0
      },
      {
        "label": "2018-09",
        "value": 0
      },
      {
        "label": "2018-10",
        "value": 0
      },
      {
        "label": "2018-11",
        "value": 0
      },
      {
        "label": "2018-12",
        "value": 0
      },
      {
        "label": "2019-01",
        "value": 0
      },
      {
        "label": "2019-02",
        "value": 0
      },
      {
        "label": "2019-03",
        "value": 0
      },
      {
        "label": "2019-04",
        "value": 0
      },
      {
        "label": "2019-05",
        "value": 0
      },
      {
        "label": "2019-06",
        "value": 0
      },
      {
        "label": "2019-07",
        "value": 0
      },
      {
        "label": "2019-08",
        "value": 0
      },
      {
        "label": "2019-09",
        "value": 0
      },
      {
        "label": "2019-10",
        "value": 0
      },
      {
        "label": "2019-11",
        "value": 0
      },
      {
        "label": "2019-12",
        "value": 0
      },
      {
        "label": "2020-01",
        "value": 0
      },
      {
        "label": "2020-02",
        "value": 0
      },
      {
        "label": "2020-03",
        "value": 0
      },
      {
        "label": "2020-04",
        "value": 0
      },
      {
        "label": "2020-05",
        "value": 0
      },
      {
        "label": "2020-06",
        "value": 0
      },
      {
        "label": "2020-07",
        "value": 0
      },
      {
        "label": "2020-08",
        "value": 0
      },
      {
        "label": "2020-09",
        "value": 0
      },
      {
        "label": "2020-10",
        "value": 0
      },
      {
        "label": "2020-11",
        "value": 0
      },
      {
        "label": "2020-12",
        "value": 0
      },
      {
        "label": "2021-01",
        "value": 0
      },
      {
        "label": "2021-02",
        "value": 0
      },
      {
        "label": "2021-03",
        "value": 0
      },
      {
        "label": "2021-04",
        "value": 0
      },
      {
        "label": "2021-05",
        "value": 0
      },
      {
        "label": "2021-06",
        "value": 0
      },
      {
        "label": "2021-07",
        "value": 0
      },
      {
        "label": "2021-08",
        "value": 0
      },
      {
        "label": "2021-09",
        "value": 0
      },
      {
        "label": "2021-10",
        "value": 0
      },
      {
        "label": "2021-11",
        "value": 0
      },
      {
        "label": "2021-12",
        "value": 0
      },
      {
        "label": "2022-01",
        "value": 0
      },
      {
        "label": "2022-02",
        "value": 0
      },
      {
        "label": "2022-03",
        "value": 0
      },
      {
        "label": "2022-04",
        "value": 0
      },
      {
        "label": "2022-05",
        "value": 0
      },
      {
        "label": "2022-06",
        "value": 0
      },
      {
        "label": "2022-07",
        "value": 0
      },
      {
        "label": "2022-08",
        "value": 0
      },
      {
        "label": "2022-09",
        "value": 0
      },
      {
        "label": "2022-10",
        "value": 27
      },
      {
        "label": "2022-11",
        "value": 30
      },
      {
        "label": "2022-12",
        "value": 31
      },
      {
        "label": "2023-01",
        "value": 9
      },
      {
        "label": "2023-02",
        "value": 0
      },
      {
        "label": "2023-03",
        "value": 0
      },
      {
        "label": "2023-04",
        "value": 0
      },
      {
        "label": "2023-05",
        "value": 0
      },
      {
        "label": "2023-06",
        "value": 0
      },
      {
        "label": "2023-07",
        "value": 0
      },
      {
        "label": "2023-08",
        "value": 6
      },
      {
        "label": "2023-09",
        "value": 30
      },
      {
        "label": "2023-10",
        "value": 31
      },
      {
        "label": "2023-11",
        "value": 30
      },
      {
        "label": "2023-12",
        "value": 20
      },
      {
        "label": "2024-01",
        "value": 0
      },
      {
        "label": "2024-02",
        "value": 0
      },
      {
        "label": "2024-03",
        "value": 0
      },
      {
        "label": "2024-04",
        "value": 0
      },
      {
        "label": "2024-05",
        "value": 0
      },
      {
        "label": "2024-06",
        "value": 0
      },
      {
        "label": "2024-07",
        "value": 0
      },
      {
        "label": "2024-08",
        "value": 0
      },
      {
        "label": "2024-09",
        "value": 0
      },
      {
        "label": "2024-10",
        "value": 0
      },
      {
        "label": "2024-11",
        "value": 0
      },
      {
        "label": "2024-12",
        "value": 0
      },
      {
        "label": "2025-01",
        "value": 0
      },
      {
        "label": "2025-02",
        "value": 0
      },
      {
        "label": "2025-03",
        "value": 0
      },
      {
        "label": "2025-04",
        "value": 0
      },
      {
        "label": "2025-05",
        "value": 0
      },
      {
        "label": "2025-06",
        "value": 0
      },
      {
        "label": "2025-07",
        "value": 0
      },
      {
        "label": "2025-08",
        "value": 0
      },
      {
        "label": "2025-09",
        "value": 0
      },
      {
        "label": "2025-10",
        "value": 0
      },
      {
        "label": "2025-11",
        "value": 0
      },
      {
        "label": "2025-12",
        "value": 0
      },
      {
        "label": "2026-01",
        "value": 0
      },
      {
        "label": "2026-02",
        "value": 0
      },
      {
        "label": "2026-03",
        "value": 0
      },
      {
        "label": "2026-04",
        "value": 0
      },
      {
        "label": "2026-05",
        "value": 0
      },
      {
        "label": "2026-06",
        "value": 0
      },
      {
        "label": "2026-07",
        "value": 0
      },
      {
        "label": "2026-08",
        "value": 0
      },
      {
        "label": "2026-09",
        "value": 0
      },
      {
        "label": "2026-10",
        "value": 0
      }
    ]
  }
};

export const MOCK_LOCATIONS = {
  locations: MOCK_LATEST_FORECAST.locations.map(loc => ({
    id: loc.id,
    name: loc.name,
    risk_level: loc.risk_level,
    risk_color: loc.risk_color,
    confidence: loc.confidence,
    coordinates: loc.coordinates,
  })),
  last_updated: MOCK_LATEST_FORECAST.metadata.last_updated,
  total_count: MOCK_LATEST_FORECAST.locations.length
};

#!/usr/bin/env python3
"""
HARIBON v2.0 API Test Script
Tests basic functionality of the enhanced red tide prediction system.
"""

import requests
import json
import sys
from datetime import datetime

def test_api_endpoint(url, description):
    """Test an API endpoint and return success status."""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print(f"✅ {description}: OK")
            return True, response.json()
        else:
            print(f"❌ {description}: HTTP {response.status_code}")
            return False, None
    except Exception as e:
        print(f"❌ {description}: {str(e)}")
        return False, None

def main():
    """Run comprehensive API tests."""
    print("🌊 HARIBON v2.0 API Test Suite")
    print("=" * 50)

    base_url = "http://127.0.0.1:8001"
    tests_passed = 0
    total_tests = 0

    # Test 1: Root endpoint
    total_tests += 1
    success, _ = test_api_endpoint(f"{base_url}/", "Root endpoint")
    if success:
        tests_passed += 1

    # Test 2: API documentation
    total_tests += 1
    success, _ = test_api_endpoint(f"{base_url}/docs", "API documentation")
    if success:
        tests_passed += 1

    # Test 3: OpenAPI schema
    total_tests += 1
    success, _ = test_api_endpoint(f"{base_url}/openapi.json", "OpenAPI schema")
    if success:
        tests_passed += 1

    # Test 4: Latest forecast
    total_tests += 1
    success, data = test_api_endpoint(f"{base_url}/api/forecast/latest", "Latest forecast")
    if success:
        tests_passed += 1
        # Check if forecast has expected structure
        if data and "forecasts" in data:
            location_count = len(data["forecasts"])
            print(f"   📍 Found {location_count} locations in forecast")
            if location_count > 0:
                sample_location = data["forecasts"][0]
                print(f"   📍 Sample location: {sample_location.get('location', 'Unknown')}")
                print(f"   🎯 Risk level: {sample_location.get('risk_level', 'Unknown')}")

    # Test 5: Locations summary
    total_tests += 1
    success, data = test_api_endpoint(f"{base_url}/api/forecast/locations", "Locations summary")
    if success:
        tests_passed += 1
        if data and "locations" in data:
            print(f"   📍 Locations available: {len(data['locations'])}")

    # Test 6: Risk summary
    total_tests += 1
    success, data = test_api_endpoint(f"{base_url}/api/summary/risk-summary", "Risk summary")
    if success:
        tests_passed += 1
        if data and "risk_distribution" in data:
            risk_dist = data["risk_distribution"]
            print(f"   📊 Risk distribution: Green={risk_dist.get('green', 0)}, Yellow={risk_dist.get('yellow', 0)}, Orange={risk_dist.get('orange', 0)}, Red={risk_dist.get('red', 0)}")

    # Test 7: Environmental overview
    total_tests += 1
    success, data = test_api_endpoint(f"{base_url}/api/summary/environmental-overview", "Environmental overview")
    if success:
        tests_passed += 1
        if data and "environmental_summary" in data:
            env = data["environmental_summary"]
            print(f"   🌡️  Avg temperature: {env.get('avg_temperature', 'N/A'):.1f}°C")
            print(f"   🧪 Avg salinity: {env.get('avg_salinity', 'N/A'):.1f} PSU")

    print("\n" + "=" * 50)
    print(f"Test Results: {tests_passed}/{total_tests} tests passed")

    if tests_passed == total_tests:
        print("🎉 All tests passed! HARIBON v2.0 is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the API setup.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
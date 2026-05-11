import React, { useState, useEffect } from 'react';
import { useAppLocation } from '../context/LocationContext';
import MapSection from '../components/dashboard/MapSection';
import RightDashboard from '../components/dashboard/RightDashboard';
import ForecastStrip from '../components/dashboard/ForecastStrip';
import ApiService from '../services/api';

export default function Dashboard() {
  const [forecastData, setForecastData] = useState(null);
  const { selectedLocation, setSelectedLocation } = useAppLocation();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchForecastData();
  }, []);

  const fetchForecastData = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await ApiService.getLatestForecast();
      setForecastData(data);

      // Always rebind selectedLocation to the newest payload object to avoid stale UI fields.
      if (data.locations && data.locations.length > 0) {
        if (selectedLocation?.id) {
          const refreshedSelected = data.locations.find((loc) => loc.id === selectedLocation.id);
          setSelectedLocation(refreshedSelected || data.locations[0]);
        } else {
          setSelectedLocation(data.locations[0]);
        }
      }
    } catch (err) {
      setError('Failed to load forecast data');
      console.error('Error fetching forecast data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleLocationSelect = (location) => {
    setSelectedLocation(location);
  };

  const handleRefreshData = async () => {
    try {
      // Fire-and-forget trigger to regenerate data
      await ApiService.triggerDailyUpdate();
    } catch (e) {
      console.warn('Failed to trigger updater, will just refetch latest:', e);
    }
    // Then fetch latest (existing API returns newest file)
    await fetchForecastData();
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-haribon-dark mx-auto mb-4"></div>
          <p className="text-lg text-gray-600">Loading forecast data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center bg-red-50 p-8 rounded-lg border border-red-200">
          <p className="text-xl text-red-600 mb-4">{error}</p>
          <button
            onClick={fetchForecastData}
            className="bg-haribon-dark text-white px-6 py-2 rounded-lg hover:bg-opacity-90 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="px-4 pb-4 pt-1 sm:px-6 lg:p-6 lg:pb-4 lg:pr-5 grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-x-6 gap-y-4 lg:gap-y-3 lg:items-stretch">
      {/* Forecast Strip - spans both columns */}
      <div className="lg:col-span-2 mt-0 lg:-mt-2 mb-1">
        <ForecastStrip
          forecastData={forecastData}
          selectedLocation={selectedLocation}
          onRefresh={handleRefreshData}
        />
      </div>

      {/* Map Section */}
      <div className="h-full min-h-[455px] lg:min-h-[653px] flex flex-col relative overflow-hidden rounded-xl shadow-sm border border-gray-100">
        <MapSection
          forecastData={forecastData}
          selectedLocation={selectedLocation}
          onLocationSelect={handleLocationSelect}
        />
      </div>

      {/* Right Dashboard */}
      <div className="h-full min-h-[420px] lg:min-h-[653px] flex flex-col">
        <RightDashboard
          forecastData={forecastData}
          selectedLocation={selectedLocation}
        />
      </div>
    </div>
  );
}
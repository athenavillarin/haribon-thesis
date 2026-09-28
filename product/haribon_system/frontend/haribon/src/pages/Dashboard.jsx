import React, { useEffect } from 'react';
import { useAppLocation } from '../context/LocationContext';
import MapSection from '../components/dashboard/MapSection';
import RightDashboard from '../components/dashboard/RightDashboard';
import ForecastStrip from '../components/dashboard/ForecastStrip';
import ForecastStatusBanner from '../components/ForecastStatusBanner';
import useLatestForecast from '../hooks/useLatestForecast';

export default function Dashboard() {
  const forecast = useLatestForecast();
  const { data: forecastData, loading, slow, error, refresh } = forecast;
  const { selectedLocation, setSelectedLocation } = useAppLocation();

  // Always rebind selectedLocation to the newest payload object to avoid stale UI fields.
  useEffect(() => {
    if (!forecastData?.locations?.length) return;
    const refreshedSelected = selectedLocation?.id
      ? forecastData.locations.find((loc) => loc.id === selectedLocation.id)
      : null;
    setSelectedLocation(refreshedSelected || forecastData.locations[0]);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [forecastData]);

  const handleLocationSelect = (location) => {
    setSelectedLocation(location);
  };

  if (!forecastData && loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-haribon-dark mx-auto mb-4"></div>
          <p className="text-lg text-gray-600">
            {slow ? 'Waking up the server, this can take up to a minute...' : 'Loading forecast data...'}
          </p>
        </div>
      </div>
    );
  }

  if (!forecastData && error) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center bg-red-50 p-8 rounded-lg border border-red-200">
          <p className="text-xl text-red-600 mb-4">Failed to load forecast data</p>
          <button
            onClick={refresh}
            className="bg-haribon-dark text-white px-6 py-2 rounded-lg hover:bg-opacity-90 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <>
      <ForecastStatusBanner {...forecast} onRetry={refresh} className="mx-4 mt-2 sm:mx-6" />
      <div className="px-4 pb-4 pt-1 sm:px-6 lg:p-6 lg:pb-4 lg:pr-5 grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-x-6 gap-y-4 lg:gap-y-3 lg:items-stretch">
        {/* Forecast Strip - spans both columns */}
        <div className="lg:col-span-2 mt-0 lg:-mt-2 mb-1">
          <ForecastStrip
            forecastData={forecastData}
            selectedLocation={selectedLocation}
            onRefresh={refresh}
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
    </>
  );
}
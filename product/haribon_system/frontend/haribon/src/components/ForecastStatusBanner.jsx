import React from 'react';

export default function ForecastStatusBanner({ data, stale, loading, slow, error, onRetry, className = '' }) {
  const refreshFailed = !stale && !loading && error && data;
  if (!stale && !refreshFailed) return null;

  const forecastDate = data?.metadata?.forecast_date;
  let message = forecastDate ? `Showing saved forecast for ${forecastDate}.` : 'Showing saved forecast.';
  if (refreshFailed) {
    message = forecastDate
      ? `Could not refresh; showing forecast for ${forecastDate}.`
      : 'Could not refresh; showing the last loaded forecast.';
  } else if (loading) {
    message += slow ? ' Waking up the server, this can take up to a minute…' : ' Checking for updates…';
  } else if (error) {
    message += ' Could not reach the server.';
  }

  return (
    <div className={`${className} flex items-center justify-between gap-3 rounded-lg border border-amber-200 bg-amber-50 px-4 py-2 text-sm text-amber-800`}>
      <span>{message}</span>
      {!loading && error && (
        <button
          onClick={onRetry}
          className="shrink-0 rounded-md bg-haribon-dark px-3 py-1 text-xs font-medium text-white hover:bg-opacity-90"
        >
          Retry
        </button>
      )}
    </div>
  );
}

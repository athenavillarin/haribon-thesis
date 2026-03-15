import React, { useState, useEffect } from 'react';
import { useAppLocation } from '../context/LocationContext';
import ApiService from '../services/api';
import ForecastStrip from '../components/dashboard/ForecastStrip';

function TrendBars({ data }) {
  if (!data.length) {
    return <p className="text-sm text-gray-400">No chart data available for the selected filters.</p>;
  }

  const maxValue = Math.max(...data.map((d) => d.value), 1);
  const minSlotWidth = data.length > 18 ? 28 : 38;
  const gap = data.length > 18 ? 6 : 10;
  const chartWidth = Math.max(680, data.length * minSlotWidth + (data.length - 1) * gap);

  return (
    <div className="w-full max-w-full min-w-0 overflow-x-auto border-t border-gray-100 pt-4">
      <div
        className="h-72 grid items-end"
        style={{
          width: `${chartWidth}px`,
          gridTemplateColumns: `repeat(${data.length}, minmax(${minSlotWidth}px, 1fr))`,
          columnGap: `${gap}px`,
        }}
      >
        {data.map((item) => {
          const height = Math.max(10, Math.round((item.value / maxValue) * 220));
          return (
            <div key={item.label} className="w-full flex flex-col items-center justify-end gap-2">
              <div className="text-[11px] text-gray-500 font-medium">{item.value}</div>
              <div className="w-full bg-[#3F6D72] rounded-t-md" style={{ height: `${height}px` }} />
              <div className="text-[10px] text-gray-500 whitespace-nowrap">{item.label}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function TrendLine({ data }) {
  if (data.length < 2) {
    return <p className="text-sm text-gray-400">Need at least two data points to render a timeline.</p>;
  }

  const width = 640;
  const height = 280;
  const padX = 44;
  const padY = 20;
  const minY = 0;
  const maxY = Math.max(...data.map((d) => d.value), 1);
  const plotMax = Math.max(1, Math.ceil(maxY));
  const tickCount = Math.min(4, plotMax);
  const usableW = width - padX * 2;
  const usableH = height - padY * 2;

  const yTicks = Array.from({ length: tickCount + 1 }, (_, i) => {
    const value = Math.round((plotMax / tickCount) * (tickCount - i));
    const y = padY + ((plotMax - value) / (plotMax - minY || 1)) * usableH;
    const label = String(value);
    return { value, y, label };
  });

  const points = data
    .map((point, index) => {
      const x = padX + (index / (data.length - 1)) * usableW;
      const y = padY + ((plotMax - point.value) / (plotMax - minY || 1)) * usableH;
      return { ...point, x, y };
    })
    .filter((point) => Number.isFinite(point.y));

  const pathD = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');

  return (
    <div className="w-full max-w-full min-w-0 overflow-hidden">
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-72">
        {yTicks.map((tick) => (
          <g key={tick.label}>
            <line x1={padX} y1={tick.y} x2={width - padX} y2={tick.y} stroke="#F1F5F9" strokeWidth="1" />
            <text x={padX - 8} y={tick.y + 4} textAnchor="end" className="fill-gray-500" fontSize="10">
              {tick.label}
            </text>
          </g>
        ))}
        <line x1={padX} y1={height - padY} x2={width - padX} y2={height - padY} stroke="#E5E7EB" strokeWidth="1" />
        <line x1={padX} y1={padY} x2={padX} y2={height - padY} stroke="#E5E7EB" strokeWidth="1" />
        <path d={pathD} fill="none" stroke="#3F6D72" strokeWidth="3" />
        {points.map((point) => (
          <g key={point.label}>
            <circle cx={point.x} cy={point.y} r="4" fill="#3F6D72" />
            <text x={point.x} y={height - 4} textAnchor="middle" className="fill-gray-500" fontSize="10">
              {point.label}
            </text>
          </g>
        ))}
      </svg>
    </div>
  );
}

export default function SeaStats() {
  const [forecastData, setForecastData] = useState(null);
  const [historicalData, setHistoricalData] = useState({ monthly_alerts: [], timeline: [], available_range: null });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [trendMode, setTrendMode] = useState('monthly');
  const [trendArea, setTrendArea] = useState('');
  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');
  const [timelineYear, setTimelineYear] = useState('');
  const { selectedLocation, setSelectedLocation } = useAppLocation();

  useEffect(() => {
    fetchForecastData();
  }, []);

  useEffect(() => {
    if (!forecastData?.locations?.length) return;
    fetchHistoricalData();
  }, [forecastData, trendArea, fromDate, toDate, trendMode]);

  const fetchForecastData = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await ApiService.getLatestForecast();
      setForecastData(data);

      // Default selected location if none is set yet
      if (data?.locations && data.locations.length > 0 && !selectedLocation) {
        setSelectedLocation(data.locations[0]);
      }
    } catch (err) {
      console.error('Error fetching forecast data:', err);
      setError('Failed to load SeaStats data');
    } finally {
      setLoading(false);
    }
  };

  const handleLocationChange = (location) => {
    setSelectedLocation(location);
    setTrendArea(location.id);
  };

  const fetchHistoricalData = async () => {
    const effectiveTrendArea = trendArea || (trendMode === 'timeline' ? selectedLocation?.id || '' : '');

    if (!effectiveTrendArea) {
      setHistoricalData({ monthly_alerts: [], timeline: [], available_range: null });
      return;
    }

    try {
      const locationId = effectiveTrendArea === 'all' ? 'all' : effectiveTrendArea;
      const options = trendMode === 'monthly' ? { fromDate, toDate } : {};
      const data = await ApiService.getHistoricalData(locationId, options);
      setHistoricalData(data || { monthly_alerts: [], timeline: [], available_range: null });
    } catch (err) {
      console.error('Error fetching historical chart data:', err);
      setHistoricalData({ monthly_alerts: [], timeline: [], available_range: null });
    }
  };

  const parseMetricValue = (value) => {
    if (value === null || value === undefined) return null;
    if (typeof value === 'number') return Number.isFinite(value) ? value : null;
    const match = String(value).match(/-?\d+(\.\d+)?/);
    return match ? Number(match[0]) : null;
  };

  const formatMetricValue = (value, decimals = 1) => {
    if (value === null || value === undefined || Number.isNaN(value)) return '--';
    return Number(value).toFixed(decimals);
  };

  const handleRefresh = async () => {
    try {
      await ApiService.triggerDailyUpdate();
    } catch (e) {
      console.warn('Failed to trigger daily update, will just refetch latest:', e);
    }
    await fetchForecastData();
  };

  const lastUpdated = forecastData?.last_updated || forecastData?.metadata?.last_updated || null;

  const monthlyAlertData = (historicalData?.monthly_alerts || []).map((row) => ({
    label: row.label,
    value: Number(row.value || 0),
  }));

  const availableTimelineYears = Array.from(
    new Set([
      ...(historicalData?.monthly_alerts || [])
        .map((row) => {
          const match = String(row.label || '').match(/^(\d{4})-(\d{2})$/);
          return match ? match[1] : null;
        })
        .filter(Boolean),
      ...(historicalData?.timeline || [])
        .map((row) => new Date(row.date).getFullYear())
        .filter((year) => Number.isFinite(year))
        .map(String),
    ])
  ).sort((a, b) => Number(a) - Number(b));

  useEffect(() => {
    if (!availableTimelineYears.length) {
      if (timelineYear) setTimelineYear('');
      return;
    }

    if (!timelineYear || !availableTimelineYears.includes(timelineYear)) {
      setTimelineYear(availableTimelineYears[availableTimelineYears.length - 1]);
    }
  }, [availableTimelineYears, timelineYear]);

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-haribon-dark mx-auto mb-4" />
          <p className="text-lg text-gray-600">Loading SeaStats data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="bg-red-50 border border-red-200 rounded-xl px-6 py-4 text-center max-w-md">
          <p className="text-red-600 font-medium mb-3">{error}</p>
          <button
            onClick={fetchForecastData}
            className="inline-flex items-center justify-center px-4 py-2 rounded-lg bg-haribon-dark text-white text-sm font-medium hover:bg-opacity-90 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const envData = selectedLocation?.environmental_data || {};
  const factorData = selectedLocation?.today_forecast?.contributing_factors || selectedLocation?.contributing_factors || {};

  const timelineMonthlyData = (() => {
    if (!timelineYear) return [];

    const monthLabels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const monthTotals = Array(12).fill(0);

    const monthlyRows = historicalData?.monthly_alerts || [];
    if (monthlyRows.length > 0) {
      monthlyRows.forEach((row) => {
        const match = String(row.label || '').match(/^(\d{4})-(\d{2})$/);
        if (!match) return;
        const year = match[1];
        const month = Number(match[2]) - 1;
        if (year !== timelineYear || month < 0 || month > 11) return;
        monthTotals[month] += Number(row.value || 0);
      });
    } else {
      (historicalData?.timeline || []).forEach((row) => {
        const date = new Date(row.date);
        if (!Number.isFinite(date.getTime())) return;
        if (String(date.getFullYear()) !== timelineYear) return;
        const monthIndex = date.getMonth();
        monthTotals[monthIndex] += Number(row.value || 0);
      });
    }

    return monthLabels.map((label, idx) => ({
      label,
      value: monthTotals[idx],
    }));
  })();

  const parameters = [
    {
      label: 'Sea-Surface Temperature',
      key: 'Temperature',
      unit: '°C',
      value: parseMetricValue(envData['Temperature']),
      status: 'Live',
      severity: 'Elevated',
      accent: 'text-amber-600 bg-amber-50 border-amber-200',
    },
    {
      label: 'Salinity',
      key: 'Salinity',
      unit: 'PSU',
      value: parseMetricValue(envData['Salinity']),
      status: 'Live',
      severity: 'Below Normal',
      accent: 'text-sky-700 bg-sky-50 border-sky-200',
    },
    {
      label: 'Chl-a Concentration',
      key: 'Chlorophyll-a',
      unit: 'mg/m³',
      value: parseMetricValue(envData['Chlorophyll-a']),
      status: 'Live',
      severity: 'Critical',
      accent: 'text-emerald-700 bg-emerald-50 border-emerald-200',
    },
    {
      label: 'Rainfall',
      key: 'Rainfall_mm',
      unit: 'mm',
      value: parseMetricValue(factorData.rainfall),
      status: '24-hour Rainfall',
      severity: 'Heavy Rain',
      accent: 'text-cyan-700 bg-cyan-50 border-cyan-200',
    },
    {
      label: 'Nutrient Runoff',
      key: 'Nutrient Runoff',
      unit: 'kg/ha',
      value: parseMetricValue(envData['Nutrient Runoff']) ?? parseMetricValue(envData['Agriculture_pct']),
      status: 'From Agricultural Land',
      severity: 'High Impact',
      accent: 'text-orange-700 bg-orange-50 border-orange-200',
    },
    {
      label: 'Wind Speed',
      key: 'Wind Speed',
      unit: 'm/s',
      value: parseMetricValue(envData['Wind Speed']),
      status: 'Live',
      severity: 'Stable',
      accent: 'text-slate-700 bg-slate-50 border-slate-200',
    },
  ];

  const effectiveTrendArea = trendArea || (trendMode === 'timeline' ? selectedLocation?.id || '' : '');

  return (
    <div className="p-6 pb-4 pr-5">
      <div className="w-full min-w-0 flex flex-col gap-6 h-full">
        {/* 5-Day Forecast strip (reuses dashboard styling, still Tailwind-only) */}
        {selectedLocation && (
          <div className="-mt-2 mb-1">
            <ForecastStrip
              forecastData={forecastData}
              selectedLocation={selectedLocation}
              onRefresh={handleRefresh}
            />
          </div>
        )}

        {/* Main content grid: trends + environmental parameters */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 flex-1 min-w-0">
          {/* Risk trends with area/date filters */}
          <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-6 flex flex-col min-w-0 max-w-full overflow-hidden">
            <div className="flex flex-col gap-4 mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Risk Trends</h2>

              <div className="grid grid-cols-1 md:grid-cols-[1fr_170px_170px] gap-3">
                <select
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-haribon-dark/40"
                  value={trendArea || (trendMode === 'timeline' ? selectedLocation?.id || '' : '')}
                  onChange={(e) => setTrendArea(e.target.value)}
                >
                  <option value="">Select Area</option>
                  <option value="all">All Areas</option>
                  {forecastData?.locations?.map((loc) => (
                    <option key={loc.id} value={loc.id}>
                      {loc.name}
                    </option>
                  ))}
                </select>

                {trendMode === 'monthly' ? (
                  <>
                    <input
                      type="date"
                      value={fromDate}
                      onChange={(e) => setFromDate(e.target.value)}
                      className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-haribon-dark/40"
                      aria-label="From date"
                    />

                    <input
                      type="date"
                      value={toDate}
                      onChange={(e) => setToDate(e.target.value)}
                      className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-haribon-dark/40"
                      aria-label="To date"
                    />
                  </>
                ) : (
                  <>
                    <select
                      className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-haribon-dark/40"
                      value={timelineYear}
                      onChange={(e) => setTimelineYear(e.target.value)}
                      aria-label="Timeline year"
                    >
                      {!availableTimelineYears.length && <option value="">No year data</option>}
                      {availableTimelineYears.map((year) => (
                        <option key={year} value={year}>{year}</option>
                      ))}
                    </select>
                    <div className="hidden md:block" />
                  </>
                )}
              </div>

              <div className="grid grid-cols-2 bg-gray-50 rounded-lg p-1 border border-gray-100 max-w-sm">
                <button
                  type="button"
                  onClick={() => setTrendMode('monthly')}
                  className={`text-sm font-medium py-2 rounded-md transition-colors ${
                    trendMode === 'monthly' ? 'bg-[#3F6D72] text-white' : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  Monthly Alerts
                </button>
                <button
                  type="button"
                  onClick={() => setTrendMode('timeline')}
                  className={`text-sm font-medium py-2 rounded-md transition-colors ${
                    trendMode === 'timeline' ? 'bg-[#3F6D72] text-white' : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  Timeline
                </button>
              </div>
            </div>

            <div className="flex-1 min-w-0 max-w-full overflow-hidden">
              {!effectiveTrendArea ? (
                <div className="h-72 flex items-center justify-center text-sm text-gray-400 border border-dashed border-gray-200 rounded-lg">
                  Select an area to view historical charts.
                </div>
              ) : trendMode === 'monthly' ? (
                <TrendBars data={monthlyAlertData} />
              ) : (
                <TrendLine data={timelineMonthlyData} />
              )}
            </div>
          </div>

          {/* Environmental parameters */}
          <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-6 flex flex-col">
            <div className="flex items-center justify-between mb-5">
              <div>
                <h2 className="text-lg font-semibold text-gray-900">Environmental Parameters</h2>
                <p className="text-xs text-gray-500 mt-1">
                  Live drivers derived from the latest forecast for the selected site
                </p>
              </div>
              {/* Area dropdown to match SeaStats design */}
              <div className="w-[220px] hidden md:block shrink-0">
                <select
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-haribon-dark/40"
                  value={selectedLocation?.id || ''}
                  onChange={(e) => {
                    const loc = forecastData?.locations?.find((l) => l.id === e.target.value);
                    if (loc) handleLocationChange(loc);
                  }}
                >
                  <option value="" disabled>
                    Select Area
                  </option>
                  {forecastData?.locations?.map((loc) => (
                    <option key={loc.id} value={loc.id}>
                      {loc.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Mobile location selector */}
            <div className="md:hidden mb-4">
              <label className="block text-xs font-medium text-gray-600 mb-1">Location</label>
              <select
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-haribon-dark/40"
                value={selectedLocation?.id || ''}
                onChange={(e) => {
                  const loc = forecastData?.locations?.find((l) => l.id === e.target.value);
                  if (loc) handleLocationChange(loc);
                }}
              >
                {forecastData?.locations?.map((loc) => (
                  <option key={loc.id} value={loc.id}>
                    {loc.name}
                  </option>
                ))}
              </select>
            </div>

            {!selectedLocation && (
              <div className="flex-1 flex items-center justify-center text-gray-400 text-sm">
                Select a location to view environmental conditions.
              </div>
            )}

            {selectedLocation && (
              <>
                <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4 mb-4">
                  {parameters.map((param) => {
                    const value = formatMetricValue(param.value, param.key === 'Nutrient Runoff' ? 2 : 1);
                    return (
                      <div
                        key={param.key}
                        className="bg-gray-50 rounded-xl border border-gray-100 px-4 py-4 flex flex-col min-h-[170px]"
                      >
                        <div>
                          <p className="text-[11px] uppercase tracking-wide text-gray-600 font-semibold">
                            {param.label}
                          </p>
                          <p className="text-[11px] text-gray-400">{param.status}</p>
                        </div>

                        <div className="mt-auto">
                          <div className="flex items-baseline gap-1">
                            <span className="text-2xl font-bold text-gray-900">
                              {value}
                            </span>
                            <span className="text-xs text-gray-500">{param.unit}</span>
                          </div>

                          <div className="mt-2">
                            <span className={`inline-flex text-[10px] font-semibold px-2.5 py-1 rounded-full border whitespace-nowrap ${param.accent}`}>
                              {param.severity}
                            </span>
                          </div>

                          <p className="text-[10px] text-gray-400 mt-3">Last updated: {new Date().toLocaleTimeString()}</p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </>
            )}
          </div>
        </div>

        {lastUpdated && (
          <div className="text-xs text-gray-500 self-end mt-auto">
            Last updated:{' '}
            <span className="font-medium text-gray-700">
              {new Date(lastUpdated).toLocaleString()}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
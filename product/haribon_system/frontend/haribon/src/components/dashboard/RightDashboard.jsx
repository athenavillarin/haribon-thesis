import React from 'react';
import { useNavigate } from 'react-router-dom';
import { FiMinus, FiPlus } from 'react-icons/fi';
import RiskIcon from '../RiskIcon';
import { getRiskStyle } from '../riskStyles';
import { getDayForecast, formatDayLabel } from './forecastDay';

const BFAR_BULLETIN_URL = 'https://www.bfar.da.gov.ph/shellfish-bulletin-no-02-2022/';

export default function RightDashboard({ forecastData, selectedLocation, selectedDate }) {
  const [isSnapshotOpen, setIsSnapshotOpen] = React.useState(false);
  const navigate = useNavigate();

  if (!selectedLocation) {
    return (
      <div className="h-full flex items-center justify-center text-gray-600">
        <p>Select a location from the map or list</p>
      </div>
    );
  }

  const day = getDayForecast(selectedLocation, selectedDate);
  const riskStyle = getRiskStyle(day.risk_color);
  const metadata = forecastData?.metadata || {};
  const todayStr = metadata.forecast_date || new Date().toLocaleDateString('en-CA');
  const dayStr = day.isToday ? todayStr : day.date;
  const lastUpdated = metadata.last_updated ? new Date(metadata.last_updated) : null;
  const lastUpdatedStr = lastUpdated && !Number.isNaN(lastUpdated.getTime())
    ? lastUpdated.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })
    : null;

  const environmentalData = selectedLocation.environmental_data || {};
  const backendRecommendations = day.isToday ? selectedLocation?.today_forecast?.recommendations || [] : [];
  const recommendationItems = backendRecommendations.length > 0
    ? backendRecommendations
    : FALLBACK_RECOMMENDATIONS[day.risk_color] || [];

  const conditionItems = Object.entries(environmentalData).map(([key, value]) =>
    parseMetricParam(key, value)
  );

  if (conditionItems.length === 0) {
    // Fallback to contributing factors if environmental_data is empty
    const factors = selectedLocation?.today_forecast?.contributing_factors || {};
    Object.entries(factors).forEach(([key, value]) => {
      conditionItems.push(parseMetricParam(key, value));
    });
  }

  if (conditionItems.length === 0) {
    conditionItems.push({ label: 'No environmental data', value: 'N/A', unit: '' });
  }

  return (
    <div className="h-full font-quicksand flex flex-col gap-4">
      <div className="rounded-xl border border-gray-100 bg-[#F3F4F6] p-5 shadow-sm ring-2 ring-[#3F6D72]">
      {/* Location Header */}
      <div className="mb-3 flex justify-between items-start gap-3">
        <div>
          <p className="text-[11px] font-bold uppercase tracking-wider text-[#3F6D72] mb-0.5">Selected bay</p>
          <h2 className="text-xl font-bold text-gray-900 leading-tight mb-1">{selectedLocation.name}</h2>
          <p className="text-sm text-gray-600 font-medium">Forecast for {day.isToday ? `today, ${dayStr}` : formatDayLabel(dayStr)}</p>
          {lastUpdatedStr && (
            <p className="text-xs text-gray-600 mt-0.5">Updated {lastUpdatedStr}</p>
          )}
        </div>
        <div
          className="px-3 py-1.5 rounded-xl border text-[13px] font-bold flex items-center gap-1.5 shrink-0"
          style={{ backgroundColor: riskStyle.tint, color: riskStyle.ink, borderColor: riskStyle.border }}
        >
          <RiskIcon riskColor={day.risk_color} size={18} />
          <span>{day.risk_level}</span>
        </div>
      </div>

      <ForecastSummary location={selectedLocation} day={day} />

      {/* Before harvesting */}
      <div className="mt-4">
        <h3 className="text-sm font-bold text-gray-800 mb-2">Before harvesting</h3>
        <ul className="space-y-1.5 mb-3">
          {recommendationItems.map((text, idx) => (
            <li key={`${selectedLocation.id || 'loc'}-rec-${idx}`} className="text-xs text-gray-700 flex gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-gray-500 mt-1.5 shrink-0"></span>
              {text}
            </li>
          ))}
        </ul>
        <a
          href={BFAR_BULLETIN_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="w-full inline-flex items-center justify-center gap-2 py-2.5 px-4 bg-[#3F6D72] hover:bg-[#32575B] text-white text-xs font-bold rounded-xl shadow-sm transition-colors duration-150 group"
        >
          <span>View BFAR Shellfish Bulletins</span>
          <svg
            className="w-3.5 h-3.5 opacity-80 group-hover:opacity-100 transition-opacity"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
          </svg>
        </a>
        <p className="mt-2 text-[11px] text-gray-600 text-center">
          Forecasts support awareness only. Always follow official BFAR and local advisories.
        </p>
      </div>

      {/* Water conditions */}
      <CollapsibleSection
        title="Water conditions"
        subtitle={day.isToday ? `Latest readings for ${todayStr}` : `Today's readings, not forecast for ${formatDayLabel(dayStr)}`}
      >
        <div className="grid grid-cols-2 gap-2">
          {conditionItems.map((item, idx) => (
            <MetricItem
              key={`${item.label}-${idx}`}
              label={item.label}
              value={item.value}
              unit={item.unit}
              isFullWidth={conditionItems.length % 2 === 1 && idx === conditionItems.length - 1}
            />
          ))}
        </div>
      </CollapsibleSection>
      </div>

      {/* Snapshot List */}
      <div className="rounded-xl border border-gray-100 bg-[#F3F4F6] p-4 shadow-sm">
        <div className="flex justify-between items-center">
          <h3 className="text-sm font-bold text-gray-800">{day.isToday ? "Today's Snapshot" : 'Snapshot'}</h3>
          <div className="flex items-center gap-3">
            <span className="text-xs text-gray-600">{day.isToday ? dayStr : formatDayLabel(dayStr)}</span>
            <button
              type="button"
              onClick={() => setIsSnapshotOpen((open) => !open)}
              aria-expanded={isSnapshotOpen}
              className="inline-flex items-center gap-1 text-xs font-semibold text-gray-700 hover:text-gray-900 transition-colors"
            >
              {isSnapshotOpen ? <FiMinus aria-hidden="true" /> : <FiPlus aria-hidden="true" />}
              {isSnapshotOpen ? 'Hide' : 'Show'}
            </button>
          </div>
        </div>

        {isSnapshotOpen && (
          <div className="mt-4">
            <div className="space-y-2 max-h-[184px] overflow-y-auto p-1">
              {forecastData?.locations?.map(loc => {
                const locDay = getDayForecast(loc, selectedDate);
                return (
                  <div
                    key={loc.id}
                    className={`bg-[#F8F9FA] rounded-lg p-3 flex justify-between items-center border transition-colors ${
                      loc.id === selectedLocation.id ? 'border-transparent ring-2 ring-[#3F6D72]' : 'border-transparent hover:border-gray-200'
                    }`}
                  >
                    <span className="text-xs font-medium text-gray-700">{loc.name}</span>
                    <span
                      className="text-[11px] font-bold flex items-center gap-1.5"
                      style={{ color: getRiskStyle(locDay.risk_color).ink }}
                    >
                      <RiskIcon riskColor={locDay.risk_color} size={14} />
                      <span>{locDay.risk_level}</span>
                    </span>
                  </div>
                );
              })}
            </div>
            <div className="pt-2 text-right">
              <button
                type="button"
                onClick={() => navigate('/seastats')}
                className="text-xs text-blue-500 font-medium hover:underline flex items-center justify-end gap-1 ml-auto"
              >
                View History <span>→</span>
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

const PARAM_DEFINITIONS = [
  { match: /^(temp|sst|sea[-_\s]?surface)/i, label: 'Temperature', unit: '°C' },
  { match: /^(chl|chlorophyll)/i, label: 'Chlorophyll-a', unit: 'mg/m³' },
  { match: /^(salinity)/i, label: 'Salinity', unit: 'PSU' },
  { match: /^(mld|mixed[-_\s]?layer)/i, label: 'Mixed Layer Depth', unit: 'm' },
  { match: /^(precip|rain)/i, label: 'Precipitation', unit: 'mm' },
  { match: /^(ndvi)/i, label: 'NDVI', unit: 'index' },
  { match: /^(u[-_\s]?wind)/i, label: 'U-Wind Speed', unit: 'm/s' },
  { match: /^(v[-_\s]?wind)/i, label: 'V-Wind Speed', unit: 'm/s' },
  { match: /^(u[-_\s]?vel|u[-_\s]?curr)/i, label: 'U-Current Velocity', unit: 'm/s' },
  { match: /^(v[-_\s]?vel|v[-_\s]?curr)/i, label: 'V-Current Velocity', unit: 'm/s' },
];

function parseMetricParam(rawKey, rawValue) {
  const cleanKey = String(rawKey || '').trim();
  const matched = PARAM_DEFINITIONS.find((def) => def.match.test(cleanKey));

  const label = matched ? matched.label : cleanKey.replace(/\s*\([^)]*\)/g, '').trim();
  let unit = matched ? matched.unit : '';

  if (!unit) {
    const parenthesized = cleanKey.match(/\(([^)]+)\)/);
    if (parenthesized) unit = parenthesized[1];
  }

  const valStr = String(rawValue ?? '').trim();
  const numMatch = valStr.match(/^-?\d+(\.\d+)?/);
  const numericValue = numMatch ? numMatch[0] : (valStr || '--');

  if (!unit && numMatch) {
    const trailing = valStr.slice(numMatch[0].length).trim();
    if (trailing) unit = trailing;
  }

  if (unit === 'mg/m3') unit = 'mg/m³';
  if (unit === 'C' || unit === 'degC') unit = '°C';

  return { label, value: numericValue, unit };
}

function MetricItem({ label, value, unit, isFullWidth }) {
  return (
    <div
      className={`bg-[#F8F9FA] rounded-xl p-3 flex flex-col justify-between min-h-[68px] border border-gray-100/80 shadow-[0_1px_2px_rgba(0,0,0,0.02)] transition-shadow hover:shadow-sm ${
        isFullWidth ? 'col-span-2' : ''
      }`}
    >
      <span className="text-[11px] text-gray-600 font-semibold leading-snug">
        {label}
      </span>
      <div className="flex items-baseline gap-1 mt-1 text-left">
        <span className="text-lg font-bold text-gray-900 tracking-tight leading-none">{value}</span>
        {unit && <span className="text-[11px] font-semibold text-gray-600">{unit}</span>}
      </div>
    </div>
  );
}

const FALLBACK_RECOMMENDATIONS = {
  red: [
    'Severe algal activity detected in the area',
    'Stop harvesting and selling shellfish immediately',
    'Avoid swimming and fishing until risk decreases',
  ],
  orange: ['Elevated risk levels detected', 'Limit harvesting and monitor local advisories closely'],
  yellow: ['Mild risk detected', 'Harvest with caution and continue regular monitoring'],
  green: ['Conditions are normal', 'Safe for harvesting and recreational activities'],
};

const RISK_MEANINGS = {
  red: 'High chance of a harmful algal bloom. Avoid harvesting, selling, or eating shellfish from this area.',
  orange: 'Elevated chance of a bloom. Hold off on non-urgent harvesting and check the latest BFAR bulletin first.',
  yellow: 'Some bloom indicators are present. Harvest with caution and check for updates daily.',
  green: 'Conditions do not point to a bloom. Continue routine monitoring and follow any official advisory.',
};

function getConfidenceExplanation(confidence) {
  const val = parseFloat(confidence);
  if (Number.isNaN(val)) {
    return 'Confidence is not available for this forecast. Treat the risk level as a rough guide.';
  }
  if (val >= 75) {
    return 'The model is fairly sure of this risk level. Conditions can still change, so check before harvesting.';
  }
  if (val >= 60) {
    return 'The model is moderately sure. The risk level could shift, so check again before large harvests.';
  }
  return 'The model is unsure about this risk level. Rely more on local observations and official advisories.';
}

function ForecastSummary({ location, day }) {
  const riskMeaning = RISK_MEANINGS[day.risk_color] || 'Risk level is not available for this area.';
  const dayLabel = day.isToday ? 'today' : formatDayLabel(day.date);

  return (
    <div className="rounded-xl bg-white border border-gray-200/90 px-3.5 py-3 space-y-1.5">
      <p className="text-[13px] text-gray-800 leading-relaxed">
        <span className="font-semibold">For {location.name}, {dayLabel}:</span> {riskMeaning}
      </p>
      <p className="text-xs text-gray-600 leading-relaxed">
        <span className="font-semibold text-gray-800">{day.confidence || 'N/A'} confidence.</span>{' '}
        {getConfidenceExplanation(day.confidence)}
      </p>
    </div>
  );
}

function CollapsibleSection({ title, subtitle, children }) {
  const [isOpen, setIsOpen] = React.useState(false);

  return (
    <div className="mt-4 border-t border-gray-200 pt-3">
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        aria-expanded={isOpen}
        className="w-full flex items-center justify-between gap-3 text-left"
      >
        <span>
          <span className="block text-sm font-bold text-gray-800">{title}</span>
          {subtitle && <span className="block text-[11px] text-gray-600">{subtitle}</span>}
        </span>
        <span className="flex items-center gap-1 text-xs font-semibold text-gray-700 shrink-0">
          {isOpen ? <FiMinus aria-hidden="true" /> : <FiPlus aria-hidden="true" />}
          {isOpen ? 'Hide' : 'Show'}
        </span>
      </button>
      {isOpen && <div className="mt-3">{children}</div>}
    </div>
  );
}

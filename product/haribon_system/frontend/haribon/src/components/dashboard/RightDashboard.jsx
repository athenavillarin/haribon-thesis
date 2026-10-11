import React from 'react';
import { useNavigate } from 'react-router-dom';
import { FiMinus, FiPlus } from 'react-icons/fi';
import RiskIcon from '../RiskIcon';
import { getRiskStyle } from '../riskStyles';

const BFAR_BULLETIN_URL = 'https://www.bfar.da.gov.ph/red-tide-archives/';

export default function RightDashboard({ forecastData, selectedLocation }) {
  const [isSnapshotOpen, setIsSnapshotOpen] = React.useState(false);
  const navigate = useNavigate();

  if (!selectedLocation) {
    return (
      <div className="h-full flex items-center justify-center text-gray-600">
        <p>Select a location from the map or list</p>
      </div>
    );
  }

  const riskStyle = getRiskStyle(selectedLocation.risk_color);
  const metadata = forecastData?.metadata || {};
  const todayStr = metadata.forecast_date || new Date().toLocaleDateString('en-CA');
  const lastUpdated = metadata.last_updated ? new Date(metadata.last_updated) : null;
  const lastUpdatedStr = lastUpdated && !Number.isNaN(lastUpdated.getTime())
    ? lastUpdated.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })
    : null;

  const environmentalData = selectedLocation.environmental_data || {};
  const recommendationItems = selectedLocation?.today_forecast?.recommendations || [];

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
          <p className="text-sm text-gray-600 font-medium">Forecast for {todayStr}</p>
          {lastUpdatedStr && (
            <p className="text-xs text-gray-600 mt-0.5">Updated {lastUpdatedStr}</p>
          )}
        </div>
        <div
          className="px-3 py-1.5 rounded-xl border text-[13px] font-bold flex items-center gap-1.5 shrink-0"
          style={{ backgroundColor: riskStyle.tint, color: riskStyle.ink, borderColor: riskStyle.border }}
        >
          <RiskIcon riskColor={selectedLocation.risk_color} size={18} />
          <span>{selectedLocation.risk_level}</span>
        </div>
      </div>

      {/* Collapsible Harvest Timing & Confidence Note */}
      <HarvestSafetyNotice location={selectedLocation} />

      <hr className="border-gray-100 mb-3" />

      {/* Conditions Grid */}
      <div className="mb-8">
        <h3 className="text-sm font-bold text-gray-800 mb-3">Current Conditions</h3>
        <div className="grid grid-cols-2 gap-2.5">
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
      </div>

      {/* Recommendations */}
      <div>
        <h3 className="text-sm font-bold text-gray-800 mb-3">Recommendations</h3>
        <div className="bg-gray-50 rounded-xl p-4 border border-gray-100">
            <ul className="space-y-2">
            {recommendationItems.length > 0 && recommendationItems.map((text, idx) => (
              <li key={`${selectedLocation.id || 'loc'}-rec-${idx}`} className="text-xs text-gray-600 flex gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-gray-400 mt-1.5 shrink-0"></span>
                {text}
              </li>
            ))}
            {recommendationItems.length === 0 && (
              <>
                {selectedLocation.risk_color === 'red' && (
                    <>
                    <li className="text-xs text-gray-600 flex gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-gray-400 mt-1.5 shrink-0"></span>
                        Severe algal activity detected in the area
                    </li>
                    <li className="text-xs text-gray-600 flex gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-gray-400 mt-1.5 shrink-0"></span>
                        Stop harvesting and selling shellfish immediately
                    </li>
                    <li className="text-xs text-gray-600 flex gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-gray-400 mt-1.5 shrink-0"></span>
                        Avoid swimming and fishing until risk decreases
                    </li>
                    </>
                )}
                 {selectedLocation.risk_color === 'green' && (
                    <>
                    <li className="text-xs text-gray-600 flex gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-gray-400 mt-1.5 shrink-0"></span>
                        Conditions are normal
                    </li>
                    <li className="text-xs text-gray-600 flex gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-gray-400 mt-1.5 shrink-0"></span>
                        Safe for harvesting and recreational activities
                    </li>
                    </>
                )}
                   {selectedLocation.risk_color === 'orange' && (
                    <>
                    <li className="text-xs text-gray-600 flex gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-gray-400 mt-1.5 shrink-0"></span>
                       Elevated risk levels detected
                    </li>
                    <li className="text-xs text-gray-600 flex gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-gray-400 mt-1.5 shrink-0"></span>
                       Limit harvesting and monitor local advisories closely
                    </li>
                    </>
                )}
                   {selectedLocation.risk_color === 'yellow' && (
                    <>
                    <li className="text-xs text-gray-600 flex gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-gray-400 mt-1.5 shrink-0"></span>
                       Mild risk detected
                    </li>
                    <li className="text-xs text-gray-600 flex gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-gray-400 mt-1.5 shrink-0"></span>
                       Harvest with caution and continue regular monitoring
                    </li>
                    </>
                  )}
                  </>
                  )}
            </ul>
          </div>
          <div className="mt-3">
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
        </div>
      </div>

      {/* Snapshot List */}
      <div className="rounded-xl border border-gray-100 bg-[#F3F4F6] p-4 shadow-sm">
        <div className="flex justify-between items-center">
          <h3 className="text-sm font-bold text-gray-800">Today's Snapshot</h3>
          <div className="flex items-center gap-3">
            <span className="text-xs text-gray-600">{todayStr}</span>
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
              {forecastData?.locations?.map(loc => (
                <div
                  key={loc.id}
                  className={`bg-[#F8F9FA] rounded-lg p-3 flex justify-between items-center border transition-colors ${
                    loc.id === selectedLocation.id ? 'border-transparent ring-2 ring-[#3F6D72]' : 'border-transparent hover:border-gray-200'
                  }`}
                >
                  <span className="text-xs font-medium text-gray-700">{loc.name}</span>
                  <span
                    className="text-[11px] font-bold flex items-center gap-1.5"
                    style={{ color: getRiskStyle(loc.risk_color).ink }}
                  >
                    <RiskIcon riskColor={loc.risk_color} size={14} />
                    <span>{loc.risk_level}</span>
                  </span>
                </div>
              ))}
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

function HarvestSafetyNotice({ location }) {
  const [isOpen, setIsOpen] = React.useState(true);

  if (!location) return null;

  const riskStyle = getRiskStyle(location.risk_color);
  const riskMeaning = RISK_MEANINGS[location.risk_color] || 'Risk level is not available for this area.';
  const confidenceInfo = getConfidenceExplanation(location.confidence);

  return (
    <div className="mb-3 rounded-xl border border-gray-200/90 bg-white shadow-[0_1px_3px_rgba(0,0,0,0.03)] overflow-hidden transition-all duration-200">
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        className="w-full px-3.5 py-2.5 flex items-center justify-between gap-2.5 hover:bg-gray-50/80 transition-colors text-left"
        aria-expanded={isOpen}
      >
        <span className="text-xs sm:text-[13px] font-semibold text-gray-800 truncate">
          What this forecast means
        </span>
        <span className="flex items-center gap-1 text-xs font-semibold text-gray-700 shrink-0">
          {isOpen ? <FiMinus aria-hidden="true" /> : <FiPlus aria-hidden="true" />}
          {isOpen ? 'Hide' : 'Show'}
        </span>
      </button>

      {isOpen && (
        <div className="px-3.5 pb-3.5 pt-2 text-xs sm:text-[13px] text-gray-700 border-t border-gray-100 bg-[#F9FAFB]/80 space-y-2.5">
          <div className="flex items-start gap-3">
            <span className="w-32 sm:w-36 shrink-0 font-semibold flex items-center gap-1.5" style={{ color: riskStyle.ink }}>
              <RiskIcon riskColor={location.risk_color} size={16} />
              <span>{location.risk_level || 'Risk level'}</span>
            </span>
            <span className="text-gray-700 leading-relaxed">
              For {location.name}: {riskMeaning}
            </span>
          </div>
          <div className="flex items-start gap-3">
            <span className="w-32 sm:w-36 shrink-0 font-semibold text-gray-900">
              {location.confidence || 'N/A'} confidence
            </span>
            <span className="text-gray-700 leading-relaxed">{confidenceInfo}</span>
          </div>
        </div>
      )}
    </div>
  );
}

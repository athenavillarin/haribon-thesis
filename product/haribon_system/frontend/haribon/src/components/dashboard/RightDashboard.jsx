import React from 'react';
import { useNavigate } from 'react-router-dom';
import { RiskIcon } from '../RiskIcon';

export default function RightDashboard({ forecastData, selectedLocation }) {
  const [isSnapshotOpen, setIsSnapshotOpen] = React.useState(false);
  const navigate = useNavigate();

  if (!selectedLocation) {
    return (
      <div className="h-full flex items-center justify-center text-gray-400">
        <p>Select a location from the map or list</p>
      </div>
    );
  }

  const getRiskBgColor = (color) => {
    switch (color) {
      case 'red': return 'bg-[#E74C3C]';
      case 'orange': return 'bg-[#E67E22]';
      case 'yellow': return 'bg-[#F1C40F]';
      case 'green': return 'bg-[#2ECC71]';
      default: return 'bg-gray-400';
    }
  };

  const todayStr = new Date().toISOString().split('T')[0];

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
      <div className="rounded-xl border border-gray-100 bg-[#F3F4F6] p-5 sm:p-5.5 shadow-sm">
      {/* Location Header */}
      <div className="mb-3 flex justify-between items-start">
        <div>
          <h2 className="text-xl font-bold text-gray-900 leading-tight mb-1">{selectedLocation.name}</h2>
          <p className="text-sm text-gray-500 font-medium">{todayStr}</p>
        </div>
        <div className={`px-4 py-2 rounded-xl text-white text-[13px] font-bold shadow-sm flex items-center gap-2 ${getRiskBgColor(selectedLocation.risk_color)}`}>
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
              href="https://www.bfar.da.gov.ph/?s=Shellfish+Bulletin"
              target="_blank"
              rel="noopener noreferrer"
              className="w-full inline-flex items-center justify-center gap-2 py-2.5 px-4 bg-[#3F6D72] hover:bg-[#32575B] text-white text-xs font-bold rounded-xl shadow-sm transition-colors duration-150 group"
            >
              <span>View Advisories</span>
              <svg
                className="w-3.5 h-3.5 opacity-80 group-hover:opacity-100 transition-opacity"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
            </a>
          </div>
        </div>
      </div>

      {/* Snapshot List */}
      <div className="rounded-xl border border-gray-100 bg-[#F3F4F6] p-4 shadow-sm">
        <div className="flex justify-between items-center">
          <h3 className="text-sm font-bold text-gray-800">Today's Snapshot</h3>
          <div className="flex items-center gap-3">
            <span className="text-xs text-gray-400">{todayStr}</span>
            <button
              type="button"
              onClick={() => setIsSnapshotOpen((open) => !open)}
              className="text-xs font-semibold text-gray-600 hover:text-gray-800 transition-colors"
            >
              {isSnapshotOpen ? 'Hide' : 'Show'}
            </button>
          </div>
        </div>

        {isSnapshotOpen && (
          <div className="mt-4">
            <div className="space-y-2 max-h-[184px] overflow-y-auto pr-1">
              {forecastData?.locations?.map(loc => (
                <div key={loc.id} className="bg-[#F8F9FA] rounded-lg p-3 flex justify-between items-center border border-transparent hover:border-gray-200 transition-colors">
                  <span className="text-xs font-medium text-gray-600">{loc.name}</span>
                  <span className={`text-[11px] font-bold flex items-center gap-1.5 ${
                    loc.risk_color === 'red' ? 'text-red-500' :
                    loc.risk_color === 'orange' ? 'text-orange-500' :
                    loc.risk_color === 'yellow' ? 'text-yellow-500' : 'text-green-500'
                  }`}>
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
      <span className="text-[11px] text-gray-500 font-semibold leading-snug">
        {label}
      </span>
      <div className="flex items-baseline gap-1 mt-1 text-left">
        <span className="text-lg font-bold text-gray-900 tracking-tight leading-none">{value}</span>
        {unit && <span className="text-[11px] font-semibold text-gray-400">{unit}</span>}
      </div>
    </div>
  );
}

function HarvestSafetyNotice({ location }) {
  const [isOpen, setIsOpen] = React.useState(false);

  if (!location) return null;

  const getRiskExplanation = (riskColor) => {
    switch (riskColor) {
      case 'red':
        return {
          meaning: 'Severe bloom conditions detected. Shellfish harvesting and consumption are strictly unsafe.',
          badgeColor: 'text-red-700 bg-red-50 border-red-200',
        };
      case 'orange':
        return {
          meaning: 'Elevated bloom threat. Delay non-urgent harvesting and verify local BFAR advisories.',
          badgeColor: 'text-amber-800 bg-amber-50 border-amber-200',
        };
      case 'yellow':
        return {
          meaning: 'Mild bloom markers observed. Harvesting is viable with caution—continue checking daily updates.',
          badgeColor: 'text-yellow-800 bg-yellow-50 border-yellow-200',
        };
      case 'green':
      default:
        return {
          meaning: 'Clean ocean conditions. Optimum window for safe shellfish harvesting and coastal activities.',
          badgeColor: 'text-emerald-800 bg-emerald-50 border-emerald-200',
        };
    }
  };

  const getConfidenceExplanation = (confidenceStr) => {
    const val = parseFloat(confidenceStr) || 75;
    if (val >= 75) {
      return 'High model certainty from sea sensors and satellite data. Dependable for scheduling harvest activities.';
    }
    if (val >= 60) {
      return 'Moderate model certainty. Weather or marine shifts may alter risk—verify before making large harvest commitments.';
    }
    return 'Developing certainty due to shifting oceanic variables. Re-verify daily with local observations.';
  };

  const riskInfo = getRiskExplanation(location.risk_color);
  const confidenceInfo = getConfidenceExplanation(location.confidence);

  return (
    <div className="mb-3 rounded-xl border border-gray-200/90 bg-white shadow-[0_1px_3px_rgba(0,0,0,0.03)] overflow-hidden transition-all duration-200">
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        className="w-full px-3.5 py-2.5 flex items-center justify-between gap-2.5 hover:bg-gray-50/80 transition-colors text-left"
        aria-expanded={isOpen}
      >
        <div className="flex items-center gap-2 min-w-0">
          <div className="w-5 h-5 rounded-full bg-[#3F6D72]/10 text-[#3F6D72] flex items-center justify-center shrink-0">
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <span className="text-xs sm:text-[13px] font-semibold text-gray-800 truncate">
            Harvest Timing & Confidence Guide
          </span>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full border flex items-center gap-1.5 ${riskInfo.badgeColor}`}>
            <RiskIcon riskColor={location.risk_color} size={14} />
            <span>{location.confidence || 'Forecast'}</span>
          </span>
          <svg
            className={`w-4 h-4 text-gray-400 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      {isOpen && (
        <div className="px-3.5 pb-3.5 pt-2 text-xs sm:text-[13px] text-gray-700 border-t border-gray-100 bg-[#F9FAFB]/80 space-y-2.5">
          <div className="flex items-start gap-3">
            <span className="w-32 sm:w-36 shrink-0 font-semibold text-gray-900 flex items-center gap-1.5">
              <RiskIcon riskColor={location.risk_color} size={16} />
              <span>{location.risk_level || 'Risk Level'}:</span>
            </span>
            <span className="text-gray-600 leading-relaxed">{riskInfo.meaning}</span>
          </div>
          <div className="flex items-start gap-3">
            <span className="w-32 sm:w-36 shrink-0 font-semibold text-gray-900">
              Confidence ({location.confidence || 'N/A'}):
            </span>
            <span className="text-gray-600 leading-relaxed">{confidenceInfo}</span>
          </div>
        </div>
      )}
    </div>
  );
}
import React from 'react';
import { useNavigate } from 'react-router-dom';

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

  const conditionItems = [];

  Object.entries(environmentalData).forEach(([key, value]) => {
    conditionItems.push({ label: key, value });
  });

  if (conditionItems.length === 0) {
    conditionItems.push({ label: 'No environmental data', value: 'N/A' });
  }

  return (
    <div className="h-full font-quicksand flex flex-col gap-4">
      <div className="rounded-xl border border-gray-100 bg-[#F3F4F6] p-6 shadow-sm">
      {/* Location Header */}
      <div className="mb-3 flex justify-between items-start">
        <div>
          <h2 className="text-xl font-bold text-gray-900 leading-tight mb-1">{selectedLocation.name}</h2>
          <p className="text-sm text-gray-500 font-medium">{todayStr}</p>
        </div>
        <div className={`px-4 py-1.5 rounded-lg text-white text-xs font-bold shadow-sm ${getRiskBgColor(selectedLocation.risk_color)}`}>
          {selectedLocation.risk_level}
        </div>
      </div>

      <hr className="border-gray-100 mb-3" />

      {/* Conditions Grid */}
      <div className="mb-8">
        <h3 className="text-sm font-bold text-gray-800 mb-4">Conditions Contributing to Risk</h3>
        <div className="grid grid-cols-2 gap-3">
            {conditionItems.map((item) => (
              <MetricItem
                key={item.label}
                label={item.label}
                value={item.value}
                isFullWidth={conditionItems.length % 2 === 1 && item === conditionItems[conditionItems.length - 1]}
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
          <div className="space-y-2 mt-4">
            {forecastData?.locations?.slice(0, 5).map(loc => (
              <div key={loc.id} className="bg-[#F8F9FA] rounded-lg p-3 flex justify-between items-center border border-transparent hover:border-gray-200 transition-colors">
                <span className="text-xs font-medium text-gray-600">{loc.name}</span>
                <span className={`text-[10px] font-bold ${
                  loc.risk_color === 'red' ? 'text-red-500' :
                  loc.risk_color === 'orange' ? 'text-orange-500' :
                  loc.risk_color === 'yellow' ? 'text-yellow-500' : 'text-green-500'
                }`}>
                  {loc.risk_level}
                </span>
              </div>
            ))}
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

function MetricItem({ label, value, isFullWidth }) {
    const valStr = String(value || "");
    const cleanValue = valStr ? valStr.replace(" mg/m3", "").replace(" °C", "").replace(" PSU", "").replace(" m/s", "") : "N/A";

    return (
        <div className={`bg-[#F8F9FA] rounded-lg p-3 flex justify-between items-center ${isFullWidth ? 'col-span-2' : ''}`}>
            <span className="text-xs text-gray-500 font-medium">{label}</span>
            <span className="text-xs font-bold text-gray-800">{cleanValue}</span>
        </div>
    )
}
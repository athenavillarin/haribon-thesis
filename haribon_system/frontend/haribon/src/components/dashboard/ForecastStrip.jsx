import React from 'react';
import { FiRefreshCw } from 'react-icons/fi';
import { FiChevronLeft } from 'react-icons/fi';
import { FiChevronRight } from 'react-icons/fi';

export default function ForecastStrip({ forecastData, selectedLocation, onRefresh }) {
  const [refreshing, setRefreshing] = React.useState(false);
  const [startIndex, setStartIndex] = React.useState(0);
  const visibleCount = 5;

  const outlook = selectedLocation?.five_day_outlook || [];
  const hasYesterdayCard =
    outlook[0]?.label === 'Yesterday'
    || outlook[0]?.day === 'Yesterday'
    || outlook[0]?.is_historical === true;
  const maxStartIndex = Math.max(0, outlook.length - visibleCount);
  const visibleOutlook = outlook.slice(startIndex, startIndex + visibleCount);

  React.useEffect(() => {
    setStartIndex(hasYesterdayCard ? 1 : 0);
  }, [selectedLocation?.id, hasYesterdayCard]);

  React.useEffect(() => {
    setStartIndex((prev) => Math.min(prev, maxStartIndex));
  }, [maxStartIndex]);

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await onRefresh();
    } finally {
      setRefreshing(false);
    }
  };

  if (!selectedLocation || !selectedLocation.five_day_outlook) return null;

  const canMoveLeft = startIndex > 0;
  const canMoveRight = startIndex < maxStartIndex;

  const handleMoveLeft = () => {
    if (!canMoveLeft) return;
    setStartIndex((prev) => Math.max(prev - 1, 0));
  };

  const handleMoveRight = () => {
    if (!canMoveRight) return;
    setStartIndex((prev) => Math.min(prev + 1, maxStartIndex));
  };

  return (
    <div className="mb-2">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-xl font-bold text-gray-800">Red Tide Risk Forecast</h2>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center gap-2 bg-white text-gray-600 border border-gray-200 px-4 py-2 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 text-sm font-medium shadow-sm"
        >
          <FiRefreshCw className={`${refreshing ? 'animate-spin' : ''}`} />
          {refreshing ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      <div className="relative">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-5 gap-4">
          {visibleOutlook.map((day, index) => (
            <ForecastCard
              key={`${day.date || 'forecast'}-${startIndex + index}`}
              data={day}
              locationName={selectedLocation.name}
              isSelected={startIndex + index === 0}
            />
          ))}
        </div>

        <button
          onClick={handleMoveLeft}
          disabled={!canMoveLeft}
          aria-label="Show previous forecast day"
          className="absolute -left-8 top-1/2 -translate-y-1/2 p-2 text-gray-600 transition-colors hover:text-gray-800 disabled:opacity-35 disabled:cursor-not-allowed z-20"
        >
          <FiChevronLeft size={24} />
        </button>

        <button
          onClick={handleMoveRight}
          disabled={!canMoveRight}
          aria-label="Show next forecast day"
          className="absolute -right-8 top-1/2 -translate-y-1/2 p-2 text-gray-600 transition-colors hover:text-gray-800 disabled:opacity-35 disabled:cursor-not-allowed z-20"
        >
          <FiChevronRight size={24} />
        </button>
      </div>
    </div>
  );
}

function ForecastCard({ data, locationName, isSelected }) {
  const getRiskColor = (color) => {
    switch (color) {
      case 'green': return 'text-[#2ECC71]'; // Haribon Green
      case 'yellow': return 'text-[#F1C40F]'; // Haribon Yellow
      case 'orange': return 'text-[#E67E22]'; // Haribon Orange
      case 'red': return 'text-[#E74C3C]'; // Haribon Red
      default: return 'text-gray-400';
    }
  };

  const getRiskAction = (color) => {
    switch (color) {
      case 'red':
        return 'No Harvesting';
      case 'orange':
        return 'Limit Harvesting';
      case 'yellow':
        return 'Proceed with Caution';
      case 'green':
        return 'Safe to Harvest';
      default:
        return 'Monitor Conditions';
    }
  };

  // Parse date to easier format
  const dateObj = new Date(data.date);
  const formattedDate = dateObj.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });

  return (
    <div className="bg-[#F3F4F6] rounded-2xl p-5 flex flex-col justify-between h-[160px] cursor-default transition-all duration-200 border-2 border-transparent">
      <div className="flex justify-between items-start">
        <div>
          <h3 className="font-bold text-gray-800 text-base mb-1">{formattedDate}</h3>
          <p className="text-gray-500 text-xs font-medium">{locationName}</p>
        </div>
      </div>

      <div className="flex justify-between items-end mt-4">
        <div>
          <div className="text-2xl font-bold text-gray-800 mb-0.5">{data.confidence}</div>
          <div className="text-[10px] text-gray-400 uppercase tracking-wide font-semibold">confidence level</div>
        </div>
        <div className="text-right">
          <div className={`font-bold text-sm mb-0.5 ${getRiskColor(data.risk_color)}`}>
            {data.risk_level}
          </div>
           <div className="text-[10px] font-bold text-[#3C6468] opacity-80">
             {getRiskAction(data.risk_color)}
          </div>
        </div>
      </div>
    </div>
  );
}

import React from 'react';
import { FiRefreshCw } from 'react-icons/fi';
import { FiChevronLeft } from 'react-icons/fi';
import { FiChevronRight } from 'react-icons/fi';

export default function ForecastStrip({ forecastData, selectedLocation, onRefresh }) {
  const [refreshing, setRefreshing] = React.useState(false);
  const [startIndex, setStartIndex] = React.useState(0);
  const [isMobileView, setIsMobileView] = React.useState(() =>
    typeof window !== 'undefined' ? window.innerWidth < 768 : false
  );

  React.useEffect(() => {
    if (typeof window === 'undefined') return;

    const mediaQuery = window.matchMedia('(max-width: 767px)');
    const handleChange = (event) => {
      setIsMobileView(event.matches);
    };

    setIsMobileView(mediaQuery.matches);

    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handleChange);
      return () => mediaQuery.removeEventListener('change', handleChange);
    }

    mediaQuery.addListener(handleChange);
    return () => mediaQuery.removeListener(handleChange);
  }, []);

  const outlook = selectedLocation?.five_day_outlook || [];
  const hasYesterdayCard =
    outlook[0]?.label === 'Yesterday'
    || outlook[0]?.day === 'Yesterday'
    || outlook[0]?.is_historical === true;
  const visibleCount = isMobileView ? outlook.length : 5;
  const maxStartIndex = Math.max(0, outlook.length - visibleCount);
  const visibleOutlook = isMobileView
    ? outlook
    : outlook.slice(startIndex, startIndex + visibleCount);

  React.useEffect(() => {
    setStartIndex(isMobileView ? 0 : (hasYesterdayCard ? 1 : 0));
  }, [selectedLocation?.id, hasYesterdayCard, isMobileView]);

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
      <div className="flex justify-between items-center mb-4 sm:mb-6 gap-3">
        <div>
          <h2 className="text-xl font-bold text-gray-800">Red Tide Risk Forecast</h2>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="inline-flex h-12 w-16 sm:h-auto sm:w-auto items-center justify-center gap-2 bg-white text-gray-600 border border-gray-200 px-3 sm:px-4 py-2 rounded-xl hover:bg-gray-50 transition-colors disabled:opacity-50 text-sm font-medium shadow-sm"
        >
          <FiRefreshCw className={`${refreshing ? 'animate-spin' : ''}`} />
          <span className="hidden sm:inline">{refreshing ? 'Refreshing...' : 'Refresh'}</span>
        </button>
      </div>

      <div className="relative">
        <div className="flex gap-3 overflow-x-auto pb-1 pr-1 snap-x snap-mandatory md:grid md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-5 md:gap-4 md:overflow-visible">
          {visibleOutlook.map((day, index) => (
            <div key={`${day.date || 'forecast'}-${startIndex + index}`} className="w-[230px] shrink-0 snap-start md:w-auto md:shrink md:snap-none">
              <ForecastCard
              data={day}
              locationName={selectedLocation.name}
              isSelected={startIndex + index === 0}
              />
            </div>
          ))}
        </div>

        <button
          onClick={handleMoveLeft}
          disabled={!canMoveLeft}
          aria-label="Show previous forecast day"
          className="hidden md:block absolute -left-8 top-1/2 -translate-y-1/2 p-2 text-gray-600 transition-colors hover:text-gray-800 disabled:opacity-35 disabled:cursor-not-allowed z-20"
        >
          <FiChevronLeft size={24} />
        </button>

        <button
          onClick={handleMoveRight}
          disabled={!canMoveRight}
          aria-label="Show next forecast day"
          className="hidden md:block absolute -right-8 top-1/2 -translate-y-1/2 p-2 text-gray-600 transition-colors hover:text-gray-800 disabled:opacity-35 disabled:cursor-not-allowed z-20"
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
    <div className="bg-[#F3F4F6] rounded-2xl p-5 flex flex-col justify-between h-[160px] cursor-default transition-all duration-200 border border-gray-200/80">
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

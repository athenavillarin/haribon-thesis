const isTodayEntry = (day) => day?.label === 'Today' || day?.day === 'Today';

export function getTodayDate(location) {
  return (location?.five_day_outlook || []).find(isTodayEntry)?.date || null;
}

// Risk for one location on a given date; falls back to today's values when the date is missing.
export function getDayForecast(location, date) {
  const today = {
    date: getTodayDate(location),
    risk_level: location?.risk_level,
    risk_color: location?.risk_color,
    confidence: location?.confidence,
    isToday: true,
  };
  if (!date || date === today.date) return today;

  const day = (location?.five_day_outlook || []).find((entry) => entry.date === date);
  if (!day) return today;

  return {
    date: day.date,
    risk_level: day.risk_level,
    risk_color: day.risk_color,
    confidence: day.confidence,
    isToday: false,
  };
}

export function formatDayLabel(date) {
  const parsed = new Date(`${date}T00:00:00`);
  if (Number.isNaN(parsed.getTime())) return date;
  return parsed.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
}

import React from 'react';
import { FiSearch, FiX } from 'react-icons/fi';
import RiskIcon from '../RiskIcon';
import { getRiskStyle } from '../riskStyles';
import { getDayForecast } from './forecastDay';

export default function MapSearch({ locations, selectedDate, onSelect }) {
  const [query, setQuery] = React.useState('');
  const [isOpen, setIsOpen] = React.useState(false);
  const [activeIndex, setActiveIndex] = React.useState(0);
  const listId = React.useId();

  const normalized = query.trim().toLowerCase();
  const matches = (locations || []).filter((loc) => loc.name.toLowerCase().includes(normalized));

  const choose = (location) => {
    onSelect(location);
    setQuery(location.name);
    setIsOpen(false);
  };

  const handleKeyDown = (event) => {
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      setIsOpen(true);
      setActiveIndex((prev) => Math.min(prev + 1, matches.length - 1));
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      setActiveIndex((prev) => Math.max(prev - 1, 0));
    } else if (event.key === 'Enter') {
      if (isOpen && matches[activeIndex]) {
        event.preventDefault();
        choose(matches[activeIndex]);
      }
    } else if (event.key === 'Escape') {
      setIsOpen(false);
    }
  };

  return (
    <div className="relative">
      <div className="flex items-center gap-2 bg-white/95 backdrop-blur-sm rounded-xl shadow-lg border border-gray-100 px-3 py-2 focus-within:ring-2 focus-within:ring-[#3F6D72]/60">
        <FiSearch className="text-gray-500 shrink-0" aria-hidden="true" />
        <input
          type="text"
          role="combobox"
          aria-label="Search for a bay"
          aria-expanded={isOpen}
          aria-controls={listId}
          aria-autocomplete="list"
          aria-activedescendant={isOpen && matches[activeIndex] ? `${listId}-${matches[activeIndex].id}` : undefined}
          placeholder="Search for a bay"
          value={query}
          onChange={(event) => {
            setQuery(event.target.value);
            setActiveIndex(0);
            setIsOpen(true);
          }}
          onFocus={() => setIsOpen(true)}
          onBlur={() => setIsOpen(false)}
          onKeyDown={handleKeyDown}
          className="w-full bg-transparent text-sm text-gray-800 placeholder:text-gray-500 focus:outline-none"
        />
        {query && (
          <button
            type="button"
            aria-label="Clear search"
            onMouseDown={(event) => event.preventDefault()}
            onClick={() => {
              setQuery('');
              setActiveIndex(0);
            }}
            className="text-gray-500 hover:text-gray-800"
          >
            <FiX aria-hidden="true" />
          </button>
        )}
      </div>

      {isOpen && (
        <ul
          id={listId}
          role="listbox"
          className="absolute left-0 right-0 top-full z-10 mt-1.5 max-h-64 overflow-y-auto bg-white rounded-xl shadow-lg border border-gray-100 py-1"
        >
          {matches.length === 0 && (
            <li className="px-3 py-2 text-sm text-gray-600">No matching bay</li>
          )}
          {matches.map((loc, idx) => {
            const day = getDayForecast(loc, selectedDate);
            return (
              <li
                key={loc.id}
                id={`${listId}-${loc.id}`}
                role="option"
                aria-selected={idx === activeIndex}
                onMouseDown={(event) => event.preventDefault()}
                onMouseEnter={() => setActiveIndex(idx)}
                onClick={() => choose(loc)}
                className={`px-3 py-2 flex items-center justify-between gap-3 cursor-pointer text-sm ${
                  idx === activeIndex ? 'bg-gray-100' : ''
                }`}
              >
                <span className="text-gray-800">{loc.name}</span>
                <span
                  className="flex items-center gap-1 text-[11px] font-bold shrink-0"
                  style={{ color: getRiskStyle(day.risk_color).ink }}
                >
                  <RiskIcon riskColor={day.risk_color} size={14} />
                  {day.risk_level}
                </span>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}

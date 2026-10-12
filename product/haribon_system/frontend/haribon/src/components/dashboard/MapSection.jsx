import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import RiskIcon from '../RiskIcon';
import { getRiskSvgString, getRiskStyle, SELECTED_ACCENT } from '../riskStyles';
import { getDayForecast, formatDayLabel } from './forecastDay';

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

export default function MapSection({ forecastData, selectedLocation, selectedDate, onLocationSelect }) {
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const markersRef = useRef(new Map());

  useEffect(() => {
    if (!mapRef.current || mapInstanceRef.current) return;

    const map = L.map(mapRef.current, {
        zoomControl: false
    }).setView([11.5, 122.5], 9);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap</a> contributors',
      maxZoom: 19
    }).addTo(map);
    L.control.zoom({ position: 'topright' }).addTo(map);

    mapInstanceRef.current = map;

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    if (!mapRef.current || !mapInstanceRef.current) return;

    const observer = new ResizeObserver(() => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.invalidateSize({ animate: false });
      }
    });

    observer.observe(mapRef.current);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!mapInstanceRef.current || !forecastData?.locations) return;

    const map = mapInstanceRef.current;

    markersRef.current.forEach(({ marker }) => map.removeLayer(marker));
    markersRef.current = new Map();

    // Markers for each location
    forecastData.locations.forEach(location => {
      const marker = L.marker([location.coordinates.lat, location.coordinates.lng], {
        icon: buildPinIcon(location.risk_color, false),
      })
        .addTo(map)
        .bindTooltip('', {
          className: 'haribon-hover-popup',
          direction: 'bottom',
          offset: [0, 20],
          opacity: 1,
          interactive: false,
          sticky: false,
        });

      // Click handler
      marker.on('click', () => {
        onLocationSelect(location);
      });

      markersRef.current.set(location.id, { marker, location });
    });

    // Fit map to show all markers
    if (markersRef.current.size > 0) {
      const group = new L.featureGroup([...markersRef.current.values()].map(({ marker }) => marker));
      map.fitBounds(group.getBounds().pad(0.1));
    }
  }, [forecastData, onLocationSelect]);

  // Restyle pins on selection without rebuilding them, so the map keeps the user's zoom and position.
  useEffect(() => {
    markersRef.current.forEach(({ marker, location }, id) => {
      const isSelected = selectedLocation?.id === id;
      const day = getDayForecast(location, selectedDate);
      marker.setIcon(buildPinIcon(day.risk_color, isSelected));
      marker.setTooltipContent(buildPopupHtml(location, day));
      marker.setZIndexOffset(isSelected ? 1000 : 0);
    });
  }, [forecastData, selectedLocation?.id, selectedDate]);

  return (
    <div className="h-full w-full relative">
      <div ref={mapRef} className="h-full w-full rounded-xl overflow-hidden" />
      <div className="hidden sm:block absolute top-4 left-4 bg-white/95 backdrop-blur-sm rounded-xl p-3.5 shadow-lg border border-gray-100 z-[1000]">
        <h3 className="font-bold text-gray-800 text-xs uppercase tracking-wider mb-0.5">Risk Levels</h3>
        <p className="text-[11px] font-semibold text-[#3F6D72] mb-2.5">
          {selectedLocation && getDayForecast(selectedLocation, selectedDate).isToday ? 'Today' : formatDayLabel(selectedDate)}
        </p>
        <div className="space-y-2 text-[13px] font-semibold">
          <div className="flex items-center gap-2" style={{ color: getRiskStyle('green').ink }}>
            <RiskIcon riskColor="green" size={18} />
            <span className="text-gray-800 font-medium">Very Low Risk</span>
          </div>
          <div className="flex items-center gap-2" style={{ color: getRiskStyle('yellow').ink }}>
            <RiskIcon riskColor="yellow" size={18} />
            <span className="text-gray-800 font-medium">Low Risk</span>
          </div>
          <div className="flex items-center gap-2" style={{ color: getRiskStyle('orange').ink }}>
            <RiskIcon riskColor="orange" size={18} />
            <span className="text-gray-800 font-medium">Moderate Risk</span>
          </div>
          <div className="flex items-center gap-2" style={{ color: getRiskStyle('red').ink }}>
            <RiskIcon riskColor="red" size={18} />
            <span className="text-gray-800 font-medium">High Risk</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function buildPinIcon(riskColor, isSelected) {
  const { fill } = getRiskStyle(riskColor);
  const pinSize = isSelected ? 54 : 46;
  const halo = isSelected
    ? `<circle cx="12" cy="9" r="10.5" fill="${SELECTED_ACCENT}" fill-opacity="0.18" stroke="${SELECTED_ACCENT}" stroke-width="2" />`
    : '';

  return L.divIcon({
    className: 'custom-pin-icon',
    html: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="-3 -3 30 30" width="${pinSize}px" height="${pinSize}px" style="filter: drop-shadow(0 3px 6px rgba(0,0,0,0.4)); display: block; overflow: visible;">
             ${halo}
             <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z" fill="${fill}" stroke="#FFFFFF" stroke-width="2.4" stroke-linejoin="round" stroke-linecap="round" />
             <circle cx="12" cy="9" r="3" fill="#FFFFFF"/>
             <circle cx="12" cy="9" r="1.5" fill="${fill}"/>
           </svg>`,
    iconSize: [pinSize, pinSize],
    iconAnchor: [pinSize / 2, pinSize],
    popupAnchor: [0, 12]
  });
}

function getRiskMessage(location, day) {
  const recs = day.isToday ? location?.today_forecast?.recommendations || [] : [];
  if (recs.length > 0) {
    return recs[0];
  }

  switch (day.risk_color) {
    case 'red':
      return 'High algal activity detected. Monitor conditions closely and avoid harvesting or selling seafood.';
    case 'orange':
      return 'Elevated risk detected. Limit harvesting and monitor local advisories closely.';
    case 'yellow':
      return 'Mild risk detected. Harvest with caution and continue regular monitoring.';
    default:
      return 'Conditions are favorable. Continue routine monitoring.';
  }
}

function buildPopupHtml(location, day) {
  const { ink, tint, border } = getRiskStyle(day.risk_color);
  const dayLabel = day.isToday ? 'Today' : formatDayLabel(day.date);

  return `
    <div class="haribon-hover-popup-card">
      <p class="haribon-popup-overline">coastal waters of</p>
      <h3 class="haribon-popup-title">${location.name}</h3>
      <div class="haribon-popup-risk" style="background-color: ${tint}; color: ${ink}; border: 1px solid ${border}; display: inline-flex; align-items: center; gap: 6px; font-size: 13px;">
        ${getRiskSvgString(day.risk_color, 16)}
        <span>${day.risk_level} · ${dayLabel}</span>
      </div>
      <p class="haribon-popup-message">${getRiskMessage(location, day)}</p>
    </div>
  `;
}

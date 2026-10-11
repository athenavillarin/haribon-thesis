import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { RiskIcon, getRiskSvgString } from '../RiskIcon';

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

export default function MapSection({ forecastData, selectedLocation, onLocationSelect }) {
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const markersRef = useRef([]);
  const tileLayerRef = useRef(null);

  const getRiskMessage = (location) => {
    const recs = location?.today_forecast?.recommendations || [];
    if (recs.length > 0) {
      return recs[0];
    }

    switch (location?.risk_color) {
      case 'red':
        return 'High algal activity detected. Monitor conditions closely and avoid harvesting or selling seafood.';
      case 'orange':
        return 'Elevated risk detected. Limit harvesting and monitor local advisories closely.';
      case 'yellow':
        return 'Mild risk detected. Harvest with caution and continue regular monitoring.';
      default:
        return 'Conditions are favorable. Continue routine monitoring.';
    }
  };

  useEffect(() => {
    if (!mapRef.current) return;

    if (!mapInstanceRef.current) {
      const map = L.map(mapRef.current, {
        zoomControl: false,
      }).setView([11.5, 122.5], 9);
      L.control.zoom({ position: 'topright' }).addTo(map);
      mapInstanceRef.current = map;
    }

    const map = mapInstanceRef.current;

    // Remove existing tile layer if present so new minimalist basemap attaches immediately
    if (tileLayerRef.current) {
      map.removeLayer(tileLayerRef.current);
    }

    // Standard OpenStreetMap tiles (100% free, public, no API key required)
    // The CSS filter in index.css automatically desaturates and softens the tiles to remove clutter
    const newTileLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap</a> contributors',
      maxZoom: 19,
    }).addTo(map);
    tileLayerRef.current = newTileLayer;

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
        tileLayerRef.current = null;
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

    markersRef.current.forEach(marker => map.removeLayer(marker));
    markersRef.current = [];

    // Vivid, high-saturation colors for crisp contrast against the clean map
    const getPinColor = (riskColor) => {
      switch (riskColor) {
        case 'red': return '#EF233C';    // Vivid high-saturation ruby red
        case 'orange': return '#FF6B00'; // Pure saturated warm orange
        case 'yellow': return '#FFB703'; // Saturated amber gold
        case 'green': return '#00C853';  // Vivid saturated emerald green
        default: return '#64748B';
      }
    };

    // Markers for each location
    forecastData.locations.forEach(location => {
      const pinColor = getPinColor(location.risk_color);
      const isSelected = selectedLocation?.id === location.id;
      const pinSize = isSelected ? 52 : 46;
      
      const customIcon = L.divIcon({
        className: 'custom-pin-icon',
        html: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="-3 -3 30 30" width="${pinSize}px" height="${pinSize}px" style="filter: drop-shadow(0 3px 6px rgba(0,0,0,0.4)); display: block; overflow: visible; transform: ${isSelected ? 'scale(1.12)' : 'scale(1)'}; transition: transform 0.2s ease;">
                 <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z" fill="${pinColor}" stroke="#FFFFFF" stroke-width="2.4" stroke-linejoin="round" stroke-linecap="round" />
                 <circle cx="12" cy="9" r="3" fill="#FFFFFF"/>
                 <circle cx="12" cy="9" r="1.5" fill="${pinColor}"/>
               </svg>`,
        iconSize: [pinSize, pinSize],
        iconAnchor: [pinSize / 2, pinSize],
        popupAnchor: [0, 12]
      });

      const popupHtml = `
        <div class="haribon-hover-popup-card">
          <p class="haribon-popup-overline">coastal waters of</p>
          <h3 class="haribon-popup-title">${location.name}</h3>
          <div class="haribon-popup-risk" style="background-color: ${pinColor}; display: inline-flex; align-items: center; gap: 6px; font-size: 13px;">
            ${getRiskSvgString(location.risk_color, 16)}
            <span>${location.risk_level}</span>
          </div>
          <p class="haribon-popup-message">${getRiskMessage(location)}</p>
        </div>
      `;

      const marker = L.marker([location.coordinates.lat, location.coordinates.lng], { icon: customIcon })
        .addTo(map)
        .bindTooltip(popupHtml, {
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

      markersRef.current.push(marker);
    });

    // Fit map to show all markers
    if (markersRef.current.length > 0) {
      const group = new L.featureGroup(markersRef.current);
      map.fitBounds(group.getBounds().pad(0.1));
    }
  }, [forecastData, selectedLocation, onLocationSelect]);

  return (
    <div className="h-full w-full relative">
      <div ref={mapRef} className="h-full w-full rounded-xl overflow-hidden" />
      <div className="hidden sm:block absolute top-4 left-4 bg-white/95 backdrop-blur-sm rounded-xl p-3.5 shadow-lg border border-gray-100 z-[1000]">
        <h3 className="font-bold text-gray-800 text-xs uppercase tracking-wider mb-2.5">Risk Levels</h3>
        <div className="space-y-2 text-[13px] font-semibold">
          <div className="flex items-center gap-2 text-[#00C853]">
            <RiskIcon riskColor="green" size={18} />
            <span className="text-gray-800 font-medium">Very Low Risk</span>
          </div>
          <div className="flex items-center gap-2 text-[#FFB703]">
            <RiskIcon riskColor="yellow" size={18} />
            <span className="text-gray-800 font-medium">Low Risk</span>
          </div>
          <div className="flex items-center gap-2 text-[#FF6B00]">
            <RiskIcon riskColor="orange" size={18} />
            <span className="text-gray-800 font-medium">Moderate Risk</span>
          </div>
          <div className="flex items-center gap-2 text-[#EF233C]">
            <RiskIcon riskColor="red" size={18} />
            <span className="text-gray-800 font-medium">High Risk</span>
          </div>
        </div>
      </div>
    </div>
  );
}
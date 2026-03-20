import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

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
    if (!mapRef.current || mapInstanceRef.current) return;

    const map = L.map(mapRef.current, {
        zoomControl: false,
        attributionControl: false
    }).setView([11.5, 122.5], 9);

    L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
      attribution: '© OpenStreetMap contributors, © CARTO',
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

    markersRef.current.forEach(marker => map.removeLayer(marker));
    markersRef.current = [];

    const getPinColor = (riskColor) => {
      switch (riskColor) {
        case 'red': return '#E74C3C';
        case 'orange': return '#E67E22';
        case 'yellow': return '#F1C40F';
        case 'green': return '#2ECC71';
        default: return '#7A8B90';
      }
    };

    // Markers for each location
    forecastData.locations.forEach(location => {
      const pinColor = getPinColor(location.risk_color);
      
      const customIcon = L.divIcon({
        className: 'custom-pin-icon',
        html: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="${pinColor}" width="40px" height="40px" stroke="white" stroke-width="2" style="filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3)); display: block;">
                 <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/>
                 <circle cx="12" cy="9" r="2.5" fill="white"/>
               </svg>`,
        iconSize: [40, 40],
        iconAnchor: [20, 40],
        popupAnchor: [0, 12]
      });

      const popupHtml = `
        <div class="haribon-hover-popup-card">
          <p class="haribon-popup-overline">coastal waters of</p>
          <h3 class="haribon-popup-title">${location.name}</h3>
          <div class="haribon-popup-risk" style="background-color: ${pinColor}">${location.risk_level}</div>
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
  }, [forecastData, onLocationSelect]);

  return (
    <div className="h-full w-full relative">
      <div ref={mapRef} className="h-full w-full rounded-xl overflow-hidden" />
      <div className="absolute top-4 left-4 bg-white/90 backdrop-blur-sm rounded-lg p-3 shadow-lg z-[1000]">
        <h3 className="font-semibold text-gray-800 mb-2">Risk Levels</h3>
        <div className="space-y-1 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-[#2ECC71]"></div>
            <span>Very Low Risk</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-[#F1C40F]"></div>
            <span>Low Risk</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-[#E67E22]"></div>
            <span>Moderate Risk</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-[#E74C3C]"></div>
            <span>High Risk</span>
          </div>
        </div>
      </div>
    </div>
  );
}
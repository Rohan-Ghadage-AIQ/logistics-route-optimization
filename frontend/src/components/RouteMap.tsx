import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { RouteItem, RouteStopDetail } from '../types';
import { Layers } from 'lucide-react';

const ROUTE_COLORS = [
  '#d97706', '#2563eb', '#059669', '#dc2626', '#7c3aed',
  '#0891b2', '#ea580c', '#4f46e5', '#16a34a', '#db2777',
];

interface RouteMapProps {
  routes: RouteItem[];
  selectedRouteId: string | null;
  onRouteSelect: (routeId: string) => void;
  onStopSelect?: (stop: RouteStopDetail, routeId: string) => void;
}

const TILE_LAYERS = {
  light: 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',
  osm: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
  dark: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
  satellite: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
};

function getOrdinal(n: number): string {
  const s = ['th', 'st', 'nd', 'rd'];
  const v = n % 100;
  return n + (s[(v - 20) % 10] || s[v] || s[0]);
}

function createStopIcon(color: string, sequence: number, isLate: boolean = false) {
  const badgeColor = isLate ? '#ef4444' : color;
  const pulseClass = isLate ? 'ring-2 ring-red-400 animate-bounce' : '';

  return L.divIcon({
    className: 'custom-stop-marker',
    html: `
      <div style="
        display: flex;
        align-items: center;
        justify-content: center;
        width: 26px;
        height: 26px;
        border-radius: 50%;
        background-color: ${badgeColor};
        color: #ffffff;
        font-weight: 800;
        font-size: 11px;
        border: 2px solid #ffffff;
        box-shadow: 0 2px 6px rgba(0,0,0,0.35);
        cursor: pointer;
        font-family: Inter, sans-serif;
      " class="${pulseClass}">
        ${sequence}
      </div>
    `,
    iconSize: [26, 26],
    iconAnchor: [13, 13],
    popupAnchor: [0, -14],
  });
}

function createHubIcon(label: string = 'HUB') {
  return L.divIcon({
    className: 'custom-hub-marker',
    html: `
      <div style="
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        background: #0f172a;
        color: #f59e0b;
        border: 2px solid #f59e0b;
        border-radius: 8px;
        padding: 4px 8px;
        font-weight: 800;
        font-size: 11px;
        letter-spacing: 0.5px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.4);
        cursor: pointer;
        font-family: Inter, sans-serif;
        white-space: nowrap;
      ">
        <span style="font-size: 13px; line-height: 1;">🏢</span>
        <span style="font-size: 10px; font-weight: 900; margin-top: 1px;">${label}</span>
      </div>
    `,
    iconSize: [44, 34],
    iconAnchor: [22, 17],
    popupAnchor: [0, -18],
  });
}

function calculateBearing(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const toRad = (d: number) => (d * Math.PI) / 180;
  const toDeg = (r: number) => (r * 180) / Math.PI;
  const dLon = toRad(lon2 - lon1);
  const y = Math.sin(dLon) * Math.cos(toRad(lat2));
  const x =
    Math.cos(toRad(lat1)) * Math.sin(toRad(lat2)) -
    Math.sin(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.cos(dLon);
  return (toDeg(Math.atan2(y, x)) + 360) % 360;
}

function createArrowIcon(color: string, angle: number) {
  return L.divIcon({
    className: 'road-arrow-icon',
    html: `
      <div style="
        transform: rotate(${angle}deg);
        display: flex;
        align-items: center;
        justify-content: center;
        width: 14px;
        height: 14px;
        color: ${color};
        filter: drop-shadow(0 1px 2px rgba(0,0,0,0.5));
      ">
        <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
          <path d="M12 2L4 20l8-4 8 4z"/>
        </svg>
      </div>
    `,
    iconSize: [14, 14],
    iconAnchor: [7, 7],
  });
}

export const RouteMap: React.FC<RouteMapProps> = ({
  routes,
  selectedRouteId,
  onRouteSelect,
  onStopSelect,
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const tileLayerRef = useRef<L.TileLayer | null>(null);
  const routeLayersRef = useRef<L.LayerGroup | null>(null);
  const [currentStyle, setCurrentStyle] = useState<'light' | 'osm' | 'dark' | 'satellite'>('light');
  const [showStyleMenu, setShowStyleMenu] = useState(false);

  // Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    const map = L.map(mapContainerRef.current, {
      center: [19.2812, 72.8561],
      zoom: 12,
      zoomControl: false,
    });

    L.control.zoom({ position: 'bottomright' }).addTo(map);

    const tileLayer = L.tileLayer(TILE_LAYERS[currentStyle], {
      attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
      maxZoom: 19,
    }).addTo(map);

    const routeLayerGroup = L.layerGroup().addTo(map);

    mapInstanceRef.current = map;
    tileLayerRef.current = tileLayer;
    routeLayersRef.current = routeLayerGroup;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // Update Tile Layer Basemap
  useEffect(() => {
    if (!tileLayerRef.current || !mapInstanceRef.current) return;
    tileLayerRef.current.setUrl(TILE_LAYERS[currentStyle]);
  }, [currentStyle]);

  // Render Routes, Polyline Paths, Turn Arrows, and Stop Markers
  useEffect(() => {
    const map = mapInstanceRef.current;
    const layerGroup = routeLayersRef.current;
    if (!map || !layerGroup) return;

    layerGroup.clearLayers();

    if (!routes || routes.length === 0) return;

    const allLatLngs: L.LatLng[] = [];
    const visibleRoutes = selectedRouteId
      ? routes.filter((r) => r.id === selectedRouteId)
      : routes;

    // 1. Draw Depot Central Hub
    const firstRoute = routes[0];
    const depotStop = firstRoute?.stops?.find(s => s.sequence === 0 || s.stop_type === 'DEPOT_START');
    if (depotStop && depotStop.latitude != null && depotStop.longitude != null) {
      const depotLat = depotStop.latitude;
      const depotLon = depotStop.longitude;

      const depotMarker = L.marker([depotLat, depotLon], {
        icon: createHubIcon('CENTRAL HUB'),
        zIndexOffset: 1000,
      }).addTo(layerGroup);

      depotMarker.bindPopup(`
        <div style="min-width:220px;font-family:Inter,sans-serif;font-size:12px;line-height:1.5;color:#0f172a;padding:4px;">
          <div style="font-weight:800;font-size:13px;color:#d97706;margin-bottom:4px;display:flex;align-items:center;gap:6px;">
            <span>🏢 Central Logistics Hub</span>
          </div>
          <div style="color:#475569;margin-bottom:6px;">
            All delivery vehicles depart and return to this central distribution depot.
          </div>
          <div style="background:#f8fafc;padding:6px;border-radius:6px;border:1px solid #e2e8f0;font-size:11px;">
            <div><strong>Active Fleet:</strong> ${routes.length} Vehicles</div>
            <div><strong>Total Deliveries:</strong> ${routes.reduce((s, r) => s + r.total_stops, 0)} parcels</div>
          </div>
        </div>
      `, { className: 'custom-popup' });

      allLatLngs.push(L.latLng(depotLat, depotLon));
    }

    // 2. Render each visible vehicle route
    visibleRoutes.forEach((route) => {
      const originalIdx = routes.findIndex((r) => r.id === route.id);
      const color = ROUTE_COLORS[(originalIdx >= 0 ? originalIdx : 0) % ROUTE_COLORS.length];
      const isSelected = selectedRouteId === route.id;
      const weight = isSelected ? 5.5 : 4;
      const opacity = 0.95;

      // Draw road geometry polyline & directional arrows
      if (route.geometry && route.geometry.coordinates?.length) {
        const rawCoords = route.geometry.coordinates;
        const coords: L.LatLngExpression[] = rawCoords.map(
          ([lng, lat]) => [lat, lng] as L.LatLngExpression
        );

        // Subtle dark casing line under the colored road polyline for crisp contrast
        L.polyline(coords, {
          color: '#ffffff',
          weight: weight + 2.5,
          opacity: 0.9,
          lineCap: 'round',
          lineJoin: 'round',
        }).addTo(layerGroup);

        const polyline = L.polyline(coords, {
          color,
          weight,
          opacity,
          smoothFactor: 1,
          lineCap: 'round',
          lineJoin: 'round',
        }).addTo(layerGroup);

        polyline.on('click', () => onRouteSelect(route.id));

        coords.forEach((c) => {
          const ll = Array.isArray(c) ? L.latLng(c[0] as number, c[1] as number) : L.latLng(c);
          allLatLngs.push(ll);
        });

        // Directional Arrows along road curves
        const step = Math.max(10, Math.floor(rawCoords.length / 25));
        for (let i = 0; i < rawCoords.length - 1; i += step) {
          const [lng1, lat1] = rawCoords[i];
          const [lng2, lat2] = rawCoords[Math.min(i + 2, rawCoords.length - 1)];
          const bearing = calculateBearing(lat1, lng1, lat2, lng2);
          
          const arrowMarker = L.marker([lat1, lng1], {
            icon: createArrowIcon(color, bearing),
            zIndexOffset: 50,
            interactive: false,
          });
          arrowMarker.addTo(layerGroup);
        }
      }

      // Draw numbered delivery stop markers (1, 2, 3, 4th delivery)
      (route.stops || []).forEach((stop) => {
        if (stop.latitude == null || stop.longitude == null || stop.sequence === 0) return;

        const ordinal = getOrdinal(stop.sequence);
        const markerIcon = createStopIcon(color, stop.sequence, stop.is_late);
        const marker = L.marker([stop.latitude, stop.longitude], {
          icon: markerIcon,
          zIndexOffset: stop.sequence * 10,
        }).addTo(layerGroup);

        const latenessBadge = stop.is_late
          ? `<span style="color:#dc2626;font-weight:700"> ⚠️ Late (+${stop.lateness_minutes}m)</span>`
          : `<span style="color:#16a34a;font-weight:600"> (On-Time)</span>`;

        marker.bindPopup(`
          <div style="min-width:240px;font-family:Inter,system-ui,sans-serif;font-size:12px;line-height:1.5;color:#0f172a;padding:4px;">
            <div style="font-weight:800;font-size:13px;color:${color};margin-bottom:6px;display:flex;align-items:center;justify-content:space-between;">
              <span>${ordinal} Delivery (Stop #${stop.sequence})</span>
              <span style="font-size:10px;color:#334155;background:#f1f5f9;border:1px solid #cbd5e1;padding:1px 5px;border-radius:4px;font-weight:700;">${route.vehicle_name}</span>
            </div>
            <div style="margin-bottom:4px;"><strong>Order ID:</strong> ${stop.external_order_id || 'N/A'}</div>
            <div style="margin-bottom:4px;color:#334155;"><strong>Address:</strong> ${stop.address}</div>
            <div style="margin-bottom:4px;"><strong>ETA:</strong> <span style="color:#0284c7;font-weight:700">${stop.estimated_arrival_time_str || 'N/A'}</span> ${latenessBadge}</div>
            <div style="margin-bottom:4px;"><strong>Time Window:</strong> ${stop.window_start_str || '09:00'} - ${stop.window_end_str || '18:00'}</div>
            <div style="margin-bottom:4px;"><strong>Service Time:</strong> ${stop.service_time_minutes || 0} min</div>
            <div><strong>Parcel Weight:</strong> ${stop.parcel_weight_kg} kg</div>
          </div>
        `, { className: 'custom-popup' });

        if (onStopSelect) {
          marker.on('click', () => onStopSelect(stop, route.id));
        }

        allLatLngs.push(L.latLng(stop.latitude, stop.longitude));
      });
    });

    if (allLatLngs.length > 0) {
      const bounds = L.latLngBounds(allLatLngs);
      map.fitBounds(bounds, { padding: [50, 50], maxZoom: 15 });
    }
  }, [routes, selectedRouteId, onRouteSelect, onStopSelect]);

  return (
    <div className="w-full h-full relative" style={{ minHeight: '100%', height: '100%' }}>
      <div ref={mapContainerRef} className="w-full h-full" style={{ minHeight: '100%', height: '100%' }} />

      {/* Floating Map Basemap Style Selector */}
      <div className="absolute top-4 right-4 z-[1000]">
        <div className="relative">
          <button
            onClick={() => setShowStyleMenu(!showStyleMenu)}
            className="px-3 py-1.5 rounded-lg bg-white/95 backdrop-blur-md border border-slate-300 text-slate-800 font-bold text-xs flex items-center gap-2 shadow-md hover:bg-slate-50 transition"
          >
            <Layers className="w-4 h-4 text-amber-600" />
            <span className="capitalize">{currentStyle} Map</span>
          </button>

          {showStyleMenu && (
            <div className="absolute right-0 top-10 w-44 bg-white border border-slate-200 rounded-xl p-1.5 shadow-xl space-y-1 z-[1001] animate-in fade-in duration-150">
              <button
                onClick={() => { setCurrentStyle('light'); setShowStyleMenu(false); }}
                className={`w-full text-left px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center justify-between transition ${
                  currentStyle === 'light' ? 'bg-amber-400 text-slate-950 font-bold' : 'text-slate-700 hover:bg-slate-100'
                }`}
              >
                <span>Carto Positron</span>
                {currentStyle === 'light' && <span className="w-1.5 h-1.5 rounded-full bg-slate-950" />}
              </button>

              <button
                onClick={() => { setCurrentStyle('osm'); setShowStyleMenu(false); }}
                className={`w-full text-left px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center justify-between transition ${
                  currentStyle === 'osm' ? 'bg-amber-400 text-slate-950 font-bold' : 'text-slate-700 hover:bg-slate-100'
                }`}
              >
                <span>OpenStreetMap</span>
                {currentStyle === 'osm' && <span className="w-1.5 h-1.5 rounded-full bg-slate-950" />}
              </button>

              <button
                onClick={() => { setCurrentStyle('dark'); setShowStyleMenu(false); }}
                className={`w-full text-left px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center justify-between transition ${
                  currentStyle === 'dark' ? 'bg-amber-400 text-slate-950 font-bold' : 'text-slate-700 hover:bg-slate-100'
                }`}
              >
                <span>Dark Theme</span>
                {currentStyle === 'dark' && <span className="w-1.5 h-1.5 rounded-full bg-slate-950" />}
              </button>

              <button
                onClick={() => { setCurrentStyle('satellite'); setShowStyleMenu(false); }}
                className={`w-full text-left px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center justify-between transition ${
                  currentStyle === 'satellite' ? 'bg-amber-400 text-slate-950 font-bold' : 'text-slate-700 hover:bg-slate-100'
                }`}
              >
                <span>Satellite</span>
                {currentStyle === 'satellite' && <span className="w-1.5 h-1.5 rounded-full bg-slate-950" />}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
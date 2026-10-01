import React, { useState } from 'react';
import { 
  Truck, Navigation, Clock, Package, ChevronDown, ChevronUp, 
  MapPin, AlertTriangle, CheckCircle2, ArrowRight, Home
} from 'lucide-react';
import { RouteItem } from '../types';

const ROUTE_COLORS = [
  '#d97706', '#2563eb', '#059669', '#dc2626', '#7c3aed',
  '#0891b2', '#ea580c', '#4f46e5', '#16a34a', '#db2777',
];

interface RightFilterPanelProps {
  routes: RouteItem[];
  selectedRouteId: string | null;
  onSelectRoute: (routeId: string | null) => void;
}

function getOrdinal(n: number): string {
  const s = ['th', 'st', 'nd', 'rd'];
  const v = n % 100;
  return n + (s[(v - 20) % 10] || s[v] || s[0]);
}

function formatMinutesToHoursMinutes(mins: number = 0): string {
  if (mins <= 0) return '0m';
  const h = Math.floor(mins / 60);
  const m = Math.round(mins % 60);
  if (h === 0) return `${m}m`;
  return `${h}h ${m}m`;
}

export const RightFilterPanel: React.FC<RightFilterPanelProps> = ({
  routes,
  selectedRouteId,
  onSelectRoute,
}) => {
  const [activeTab, setActiveTab] = useState<'timeline' | 'stops' | 'legs'>('timeline');
  const [expandedLegs, setExpandedLegs] = useState<Record<number, boolean>>({});

  if (!routes || routes.length === 0) return null;

  const selectedRoute = selectedRouteId
    ? routes.find((r) => r.id === selectedRouteId) || null
    : null;

  const selectedIndex = selectedRoute
    ? routes.findIndex((r) => r.id === selectedRoute.id)
    : -1;

  const activeColor = selectedIndex >= 0
    ? ROUTE_COLORS[selectedIndex % ROUTE_COLORS.length]
    : '#d97706';

  const toggleLeg = (legIdx: number) => {
    setExpandedLegs(prev => ({ ...prev, [legIdx]: !prev[legIdx] }));
  };

  return (
    <div className="w-84 sm:w-96 h-full bg-white border-l border-slate-200 flex flex-col z-20 shadow-lg text-slate-800">
      {/* Panel Header */}
      <div className="p-3.5 border-b border-slate-200 bg-slate-50 flex items-center justify-between shrink-0">
        <div className="flex items-center space-x-2">
          <div className="w-6 h-6 rounded bg-slate-900 text-amber-400 flex items-center justify-center font-bold text-xs">
            <Truck className="w-3.5 h-3.5" />
          </div>
          <h3 className="font-bold text-xs uppercase tracking-wider text-slate-700">
            {selectedRoute ? 'Vehicle Route Plan' : 'Fleet Route Directory'}
          </h3>
        </div>

        {selectedRoute ? (
          <button
            onClick={() => onSelectRoute(null)}
            className="text-[11px] font-bold text-amber-700 hover:text-amber-800 bg-amber-100 hover:bg-amber-200 px-2 py-0.5 rounded transition"
          >
            Show All Fleet
          </button>
        ) : (
          <span className="text-[11px] font-bold text-slate-500 bg-slate-200/80 px-2 py-0.5 rounded">
            {routes.length} Active Vans
          </span>
        )}
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {selectedRoute ? (
          <div className="space-y-3">
            {/* Selected Vehicle Overview Card */}
            <div
              className="p-3.5 rounded-xl border border-slate-200 bg-white shadow-sm"
              style={{ borderLeftWidth: 4, borderLeftColor: activeColor }}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <div
                    className="w-7 h-7 rounded-lg flex items-center justify-center font-extrabold text-xs text-white shadow-sm"
                    style={{ backgroundColor: activeColor }}
                  >
                    V{selectedIndex + 1}
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-slate-900">
                      {selectedRoute.vehicle_name}
                    </h4>
                    <p className="text-[10px] text-slate-500 font-medium">
                      Shift: {selectedRoute.start_time_str || '07:00'} - {selectedRoute.end_time_str || '19:00'}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <span className="text-xs font-bold text-slate-900 font-mono">
                    {selectedRoute.total_distance_km} km
                  </span>
                  <p className="text-[10px] text-slate-500">
                    {selectedRoute.total_stops} deliveries
                  </p>
                </div>
              </div>

              {/* Time Budget Breakdown */}
              <div className="grid grid-cols-4 gap-1.5 p-2 rounded-lg bg-slate-50 border border-slate-200 text-center text-[10px]">
                <div>
                  <span className="text-slate-500 block font-medium">Driving</span>
                  <span className="font-bold text-slate-800 font-mono">{formatMinutesToHoursMinutes(selectedRoute.driving_duration_minutes)}</span>
                </div>
                <div>
                  <span className="text-slate-500 block font-medium">Service</span>
                  <span className="font-bold text-slate-800 font-mono">{formatMinutesToHoursMinutes(selectedRoute.service_duration_minutes)}</span>
                </div>
                <div>
                  <span className="text-slate-500 block font-medium">Waiting</span>
                  <span className="font-bold text-amber-700 font-mono">{formatMinutesToHoursMinutes(selectedRoute.waiting_duration_minutes || 0)}</span>
                </div>
                <div>
                  <span className="text-slate-500 block font-medium">Total</span>
                  <span className="font-bold text-emerald-700 font-mono">{formatMinutesToHoursMinutes(selectedRoute.total_duration_minutes)}</span>
                </div>
              </div>

              {/* Payload Progress Bar */}
              <div className="mt-2.5">
                <div className="flex justify-between text-[11px] mb-1">
                  <span className="text-slate-500 font-medium">Capacity Load</span>
                  <span className="font-bold text-slate-800 font-mono">
                    {selectedRoute.total_payload_kg} / {selectedRoute.capacity_kg || 500} kg ({selectedRoute.capacity_utilization_pct}%)
                  </span>
                </div>
                <div className="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-300"
                    style={{
                      width: `${Math.min(100, selectedRoute.capacity_utilization_pct)}%`,
                      backgroundColor: activeColor,
                    }}
                  />
                </div>
              </div>
            </div>

            {/* Sub-Tabs: Timeline / Stops / Turn-by-Turn Legs */}
            <div className="flex rounded-lg bg-slate-100 p-1 border border-slate-200 text-xs font-semibold">
              <button
                onClick={() => setActiveTab('timeline')}
                className={`flex-1 py-1 rounded-md transition ${
                  activeTab === 'timeline'
                    ? 'bg-white text-slate-900 shadow-xs font-bold'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Timeline
              </button>
              <button
                onClick={() => setActiveTab('stops')}
                className={`flex-1 py-1 rounded-md transition ${
                  activeTab === 'stops'
                    ? 'bg-white text-slate-900 shadow-xs font-bold'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Stops ({selectedRoute.total_stops})
              </button>
              <button
                onClick={() => setActiveTab('legs')}
                className={`flex-1 py-1 rounded-md transition ${
                  activeTab === 'legs'
                    ? 'bg-white text-slate-900 shadow-xs font-bold'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Turn-by-Turn
              </button>
            </div>

            {/* Tab Content 1: Continuous Schedule Timeline */}
            {activeTab === 'timeline' && (
              <div className="space-y-2 relative pl-4 border-l-2 border-slate-200 ml-3">
                {/* 1. Hub Departure */}
                <div className="relative group">
                  <div className="absolute -left-[23px] top-1 w-4 h-4 rounded-full bg-slate-900 border-2 border-white flex items-center justify-center text-[8px] text-amber-400 font-bold shadow-sm">
                    <Home className="w-2.5 h-2.5" />
                  </div>
                  <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-900">Hub Departure</span>
                      <span className="text-xs font-mono font-bold text-amber-700">
                        {selectedRoute.start_time_str || '07:00'}
                      </span>
                    </div>
                    <p className="text-[10px] text-slate-500 mt-0.5">Central Logistics Depot &bull; Vehicle Dispatched</p>
                  </div>
                </div>

                {/* 2. Intermediate Deliveries */}
                {selectedRoute.stops
                  .filter((s) => s.sequence > 0)
                  .map((stop, sIdx) => {
                    const ordinal = getOrdinal(stop.sequence);
                    return (
                      <div key={sIdx} className="relative group">
                        <div
                          className="absolute -left-[23px] top-1.5 w-4 h-4 rounded-full border-2 border-white flex items-center justify-center text-[8px] text-white font-bold shadow-sm"
                          style={{ backgroundColor: activeColor }}
                        >
                          {stop.sequence}
                        </div>
                        <div className="p-2.5 rounded-lg bg-white border border-slate-200 hover:border-slate-300 hover:shadow-sm transition">
                          <div className="flex items-start justify-between">
                            <div>
                              <span className="text-xs font-bold text-slate-900">
                                {ordinal} Delivery ({stop.external_order_id || `#${stop.sequence}`})
                              </span>
                              <p className="text-[11px] text-slate-600 mt-0.5 line-clamp-1">{stop.address}</p>
                            </div>
                            <span className="text-xs font-mono font-bold text-slate-900 ml-2">
                              {stop.estimated_arrival_time_str}
                            </span>
                          </div>

                          <div className="flex items-center gap-2 mt-1.5 text-[10px] text-slate-500 border-t border-slate-100 pt-1.5">
                            <span>Window: {stop.window_start_str || '09:00'} - {stop.window_end_str || '18:00'}</span>
                            <span>&bull;</span>
                            <span>{stop.parcel_weight_kg} kg</span>
                            {stop.is_late ? (
                              <span className="ml-auto text-rose-600 font-bold flex items-center gap-0.5">
                                <AlertTriangle className="w-3 h-3" /> +{stop.lateness_minutes}m Late
                              </span>
                            ) : (
                              <span className="ml-auto text-emerald-600 font-bold flex items-center gap-0.5">
                                <CheckCircle2 className="w-3 h-3" /> On-Time
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}

                {/* 3. Hub Return */}
                <div className="relative group">
                  <div className="absolute -left-[23px] top-1 w-4 h-4 rounded-full bg-slate-900 border-2 border-white flex items-center justify-center text-[8px] text-amber-400 font-bold shadow-sm">
                    <Home className="w-2.5 h-2.5" />
                  </div>
                  <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-900">Return to Depot</span>
                      <span className="text-xs font-mono font-bold text-amber-700">
                        {selectedRoute.end_time_str || '19:00'}
                      </span>
                    </div>
                    <p className="text-[10px] text-slate-500 mt-0.5">Route Completed &bull; Circuit Closed</p>
                  </div>
                </div>
              </div>
            )}

            {/* Tab Content 2: Stops List */}
            {activeTab === 'stops' && (
              <div className="space-y-2">
                {selectedRoute.stops
                  .filter((s) => s.sequence > 0)
                  .map((stop, sIdx) => {
                    const ordinal = getOrdinal(stop.sequence);
                    return (
                      <div
                        key={sIdx}
                        className="p-2.5 rounded-lg bg-white border border-slate-200 hover:border-slate-300 transition shadow-xs"
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex items-start space-x-2">
                            <div
                              className="w-5 h-5 rounded-full flex items-center justify-center font-bold text-[10px] text-white shrink-0 mt-0.5 shadow-xs"
                              style={{ backgroundColor: activeColor }}
                            >
                              {stop.sequence}
                            </div>
                            <div>
                              <p className="text-xs font-bold text-slate-900 leading-tight">
                                {ordinal} Delivery &bull; Order {stop.external_order_id || '#' + stop.sequence}
                              </p>
                              <p className="text-[11px] text-slate-600 mt-0.5 line-clamp-2">
                                {stop.address}
                              </p>
                            </div>
                          </div>
                          <div className="text-right shrink-0">
                            <span className="text-xs font-bold font-mono text-slate-900">
                              {stop.estimated_arrival_time_str || '--:--'}
                            </span>
                            <p className="text-[10px] text-slate-500 font-mono mt-0.5">
                              {stop.parcel_weight_kg} kg
                            </p>
                          </div>
                        </div>
                      </div>
                    );
                  })}
              </div>
            )}

            {/* Tab Content 3: Turn-by-Turn Maneuvers */}
            {activeTab === 'legs' && (
              <div className="space-y-2">
                {selectedRoute.legs && selectedRoute.legs.length > 0 ? (
                  selectedRoute.legs.map((leg, lIdx) => {
                    const isExpanded = !!expandedLegs[lIdx];
                    return (
                      <div key={lIdx} className="rounded-lg border border-slate-200 bg-white overflow-hidden shadow-xs">
                        <button
                          onClick={() => toggleLeg(lIdx)}
                          className="w-full p-2.5 flex items-center justify-between text-left hover:bg-slate-50 transition"
                        >
                          <div className="flex items-center gap-2">
                            <span className="w-5 h-5 rounded bg-slate-100 text-slate-800 font-mono text-[10px] font-bold flex items-center justify-center border border-slate-300">
                              L{lIdx + 1}
                            </span>
                            <div>
                              <div className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                                <span>{leg.from_name}</span>
                                <ArrowRight className="w-3 h-3 text-slate-400" />
                                <span>{leg.to_name}</span>
                              </div>
                              <div className="text-[10px] text-slate-500 mt-0.5">
                                {leg.distance_km} km &bull; {Math.round(leg.driving_duration_minutes)} min driving
                              </div>
                            </div>
                          </div>
                          {isExpanded ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
                        </button>

                        {isExpanded && leg.maneuvers && (
                          <div className="p-2.5 border-t border-slate-200 bg-slate-50 space-y-1.5 text-xs">
                            {leg.maneuvers.length === 0 ? (
                              <p className="text-[11px] text-slate-500 italic">Direct road navigation segment.</p>
                            ) : (
                              leg.maneuvers.map((m, mIdx) => (
                                <div key={mIdx} className="flex items-start space-x-2 text-slate-700">
                                  <span className="text-[10px] font-mono text-amber-700 font-bold shrink-0 mt-0.5">{mIdx + 1}.</span>
                                  <div className="flex-1">
                                    <p className="font-semibold text-[11px] leading-tight text-slate-900">{m.instruction}</p>
                                    <p className="text-[10px] text-slate-500 mt-0.5">{m.distance_km} km ({m.duration_minutes} min)</p>
                                  </div>
                                </div>
                              ))
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })
                ) : (
                  <p className="text-xs text-slate-500 p-3 italic">Leg breakdown generated automatically upon routing.</p>
                )}
              </div>
            )}
          </div>
        ) : (
          /* All Vehicles Fleet Directory */
          <div className="space-y-2">
            <div className="flex items-center justify-between px-1 mb-1">
              <span className="text-xs font-bold text-slate-600 uppercase tracking-wider">Active Fleet Vehicles</span>
              <span className="text-[10px] text-slate-400">Click to isolate route</span>
            </div>
            
            {routes.map((route, idx) => {
              const color = ROUTE_COLORS[idx % ROUTE_COLORS.length];
              return (
                <div
                  key={route.id}
                  onClick={() => onSelectRoute(route.id)}
                  className="p-3 rounded-xl bg-white border border-slate-200 hover:border-amber-400 hover:shadow-sm transition cursor-pointer group"
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-2.5">
                      <div
                        className="w-7 h-7 rounded-lg flex items-center justify-center font-bold text-xs shadow-xs"
                        style={{ background: color + '15', color, border: '1.5px solid ' + color }}
                      >
                        V{idx + 1}
                      </div>
                      <div>
                        <h4 className="text-xs font-bold text-slate-900 group-hover:text-amber-700 transition">
                          {route.vehicle_name}
                        </h4>
                        <p className="text-[10px] text-slate-500">
                          {route.total_stops} deliveries &bull; {route.total_distance_km} km
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <span className="text-xs font-mono font-bold text-slate-800">
                        {route.capacity_utilization_pct}%
                      </span>
                      <p className="text-[9px] text-slate-400 font-medium">Capacity</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-1 text-[10px] bg-slate-50 rounded-lg p-1.5 border border-slate-200 text-slate-600">
                    <div>Drive: <span className="text-slate-900 font-bold">{formatMinutesToHoursMinutes(route.driving_duration_minutes)}</span></div>
                    <div>Service: <span className="text-slate-900 font-bold">{formatMinutesToHoursMinutes(route.service_duration_minutes)}</span></div>
                    <div>Total: <span className="text-emerald-700 font-bold">{formatMinutesToHoursMinutes(route.total_duration_minutes)}</span></div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
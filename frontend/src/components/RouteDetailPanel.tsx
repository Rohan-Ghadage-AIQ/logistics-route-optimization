import React from 'react';
import {
  X, Truck, MapPin, Clock, Navigation, Weight, Package,
  ChevronRight, AlertTriangle, CheckCircle2, ArrowRight
} from 'lucide-react';
import { RouteItem } from '../types';

const ROUTE_COLORS = [
  '#0ea5e9', '#a855f7', '#f97316', '#10b981', '#ec4899',
  '#eab308', '#06b6d4', '#f43f5e', '#8b5cf6', '#14b8a6',
  '#3b82f6', '#84cc16',
];

interface RouteDetailPanelProps {
  route: RouteItem | null;
  routeIndex: number;
  onClose: () => void;
}

export const RouteDetailPanel: React.FC<RouteDetailPanelProps> = ({ route, routeIndex, onClose }) => {
  if (!route) return null;

  const color = ROUTE_COLORS[routeIndex % ROUTE_COLORS.length];

  return (
    <div className="w-96 bg-slate-900 border-l border-slate-800 flex flex-col h-full overflow-hidden shrink-0">
      {/* Header */}
      <div className="px-5 py-4 border-b border-slate-800 flex items-center justify-between shrink-0">
        <div className="flex items-center space-x-3">
          <div
            className="w-9 h-9 rounded-xl flex items-center justify-center"
            style={{ background: `${color}20`, border: `2px solid ${color}` }}
          >
            <Truck className="w-5 h-5" style={{ color }} />
          </div>
          <div>
            <h3 className="font-bold text-white text-sm">{route.vehicle_name}</h3>
            <p className="text-[11px] text-slate-400">{route.total_stops} stops · {route.total_distance_km} km</p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-2 px-5 py-3 border-b border-slate-800 shrink-0">
        <div className="bg-slate-850/80 rounded-lg p-2.5 border border-slate-800">
          <div className="flex items-center space-x-1.5 text-slate-400 text-[10px] uppercase font-semibold tracking-wider mb-1">
            <Navigation className="w-3 h-3" /><span>Distance</span>
          </div>
          <span className="text-lg font-bold text-white">{route.total_distance_km} <span className="text-xs text-slate-400">km</span></span>
        </div>
        <div className="bg-slate-850/80 rounded-lg p-2.5 border border-slate-800">
          <div className="flex items-center space-x-1.5 text-slate-400 text-[10px] uppercase font-semibold tracking-wider mb-1">
            <Clock className="w-3 h-3" /><span>Duration</span>
          </div>
          <span className="text-lg font-bold text-white">{(route.total_duration_minutes / 60).toFixed(1)} <span className="text-xs text-slate-400">hrs</span></span>
        </div>
        <div className="bg-slate-850/80 rounded-lg p-2.5 border border-slate-800">
          <div className="flex items-center space-x-1.5 text-slate-400 text-[10px] uppercase font-semibold tracking-wider mb-1">
            <Weight className="w-3 h-3" /><span>Payload</span>
          </div>
          <span className="text-lg font-bold text-white">{route.total_payload_kg} <span className="text-xs text-slate-400">kg</span></span>
        </div>
        <div className="bg-slate-850/80 rounded-lg p-2.5 border border-slate-800">
          <div className="flex items-center space-x-1.5 text-slate-400 text-[10px] uppercase font-semibold tracking-wider mb-1">
            <Package className="w-3 h-3" /><span>Utilization</span>
          </div>
          <span className="text-lg font-bold" style={{ color }}>{route.capacity_utilization_pct}%</span>
        </div>
      </div>

      {/* Stop List */}
      <div className="flex-1 overflow-y-auto px-5 py-3 space-y-1">
        <p className="text-[10px] uppercase font-bold tracking-wider text-slate-400 mb-2">
          Stop Sequence
        </p>
        {route.stops.map((stop, idx) => (
          <div key={idx}>
            <div className={`flex items-start space-x-3 p-2.5 rounded-lg transition ${
              stop.is_late
                ? 'bg-rose-950/30 border border-rose-900/40'
                : 'bg-slate-850/50 border border-slate-800/60 hover:bg-slate-800/60'
            }`}>
              {/* Sequence Badge */}
              <div
                className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0 mt-0.5"
                style={{
                  background: stop.is_late ? 'rgba(244,63,94,0.15)' : `${color}15`,
                  border: `2px solid ${stop.is_late ? '#f43f5e' : color}`,
                  color: stop.is_late ? '#fda4af' : color,
                }}
              >
                {stop.sequence}
              </div>

              {/* Stop Info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <p className="text-xs font-semibold text-white truncate max-w-[200px]">
                    {stop.external_order_id || `Stop ${stop.sequence}`}
                  </p>
                  <div className="flex items-center space-x-1">
                    {stop.is_late ? (
                      <AlertTriangle className="w-3 h-3 text-rose-400" />
                    ) : (
                      <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                    )}
                  </div>
                </div>
                <p className="text-[11px] text-slate-400 truncate mt-0.5">{stop.address}</p>
                <div className="flex items-center space-x-3 mt-1.5 text-[10px]">
                  <span className="text-sky-400 font-semibold">ETA {stop.estimated_arrival_time_str}</span>
                  <span className="text-slate-500">
                    {stop.window_start_str} – {stop.window_end_str}
                  </span>
                  <span className="text-slate-500">{stop.parcel_weight_kg}kg</span>
                </div>
                {stop.is_late && (
                  <p className="text-[10px] text-rose-400 font-semibold mt-1">
                    ⚠ {stop.lateness_minutes} min late
                  </p>
                )}
              </div>
            </div>

            {/* Connector Arrow */}
            {idx < route.stops.length - 1 && (
              <div className="flex justify-center py-0.5">
                <div className="w-px h-4 bg-slate-800" />
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="px-5 py-3 border-t border-slate-800 shrink-0">
        <div className="flex items-center justify-between text-xs">
          <span className="text-slate-400">Operational Cost</span>
          <span className="text-teal-300 font-bold text-sm">₹{route.operational_cost.toLocaleString()}</span>
        </div>
      </div>
    </div>
  );
};

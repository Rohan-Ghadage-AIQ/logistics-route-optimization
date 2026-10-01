import React from 'react';
import { Truck, Navigation, Clock, ChevronRight, Package } from 'lucide-react';
import { RouteItem } from '../types';

const ROUTE_COLORS = [
  '#0ea5e9', '#a855f7', '#f97316', '#10b981', '#ec4899',
  '#eab308', '#06b6d4', '#f43f5e', '#8b5cf6', '#14b8a6',
  '#3b82f6', '#84cc16',
];

interface RouteListSidebarProps {
  routes: RouteItem[];
  selectedRouteId: string | null;
  onSelectRoute: (routeId: string) => void;
}

export const RouteListSidebar: React.FC<RouteListSidebarProps> = ({
  routes,
  selectedRouteId,
  onSelectRoute,
}) => {
  if (!routes.length) return null;

  return (
    <div className="w-72 bg-slate-900/95 border-r border-slate-800 flex flex-col h-full shrink-0 overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-slate-800 shrink-0">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
          <Truck className="w-4 h-4 text-sky-400" />
          Fleet Routes ({routes.length})
        </h3>
      </div>

      {/* Scrollable list */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1.5">
        {routes.map((route, idx) => {
          const color = ROUTE_COLORS[idx % ROUTE_COLORS.length];
          const isSelected = route.id === selectedRouteId;

          return (
            <button
              key={route.id}
              onClick={() => onSelectRoute(route.id)}
              className={`w-full text-left p-3 rounded-xl transition-all group ${
                isSelected
                  ? 'bg-slate-800 border-sky-500/40 shadow-md shadow-sky-500/5'
                  : 'bg-slate-850/60 hover:bg-slate-800/80 border-transparent'
              } border`}
            >
              <div className="flex items-center space-x-2.5">
                {/* Color indicator */}
                <div
                  className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0"
                  style={{
                    background: `${color}15`,
                    border: `2px solid ${color}`,
                  }}
                >
                  <span className="text-xs font-extrabold" style={{ color }}>
                    V{route.vehicle_id}
                  </span>
                </div>

                {/* Vehicle info */}
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-bold text-white truncate">{route.vehicle_name}</p>
                  <div className="flex items-center space-x-2 mt-1 text-[10px] text-slate-400">
                    <span className="flex items-center gap-0.5">
                      <Package className="w-3 h-3" />{route.total_stops}
                    </span>
                    <span className="flex items-center gap-0.5">
                      <Navigation className="w-3 h-3" />{route.total_distance_km}km
                    </span>
                    <span className="flex items-center gap-0.5">
                      <Clock className="w-3 h-3" />{(route.total_duration_minutes / 60).toFixed(1)}h
                    </span>
                  </div>
                </div>

                {/* Arrow */}
                <ChevronRight
                  className={`w-4 h-4 text-slate-500 transition ${
                    isSelected ? 'text-sky-400' : 'group-hover:text-slate-300'
                  }`}
                />
              </div>

              {/* Capacity bar */}
              <div className="mt-2">
                <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all"
                    style={{
                      width: `${Math.min(route.capacity_utilization_pct, 100)}%`,
                      background: color,
                      opacity: isSelected ? 1 : 0.7,
                    }}
                  />
                </div>
                <p className="text-[9px] text-slate-500 mt-0.5 text-right font-mono">
                  {route.capacity_utilization_pct}% capacity
                </p>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};

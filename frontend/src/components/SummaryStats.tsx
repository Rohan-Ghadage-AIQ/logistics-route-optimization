import React from 'react';
import { Package, Truck, Navigation, Clock, IndianRupee, PieChart, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { JobDetail } from '../types';

interface SummaryStatsProps {
  job: JobDetail;
}

export const SummaryStats: React.FC<SummaryStatsProps> = ({ job }) => {
  const summary = job.summary;
  const totalOrders = job.total_orders || 0;
  const assigned = job.assigned_orders || 0;
  const unassigned = job.unassigned_orders || 0;
  const vehiclesUsed = job.vehicles_used || 0;
  const distanceKm = job.total_distance_km || 0;
  const durationHours = (job.total_duration_minutes / 60).toFixed(1);
  const totalCost = job.total_cost || 0;
  const avgUtilization = summary?.average_capacity_utilization_pct || 0;

  return (
    <div className="bg-white border-b border-slate-200 px-4 py-2 shadow-sm z-20">
      <div className="flex items-center gap-2 overflow-x-auto no-scrollbar">
        {/* Total Orders */}
        <div className="flex items-center gap-2.5 bg-slate-50 hover:bg-slate-100 border border-slate-200/80 rounded-lg px-3 py-1.5 transition shrink-0">
          <div className="w-7 h-7 rounded-md bg-amber-400/20 text-amber-700 flex items-center justify-center border border-amber-400/40">
            <Package className="w-3.5 h-3.5 stroke-[2.5]" />
          </div>
          <div>
            <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider leading-none">Orders</div>
            <div className="flex items-baseline gap-1 mt-0.5">
              <span className="text-sm font-extrabold text-slate-900 leading-none">{totalOrders}</span>
              <span className="text-[10px] font-semibold text-slate-500">parcels</span>
            </div>
          </div>
        </div>

        {/* Assigned Orders */}
        <div className="flex items-center gap-2.5 bg-slate-50 hover:bg-slate-100 border border-slate-200/80 rounded-lg px-3 py-1.5 transition shrink-0">
          <div className="w-7 h-7 rounded-md bg-emerald-50 text-emerald-700 flex items-center justify-center border border-emerald-200">
            <CheckCircle2 className="w-3.5 h-3.5 stroke-[2.5]" />
          </div>
          <div>
            <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider leading-none">Assigned</div>
            <div className="flex items-center gap-1.5 mt-0.5">
              <span className="text-sm font-extrabold text-emerald-700 leading-none">{assigned}</span>
              {unassigned > 0 && (
                <span className="text-[10px] font-bold text-amber-800 bg-amber-100 border border-amber-300 px-1.5 py-0.2 rounded">
                  {unassigned} dropped
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Fleet Used */}
        <div className="flex items-center gap-2.5 bg-slate-50 hover:bg-slate-100 border border-slate-200/80 rounded-lg px-3 py-1.5 transition shrink-0">
          <div className="w-7 h-7 rounded-md bg-slate-900 text-amber-400 flex items-center justify-center shadow-sm">
            <Truck className="w-3.5 h-3.5 stroke-[2.5]" />
          </div>
          <div>
            <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider leading-none">Fleet Used</div>
            <div className="flex items-baseline gap-1 mt-0.5">
              <span className="text-sm font-extrabold text-slate-900 leading-none">{vehiclesUsed}</span>
              <span className="text-[10px] font-semibold text-slate-500">vans active</span>
            </div>
          </div>
        </div>

        {/* Distance */}
        <div className="flex items-center gap-2.5 bg-slate-50 hover:bg-slate-100 border border-slate-200/80 rounded-lg px-3 py-1.5 transition shrink-0">
          <div className="w-7 h-7 rounded-md bg-slate-100 text-slate-700 flex items-center justify-center border border-slate-300">
            <Navigation className="w-3.5 h-3.5 stroke-[2.5]" />
          </div>
          <div>
            <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider leading-none">Road Dist</div>
            <div className="flex items-baseline gap-1 mt-0.5">
              <span className="text-sm font-extrabold text-slate-900 leading-none">{distanceKm}</span>
              <span className="text-[10px] font-semibold text-slate-500">km total</span>
            </div>
          </div>
        </div>

        {/* Duration */}
        <div className="flex items-center gap-2.5 bg-slate-50 hover:bg-slate-100 border border-slate-200/80 rounded-lg px-3 py-1.5 transition shrink-0">
          <div className="w-7 h-7 rounded-md bg-slate-100 text-slate-700 flex items-center justify-center border border-slate-300">
            <Clock className="w-3.5 h-3.5 stroke-[2.5]" />
          </div>
          <div>
            <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider leading-none">Duration</div>
            <div className="flex items-baseline gap-1 mt-0.5">
              <span className="text-sm font-extrabold text-slate-900 leading-none">{durationHours}</span>
              <span className="text-[10px] font-semibold text-slate-500">hours</span>
            </div>
          </div>
        </div>

        {/* Fleet Cost */}
        <div className="flex items-center gap-2.5 bg-slate-50 hover:bg-slate-100 border border-slate-200/80 rounded-lg px-3 py-1.5 transition shrink-0" title="Fixed Vehicle Dispatch Cost + (Distance km x Fuel/km Cost)">
          <div className="w-7 h-7 rounded-md bg-amber-400 text-slate-950 flex items-center justify-center font-bold text-xs shadow-sm">
            ₹
          </div>
          <div>
            <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider leading-none">Est. Cost</div>
            <div className="flex items-baseline gap-1 mt-0.5">
              <span className="text-sm font-extrabold text-slate-900 leading-none">
                ₹ {Number(totalCost).toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 2 })}
              </span>
              <span className="text-[9px] font-medium text-slate-400">Dispatch & fuel</span>
            </div>
          </div>
        </div>

        {/* Avg Payload */}
        <div className="flex items-center gap-2.5 bg-slate-50 hover:bg-slate-100 border border-slate-200/80 rounded-lg px-3 py-1.5 transition shrink-0">
          <div className="w-7 h-7 rounded-md bg-slate-100 text-slate-700 flex items-center justify-center border border-slate-300">
            <PieChart className="w-3.5 h-3.5 stroke-[2.5]" />
          </div>
          <div>
            <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider leading-none">Avg Payload</div>
            <div className="flex items-baseline gap-1 mt-0.5">
              <span className="text-sm font-extrabold text-slate-900 leading-none">{avgUtilization}%</span>
              <span className="text-[10px] font-semibold text-slate-500">capacity</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
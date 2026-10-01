import React from 'react';
import { Upload, Truck, MapPin, Cpu, Navigation, ArrowRight } from 'lucide-react';

interface EmptyStateProps {
  onUpload: () => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ onUpload }) => {
  return (
    <div className="flex-1 flex items-center justify-center bg-slate-950">
      <div className="max-w-xl text-center px-8">
        {/* Animated Hero Icon */}
        <div className="relative mx-auto w-28 h-28 mb-8">
          <div className="absolute inset-0 rounded-3xl bg-gradient-to-tr from-sky-500/20 to-indigo-600/20 animate-pulse" />
          <div className="absolute inset-2 rounded-2xl bg-gradient-to-tr from-sky-500 to-indigo-600 flex items-center justify-center shadow-xl shadow-sky-500/30">
            <Truck className="w-14 h-14 text-white" />
          </div>
        </div>

        <h2 className="text-2xl font-extrabold text-white mb-3">
          Logistics Route Optimization
        </h2>
        <p className="text-sm text-slate-400 mb-8 max-w-md mx-auto leading-relaxed">
          Upload your delivery manifest to generate optimized routes using
          <span className="text-sky-400 font-semibold"> Valhalla</span> road-network routing and
          <span className="text-indigo-400 font-semibold"> Google OR-Tools</span> constraint optimization.
        </p>

        {/* Pipeline Steps */}
        <div className="flex items-center justify-center space-x-2 mb-8">
          {[
            { icon: Upload, label: 'Upload', color: 'text-sky-400' },
            { icon: MapPin, label: 'Geocode', color: 'text-emerald-400' },
            { icon: Navigation, label: 'Valhalla Matrix', color: 'text-amber-400' },
            { icon: Cpu, label: 'OR-Tools', color: 'text-purple-400' },
            { icon: Truck, label: 'Routes', color: 'text-teal-400' },
          ].map((step, idx, arr) => (
            <React.Fragment key={step.label}>
              <div className="flex flex-col items-center space-y-1.5">
                <div className="w-10 h-10 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-center">
                  <step.icon className={`w-5 h-5 ${step.color}`} />
                </div>
                <span className="text-[10px] text-slate-500 font-medium">{step.label}</span>
              </div>
              {idx < arr.length - 1 && (
                <ArrowRight className="w-4 h-4 text-slate-700 mt-[-16px]" />
              )}
            </React.Fragment>
          ))}
        </div>

        {/* CTA */}
        <button
          onClick={onUpload}
          className="inline-flex items-center space-x-2 px-6 py-3 rounded-xl bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-white text-sm font-bold transition shadow-lg shadow-sky-500/20 active:scale-95"
        >
          <Upload className="w-5 h-5" />
          <span>Upload Delivery Manifest</span>
        </button>

        <p className="text-[11px] text-slate-600 mt-4">
          Supports .xlsx, .xls, and .csv files
        </p>
      </div>
    </div>
  );
};

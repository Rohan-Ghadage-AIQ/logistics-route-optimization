import React from 'react';
import { Truck, Upload, Settings, FileSpreadsheet } from 'lucide-react';

interface NavbarProps {
  onOpenUpload: () => void;
  onOpenFleet: () => void;
  onExport: () => void;
  hasActiveJob: boolean;
  valhallaConnected?: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  onOpenUpload,
  onOpenFleet,
  onExport,
  hasActiveJob,
}) => {
  return (
    <header className="h-13 py-2 px-5 bg-slate-900 border-b border-slate-800 flex items-center justify-between z-30 sticky top-0 shadow-sm">
      {/* Brand & Logo */}
      <div className="flex items-center space-x-3">
        <div className="w-8 h-8 rounded-lg bg-amber-400 flex items-center justify-center shadow-sm">
          <Truck className="w-5 h-5 text-slate-950 stroke-[2.5]" />
        </div>
        <div className="flex items-center gap-2">
          <h1 className="font-extrabold text-sm sm:text-base text-white tracking-tight">
            Logistics Route Optimizer
          </h1>
          <span className="text-[10px] uppercase font-extrabold px-2 py-0.5 rounded bg-amber-400/20 text-amber-300 border border-amber-400/40 tracking-wider">
            FLEET
          </span>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex items-center space-x-2">
        {/* Fleet Configuration Button */}
        <button
          onClick={onOpenFleet}
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-750 border border-slate-700 text-slate-200 text-xs font-semibold transition"
        >
          <Settings className="w-3.5 h-3.5 text-amber-400" />
          <span>Fleet Settings</span>
        </button>

        {/* Export Excel Button */}
        {hasActiveJob && (
          <button
            onClick={onExport}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-750 border border-slate-700 text-slate-200 text-xs font-semibold transition"
          >
            <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-400" />
            <span>Export Excel</span>
          </button>
        )}

        {/* Upload Manifest Button */}
        <button
          onClick={onOpenUpload}
          className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg bg-amber-400 hover:bg-amber-300 text-slate-950 text-xs font-bold transition shadow-sm active:scale-[0.98]"
        >
          <Upload className="w-3.5 h-3.5 stroke-[2.5]" />
          <span>Upload Manifest</span>
        </button>
      </div>
    </header>
  );
};
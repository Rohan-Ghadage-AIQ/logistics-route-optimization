import React, { useState, useCallback, useMemo } from 'react';
import { Navbar } from './components/Navbar';
import { UploadModal } from './components/UploadModal';
import { FleetPanel } from './components/FleetPanel';
import { JobStatusTimeline } from './components/JobStatusTimeline';
import { SummaryStats } from './components/SummaryStats';
import { RouteMap } from './components/RouteMap';
import { RightFilterPanel } from './components/RightFilterPanel';
import { useJobPolling, useFleet } from './hooks';
import { api } from './services/api';
import { Upload, Truck } from 'lucide-react';

const App: React.FC = () => {
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showFleetPanel, setShowFleetPanel] = useState(false);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [selectedRouteId, setSelectedRouteId] = useState<string | null>(null);

  const { job } = useJobPolling(activeJobId);
  const { fleet, loading: fleetLoading, addVehicle, updateVehicle, deleteVehicle } = useFleet();

  const isCompleted = job?.status === 'COMPLETED';
  const routes = useMemo(() => job?.routes || [], [job?.routes]);

  const handleJobCreated = useCallback((jobId: string) => {
    setActiveJobId(jobId);
    setSelectedRouteId(null);
  }, []);

  const handleRouteSelect = useCallback((routeId: string | null) => {
    setSelectedRouteId(routeId);
  }, []);

  const handleExport = useCallback(() => {
    if (!activeJobId) return;
    window.open(api.getExportUrl(activeJobId), '_blank');
  }, [activeJobId]);

  return (
    <div className="h-screen w-screen flex flex-col bg-slate-100 text-slate-900 overflow-hidden font-sans">
      {/* Top Navbar */}
      <Navbar
        onOpenUpload={() => setShowUploadModal(true)}
        onOpenFleet={() => setShowFleetPanel(true)}
        onExport={handleExport}
        hasActiveJob={!!job && isCompleted}
        valhallaConnected={true}
      />

      {/* Progress Timeline during execution */}
      {job && !isCompleted && (
        <JobStatusTimeline job={job} />
      )}

      {/* Top KPI Metrics Bar (Visible when routes are calculated) */}
      {isCompleted && job && (
        <SummaryStats job={job} />
      )}

      {/* Main Workspace (Map + Right Filter Panel) */}
      <div className="flex-1 flex relative overflow-hidden">
        {/* Full Interactive Map Canvas */}
        <div className="flex-1 h-full w-full relative">
          <RouteMap
            routes={routes}
            selectedRouteId={selectedRouteId}
            onRouteSelect={handleRouteSelect}
          />

          {/* Empty / Welcome Floating Banner when no job is active */}
          {(!job || routes.length === 0) && (
            <div className="absolute top-6 left-6 z-[1000] max-w-sm bg-white/95 backdrop-blur-md p-5 rounded-2xl border border-slate-200 shadow-xl">
              <div className="w-10 h-10 rounded-xl bg-slate-900 text-amber-400 flex items-center justify-center mb-3 shadow-md">
                <Truck className="w-5 h-5 stroke-[2.5]" />
              </div>
              <h2 className="text-base font-extrabold text-slate-900">Logistics Route Optimization</h2>
              <p className="text-xs text-slate-600 mt-1.5 leading-relaxed">
                Upload your delivery manifest (Excel / CSV) to automatically compute optimal vehicle routes, time windows, capacity limits, and turn-by-turn guidance.
              </p>
              <button
                onClick={() => setShowUploadModal(true)}
                className="mt-4 w-full py-2.5 px-4 rounded-xl bg-amber-400 hover:bg-amber-300 font-bold text-xs text-slate-950 shadow-md transition flex items-center justify-center gap-2 active:scale-[0.98]"
              >
                <Upload className="w-4 h-4 stroke-[2.5]" />
                Upload Manifest File
              </button>
            </div>
          )}

          {/* Map Info Badge (When active) */}
          {isCompleted && routes.length > 0 && (
            <div className="absolute top-4 left-4 bg-white/95 backdrop-blur-md rounded-xl px-3.5 py-1.5 text-xs text-slate-800 font-semibold flex items-center space-x-2 z-[1000] border border-slate-200 shadow-md">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
              <span>
                {selectedRouteId
                  ? `Viewing ${routes.find(r => r.id === selectedRouteId)?.vehicle_name || 'Vehicle Route'}`
                  : `All ${routes.length} vehicle routes (${routes.reduce((s, r) => s + r.total_stops, 0)} stops)`}
              </span>
            </div>
          )}
        </div>

        {/* Right-Side Vehicle Route Filter & Stop Inspection Panel */}
        {isCompleted && routes.length > 0 && (
          <RightFilterPanel
            routes={routes}
            selectedRouteId={selectedRouteId}
            onSelectRoute={handleRouteSelect}
          />
        )}
      </div>

      {/* Modals */}
      <UploadModal
        isOpen={showUploadModal}
        onClose={() => setShowUploadModal(false)}
        onJobCreated={handleJobCreated}
      />

      <FleetPanel
        isOpen={showFleetPanel}
        onClose={() => setShowFleetPanel(false)}
        fleet={fleet}
        loading={fleetLoading}
        onAdd={addVehicle}
        onUpdate={updateVehicle}
        onDelete={deleteVehicle}
      />
    </div>
  );
};

export default App;
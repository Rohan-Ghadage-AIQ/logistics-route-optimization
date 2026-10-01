import React from 'react';
import { Loader2, CheckCircle2, AlertCircle, FileCheck, MapPin, Grid, Cpu, Navigation } from 'lucide-react';
import { JobDetail } from '../types';

interface JobStatusTimelineProps {
  job: JobDetail;
}

interface StepItem {
  id: string;
  label: string;
  icon: React.ElementType;
}

const STEPS: StepItem[] = [
  { id: 'VALIDATING', label: 'Validate Manifest', icon: FileCheck },
  { id: 'GEOCODING', label: 'Geocoding', icon: MapPin },
  { id: 'MATRIX_GENERATION', label: 'Valhalla Matrix', icon: Grid },
  { id: 'OPTIMIZING', label: 'OR-Tools Engine', icon: Cpu },
  { id: 'ROUTE_GENERATION', label: 'Valhalla Routes', icon: Navigation },
];

export const JobStatusTimeline: React.FC<JobStatusTimelineProps> = ({ job }) => {
  const getStepStatus = (stepId: string) => {
    const stepOrder = ['PENDING', 'VALIDATING', 'GEOCODING', 'MATRIX_GENERATION', 'OPTIMIZING', 'ROUTE_GENERATION', 'COMPLETED'];
    const currentIdx = stepOrder.indexOf(job.status);
    const stepIdx = stepOrder.indexOf(stepId);

    if (job.status === 'FAILED') return 'failed';
    if (job.status === 'COMPLETED' || currentIdx > stepIdx) return 'completed';
    if (currentIdx === stepIdx) return 'active';
    return 'pending';
  };

  return (
    <div className="bg-white border-b border-slate-200 px-6 py-3 shadow-xs">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-2">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Active Job:</span>
            <span className="text-sm font-extrabold text-slate-900">{job.filename}</span>
            <span className="text-xs text-slate-400 font-mono">({job.job_id.slice(0, 8)})</span>
          </div>
          <p className="text-xs text-slate-600 mt-0.5 flex items-center gap-1.5 font-medium">
            {job.status !== 'COMPLETED' && job.status !== 'FAILED' && (
              <Loader2 className="w-3.5 h-3.5 text-amber-500 animate-spin" />
            )}
            <span>{job.current_step}</span>
          </p>
        </div>

        {/* Progress Bar */}
        <div className="w-full sm:w-64 flex flex-col items-end">
          <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden border border-slate-200">
            <div
              className={`h-full transition-all duration-500 ${
                job.status === 'FAILED'
                  ? 'bg-rose-500'
                  : job.status === 'COMPLETED'
                  ? 'bg-emerald-500'
                  : 'bg-amber-400'
              }`}
              style={{ width: `${job.progress_percentage}%` }}
            />
          </div>
          <span className="text-[11px] font-mono font-bold text-slate-600 mt-1">
            {job.progress_percentage}% Completed
          </span>
        </div>
      </div>

      {/* Steps Row */}
      <div className="grid grid-cols-5 gap-2 pt-2 border-t border-slate-100">
        {STEPS.map((step) => {
          const status = getStepStatus(step.id);
          const Icon = step.icon;

          return (
            <div
              key={step.id}
              className={`flex items-center space-x-2 p-1.5 rounded-lg text-xs transition ${
                status === 'completed'
                  ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                  : status === 'active'
                  ? 'bg-amber-50 text-amber-900 border border-amber-300 shadow-xs'
                  : status === 'failed'
                  ? 'bg-rose-50 text-rose-800 border border-rose-200'
                  : 'bg-slate-50 text-slate-400 border border-slate-200'
              }`}
            >
              {status === 'completed' && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />}
              {status === 'active' && <Loader2 className="w-3.5 h-3.5 text-amber-600 animate-spin shrink-0" />}
              {status === 'failed' && <AlertCircle className="w-3.5 h-3.5 text-rose-600 shrink-0" />}
              {status === 'pending' && <Icon className="w-3.5 h-3.5 text-slate-400 shrink-0" />}
              <span className="font-bold truncate hidden md:inline">{step.label}</span>
            </div>
          );
        })}
      </div>

      {/* Error Message if Failed */}
      {job.error_message && (
        <div className="mt-2.5 p-2.5 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center space-x-2 font-medium">
          <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
          <span>{job.error_message}</span>
        </div>
      )}
    </div>
  );
};
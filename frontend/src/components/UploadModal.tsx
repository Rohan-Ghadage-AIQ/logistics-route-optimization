import React, { useState, useRef, useCallback } from 'react';
import { Upload, X, FileSpreadsheet, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import { api } from '../services/api';

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onJobCreated: (jobId: string) => void;
}

type UploadState = 'idle' | 'dragging' | 'uploading' | 'success' | 'error';

export const UploadModal: React.FC<UploadModalProps> = ({ isOpen, onClose, onJobCreated }) => {
  const [state, setState] = useState<UploadState>('idle');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [errorMsg, setErrorMsg] = useState('');
  const [successJobId, setSuccessJobId] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const reset = useCallback(() => {
    setState('idle');
    setSelectedFile(null);
    setErrorMsg('');
    setSuccessJobId('');
  }, []);

  const handleClose = () => {
    reset();
    onClose();
  };

  const handleFileSelect = (file: File) => {
    const validExtensions = ['.xlsx', '.xls', '.csv'];
    const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();

    if (!validExtensions.includes(ext)) {
      setErrorMsg('Invalid file type. Please upload an Excel (.xlsx, .xls) or CSV (.csv) file.');
      setState('error');
      return;
    }
    if (file.size > 50 * 1024 * 1024) {
      setErrorMsg('File size exceeds 50MB limit.');
      setState('error');
      return;
    }
    setSelectedFile(file);
    setErrorMsg('');
    setState('idle');
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setState('idle');
    const file = e.dataTransfer.files[0];
    if (file) handleFileSelect(file);
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    setState('uploading');
    setErrorMsg('');
    try {
      const result = await api.uploadManifest(selectedFile);
      setSuccessJobId(result.job_id);
      setState('success');
      setTimeout(() => {
        onJobCreated(result.job_id);
        handleClose();
      }, 1000);
    } catch (err: any) {
      setErrorMsg(err?.response?.data?.detail || err.message || 'Upload failed.');
      setState('error');
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-slate-950/60 backdrop-blur-sm"
        onClick={handleClose}
      />

      {/* Modal Card */}
      <div className="relative w-full max-w-lg bg-white border border-slate-200 rounded-2xl shadow-2xl overflow-hidden z-10">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 bg-slate-50">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-slate-900 text-amber-400 flex items-center justify-center shadow-sm">
              <Upload className="w-5 h-5 stroke-[2.5]" />
            </div>
            <div>
              <h2 className="text-base font-extrabold text-slate-900">Upload Delivery Manifest</h2>
              <p className="text-xs text-slate-500">Excel (.xlsx, .xls) or CSV delivery order sheet</p>
            </div>
          </div>
          <button
            onClick={handleClose}
            className="p-1.5 rounded-lg hover:bg-slate-200 text-slate-500 hover:text-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-4">
          {/* Drop Zone & File Selector */}
          <div
            className={`border-2 border-dashed rounded-xl p-6 text-center transition-all ${
              state === 'dragging'
                ? 'border-amber-500 bg-amber-50'
                : state === 'error'
                ? 'border-rose-400 bg-rose-50'
                : state === 'success'
                ? 'border-emerald-500 bg-emerald-50'
                : 'border-slate-300 hover:border-slate-400 bg-slate-50/80'
            }`}
            onDragOver={(e) => { e.preventDefault(); setState('dragging'); }}
            onDragLeave={() => setState('idle')}
            onDrop={handleDrop}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".xlsx,.xls,.csv"
              style={{ display: 'none' }}
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) handleFileSelect(f);
              }}
            />

            {state === 'uploading' ? (
              <div className="flex flex-col items-center py-4 space-y-2">
                <Loader2 className="w-9 h-9 text-amber-500 animate-spin" />
                <p className="text-sm font-bold text-slate-800">Processing Orders & Routing...</p>
                <p className="text-xs text-slate-500">Calculating Valhalla road matrices & OR-Tools schedules</p>
              </div>
            ) : state === 'success' ? (
              <div className="flex flex-col items-center py-4 space-y-2">
                <CheckCircle2 className="w-9 h-9 text-emerald-600" />
                <p className="text-sm font-bold text-emerald-800">Manifest Loaded Successfully!</p>
                <p className="text-xs text-slate-500 font-mono">Job ID: {successJobId.slice(0, 8)}...</p>
              </div>
            ) : (
              <div className="flex flex-col items-center py-2 space-y-3">
                <FileSpreadsheet className={`w-12 h-12 ${selectedFile ? 'text-emerald-600' : 'text-slate-700'}`} />
                {selectedFile ? (
                  <div>
                    <p className="text-sm font-bold text-slate-900">{selectedFile.name}</p>
                    <p className="text-xs text-emerald-700 font-mono mt-0.5">
                      {(selectedFile.size / 1024).toFixed(1)} KB &bull; Ready to optimize
                    </p>
                  </div>
                ) : (
                  <div>
                    <p className="text-sm font-bold text-slate-800">
                      Drag and drop your Excel / CSV manifest here
                    </p>
                    <p className="text-xs text-slate-500 mt-1">Accepts consignments, addresses, weights & time windows</p>
                  </div>
                )}

                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="px-4 py-2 rounded-lg bg-white hover:bg-slate-100 border border-slate-300 text-xs font-bold text-slate-800 transition shadow-xs"
                >
                  {selectedFile ? 'Choose Different File' : 'Browse Computer Files'}
                </button>
              </div>
            )}
          </div>

          {/* Error Message */}
          {state === 'error' && errorMsg && (
            <div className="flex items-center space-x-2 px-3.5 py-2.5 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-xs font-medium">
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Expected Columns Info */}
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-600 space-y-1.5">
            <p className="font-bold text-slate-800">Detected Manifest Columns:</p>
            <div className="flex flex-wrap gap-1.5">
              {['address', 'weight_kg', 'window_start', 'window_end', 'consignment_id'].map((col) => (
                <span key={col} className="px-2 py-0.5 rounded bg-white border border-slate-200 text-slate-700 font-mono text-[11px]">
                  {col}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-200 bg-slate-50 flex justify-end space-x-3">
          <button
            type="button"
            onClick={handleClose}
            className="px-4 py-2 rounded-lg text-xs font-semibold text-slate-700 bg-white border border-slate-300 hover:bg-slate-100 transition"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleUpload}
            disabled={!selectedFile || state === 'uploading' || state === 'success'}
            className="px-5 py-2 rounded-lg text-xs font-bold text-slate-950 bg-amber-400 hover:bg-amber-300 transition shadow-sm disabled:opacity-40 disabled:cursor-not-allowed active:scale-95 flex items-center gap-1.5"
          >
            {state === 'uploading' ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>Optimizing...</span>
              </>
            ) : (
              <span>Start Optimization</span>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
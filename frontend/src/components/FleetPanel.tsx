import React, { useState } from 'react';
import { X, Truck, Plus, Trash2, Edit3, Save, Loader2, Check, Clock, Weight } from 'lucide-react';
import { FleetVehicle } from '../types';

interface FleetPanelProps {
  isOpen: boolean;
  onClose: () => void;
  fleet: FleetVehicle[];
  loading: boolean;
  onAdd: (data: Partial<FleetVehicle>) => Promise<FleetVehicle>;
  onUpdate: (id: number, data: Partial<FleetVehicle>) => Promise<FleetVehicle>;
  onDelete: (id: number) => Promise<void>;
}

const minutesToTime = (m: number = 480): string => {
  const h = Math.floor(m / 60);
  const min = m % 60;
  return `${h.toString().padStart(2, '0')}:${min.toString().padStart(2, '0')}`;
};

const timeToMinutes = (t: string): number => {
  if (!t) return 480;
  const [h, m] = t.split(':').map(Number);
  return (h || 0) * 60 + (m || 0);
};

interface VehicleForm {
  name: string;
  capacity_kg: number;
  cost_per_km: number;
  shift_start: string;
  shift_end: string;
}

const DEFAULT_FORM: VehicleForm = {
  name: '',
  capacity_kg: 500,
  cost_per_km: 12,
  shift_start: '07:00',
  shift_end: '19:00',
};

export const FleetPanel: React.FC<FleetPanelProps> = ({
  isOpen,
  onClose,
  fleet,
  loading,
  onAdd,
  onUpdate,
  onDelete,
}) => {
  const [showAddForm, setShowAddForm] = useState(false);
  const [editId, setEditId] = useState<number | null>(null);
  const [form, setForm] = useState<VehicleForm>({ ...DEFAULT_FORM });
  const [saving, setSaving] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  const handleSaveNew = async () => {
    if (!form.name.trim()) return;
    setSaving(true);
    try {
      await onAdd({
        name: form.name.trim(),
        capacity_kg: Number(form.capacity_kg) || 500,
        cost_per_km: Number(form.cost_per_km) || 12,
        shift_start_minutes: timeToMinutes(form.shift_start),
        shift_end_minutes: timeToMinutes(form.shift_end),
        is_active: true,
      });
      setShowAddForm(false);
      setForm({ ...DEFAULT_FORM });
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (v: FleetVehicle) => {
    setEditId(v.id);
    setForm({
      name: v.name,
      capacity_kg: v.capacity_kg,
      cost_per_km: v.cost_per_km,
      shift_start: minutesToTime(v.shift_start_minutes),
      shift_end: minutesToTime(v.shift_end_minutes),
    });
  };

  const handleSaveEdit = async () => {
    if (!editId || !form.name.trim()) return;
    setSaving(true);
    try {
      await onUpdate(editId, {
        name: form.name.trim(),
        capacity_kg: Number(form.capacity_kg) || 500,
        cost_per_km: Number(form.cost_per_km) || 12,
        shift_start_minutes: timeToMinutes(form.shift_start),
        shift_end_minutes: timeToMinutes(form.shift_end),
      });
      setEditId(null);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (fleet.length <= 1) return;
    setDeletingId(id);
    try {
      await onDelete(id);
    } finally {
      setDeletingId(null);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-slate-950/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal Container */}
      <div className="relative w-full max-w-3xl max-h-[90vh] bg-white border border-slate-200 rounded-2xl shadow-2xl overflow-hidden z-10 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 bg-slate-50 shrink-0">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-slate-900 text-amber-400 flex items-center justify-center shadow-sm">
              <Truck className="w-5 h-5 stroke-[2.5]" />
            </div>
            <div>
              <h2 className="text-base font-extrabold text-slate-900">Fleet Management</h2>
              <p className="text-xs text-slate-500">Configure vehicle capacity, working shifts & cost constraints</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            {!showAddForm && (
              <button
                onClick={() => {
                  setShowAddForm(true);
                  setForm({ ...DEFAULT_FORM, name: `Vehicle ${fleet.length + 1}` });
                }}
                className="px-3.5 py-1.5 rounded-lg bg-amber-400 hover:bg-amber-300 text-slate-950 font-bold text-xs flex items-center gap-1.5 shadow-sm transition"
              >
                <Plus className="w-3.5 h-3.5 stroke-[2.5]" />
                <span>Add Vehicle</span>
              </button>
            )}
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg hover:bg-slate-200 text-slate-500 hover:text-slate-800 transition"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Body Content */}
        <div className="p-6 overflow-y-auto space-y-4 flex-1">
          {/* Add Vehicle Inline Form */}
          {showAddForm && (
            <div className="p-4 rounded-xl bg-slate-50 border border-amber-400/60 space-y-3">
              <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">New Vehicle Parameters</h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                <div>
                  <label className="block text-slate-600 font-semibold mb-1">Vehicle Name</label>
                  <input
                    type="text"
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                    className="w-full px-3 py-1.5 rounded-lg bg-white border border-slate-300 text-slate-900 font-semibold focus:outline-none focus:border-amber-500"
                    placeholder="e.g. Delivery Van 11"
                  />
                </div>
                <div>
                  <label className="block text-slate-600 font-semibold mb-1">Max Payload (kg)</label>
                  <input
                    type="number"
                    value={form.capacity_kg}
                    onChange={(e) => setForm({ ...form, capacity_kg: Number(e.target.value) })}
                    className="w-full px-3 py-1.5 rounded-lg bg-white border border-slate-300 text-slate-900 font-semibold focus:outline-none focus:border-amber-500"
                  />
                </div>
                <div>
                  <label className="block text-slate-600 font-semibold mb-1">Shift Start</label>
                  <input
                    type="time"
                    value={form.shift_start}
                    onChange={(e) => setForm({ ...form, shift_start: e.target.value })}
                    className="w-full px-3 py-1.5 rounded-lg bg-white border border-slate-300 text-slate-900 font-semibold font-mono focus:outline-none focus:border-amber-500"
                  />
                </div>
                <div>
                  <label className="block text-slate-600 font-semibold mb-1">Shift End</label>
                  <input
                    type="time"
                    value={form.shift_end}
                    onChange={(e) => setForm({ ...form, shift_end: e.target.value })}
                    className="w-full px-3 py-1.5 rounded-lg bg-white border border-slate-300 text-slate-900 font-semibold font-mono focus:outline-none focus:border-amber-500"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  onClick={() => setShowAddForm(false)}
                  className="px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-600 hover:bg-slate-200 transition"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSaveNew}
                  disabled={saving || !form.name.trim()}
                  className="px-4 py-1.5 rounded-lg bg-amber-400 hover:bg-amber-300 text-slate-950 font-bold text-xs transition flex items-center gap-1.5 shadow-sm disabled:opacity-50"
                >
                  {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5 stroke-[2.5]" />}
                  Save Vehicle to Fleet
                </button>
              </div>
            </div>
          )}

          {/* Vehicle List */}
          {loading ? (
            <div className="py-12 flex flex-col items-center justify-center text-slate-500">
              <Loader2 className="w-6 h-6 animate-spin text-amber-500 mb-2" />
              <span className="text-xs font-semibold">Loading fleet configuration...</span>
            </div>
          ) : fleet.length === 0 ? (
            <div className="py-12 text-center text-slate-500 text-xs">
              No vehicles configured. Click "Add Vehicle" to register vans.
            </div>
          ) : (
            <div className="space-y-2">
              {fleet.map((vehicle, idx) => {
                const isEditing = editId === vehicle.id;

                if (isEditing) {
                  return (
                    <div key={vehicle.id} className="p-4 rounded-xl bg-slate-50 border border-amber-400/60 space-y-3">
                      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                        <div>
                          <label className="block text-slate-600 font-semibold mb-1">Vehicle Name</label>
                          <input
                            type="text"
                            value={form.name}
                            onChange={(e) => setForm({ ...form, name: e.target.value })}
                            className="w-full px-3 py-1.5 rounded-lg bg-white border border-slate-300 text-slate-900 font-semibold"
                          />
                        </div>
                        <div>
                          <label className="block text-slate-600 font-semibold mb-1">Capacity (kg)</label>
                          <input
                            type="number"
                            value={form.capacity_kg}
                            onChange={(e) => setForm({ ...form, capacity_kg: Number(e.target.value) })}
                            className="w-full px-3 py-1.5 rounded-lg bg-white border border-slate-300 text-slate-900 font-semibold"
                          />
                        </div>
                        <div>
                          <label className="block text-slate-600 font-semibold mb-1">Shift Start</label>
                          <input
                            type="time"
                            value={form.shift_start}
                            onChange={(e) => setForm({ ...form, shift_start: e.target.value })}
                            className="w-full px-3 py-1.5 rounded-lg bg-white border border-slate-300 text-slate-900 font-semibold font-mono"
                          />
                        </div>
                        <div>
                          <label className="block text-slate-600 font-semibold mb-1">Shift End</label>
                          <input
                            type="time"
                            value={form.shift_end}
                            onChange={(e) => setForm({ ...form, shift_end: e.target.value })}
                            className="w-full px-3 py-1.5 rounded-lg bg-white border border-slate-300 text-slate-900 font-semibold font-mono"
                          />
                        </div>
                      </div>

                      <div className="flex justify-end gap-2 pt-1">
                        <button
                          onClick={() => setEditId(null)}
                          className="px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-600 hover:bg-slate-200"
                        >
                          Cancel
                        </button>
                        <button
                          onClick={handleSaveEdit}
                          disabled={saving}
                          className="px-3.5 py-1.5 rounded-lg bg-amber-400 hover:bg-amber-300 text-slate-950 font-bold text-xs flex items-center gap-1.5 shadow-sm"
                        >
                          {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5 stroke-[2.5]" />}
                          Save Changes
                        </button>
                      </div>
                    </div>
                  );
                }

                return (
                  <div
                    key={vehicle.id}
                    className="p-3.5 rounded-xl bg-white border border-slate-200 hover:border-slate-300 transition flex items-center justify-between shadow-xs"
                  >
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 rounded-lg bg-slate-100 border border-slate-200 flex items-center justify-center font-bold text-xs text-slate-800">
                        V{idx + 1}
                      </div>
                      <div>
                        <h4 className="font-bold text-xs text-slate-900 flex items-center gap-2">
                          <span>{vehicle.name}</span>
                          <span className="text-[10px] font-bold px-2 py-0.2 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                            Active
                          </span>
                        </h4>
                        <div className="flex items-center gap-3 text-[11px] text-slate-500 mt-1">
                          <span className="flex items-center gap-1">
                            <Weight className="w-3 h-3 text-slate-400" />
                            <strong>{vehicle.capacity_kg} kg</strong> capacity
                          </span>
                          <span>&bull;</span>
                          <span className="flex items-center gap-1 font-mono">
                            <Clock className="w-3 h-3 text-slate-400" />
                            {minutesToTime(vehicle.shift_start_minutes)} - {minutesToTime(vehicle.shift_end_minutes)}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => handleEdit(vehicle)}
                        className="p-1.5 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition"
                        title="Edit Vehicle"
                      >
                        <Edit3 className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(vehicle.id)}
                        disabled={deletingId === vehicle.id || fleet.length <= 1}
                        className="p-1.5 rounded-lg text-slate-500 hover:text-rose-600 hover:bg-slate-100 transition disabled:opacity-30"
                        title={fleet.length <= 1 ? "At least 1 vehicle required" : "Delete Vehicle"}
                      >
                        {deletingId === vehicle.id ? (
                          <Loader2 className="w-4 h-4 animate-spin text-rose-500" />
                        ) : (
                          <Trash2 className="w-4 h-4" />
                        )}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-slate-200 bg-slate-50 flex items-center justify-between text-xs text-slate-500 shrink-0">
          <span>Fleet parameters automatically enforce OR-Tools vehicle capacity & shift boundaries.</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-white font-bold transition shadow-xs"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
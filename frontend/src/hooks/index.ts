import { useState, useEffect, useCallback, useRef } from 'react';
import { JobDetail, FleetVehicle } from '../types';
import { api } from '../services/api';

/** Custom hook — polls job status and fetches full details upon completion. */
export function useJobPolling(jobId: string | null) {
  const [job, setJob] = useState<JobDetail | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setIsPolling(false);
  }, []);

  const fetchFull = useCallback(async (id: string) => {
    try {
      const details = await api.getJobDetails(id);
      setJob(details);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch job details');
    }
  }, []);

  useEffect(() => {
    if (!jobId) {
      stopPolling();
      return;
    }

    setIsPolling(true);
    setError(null);

    const poll = async () => {
      try {
        const status = await api.getJobStatus(jobId);

        // Update local state with lightweight polling data
        setJob(prev => prev ? { ...prev, ...status } : status as any);

        if (status.status === 'COMPLETED' || status.status === 'FAILED') {
          stopPolling();
          // Fetch full detail payload (routes, orders, geometry)
          await fetchFull(jobId);
        }
      } catch (err: any) {
        setError(err.message || 'Failed to poll job status');
        stopPolling();
      }
    };

    // Initial immediate poll
    poll();

    // Then poll every 2 seconds
    intervalRef.current = setInterval(poll, 2000);

    return () => stopPolling();
  }, [jobId, stopPolling, fetchFull]);

  return { job, isPolling, error };
}

/** Custom hook — manages fleet CRUD state. */
export function useFleet() {
  const [fleet, setFleet] = useState<FleetVehicle[]>([]);
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.getFleet();
      setFleet(data);
    } catch {
      // fail silently — fleet panel will show empty
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const addVehicle = async (data: Partial<FleetVehicle>) => {
    const created = await api.createVehicle(data);
    setFleet(prev => [...prev, created]);
    return created;
  };

  const updateVehicle = async (id: number, data: Partial<FleetVehicle>) => {
    const updated = await api.updateVehicle(id, data);
    setFleet(prev => prev.map(v => v.id === id ? updated : v));
    return updated;
  };

  const deleteVehicle = async (id: number) => {
    await api.deleteVehicle(id);
    setFleet(prev => prev.filter(v => v.id !== id));
  };

  return { fleet, loading, refresh, addVehicle, updateVehicle, deleteVehicle };
}

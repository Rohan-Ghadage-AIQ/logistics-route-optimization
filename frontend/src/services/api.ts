import axios from 'axios';
import { JobDetail, FleetVehicle } from '../types';

const API_BASE = '/api/v1';

export const api = {
  // Job Operations
  async uploadManifest(file: File): Promise<{ job_id: string; filename: string; status: string }> {
    const formData = new FormData();
    formData.append('file', file);
    const response = await axios.post(`${API_BASE}/jobs/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  async getJobStatus(jobId: string): Promise<JobDetail> {
    const response = await axios.get(`${API_BASE}/jobs/${jobId}/status`);
    return response.data;
  },

  async getJobDetails(jobId: string): Promise<JobDetail> {
    const response = await axios.get(`${API_BASE}/jobs/${jobId}`);
    return response.data;
  },

  async listJobs(): Promise<JobDetail[]> {
    const response = await axios.get(`${API_BASE}/jobs`);
    return response.data;
  },

  getExportUrl(jobId: string): string {
    return `${API_BASE}/jobs/${jobId}/export`;
  },

  // Fleet Operations
  async getFleet(): Promise<FleetVehicle[]> {
    const response = await axios.get(`${API_BASE}/fleet`);
    return response.data;
  },

  async createVehicle(data: Partial<FleetVehicle>): Promise<FleetVehicle> {
    const response = await axios.post(`${API_BASE}/fleet`, data);
    return response.data;
  },

  async updateVehicle(id: number, data: Partial<FleetVehicle>): Promise<FleetVehicle> {
    const response = await axios.put(`${API_BASE}/fleet/${id}`, data);
    return response.data;
  },

  async deleteVehicle(id: number): Promise<void> {
    await axios.delete(`${API_BASE}/fleet/${id}`);
  },

  // Health
  async getHealth(): Promise<any> {
    const response = await axios.get(`${API_BASE}/health`);
    return response.data;
  }
};

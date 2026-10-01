export interface RouteStopDetail {
  sequence: number;
  stop_type: string; // 'DEPOT_START' | 'DELIVERY' | 'DEPOT_RETURN'
  order_id?: string;
  external_order_id?: string;
  address: string;
  latitude: number;
  longitude: number;
  parcel_weight_kg: number;
  estimated_arrival_minutes: number;
  estimated_arrival_time_str: string;
  waiting_time_minutes?: number;
  service_start_minutes?: number;
  service_start_time_str?: string;
  service_time_minutes: number;
  departure_minutes?: number;
  departure_time_str?: string;
  window_start_minutes?: number;
  window_end_minutes?: number;
  window_start_str?: string;
  window_end_str?: string;
  is_late: boolean;
  lateness_minutes: number;
  time_window_status?: 'ON_TIME' | 'EARLY_WAITING' | 'LATE_VIOLATION';
}

export interface RouteLegDetail {
  leg_index: number;
  from_name: string;
  to_name: string;
  from_type: string;
  to_type: string;
  distance_km: number;
  driving_duration_minutes: number;
  departure_time_str?: string;
  arrival_time_str?: string;
  geometry?: {
    type: string;
    coordinates: [number, number][];
  };
  maneuvers: Array<{
    instruction: string;
    distance_km: number;
    duration_minutes: number;
    street_name?: string;
    type?: string;
  }>;
}

export interface RouteTimelineEvent {
  time_str: string;
  time_minutes: number;
  type: string;
  title: string;
  description: string;
  address: string;
  stop_sequence?: number;
  waiting_minutes?: number;
  service_minutes?: number;
  is_violation?: boolean;
}

export interface RouteItem {
  id: string;
  vehicle_id: number;
  vehicle_name: string;
  capacity_kg?: number;
  total_payload_kg: number;
  capacity_utilization_pct: number;
  is_over_capacity?: boolean;
  total_stops: number;
  
  // Strict Duration Breakdown (Single Source of Truth)
  total_distance_km: number;
  driving_duration_minutes?: number;
  service_duration_minutes?: number;
  waiting_duration_minutes?: number;
  total_duration_minutes: number;
  
  start_time_minutes?: number;
  start_time_str?: string;
  end_time_minutes?: number;
  end_time_str?: string;
  
  operational_cost: number;
  geometry?: {
    type: string;
    coordinates: [number, number][];
  };
  maneuvers?: Array<{
    instruction: string;
    distance_km: number;
    duration_minutes: number;
    street_name?: string;
    type?: string;
  }>;
  legs?: RouteLegDetail[];
  stops: RouteStopDetail[];
  timeline?: RouteTimelineEvent[];
  validation?: {
    is_valid?: boolean;
    errors?: string[];
    warnings?: string[];
    [key: string]: any;
  };
}

export interface OrderItem {
  id: string;
  job_id: string;
  external_order_id: string;
  raw_address: string;
  resolved_address?: string;
  latitude?: number;
  longitude?: number;
  parcel_weight_kg: number;
  service_time_minutes: number;
  window_start_minutes: number;
  window_end_minutes: number;
  geocoding_status: string;
  geocoding_error?: string;
  is_assigned: boolean;
  unassigned_reason?: string;
  assigned_vehicle_id?: number;
  stop_sequence?: number;
  estimated_arrival_time_str?: string;
}

export interface OptimizationSummary {
  total_orders: number;
  assigned_orders: number;
  unassigned_orders: number;
  vehicles_available: number;
  vehicles_used: number;
  total_distance_km: number;
  total_driving_minutes?: number;
  total_service_minutes?: number;
  total_waiting_minutes?: number;
  total_duration_minutes: number;
  total_cost: number;
  average_capacity_utilization_pct: number;
  unassigned_details: Array<{
    order_id: string;
    address: string;
    reason: string;
  }>;
}

export interface JobDetail {
  job_id: string;
  filename: string;
  status: 'PENDING' | 'VALIDATING' | 'GEOCODING' | 'MATRIX_GENERATION' | 'OPTIMIZING' | 'ROUTE_GENERATION' | 'COMPLETED' | 'FAILED';
  current_step: string;
  progress_percentage: number;
  error_message?: string;
  created_at: string;
  completed_at?: string;
  total_orders: number;
  assigned_orders: number;
  unassigned_orders: number;
  vehicles_used: number;
  total_distance_km: number;
  total_duration_minutes: number;
  total_cost: number;
  summary?: OptimizationSummary;
  routes: RouteItem[];
  orders: OrderItem[];
}

export interface FleetVehicle {
  id: number;
  name: string;
  capacity_kg: number;
  cost_per_km: number;
  shift_start_minutes: number;
  shift_end_minutes: number;
  is_active: boolean;
  shift_start_str?: string;
  shift_end_str?: string;
}

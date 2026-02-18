// TypeScript types for FactoryOps

// Authentication
export interface User {
  id: number;
  email: string;
  role: 'super_admin' | 'admin';
  permissions: Record<string, boolean>;
  last_login?: string;
}

export interface Factory {
  id: number;
  name: string;
  slug: string;
  timezone?: string;
}

export interface AuthState {
  user: User | null;
  factory: Factory | null;
  token: string | null;
  isAuthenticated: boolean;
}

// Devices
export interface Device {
  id: number;
  device_key: string;
  name?: string;
  manufacturer?: string;
  model?: string;
  region?: string;
  is_active: boolean;
  last_seen?: string;
  api_key?: string;
  created_at: string;
  updated_at: string;
}

export interface DeviceListItem extends Device {
  health_score: number;
  current_energy_kw: number;
  active_alert_count: number;
}

export interface DeviceCreate {
  device_key: string;
  name?: string;
  manufacturer?: string;
  model?: string;
  region?: string;
}

export interface DeviceUpdate {
  name?: string;
  manufacturer?: string;
  model?: string;
  region?: string;
  is_active?: boolean;
}

// Parameters
export interface DeviceParameter {
  id: number;
  parameter_key: string;
  display_name?: string;
  unit?: string;
  data_type: 'float' | 'int' | 'string';
  is_kpi_selected: boolean;
  discovered_at: string;
  updated_at: string;
}

export interface ParameterUpdate {
  display_name?: string;
  unit?: string;
  is_kpi_selected?: boolean;
}

// KPIs
export interface KPIValue {
  parameter_key: string;
  display_name?: string;
  unit?: string;
  value: number;
  is_stale: boolean;
}

export interface KPILiveResponse {
  device_id: number;
  timestamp: string;
  kpis: KPIValue[];
}

export interface DataPoint {
  timestamp: string;
  value: number;
}

export interface KPIHistoryResponse {
  parameter_key: string;
  display_name?: string;
  unit?: string;
  interval: string;
  points: DataPoint[];
}

export interface KPIHistoryParams {
  parameter: string;
  start: string;
  end: string;
  interval?: '1m' | '5m' | '1h' | '1d';
}

// Rules
export interface ConditionLeaf {
  parameter: string;
  operator: 'gt' | 'lt' | 'gte' | 'lte' | 'eq' | 'neq';
  value: number;
}

export interface ConditionTree {
  operator: 'AND' | 'OR';
  conditions: (ConditionLeaf | ConditionTree)[];
}

export interface Rule {
  id: number;
  name: string;
  description?: string;
  scope: 'device' | 'global';
  is_active: boolean;
  conditions: ConditionTree;
  cooldown_minutes: number;
  severity: 'low' | 'medium' | 'high' | 'critical';
  schedule_type: 'always' | 'time_window' | 'date_range';
  schedule_config?: {
    start_time?: string;
    end_time?: string;
    days?: number[];
    start_date?: string;
    end_date?: string;
  };
  notification_channels?: {
    email: boolean;
    whatsapp: boolean;
  };
  device_ids: number[];
  created_at: string;
  updated_at: string;
}

export interface RuleCreate {
  name: string;
  description?: string;
  scope: 'device' | 'global';
  device_ids: number[];
  conditions: ConditionTree;
  cooldown_minutes: number;
  severity: 'low' | 'medium' | 'high' | 'critical';
  schedule_type: 'always' | 'time_window' | 'date_range';
  schedule_config?: Rule['schedule_config'];
  notification_channels?: Rule['notification_channels'];
}

export interface RuleUpdate extends Partial<RuleCreate> {
  is_active?: boolean;
}

// Alerts
export interface Alert {
  id: number;
  rule_id: number;
  rule_name?: string;
  device_id: number;
  device_name?: string;
  triggered_at: string;
  resolved_at?: string;
  severity: string;
  message?: string;
  telemetry_snapshot?: Record<string, number>;
}

export interface AlertFilters {
  device_id?: number;
  severity?: string;
  resolved?: boolean;
  start?: string;
  end?: string;
}

// Analytics
export interface AnalyticsJob {
  id: string;
  factory_id: number;
  created_by: number;
  job_type: 'anomaly' | 'failure_prediction' | 'energy_forecast' | 'ai_copilot';
  mode: 'standard' | 'ai_copilot';
  device_ids: number[];
  date_range_start: string;
  date_range_end: string;
  status: 'pending' | 'running' | 'complete' | 'failed';
  result_url?: string;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
}

export interface StartAnalyticsJobRequest {
  job_type: AnalyticsJob['job_type'];
  mode?: 'standard' | 'ai_copilot';
  device_ids: number[];
  date_range_start: string;
  date_range_end: string;
}

// Reports
export interface Report {
  id: string;
  factory_id: number;
  created_by: number;
  title?: string;
  device_ids: number[];
  date_range_start: string;
  date_range_end: string;
  format: 'pdf' | 'excel' | 'json';
  include_analytics: boolean;
  analytics_job_id?: string;
  status: 'pending' | 'running' | 'complete' | 'failed';
  file_url?: string;
  file_size_bytes?: number;
  error_message?: string;
  expires_at?: string;
  created_at: string;
}

export interface CreateReportRequest {
  title?: string;
  device_ids: number[];
  date_range_start: string;
  date_range_end: string;
  format: 'pdf' | 'excel' | 'json';
  include_analytics: boolean;
  analytics_job_id?: string;
}

// Dashboard
export interface DashboardSummary {
  total_devices: number;
  active_devices: number;
  offline_devices: number;
  current_energy_kw: number;
  active_alerts: number;
  critical_alerts: number;
  health_score: number;
  energy_today_kwh: number;
  energy_this_month_kwh: number;
}

// Users
export interface FactoryUser {
  id: number;
  email: string;
  whatsapp_number?: string;
  role: string;
  is_active: boolean;
  permissions: Record<string, boolean>;
  last_login?: string;
}

export interface InviteUserRequest {
  email: string;
  whatsapp_number?: string;
  permissions: Record<string, boolean>;
}

// Pagination
export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  per_page: number;
}

// UI
export interface AppNotification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
}

export interface UIState {
  sidebarOpen: boolean;
  notifications: AppNotification[];
}

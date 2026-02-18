// Typed API endpoints
import { api, extractData } from './client';
import {
  Factory,
  User,
  Device,
  DeviceCreate,
  DeviceUpdate,
  DeviceListItem,
  DeviceParameter,
  ParameterUpdate,
  KPIValue,
  KPIHistoryResponse,
  KPIHistoryParams,
  Rule,
  RuleCreate,
  RuleUpdate,
  Alert,
  AlertFilters,
  AnalyticsJob,
  StartAnalyticsJobRequest,
  Report,
  CreateReportRequest,
  DashboardSummary,
  FactoryUser,
  InviteUserRequest,
  PaginatedResponse,
} from '../types';

// Auth endpoints
export const auth = {
  listFactories: () => api.get<{ data: Factory[] }>('/factories').then(r => extractData(r)),
  
  login: (factory_id: number, email: string, password: string) =>
    api.post<{ data: { access_token: string; token_type: string; expires_in: number; user: User } }>(
      '/auth/login',
      { factory_id, email, password }
    ).then(r => extractData(r)),
  
  refresh: () =>
    api.post<{ data: { access_token: string; token_type: string; expires_in: number } }>('/auth/refresh')
      .then(r => extractData(r)),
};

// Devices endpoints
export const devices = {
  list: (params?: { page?: number; per_page?: number; search?: string; is_active?: boolean }) =>
    api.get<{ data: PaginatedResponse<DeviceListItem> }>('/devices', { params })
      .then(r => extractData(r)),
  
  getById: (deviceId: number) =>
    api.get<{ data: Device }>(`/devices/${deviceId}`).then(r => extractData(r)),
  
  create: (data: DeviceCreate) =>
    api.post<{ data: Device }>('/devices', data).then(r => extractData(r)),
  
  update: (deviceId: number, data: DeviceUpdate) =>
    api.patch<{ data: Device }>(`/devices/${deviceId}`, data).then(r => extractData(r)),
  
  delete: (deviceId: number) =>
    api.delete(`/devices/${deviceId}`),
};

// Parameters endpoints
export const parameters = {
  list: (deviceId: number) =>
    api.get<{ data: { data: DeviceParameter[] } }>(`/devices/${deviceId}/parameters`)
      .then(r => extractData(r).data),
  
  update: (deviceId: number, paramId: number, data: ParameterUpdate) =>
    api.patch<{ data: DeviceParameter }>(`/devices/${deviceId}/parameters/${paramId}`, data)
      .then(r => extractData(r)),
};

// KPIs endpoints
export const kpis = {
  getLive: (deviceId: number) =>
    api.get<{ data: { device_id: number; timestamp: string; kpis: KPIValue[] } }>(
      `/devices/${deviceId}/kpis/live`
    ).then(r => extractData(r)),
  
  getHistory: (deviceId: number, params: KPIHistoryParams) =>
    api.get<{ data: KPIHistoryResponse }>(`/devices/${deviceId}/kpis/history`, { params })
      .then(r => extractData(r)),
};

// Rules endpoints
export const rules = {
  list: (params?: { device_id?: number; is_active?: boolean; scope?: string; page?: number; per_page?: number }) =>
    api.get<{ data: PaginatedResponse<Rule> }>('/rules', { params })
      .then(r => extractData(r)),
  
  getById: (ruleId: number) =>
    api.get<{ data: Rule }>(`/rules/${ruleId}`).then(r => extractData(r)),
  
  create: (data: RuleCreate) =>
    api.post<{ data: Rule }>('/rules', data).then(r => extractData(r)),
  
  update: (ruleId: number, data: RuleUpdate) =>
    api.patch<{ data: Rule }>(`/rules/${ruleId}`, data).then(r => extractData(r)),
  
  delete: (ruleId: number) =>
    api.delete(`/rules/${ruleId}`),
  
  toggle: (ruleId: number) =>
    api.patch<{ data: Rule }>(`/rules/${ruleId}/toggle`).then(r => extractData(r)),
};

// Alerts endpoints
export const alerts = {
  list: (params?: AlertFilters & { page?: number; per_page?: number }) =>
    api.get<{ data: PaginatedResponse<Alert> }>('/alerts', { params })
      .then(r => extractData(r)),
  
  getById: (alertId: number) =>
    api.get<{ data: Alert }>(`/alerts/${alertId}`).then(r => extractData(r)),
  
  resolve: (alertId: number) =>
    api.patch<{ data: { id: number; resolved_at: string } }>(`/alerts/${alertId}/resolve`)
      .then(r => extractData(r)),
};

// Analytics endpoints
export const analytics = {
  startJob: (data: StartAnalyticsJobRequest) =>
    api.post<{ data: { job_id: string; status: string } }>('/analytics/jobs', data)
      .then(r => extractData(r)),
  
  getJob: (jobId: string) =>
    api.get<{ data: AnalyticsJob }>(`/analytics/jobs/${jobId}`)
      .then(r => extractData(r)),
};

// Reports endpoints
export const reports = {
  list: (params?: { status?: string; page?: number; per_page?: number }) =>
    api.get<{ data: Report[]; total: number; page: number; per_page: number }>('/reports', { params })
      .then(r => extractData(r)),
  
  create: (data: CreateReportRequest) =>
    api.post<{ data: { report_id: string; status: string } }>('/reports', data)
      .then(r => extractData(r)),
  
  getById: (reportId: string) =>
    api.get<{ data: Report }>(`/reports/${reportId}`).then(r => extractData(r)),
  
  download: (reportId: string) =>
    api.get(`/reports/${reportId}/download`, { responseType: 'blob' }),
  
  delete: (reportId: string) =>
    api.delete(`/reports/${reportId}`),
};

// Users endpoints
export const users = {
  list: () =>
    api.get<{ data: FactoryUser[] }>('/users').then(r => extractData(r)),
  
  invite: (data: InviteUserRequest) =>
    api.post<{ data: { id: number; email: string; invite_sent: boolean } }>('/users/invite', data)
      .then(r => extractData(r)),
  
  updatePermissions: (userId: number, permissions: Record<string, boolean>) =>
    api.patch(`/users/${userId}/permissions`, { permissions }),
  
  deactivate: (userId: number) =>
    api.delete(`/users/${userId}`),
};

// Dashboard endpoint
export const dashboard = {
  getSummary: () =>
    api.get<{ data: DashboardSummary }>('/dashboard/summary').then(r => extractData(r)),
};

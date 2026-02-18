// API client with interceptors
import axios, { AxiosError, AxiosResponse, InternalAxiosRequestConfig } from 'axios';
import { useAuthStore } from '../stores/authStore';

const API_BASE_URL = '/api/v1';

// Create axios instance
export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: Add auth token
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = useAuthStore.getState().token;
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => Promise.reject(error)
);

// Response interceptor: Handle errors
api.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Clear auth and redirect to login
      useAuthStore.getState().logout();
      window.location.href = '/login';
    }
    
    // Normalize error shape
    const normalizedError = {
      ...error,
      message: (error.response?.data as any)?.error?.message || error.message,
      code: (error.response?.data as any)?.error?.code || 'UNKNOWN_ERROR',
    };
    
    return Promise.reject(normalizedError);
  }
);

// Helper to extract data from response
export const extractData = <T>(response: AxiosResponse<{ data: T }>): T => {
  return response.data.data;
};

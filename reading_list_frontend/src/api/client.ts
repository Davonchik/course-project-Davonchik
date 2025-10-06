import axios, { AxiosInstance, AxiosResponse } from 'axios';
import {
  RegisterIn,
  LoginIn,
  RefreshIn,
  TokenOut,
  User,
  Entry,
  EntryCreate,
  EntryUpdate,
  ListEntriesParams,
  ListEntriesResponse,
  HTTPValidationError,
  LogoutIn,
  UserListItem
} from '../types/api';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('access_token');
        const deviceId = this.ensureDeviceId();
        const userAgent = typeof navigator !== 'undefined' ? navigator.userAgent : undefined;
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        if (deviceId) {
          (config.headers as any)['X-Device-Id'] = deviceId;
        }
        if (userAgent) {
          (config.headers as any)['User-Agent'] = userAgent;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor to handle token refresh
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            const refreshToken = localStorage.getItem('refresh_token');
            if (refreshToken) {
              const response = await this.refreshToken({ refresh_token: refreshToken });
              localStorage.setItem('access_token', response.data.access_token);
              localStorage.setItem('refresh_token', response.data.refresh_token);
              localStorage.setItem('device_id', response.data.device_id);

              originalRequest.headers.Authorization = `Bearer ${response.data.access_token}`;
              return this.client(originalRequest);
            }
          } catch (refreshError) {
            // Refresh failed, redirect to login
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('device_id');
            window.location.href = '/login';
          }
        }

        return Promise.reject(error);
      }
    );
  }

  private ensureDeviceId(): string {
    let deviceId: string | null = localStorage.getItem('device_id');
    if (!deviceId) {
      const g: any = typeof globalThis !== 'undefined' ? globalThis : {};
      const uuid = g.crypto && typeof g.crypto.randomUUID === 'function' ? g.crypto.randomUUID() : Math.random().toString(36).slice(2);
      deviceId = String(uuid);
      localStorage.setItem('device_id', deviceId);
    }
    return deviceId as string;
  }

  // Auth endpoints
  async register(data: RegisterIn): Promise<AxiosResponse<TokenOut>> {
    const payload: RegisterIn = {
      ...data,
      device_id: data.device_id ?? this.ensureDeviceId(),
    };
    return this.client.post('/api/v1/auth/register', payload, {
      headers: {
        'User-Agent': typeof navigator !== 'undefined' ? navigator.userAgent : '',
      },
    });
  }

  async login(data: LoginIn): Promise<AxiosResponse<TokenOut>> {
    const formData = new URLSearchParams();
    formData.append('username', data.username);
    formData.append('password', data.password);
    if (data.grant_type) formData.append('grant_type', data.grant_type);
    if (data.scope) formData.append('scope', data.scope);
    if (data.client_id) formData.append('client_id', data.client_id);
    if (data.client_secret) formData.append('client_secret', data.client_secret);

    return this.client.post('/api/v1/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': typeof navigator !== 'undefined' ? navigator.userAgent : '',
        'X-Device-Id': this.ensureDeviceId(),
      },
    });
  }

  async refreshToken(data: RefreshIn): Promise<AxiosResponse<TokenOut>> {
    return this.client.post('/api/v1/auth/refresh', data, {
      headers: {
        'User-Agent': typeof navigator !== 'undefined' ? navigator.userAgent : '',
      },
    });
  }

  async getMe(): Promise<AxiosResponse<User>> {
    return this.client.get('/api/v1/auth/me');
  }

  async logout(data: LogoutIn): Promise<AxiosResponse<void>> {
    return this.client.post('/api/v1/auth/logout', data);
  }

  async getUsers(q?: string, limit?: number, offset?: number): Promise<AxiosResponse<UserListItem[]>> {
    return this.client.get('/api/v1/admin', { params: { q, limit, offset } });
  }

  // Entries endpoints
  async getEntries(params?: ListEntriesParams): Promise<AxiosResponse<ListEntriesResponse>> {
    return this.client.get('/api/v1/entries', { params });
  }

  async getEntry(id: number): Promise<AxiosResponse<Entry>> {
    return this.client.get(`/api/v1/entries/${id}`);
  }

  async createEntry(data: EntryCreate): Promise<AxiosResponse<Entry>> {
    return this.client.post('/api/v1/entries', data);
  }

  async updateEntry(id: number, data: EntryUpdate): Promise<AxiosResponse<Entry>> {
    return this.client.patch(`/api/v1/entries/${id}`, data);
  }

  async deleteEntry(id: number): Promise<AxiosResponse<void>> {
    return this.client.delete(`/api/v1/entries/${id}`);
  }

  // Helper method to check if error is validation error
  isValidationError(error: any): error is { response: { data: HTTPValidationError } } {
    return error.response?.data?.detail && Array.isArray(error.response.data.detail);
  }

  // Helper method to get validation errors
  getValidationErrors(error: any): string[] {
    if (this.isValidationError(error)) {
      return error.response.data.detail.map((err: any) => err.msg);
    }
    return [error.response?.data?.detail || 'An error occurred'];
  }
}

export const apiClient = new ApiClient();

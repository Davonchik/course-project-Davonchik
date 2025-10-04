import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User } from '../types/api';
import { apiClient } from '../api/client';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const isAuthenticated = !!user;

  const login = async (email: string, password: string) => {
    try {
      const response = await apiClient.login({
        username: email,
        password,
      });

      const { access_token, refresh_token, device_id } = response.data;
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      if (device_id) localStorage.setItem('device_id', device_id);

      // Get user info
      await refreshUser();
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  };

  const register = async (email: string, password: string) => {
    try {
      const response = await apiClient.register({
        email,
        password,
        device_id: localStorage.getItem('device_id') || undefined,
      });

      const { access_token, refresh_token, device_id } = response.data;
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      if (device_id) localStorage.setItem('device_id', device_id);

      // Get user info
      await refreshUser();
    } catch (error) {
      console.error('Registration error:', error);
      throw error;
    }
  };

  const logout = async () => {
    try {
      const device_id = localStorage.getItem('device_id') || '';
      const refresh_token = localStorage.getItem('refresh_token');
      await apiClient.logout({ device_id, refresh_token: refresh_token || null });
    } catch (e) {
      // ignore logout API errors
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('device_id');
      setUser(null);
    }
  };

  const refreshUser = async () => {
    try {
      const response = await apiClient.getMe();
      setUser(response.data);
    } catch (error) {
      console.error('Failed to get user info:', error);
      logout();
    }
  };

  // Check if user is logged in on app start
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('access_token');
      if (token) {
        try {
          await refreshUser();
        } catch (error) {
          console.error('Auth check failed:', error);
          logout();
        }
      }
      setIsLoading(false);
    };

    checkAuth();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const value: AuthContextType = {
    user,
    isAuthenticated,
    isLoading,
    login,
    register,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User, LoginCredentials, RegisterData, AuthResponse } from '../types';
import { API_BASE_URL } from '../config/api';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
  updateUser: (user: Partial<User>) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchWithTimeout = async (url: string, options: RequestInit = {}, timeoutMs = 10000) => {
    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs);

    try {
      return await fetch(url, { ...options, signal: controller.signal });
    } finally {
      window.clearTimeout(timeoutId);
    }
  };

  const clearStoredSession = () => {
    localStorage.removeItem('scoutpro_token');
    localStorage.removeItem('scoutpro_user');
    setToken(null);
    setUser(null);
  };

  const persistSession = (authData: AuthResponse) => {
    localStorage.setItem('scoutpro_token', authData.token);
    localStorage.setItem('scoutpro_user', JSON.stringify(authData.user));
    setToken(authData.token);
    setUser(authData.user);
  };

  const getErrorMessage = async (response: Response, fallbackMessage: string) => {
    const errorData = await response.json().catch(() => null);
    const apiMessage = errorData?.message || errorData?.error;
    return apiMessage || `${fallbackMessage} (HTTP ${response.status})`;
  };

  // Load user from localStorage on mount
  useEffect(() => {
    const storedToken = localStorage.getItem('scoutpro_token');
    const storedUser = localStorage.getItem('scoutpro_user');

    const loadSession = async () => {
      if (!storedToken || !storedUser || storedToken.startsWith('mock-jwt-token-')) {
        clearStoredSession();
        setIsLoading(false);
        return;
      }

      try {
        JSON.parse(storedUser);
      } catch (error) {
        console.error('Error parsing stored user:', error);
        clearStoredSession();
        setIsLoading(false);
        return;
      }

      try {
        const response = await fetchWithTimeout(`${API_BASE_URL}/auth/me`, {
          headers: {
            Authorization: `Bearer ${storedToken}`,
          },
        });

        if (!response.ok) {
          throw new Error('Stored session is no longer valid');
        }

        const liveUser: User = await response.json();
        localStorage.setItem('scoutpro_user', JSON.stringify(liveUser));
        setToken(storedToken);
        setUser(liveUser);
      } catch (error) {
        console.error('Session restore error:', error);
        clearStoredSession();
      } finally {
        setIsLoading(false);
      }
    };

    loadSession();
  }, []);

  const login = async (credentials: LoginCredentials) => {
    setIsLoading(true);

    try {
      const response = await fetchWithTimeout(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials),
      });

      if (!response.ok) {
        throw new Error(await getErrorMessage(response, 'Login failed'));
      }

      const authData: AuthResponse = await response.json();
      persistSession(authData);
    } catch (error) {
      console.error('Login error:', error);

      if (error instanceof DOMException && error.name === 'AbortError') {
        throw new Error('Login request timed out. Ensure the API gateway is reachable at localhost:3001.');
      }

      if (error instanceof TypeError) {
        throw new Error('Could not reach the API gateway. Check frontend API base URL and gateway health.');
      }

      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (data: RegisterData) => {
    setIsLoading(true);

    try {
      const response = await fetchWithTimeout(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error(await getErrorMessage(response, 'Registration failed'));
      }

      const authData: AuthResponse = await response.json();
      persistSession(authData);
    } catch (error) {
      console.error('Registration error:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    clearStoredSession();
  };

  const updateUser = (updates: Partial<User>) => {
    if (user) {
      const updatedUser = { ...user, ...updates, updatedAt: new Date().toISOString() };
      setUser(updatedUser);
      localStorage.setItem('scoutpro_user', JSON.stringify(updatedUser));
    }
  };

  const value: AuthContextType = {
    user,
    token,
    isAuthenticated: !!token && !!user,
    isLoading,
    login,
    register,
    logout,
    updateUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export default AuthContext;

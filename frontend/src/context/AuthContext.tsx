import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User, LoginCredentials, RegisterData, AuthResponse } from '../types';

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

  // Load user from localStorage on mount
  useEffect(() => {
    const storedToken = localStorage.getItem('scoutpro_token');
    const storedUser = localStorage.getItem('scoutpro_user');

    if (storedToken && storedUser) {
      try {
        const parsedUser = JSON.parse(storedUser);
        setToken(storedToken);
        setUser(parsedUser);
      } catch (error) {
        console.error('Error parsing stored user:', error);
        localStorage.removeItem('scoutpro_token');
        localStorage.removeItem('scoutpro_user');
      }
    }

    setIsLoading(false);
  }, []);

  const login = async (credentials: LoginCredentials) => {
    setIsLoading(true);

    try {
      // In mock mode, simulate successful login
      const useMockData = import.meta.env.VITE_USE_MOCK_DATA === 'true';

      if (useMockData) {
        // Determine role based on email for demo purposes
        let role: 'admin' | 'scout' | 'analyst' | 'viewer' = 'scout';
        let permissions: string[] = [];

        if (credentials.email.includes('admin')) {
          role = 'admin';
          permissions = [
            'view_players', 'view_matches', 'create_reports', 'export_data',
            'manage_users', 'manage_system', 'manage_data', 'delete_data',
            'view_analytics', 'manage_roles'
          ];
        } else if (credentials.email.includes('analyst')) {
          role = 'analyst';
          permissions = ['view_players', 'view_matches', 'view_analytics', 'create_reports', 'ml_access'];
        } else if (credentials.email.includes('viewer')) {
          role = 'viewer';
          permissions = ['view_players', 'view_matches', 'view_reports'];
        } else {
          role = 'scout';
          permissions = ['view_players', 'view_matches', 'create_reports', 'export_data', 'video_analysis'];
        }

        // Mock successful login
        const mockUser: User = {
          id: 'user-001',
          email: credentials.email,
          name: credentials.email.split('@')[0],
          role,
          team: 'Real Madrid',
          avatar: 'https://images.pexels.com/photos/220453/pexels-photo-220453.jpeg?auto=compress&cs=tinysrgb&w=100&h=100&fit=crop',
          permissions,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        };

        const mockToken = 'mock-jwt-token-' + Date.now();

        // Store in localStorage
        localStorage.setItem('scoutpro_token', mockToken);
        localStorage.setItem('scoutpro_user', JSON.stringify(mockUser));

        setToken(mockToken);
        setUser(mockUser);
      } else {
        // Real API call
        const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/auth/login`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(credentials),
        });

        if (!response.ok) {
          throw new Error('Login failed');
        }

        const data: AuthResponse = await response.json();

        // Store in localStorage
        localStorage.setItem('scoutpro_token', data.token);
        localStorage.setItem('scoutpro_user', JSON.stringify(data.user));

        setToken(data.token);
        setUser(data.user);
      }
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (data: RegisterData) => {
    setIsLoading(true);

    try {
      const useMockData = import.meta.env.VITE_USE_MOCK_DATA === 'true';

      if (useMockData) {
        // Mock successful registration
        const mockUser: User = {
          id: 'user-' + Date.now(),
          email: data.email,
          name: data.name,
          role: data.role || 'viewer',
          team: data.team,
          avatar: 'https://images.pexels.com/photos/220453/pexels-photo-220453.jpeg?auto=compress&cs=tinysrgb&w=100&h=100&fit=crop',
          permissions: ['view_players', 'view_matches'],
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        };

        const mockToken = 'mock-jwt-token-' + Date.now();

        localStorage.setItem('scoutpro_token', mockToken);
        localStorage.setItem('scoutpro_user', JSON.stringify(mockUser));

        setToken(mockToken);
        setUser(mockUser);
      } else {
        // Real API call
        const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/auth/register`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(data),
        });

        if (!response.ok) {
          throw new Error('Registration failed');
        }

        const authData: AuthResponse = await response.json();

        localStorage.setItem('scoutpro_token', authData.token);
        localStorage.setItem('scoutpro_user', JSON.stringify(authData.user));

        setToken(authData.token);
        setUser(authData.user);
      }
    } catch (error) {
      console.error('Registration error:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('scoutpro_token');
    localStorage.removeItem('scoutpro_user');
    setToken(null);
    setUser(null);
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

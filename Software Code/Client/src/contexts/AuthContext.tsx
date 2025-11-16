// src/contexts/AuthContext.tsx
import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { AUTH_ENDPOINTS } from '@/config/api';

interface User {
  id: string;
  email: string;
  full_name?: string;
  role: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isAdmin: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  register: (email: string, password: string, fullName?: string) => Promise<void>;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  // Check if user is authenticated on mount
  useEffect(() => {
    if (token) {
      fetchCurrentUser();
    } else {
      setLoading(false);
    }
  }, [token]);

  const fetchCurrentUser = async () => {
    try {
      console.log('Fetching current user with token:', token);
      
      const response = await fetch(AUTH_ENDPOINTS.GET_CURRENT_USER, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      console.log('User fetch response status:', response.status);
      console.log('User fetch response headers:', response.headers.get('content-type'));

      if (response.ok) {
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
          const userData = await response.json();
          console.log('User data received:', userData);
          setUser(userData);
        } else {
          console.error('Response is not JSON:', await response.text());
          throw new Error('Invalid response format');
        }
      } else {
        // Token invalid, clear auth
        console.error('Failed to fetch user, status:', response.status);
        localStorage.removeItem('token');
        setToken(null);
        setUser(null);
      }
    } catch (error) {
      console.error('Failed to fetch user:', error);
      localStorage.removeItem('token');
      setToken(null);
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    const response = await fetch(AUTH_ENDPOINTS.LOGIN_JSON, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Login failed');
    }

    const data = await response.json();
    const newToken = data.access_token;
    
    localStorage.setItem('token', newToken);
    setToken(newToken);
    
    // Fetch user data immediately after setting token
    const userResponse = await fetch(AUTH_ENDPOINTS.GET_CURRENT_USER, {
      headers: {
        'Authorization': `Bearer ${newToken}`,
        'Content-Type': 'application/json',
      },
    });
    
    if (userResponse.ok) {
      const userData = await userResponse.json();
      setUser(userData);
    }
  };

  const logout = async () => {
    try {
      if (token) {
        await fetch(AUTH_ENDPOINTS.LOGOUT, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      localStorage.removeItem('token');
      setToken(null);
      setUser(null);
    }
  };

  const register = async (email: string, password: string, fullName?: string) => {
    const response = await fetch(AUTH_ENDPOINTS.REGISTER, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email,
        password,
        full_name: fullName,
        role: 'user',
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Registration failed');
    }

    // Auto login after registration
    await login(email, password);
  };

  const value = {
    user,
    token,
    isAuthenticated: !!user,
    isAdmin: user?.role === 'admin',
    login,
    logout,
    register,
    loading,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
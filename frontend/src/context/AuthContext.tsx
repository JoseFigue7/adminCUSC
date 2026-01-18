import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { login as loginApi, register as registerApi, getProfile, AuthResponse } from '../services/authApi';
import api from '../services/api';

interface User {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role?: {
    id: string;
    name: string;
    description: string;
    can_manage_students?: boolean;
    can_manage_payments?: boolean;
    can_manage_academics?: boolean;
    can_manage_scholarships?: boolean;
    can_manage_thesis?: boolean;
    can_view_reports?: boolean;
    can_manage_users?: boolean;
    can_manage_settings?: boolean;
  };
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (data: any) => Promise<void>;
  logout: () => void;
  hasPermission: (permission: string) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Intentar cargar usuario desde localStorage
    const token = localStorage.getItem('access_token');
    if (token) {
      // Configurar token en axios
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      // Cargar perfil
      loadUser();
    } else {
      setLoading(false);
    }
  }, []);

  const loadUser = async () => {
    try {
      const response = await getProfile();
      setUser(response.data);
    } catch (error) {
      console.error('Error loading user:', error);
      // Si falla, limpiar tokens
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      delete api.defaults.headers.common['Authorization'];
    } finally {
      setLoading(false);
    }
  };

  const login = async (username: string, password: string) => {
    try {
      const response = await loginApi({ username, password });
      const { access, refresh, user: userData } = response.data;
      
      // Guardar tokens
      localStorage.setItem('access_token', access);
      localStorage.setItem('refresh_token', refresh);
      
      // Configurar token en axios
      api.defaults.headers.common['Authorization'] = `Bearer ${access}`;
      
      // Guardar usuario
      setUser(userData);
    } catch (error: any) {
      console.error('Login error:', error);
      throw error;
    }
  };

  const register = async (data: any) => {
    try {
      const response = await registerApi(data);
      const { access, refresh, user: userData } = response.data;
      
      // Guardar tokens
      localStorage.setItem('access_token', access);
      localStorage.setItem('refresh_token', refresh);
      
      // Configurar token en axios
      api.defaults.headers.common['Authorization'] = `Bearer ${access}`;
      
      // Guardar usuario
      setUser(userData);
    } catch (error: any) {
      console.error('Register error:', error);
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    delete api.defaults.headers.common['Authorization'];
    setUser(null);
  };

  const hasPermission = (permission: string): boolean => {
    if (!user || !user.role) return false;
    
    // Super admin tiene todos los permisos
    if (user.role.name === 'SUPER_ADMIN') return true;
    
    const permissionMap: { [key: string]: boolean | undefined } = {
      'manage_students': user.role.can_manage_students,
      'manage_payments': user.role.can_manage_payments,
      'manage_academics': user.role.can_manage_academics,
      'manage_scholarships': user.role.can_manage_scholarships,
      'manage_thesis': user.role.can_manage_thesis,
      'view_reports': user.role.can_view_reports,
      'manage_users': user.role.can_manage_users,
      'manage_settings': user.role.can_manage_settings,
    };
    
    return permissionMap[permission] || false;
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isAuthenticated: !!user,
        login,
        register,
        logout,
        hasPermission,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};











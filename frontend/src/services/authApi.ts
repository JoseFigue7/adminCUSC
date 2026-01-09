import api from './api';

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterData {
  username: string;
  email: string;
  password: string;
  password_confirm: string;
  first_name?: string;
  last_name?: string;
  phone?: string;
}

export interface AuthResponse {
  access: string;
  refresh: string;
  user: {
    id: string;
    username: string;
    email: string;
    first_name: string;
    last_name: string;
    role?: {
      id: string;
      name: string;
      description: string;
    };
  };
}

export const login = (credentials: LoginCredentials) => 
  api.post<AuthResponse>('/auth/login/', credentials);

export const register = (data: RegisterData) => 
  api.post<AuthResponse>('/users/register/', data);

export const refreshToken = (refresh: string) => 
  api.post('/auth/refresh/', { refresh });

export const getProfile = () => 
  api.get('/users/profile/');

export const changePassword = (oldPassword: string, newPassword: string) =>
  api.post('/users/change_password/', {
    old_password: oldPassword,
    new_password: newPassword,
  });





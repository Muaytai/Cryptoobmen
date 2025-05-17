import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
  id: string | number;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
  avatar?: string;
  phone_number?: string;
  is_verified?: boolean;
  kyc_verified?: boolean;
  telegram_id?: string;
  date_joined?: string;
  has_2fa?: boolean;
  notify_via_email?: boolean;
  notify_via_telegram?: boolean;
}

interface Credentials {
  email: string;
  password: string;
}

interface RegistrationData {
  username: string;
  email: string;
  password1: string;
  password2: string;
}

interface AuthResponse {
  user: User;
  token: string;
  refresh_token?: string;
}

interface ErrorResponse {
  detail?: string;
  email?: string[];
  username?: string[];
  password?: string[];
  non_field_errors?: string[];
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  showEmailConfirmedModal: boolean;
  disableAutoLogin: boolean;
  
  login: (credentials: Credentials) => Promise<void>;
  register: (data: RegistrationData) => Promise<void>;
  logout: () => Promise<void>;
  clearError: () => void;
  checkAuthStatus: () => Promise<void>;
  setShowEmailConfirmedModal: (show: boolean) => void;
  setDisableAutoLogin: (disable: boolean) => void;
}

const TOKEN_NAME = 'auth-token';
const REFRESH_TOKEN_NAME = 'refresh-token';

const handleApiError = (error: any, defaultMessage: string): string => {
  if (error instanceof Error) {
    return error.message;
  }
  if (typeof error === 'string') {
    return error;
  }
  return defaultMessage;
};

const clearAuthData = () => {
  localStorage.removeItem(TOKEN_NAME);
  localStorage.removeItem(REFRESH_TOKEN_NAME);
  localStorage.removeItem('auth-storage');
  
  // Очищаем куки с учетом всех возможных путей
  const cookies = ['sessionid', 'csrftoken', 'auth-token', 'refresh-token'];
  const paths = ['/', '/api', '/accounts'];
  
  cookies.forEach(cookie => {
    paths.forEach(path => {
      document.cookie = `${cookie}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=${path};`;
    });
  });
};

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      showEmailConfirmedModal: false,
      disableAutoLogin: false,
      
      login: async (credentials: Credentials) => {
        set({ isLoading: true, error: null });
        try {
          const response = await fetch('/api/auth/login/', {
            method: 'POST',
            credentials: 'include',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(credentials),
          });

          const responseText = await response.text();
          
          if (!response.ok) {
            let errorMessage = 'Ошибка входа';
            try {
              if (responseText) {
                const errorData: ErrorResponse = JSON.parse(responseText);
                errorMessage = errorData.detail || errorData.non_field_errors?.[0] || 'Ошибка входа';
              }
            } catch (e) {
              console.error('Ошибка при разборе ответа:', e);
            }
            throw new Error(errorMessage);
          }

          let data: AuthResponse;
          try {
            data = responseText ? JSON.parse(responseText) : { user: null, token: '' };
          } catch (e) {
            console.error('Ошибка при разборе JSON:', e);
            throw new Error('Ошибка при обработке ответа сервера');
          }

          if (data.token) {
            localStorage.setItem(TOKEN_NAME, data.token);
            if (data.refresh_token) {
              localStorage.setItem(REFRESH_TOKEN_NAME, data.refresh_token);
            }
          }
            
          set({ 
            user: data.user,
            isAuthenticated: true,
            isLoading: false,
            error: null,
            disableAutoLogin: false
          });
          
        } catch (error) {
          console.error('Ошибка входа:', error);
          set({ 
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: handleApiError(error, 'Произошла ошибка при входе'),
            disableAutoLogin: true
          });
        }
      },
      
      register: async (data: RegistrationData) => {
        set({ isLoading: true, error: null });
        try {
          const response = await fetch('/api/auth/registration/', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
            credentials: 'include',
          });

          const responseText = await response.text();
          
          if (!response.ok) {
            let errorMessage = 'Ошибка регистрации';
            try {
              if (responseText) {
                const errorData: ErrorResponse = JSON.parse(responseText);
                if (errorData.email) errorMessage = `Email: ${errorData.email[0]}`;
                else if (errorData.username) errorMessage = `Пользователь: ${errorData.username[0]}`;
                else if (errorData.password) errorMessage = `Пароль: ${errorData.password[0]}`;
                else if (errorData.non_field_errors) errorMessage = errorData.non_field_errors[0];
                else if (errorData.detail) errorMessage = errorData.detail;
              }
            } catch (e) {
              console.error('Ошибка при разборе ответа:', e);
            }
            throw new Error(errorMessage);
          }

          set({ isLoading: false });
          
        } catch (error) {
          console.error('Ошибка регистрации:', error);
          set({
            isLoading: false,
            error: handleApiError(error, 'Ошибка регистрации'),
          });
          throw error;
        }
      },
      
      logout: async () => {
        set({ isLoading: true, error: null });
        try {
          const response = await fetch('/api/auth/logout/', { 
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            credentials: 'include',
          });
          
          if (!response.ok) {
            console.warn('Не удалось выполнить выход на сервере');
          }
        } catch (error) {
          console.error('Ошибка при выходе:', error);
        } finally {
          clearAuthData();
          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: null,
            disableAutoLogin: true,
          });
          
          window.location.href = '/';
        }
      },
      
      clearError: () => set({ error: null }),

      setShowEmailConfirmedModal: (show: boolean) => {
        set({ showEmailConfirmedModal: show });
      },

      setDisableAutoLogin: (disable: boolean) => {
        localStorage.setItem('disableAutoLogin', disable.toString());
        set({ disableAutoLogin: disable });
      },

      checkAuthStatus: async () => {
        const state = get();
        
        if (state.disableAutoLogin || state.isLoading) {
          return;
        }

        const token = localStorage.getItem(TOKEN_NAME);
        if (!token) {
          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: null,
          });
          return;
        }

        set({ isLoading: true, error: null });
        
        try {
          const response = await fetch('/api/auth/user/', {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`,
            },
            credentials: 'include',
          });

          if (!response.ok) {
            throw new Error('Не авторизован');
          }

          const userData: User = await response.json();
          
          set({
            user: userData,
            isAuthenticated: true,
            isLoading: false,
            error: null,
            disableAutoLogin: false,
          });
          
        } catch (error) {
          console.error('Ошибка проверки статуса:', error);
          clearAuthData();
          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: null,
          });
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ 
        user: state.user,
        isAuthenticated: state.isAuthenticated,
        disableAutoLogin: state.disableAutoLogin
      }),
    }
  )
); 
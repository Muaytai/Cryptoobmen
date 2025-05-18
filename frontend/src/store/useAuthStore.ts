import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { api } from '@/lib/api/fetch';

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

interface Tokens {
  access: string;
  refresh: string;
}

interface AuthResponse {
  user: User;
  token: string;
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
  tokens: Tokens | null;
  
  login: (credentials: Credentials) => Promise<void>;
  register: (data: RegistrationData) => Promise<void>;
  logout: () => Promise<void>;
  clearError: () => void;
  checkAuthStatus: () => Promise<void>;
  setShowEmailConfirmedModal: (show: boolean) => void;
  setDisableAutoLogin: (disable: boolean) => void;
  setTokens: (tokens: Tokens) => void;
}

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
  // Очищаем localStorage и sessionStorage
  localStorage.clear();
  sessionStorage.clear();
  
  // Очищаем все куки
  const cookies = [
    'access_token',
    'refresh_token',
    'sessionid',
    'dj_session_id',
    'csrftoken',
    'auth_token',
    'next_hmr_refresh_hash'
  ];

  cookies.forEach(cookie => {
    document.cookie = `${cookie}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=localhost; samesite=lax`;
    document.cookie = `${cookie}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; samesite=lax`;
  });
  
  // Устанавливаем флаг блокировки автовхода
  localStorage.setItem('disableAutoLogin', 'true');
};

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      showEmailConfirmedModal: false,
      disableAutoLogin: true, // По умолчанию автологин отключен
      tokens: null,
      
      setTokens: (tokens: Tokens) => {
        set({ tokens, isAuthenticated: true });
        // Сохраняем токены в localStorage
        localStorage.setItem('access_token', tokens.access);
        localStorage.setItem('refresh_token', tokens.refresh);
      },
      
      login: async (credentials: Credentials) => {
        set({ isLoading: true, error: null });
        try {
          const response = await api.auth.login(credentials.email, credentials.password);
          const userData = response.data;
          
          // После успешного логина получаем данные пользователя
          const userResponse = await api.auth.getUser();
          const user = userResponse.data;
          
          // Сбрасываем флаг блокировки автологина только при успешном входе
          localStorage.removeItem('disableAutoLogin');
          
          set({ 
            user,
            isAuthenticated: true,
            isLoading: false,
            error: null,
            disableAutoLogin: false
          });
        } catch (error) {
          console.error('Ошибка входа:', error);
          clearAuthData();
          set({ 
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: error instanceof Error ? error.message : 'Произошла ошибка при входе',
            disableAutoLogin: true
          });
        }
      },
      
      register: async (data: RegistrationData) => {
        set({ isLoading: true, error: null });
        try {
          await api.post('/auth/registration/', data);
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
        set({ isLoading: true });
        try {
          // Сначала очищаем данные на фронтенде
          clearAuthData();
          
          // Затем делаем запрос на бэкенд для выхода
          await api.auth.logout();
          
          // Устанавливаем состояние после выхода
          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: null,
            disableAutoLogin: true,
            tokens: null
          });
          
          // Принудительно перезагружаем страницу для очистки всех состояний
          window.location.href = '/login?force_login=true';
        } catch (error) {
          console.error('Ошибка при выходе:', error);
          // Даже при ошибке очищаем все данные
          clearAuthData();
          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: null,
            disableAutoLogin: true,
            tokens: null
          });
          // Перенаправляем на страницу входа
          window.location.href = '/login?force_login=true';
        }
      },
      
      checkAuthStatus: async () => {
        const state = get();
        const disableAutoLogin = localStorage.getItem('disableAutoLogin') === 'true';
        
        // Не проверяем статус если:
        // 1. Идет загрузка
        // 2. Автологин отключен
        if (state.isLoading || disableAutoLogin) {
          set({ 
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: null,
            disableAutoLogin: true,
            tokens: null
          });
          return;
        }
        
        set({ isLoading: true });
        try {
          const response = await api.auth.getUser();
          const user = response.data;
          
          set({ 
            user, 
            isAuthenticated: true, 
            isLoading: false,
            error: null,
            disableAutoLogin: false
          });
        } catch (error) {
          console.error('Ошибка проверки аутентификации:', error);
          clearAuthData();
          set({ 
            user: null, 
            isAuthenticated: false, 
            isLoading: false,
            error: null,
            disableAutoLogin: true,
            tokens: null
          });
        }
      },
      
      clearError: () => set({ error: null }),
      
      setShowEmailConfirmedModal: (show: boolean) => {
        set({ showEmailConfirmedModal: show });
      },
      
      setDisableAutoLogin: (disable: boolean) => {
        if (disable) {
          localStorage.setItem('disableAutoLogin', 'true');
        } else {
          localStorage.removeItem('disableAutoLogin');
        }
        set({ disableAutoLogin: disable });
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ 
        user: state.user,
        isAuthenticated: state.isAuthenticated,
        disableAutoLogin: state.disableAutoLogin,
        tokens: state.tokens
      }),
    }
  )
); 
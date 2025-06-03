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
  setTokens: (tokens: Tokens | null) => void;
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
  console.log('clearAuthData: Очистка данных аутентификации');
  // Очищаем специфичные ключи из localStorage
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user'); // Если пользователь хранится отдельно
  localStorage.removeItem('auth-storage'); // Ключ persist от Zustand
  // sessionStorage.removeItem('some_auth_key'); // Если используется sessionStorage

  // Очищаем все куки
  const cookies = [
    'access_token',
    'refresh_token',
    'sessionid',
    'dj_session_id',
    'csrftoken',
    'auth_token',
    // 'next_hmr_refresh_hash' // этот можно оставить, если он не связан с сессией
  ];

  cookies.forEach(cookie => {
    document.cookie = `${cookie}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=localhost; samesite=lax`;
    document.cookie = `${cookie}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; samesite=lax`;
    document.cookie = `${cookie}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
  });
  
  // Устанавливаем флаг блокировки автовхода
  localStorage.setItem('disableAutoLogin', 'true');
  console.log('clearAuthData: disableAutoLogin установлен в true в localStorage');
};

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: false,
      isLoading: true,
      error: null,
      showEmailConfirmedModal: false,
      disableAutoLogin: true,
      tokens: null,
      
      setTokens: (tokens: Tokens | null) => {
        set({ tokens, isAuthenticated: !!(tokens && tokens.access), user: null }); 
      },
      
      login: async (credentials: Credentials) => {
        set({ isLoading: true, error: null });
        try {
          // 1. Вызываем /api/auth/login/, который должен установить HttpOnly cookies
          await api.auth.login(credentials.email, credentials.password); 
          
          // 2. После успешного вызова login, немедленно проверяем статус аутентификации.
          //    checkAuthStatus загрузит пользователя и обновит isAuthenticated, isLoading.
          await get().checkAuthStatus(); 

        } catch (error: any) {
          console.error('[useAuthStore login] Ошибка входа или проверки статуса:', error);
          clearAuthData(); // Убедимся, что все старые данные аутентификации очищены
          set({
            error: handleApiError(error, 'Ошибка входа. Проверьте email и пароль или попробуйте позже.'),
            isLoading: false,
            isAuthenticated: false,
            user: null,
            tokens: null, // Очищаем состояние токенов в Zustand на случай, если они там были
            disableAutoLogin: true,
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
        set({ isLoading: true, error: null });
        try {
          await api.auth.logout();
        } catch (error: any) {
          console.error("Ошибка при выходе на бэкенде:", error.message);
        }
        get().setTokens(null);
        set({ user: null, isAuthenticated: false, isLoading: false });
      },
      
      checkAuthStatus: async () => {
        set({ isLoading: true, error: null });
        try {
          const response = await api.auth.getUser();
          set({ user: response.data, isAuthenticated: true, isLoading: false });
        } catch (error) {
          get().setTokens(null);
          set({ user: null, isAuthenticated: false, isLoading: false });
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
        // tokens: state.tokens // Токены больше не храним здесь, они в HttpOnly куках
      }),
    }
  )
); 
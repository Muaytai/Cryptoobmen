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
  checkAuthStatus: (isLoginProcess?: boolean) => Promise<void>;
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
  localStorage.removeItem('user'); // Если пользователь хранится отдельно
  localStorage.removeItem('auth-storage'); // Ключ persist от Zustand
  // localStorage.removeItem('access_token'); // Больше не храним в localStorage
  // localStorage.removeItem('refresh_token'); // Больше не храним в localStorage

  // Очищаем НЕ HttpOnly куки, если они есть и управляются фронтом
  const clientSideCookiesToDelete = [
    // 'sessionid', // Управляется бэкендом (HttpOnly)
    // 'csrftoken', // Управляется бэкендом (может быть не HttpOnly, но лучше оставить бэкенду)
    'text', // Пример какой-то клиентской куки, если есть. Если такой нет, массив будет пустым.
    // 'dj_session_id', // Управляется бэкендом (HttpOnly)
    // 'auth_token', // Это другое название для access_token, управляется бэкендом (HttpOnly)
  ];

  clientSideCookiesToDelete.forEach(cookieName => {
    // Удаляем куку для основного пути
    document.cookie = `${cookieName}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; SameSite=Lax;`;
    // Пытаемся удалить и без указания SameSite, если вдруг была установлена так
    document.cookie = `${cookieName}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`; 
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
        console.log('[AuthStore] login: Начало входа');
        set({ isLoading: true, error: null });
        try {
          await api.auth.login(credentials.email, credentials.password); 
          console.log('[AuthStore] login: api.auth.login успешно выполнен. Вызов checkAuthStatus(true)...');
          await get().checkAuthStatus(true);
          console.log(
            '[AuthStore] login: checkAuthStatus завершен. Текущее состояние: user: ',
            get().user,
            ', isAuthenticated: ',
            get().isAuthenticated
          );
        } catch (error: any) {
          console.error('[useAuthStore login] Ошибка входа или проверки статуса:', error);
          clearAuthData();
          set({
            error: handleApiError(error, 'Ошибка входа. Проверьте email и пароль или попробуйте позже.'),
            isLoading: false, 
            isAuthenticated: false,
            user: null,
            tokens: null, 
            disableAutoLogin: true,
          });
          console.log('[AuthStore] login: Ошибка, состояние сброшено.');
        } finally {
          console.log('[AuthStore] login: Блок finally, установка isLoading: false.');
          set({ isLoading: false });
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
        console.log('[AuthStore] logout: Начало выхода.');
        set({ isLoading: true, error: null });
        try {
          await api.auth.logout();
          console.log('[AuthStore] logout: api.auth.logout успешно выполнен.');
        } catch (error: any) {
          console.error("[AuthStore] logout: Ошибка при выходе на бэкенде:", error.message);
          // Продолжаем очистку на клиенте независимо от ошибки бэкенда
        }
        clearAuthData();
        get().setDisableAutoLogin(true); // Устанавливаем флаг для предотвращения авто-входа
        set({ user: null, isAuthenticated: false, isLoading: false });
        console.log('[AuthStore] logout: Выход выполнен, disableAutoLogin установлен.');
      },
      
      checkAuthStatus: async (isLoginProcess = false) => {
        const store = get();
        if (!isLoginProcess && store.disableAutoLogin) {
          console.warn(
            '[AuthStore] checkAuthStatus: Выполнение прервано из-за флага disableAutoLogin (не в процессе логина).'
          );
          set({ isLoading: false, user: null, isAuthenticated: false });
          return;
        }

        console.log('[AuthStore] checkAuthStatus: Начало проверки статуса аутентификации.');
        // Устанавливаем isLoading в true только если это не процесс логина,
        // так как login уже установил isLoading: true.
        // Или всегда устанавливать, а login в finally сбросит. Лучше всегда устанавливать для консистентности.
        set({ isLoading: true });
        try {
          const response = await api.auth.getUser(); // Получаем полный ответ
          const userData = response.data; // Извлекаем данные пользователя из response.data

          if (userData) {
            set({
              user: userData, // Теперь userData должен иметь правильный тип User
              isAuthenticated: true,
              isLoading: false,
              error: null,
            });
            store.setDisableAutoLogin(false); // Успешная аутентификация, сбрасываем флаг
            console.log('[AuthStore] checkAuthStatus: Пользователь аутентифицирован:', userData);
          } else {
            // Этого не должно происходить при успешном getUser, но на всякий случай
            console.warn('[AuthStore] checkAuthStatus: Пользователь НЕ аутентифицирован (нет данных пользователя).');
            clearAuthData(); // Очищаем все локальные данные
            set({ user: null, isAuthenticated: false, isLoading: false });
          }
        } catch (error: any) {
          console.warn('[AuthStore] checkAuthStatus: Ошибка при проверке статуса или пользователь не аутентифицирован:', error.message);
          clearAuthData(); // Очищаем все локальные данные при ошибке (например, 401)
          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            // Не устанавливаем error здесь, т.к. это может быть обычная проверка (нет сессии)
          });
          // Важно: не сбрасываем disableAutoLogin при ошибке, он сбрасывается только при успехе
        }
      },
      
      clearError: () => set({ error: null }),
      
      setShowEmailConfirmedModal: (show: boolean) => {
        set({ showEmailConfirmedModal: show });
      },
      
      setDisableAutoLogin: (disable: boolean) => {
        set({ disableAutoLogin: disable });
        if (typeof window !== 'undefined') {
          if (disable) {
            localStorage.setItem('disableAutoLogin', 'true');
            console.log('[AuthStore] setDisableAutoLogin: localStorage.disableAutoLogin установлен в true');
          } else {
            localStorage.removeItem('disableAutoLogin');
            console.log('[AuthStore] setDisableAutoLogin: localStorage.disableAutoLogin удален');
          }
        }
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
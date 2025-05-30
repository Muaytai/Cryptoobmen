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
          
          // Проверяем наличие user, access токена и refresh токена напрямую в userData
          if (userData && userData.user && userData.access && typeof userData.refresh === 'string') {
            const newTokens = {
              access: userData.access,
              refresh: userData.refresh
            };

            localStorage.setItem('access_token', newTokens.access);
            localStorage.setItem('refresh_token', newTokens.refresh);
            localStorage.removeItem('disableAutoLogin'); // Успешный вход, разрешаем автологин

            set({
              user: userData.user,
              tokens: newTokens, // Сохраняем токены в правильном формате
              isAuthenticated: true,
              isLoading: false,
              error: null,
              disableAutoLogin: false,
            });
            console.log('[useAuthStore login] Состояние обновлено успешно:', get());
          } else {
            // Если структура ответа все еще не та, что ожидается
            console.error('[useAuthStore login] Ошибка: Неожиданный или неполный формат ответа от API логина', userData);
            set({
              isLoading: false,
              error: 'Ошибка входа: неверный или неполный формат ответа от сервера.',
              isAuthenticated: false,
              user: null,
              tokens: null,
            });
          }
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
        const initialStoreState = get();
        console.log('checkAuthStatus: Начало проверки. Состояние store:', {
          isAuthenticated: initialStoreState.isAuthenticated,
          isLoading: initialStoreState.isLoading,
          user: initialStoreState.user,
          disableAutoLoginStore: initialStoreState.disableAutoLogin,
          tokensStore: initialStoreState.tokens
        });

        const storedDisableAutoLogin = localStorage.getItem('disableAutoLogin') === 'true';
        console.log('checkAuthStatus: disableAutoLogin из localStorage:', storedDisableAutoLogin);

        const accessTokenLocal = localStorage.getItem('access_token');
        const refreshTokenLocal = localStorage.getItem('refresh_token');
        const hasAccessTokenCookie = document.cookie.includes('access_token=');
        const hasRefreshTokenCookie = document.cookie.includes('refresh_token=');

        const hasAnyToken = !!accessTokenLocal || !!refreshTokenLocal || hasAccessTokenCookie || hasRefreshTokenCookie;

        console.log('checkAuthStatus: Результаты проверки токенов:', {
          hasAccessTokenCookie,
          hasRefreshTokenCookie,
          hasAccessTokenLocal: !!accessTokenLocal,
          hasRefreshTokenLocal: !!refreshTokenLocal,
          hasAnyToken,
          storedDisableAutoLogin
        });

        if (initialStoreState.isLoading) {
          console.log('checkAuthStatus: Пропускаем, так как уже идет загрузка (isLoading is true).');
          return;
        }

        if (storedDisableAutoLogin && !hasAnyToken) {
          console.log('checkAuthStatus: Пропускаем. Автологин отключен (localStorage) и нет токенов.');
          // Убедимся, что состояние store синхронизировано
          if (initialStoreState.isAuthenticated || initialStoreState.user || initialStoreState.tokens || !initialStoreState.disableAutoLogin) {
            set({
              user: null,
              isAuthenticated: false,
              isLoading: false,
              error: null,
              disableAutoLogin: true,
              tokens: null
            });
          }
          return;
        }
        
        set({ isLoading: true, error: null }); // Начинаем процесс проверки

        // Если есть токены, но они не в состоянии, или disableAutoLogin был активен, но теперь есть токены
        // Важно: если storedDisableAutoLogin был true, но hasAnyToken тоже true, значит, что-то произошло (например, логин на другой вкладке)
        // и мы должны попытаться войти.
        if (hasAnyToken && (storedDisableAutoLogin || !initialStoreState.tokens?.access)) {
            console.log('checkAuthStatus: Обнаружены токены и либо автологин был отключен, либо токены не в состоянии. Попытка синхронизации.');
            const newAccessToken = accessTokenLocal || (hasAccessTokenCookie ? 'from_cookie_placeholder' : ''); // Реальное значение из куки сложнее достать без парсинга
            const newRefreshToken = refreshTokenLocal || (hasRefreshTokenCookie ? 'from_cookie_placeholder' : '');
            
            set({
                tokens: { access: newAccessToken, refresh: newRefreshToken },
                // isAuthenticated: true, // Пока не подтверждено сервером
                disableAutoLogin: false // Разрешаем попытку автологина
            });
            localStorage.removeItem('disableAutoLogin'); // Снимаем флаг, так как пытаемся войти
            console.log('checkAuthStatus: disableAutoLogin сброшен в localStorage и store.');
        }

        try {
          console.log('checkAuthStatus: Отправляем запрос на получение данных пользователя.');
          const response = await api.auth.getUser();
          const user = response.data;
          console.log('checkAuthStatus: Получены данные пользователя:', user);

          localStorage.removeItem('disableAutoLogin'); // Успешный вход, убираем флаг
          set({
            user,
            isAuthenticated: true,
            isLoading: false,
            error: null,
            disableAutoLogin: false,
            // Токены уже должны быть в состоянии, если они из localStorage, или API вернул новые в cookie
          });
          console.log('checkAuthStatus: Пользователь успешно аутентифицирован.');

        } catch (error) {
          console.error('checkAuthStatus: Ошибка проверки аутентификации:', error);
          clearAuthData(); // Очищаем все токены, куки и ставим disableAutoLogin = true
          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: 'Ошибка сессии. Пожалуйста, войдите снова.', // Более общее сообщение
            disableAutoLogin: true, // Важно установить и в store
            tokens: null
          });
          console.log('checkAuthStatus: Данные аутентификации очищены из-за ошибки.');
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
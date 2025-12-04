import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import api from '@/lib/api/fetch';
import { useGoogleReCaptcha } from 'react-google-recaptcha-v3';

export interface User {
  id: string | number;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
  full_name?: string; // Полное имя пользователя
  avatar?: string;
  phone_number?: string;
  date_of_birth?: string; // Дата рождения в формате YYYY-MM-DD
  address?: string; // Адрес проживания
  is_verified?: boolean;
  kyc_verified?: boolean;
  telegram_id?: string;
  date_joined?: string;
  has_2fa?: boolean;
  is_site_admin?: boolean; // Право администратора сайта (frontend-контроль доступа)
  notify_via_email?: boolean;
  notify_via_telegram?: boolean;
  profile?: {
    website?: string;
    bio?: string; // Информация о себе
  };
}

interface Credentials {
  email: string;
  password: string;
  recaptcha_token: string;
}

interface RegistrationData {
  username: string;
  email: string;
  password1: string;
  password2: string;
  recaptcha_token: string;
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
  shouldPlayAnimation: boolean; // Флаг для анимации успеха
  
  login: (credentials: Credentials) => Promise<void>;
  register: (data: RegistrationData) => Promise<void>;
  logout: () => Promise<void>;
  clearError: () => void;
  checkAuthStatus: (isLoginProcess?: boolean) => Promise<void>;
  setShowEmailConfirmedModal: (show: boolean) => void;
  setDisableAutoLogin: (disable: boolean) => void;
  setTokens: (tokens: Tokens | null) => void;
  updateProfile: (profileData: Partial<User>, skipRefresh?: boolean) => Promise<void>;
  updateAvatar: (file: File) => Promise<void>;
  getAuthHeaders: () => Record<string, string>;
  setShouldPlayAnimation: (value: boolean) => void; // Функция для установки флага анимации
  socialLogin: () => void; // Функция для подготовки к социальному логину
}

const handleApiError = (error: unknown, defaultMessage: string): string => {
  if (error instanceof Error) {
    return error.message;
  }
  if (typeof error === 'string') {
    return error;
  }
  return defaultMessage;
};

const extractApiData = <T>(payload: unknown): T | null => {
  if (payload && typeof payload === 'object' && 'data' in payload) {
    const withData = payload as { data?: T };
    return withData.data ?? null;
  }
  return (payload as T) ?? null;
};

type RawUserResponse = User & { pk?: string | number };

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
      shouldPlayAnimation: false,
      
      setTokens: (tokens: Tokens | null) => {
        set({ tokens, isAuthenticated: !!(tokens && tokens.access), user: null }); 
      },
      
      login: async (credentials: Credentials) => {
        console.log('[AuthStore] login: Начало входа');
        set({ isLoading: true, error: null });
        try {
          // Используем токен reCAPTCHA, переданный из формы
          const payload: Credentials = { ...credentials };
          
          // Проверяем, что токен reCAPTCHA присутствует
          if (!payload.recaptcha_token) {
            throw new Error('Отсутствует токен reCAPTCHA');
          }

          // Шаг 1: Выполняем вход и получаем токены (предполагается, что бэкенд устанавливает HttpOnly куки)
          await api.post('/auth/login/', payload);
          console.log('[AuthStore] login: api.post(/auth/login/) успешно выполнен.');

          // Шаг 2: Сбрасываем флаг блокировки автовхода
          localStorage.removeItem('disableAutoLogin');
          set({ disableAutoLogin: false });
          console.log('[AuthStore] login: Флаг disableAutoLogin сброшен.');

          // Шаг 3: Загружаем данные пользователя и устанавливаем состояние аутентификации
          // Важно: дожидаемся завершения checkAuthStatus, чтобы user был загружен перед редиректом
          await get().checkAuthStatus(true);
          const finalState = get();
          console.log(
            '[AuthStore] login: checkAuthStatus завершен. Текущее состояние: user: ',
            finalState.user,
            ', isAuthenticated: ',
            finalState.isAuthenticated,
            ', isLoading: ',
            finalState.isLoading
          );
          
          // Убеждаемся, что isLoading установлен в false после успешного логина
          if (finalState.isAuthenticated && finalState.user && finalState.isLoading) {
            console.log('[AuthStore] login: Принудительно устанавливаем isLoading в false');
            set({ isLoading: false });
          }
        } catch (error) {
          console.error('[useAuthStore login] Ошибка входа:', error);
          clearAuthData(); // Очищаем все данные при ошибке входа
          set({
            error: handleApiError(error, 'Ошибка входа. Проверьте email и пароль или попробуйте позже.'),
            isLoading: false,
            isAuthenticated: false,
            user: null,
            tokens: null,
            disableAutoLogin: true,
          });
          console.log('[AuthStore] login: Ошибка, состояние сброшено.');
          throw error; // Пробрасываем ошибку, чтобы компонент мог на нее среагировать
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
          await api.post('/auth/logout/', {});
          console.log('[AuthStore] logout: api.auth.logout успешно выполнен.');
        } catch (error) {
          const message = error instanceof Error ? error.message : String(error);
          console.error("[AuthStore] logout: Ошибка при выходе на бэкенде:", message);
          // Продолжаем очистку на клиенте независимо от ошибки бэкенда
        }
        clearAuthData(); // clearAuthData устанавливает disableAutoLogin в localStorage
        // get().setDisableAutoLogin(true); // Больше не нужно здесь, clearAuthData это делает
        set({ user: null, isAuthenticated: false, isLoading: false, tokens: null, disableAutoLogin: true }); // Убедимся, что disableAutoLogin в сторе тоже true
        console.log('[AuthStore] logout: Выход выполнен, disableAutoLogin установлен.');
      },
      
      checkAuthStatus: async (isLoginProcess = false) => {
        const store = get();
        
        if (!isLoginProcess && store.disableAutoLogin) {
          console.warn(
            '[AuthStore] checkAuthStatus: Выполнение прервано из-за флага disableAutoLogin (не в процессе логина).'
          );
          set({ isLoading: false, user: null, isAuthenticated: false, tokens: null });
          return;
        }

        console.log(`[AuthStore] checkAuthStatus: Начало проверки. isLoginProcess: ${isLoginProcess}, disableAutoLogin в сторе: ${store.disableAutoLogin}`);
        set({ isLoading: true, error: null });
        
        

        try {
          console.log('[AuthStore] checkAuthStatus: Попытка загрузить профиль пользователя (api.auth.getUser).');
          
          // Получаем все доступные заголовки аутентификации
          const headers = get().getAuthHeaders();
          
          const response = await api.get<RawUserResponse | { data: RawUserResponse }>('/accounts/users/me/', { headers }); 
          const userData = extractApiData<RawUserResponse>(response);

          if (userData) {
            console.log('[AuthStore] checkAuthStatus: Профиль пользователя успешно загружен:', userData);
            const normalizedUser = {
              ...userData,
              id: userData.id ?? userData.pk ?? `unknown`,
              username: userData.username || userData.email || `user_${userData.pk ?? userData.id ?? 'unknown'}`,
            };
            
            // Проверяем, что все обязательные поля присутствуют
            if (normalizedUser.id !== null && normalizedUser.email && normalizedUser.username) {
              console.log('[AuthStore] checkAuthStatus: Нормализованный пользователь:', normalizedUser);
              set({
                user: normalizedUser,
                isAuthenticated: true,
                isLoading: false,
                error: null,
                disableAutoLogin: false,
                tokens: store.tokens,
              });
              if (localStorage.getItem('disableAutoLogin') === 'true') {
                localStorage.removeItem('disableAutoLogin');
                console.log('[AuthStore] checkAuthStatus: Флаг disableAutoLogin удален из localStorage.');
              }

              return;
            } else {
              console.error('[AuthStore] checkAuthStatus: Отсутствуют обязательные поля в данных пользователя:', 
                { id: normalizedUser.id, email: normalizedUser.email, username: normalizedUser.username });
            }
          } else {
            console.warn('[AuthStore] checkAuthStatus: Профиль пользователя загружен, но данные отсутствуют (userData is null/undefined). Это неожиданно.');
            // Если userData пустой, но запрос прошел успешно (что странно), считаем не аутентифицированным
            // Это приведет к установке неаутентифицированного состояния ниже
          }
        } catch (error) {
          const message = error instanceof Error ? error.message : String(error);
          console.warn(`[AuthStore] checkAuthStatus: Ошибка при загрузке профиля пользователя (вероятно, не аутентифицирован или API недоступен):`, message);
          if (isLoginProcess) {
            console.log('[AuthStore] checkAuthStatus: Ошибка в процессе логина, пробрасываю дальше.');
            set({ isLoading: false }); // Устанавливаем isLoading false перед пробросом
            throw error; // Позволяем функции login обработать эту ошибку
          }
          // Если не процесс логина, то просто фиксируем ошибку и далее установим неаутентифицированное состояние
          // (ошибка уже залогирована)
        }

        // Если мы здесь, значит, userData не был получен или была ошибка (не в процессе логина)
        console.log('[AuthStore] checkAuthStatus: Установка неаутентифицированного состояния (профиль не загружен или ошибка).');
        set({
          user: null,
          isAuthenticated: false,
          isLoading: false, 
          error: !isLoginProcess ? (store.error || 'Не удалось проверить сессию.') : store.error,
          // disableAutoLogin не меняем здесь принудительно на true, если это была ошибка API,
          // но если это был не логин процесс и проверка не удалась, то disableAutoLogin установится.
        });

        if (!isLoginProcess) {
          // Если это была фоновая проверка и она не удалась, тогда устанавливаем disableAutoLogin,
          // чтобы не пытаться автоматически логиниться с невалидной сессией.
          const currentDisableAutoLogin = get().disableAutoLogin;
          if (!currentDisableAutoLogin) { // Устанавливаем, только если еще не установлен
             get().setDisableAutoLogin(true); 
             console.log('[AuthStore] checkAuthStatus: Установлен disableAutoLogin т.к. фоновая проверка сессии не удалась.');
          }
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

      // Функция для получения всех доступных заголовков аутентификации
      getAuthHeaders: () => {
        if (typeof window === 'undefined') return {};
        
        const cookies = document.cookie;
        const headers: Record<string, string> = {};
        
        // Извлекаем CSRF токен
        const csrfToken = cookies.split(';').find(c => c.trim().startsWith('csrftoken='))?.split('=')[1];
        if (csrfToken) {
          headers['X-CSRFToken'] = csrfToken;
        }
        
        // Извлекаем другие важные куки
        const sessionId = cookies.split(';').find(c => c.trim().startsWith('sessionid='))?.split('=')[1];
        if (sessionId) {
          headers['X-Session-ID'] = sessionId;
        }
        
        // Логируем все доступные куки для отладки
        console.log('[AuthStore] getAuthHeaders: Все доступные куки:', cookies);
        console.log('[AuthStore] getAuthHeaders: Сформированы заголовки:', headers);
        
        return headers;
      },

      updateProfile: async (profileData: Partial<User>, skipRefresh: boolean = false) => {
        console.log('[AuthStore] updateProfile: Начало обновления профиля', { skipRefresh });
        set({ isLoading: true, error: null });
        
        try {
          // Получаем все доступные заголовки аутентификации
          const headers = get().getAuthHeaders();
          
          const response = await api.patch<User | { data: User }>('/accounts/users/update_profile/', profileData, { headers });
          const updatedUserData = extractApiData<User>(response);
          
          // Всегда устанавливаем isLoading в false после успешного запроса
          if (updatedUserData && !skipRefresh) {
            const currentUser = get().user;
            const updatedUser = currentUser ? { ...currentUser, ...updatedUserData } : null;
            set({ user: updatedUser, isLoading: false, error: null });
            console.log('[AuthStore] updateProfile: Профиль успешно обновлен с данными от сервера');
          } else if (!skipRefresh) {
            // Если нет данных в ответе, но нужно обновить store, используем отправленные данные
            const currentUser = get().user;
            const updatedUser = currentUser ? { ...currentUser, ...profileData } : null;
            set({ user: updatedUser, isLoading: false, error: null });
            console.log('[AuthStore] updateProfile: Профиль обновлен с отправленными данными');
          } else {
            // Если skipRefresh = true, не обновляем store
            set({ isLoading: false, error: null });
            console.log('[AuthStore] updateProfile: Профиль обновлен (пропущен refresh)');
          }
        } catch (error) {
          console.error('[AuthStore] updateProfile: Ошибка обновления профиля:', error);
          set({
            isLoading: false,
            error: handleApiError(error, 'Ошибка обновления профиля'),
          });
          throw error;
        }
      },





      updateAvatar: async (file: File) => {
        console.log('[AuthStore] updateAvatar: Начало обновления аватара');
        set({ isLoading: true, error: null });
        
        try {
          const formData = new FormData();
          formData.append('avatar', file);
          
          // Получаем все доступные заголовки аутентификации
          const headers = get().getAuthHeaders();
          
          // Для FormData не указываем Content-Type, браузер сам установит правильную границу
          const response = await api.patch<User | { data: User }>('/accounts/users/update_profile/', formData, { headers });
          
          const updatedUserData = extractApiData<User>(response);
          if (updatedUserData) {
            const currentUser = get().user;
            const updatedUser = currentUser ? { ...currentUser, avatar: updatedUserData.avatar } : null;
            set({ user: updatedUser, isLoading: false, error: null });
            console.log('[AuthStore] updateAvatar: Аватар успешно обновлен с данными от сервера');
          } else {
            // Если нет данных в ответе, принудительно обновляем аватар в сторе
            const currentUser = get().user;
            if (currentUser) {
              // Создаем временный URL для файла и обновляем аватар
              const tempAvatarUrl = URL.createObjectURL(file);
              const updatedUser = { ...currentUser, avatar: tempAvatarUrl };
              set({ user: updatedUser, isLoading: false, error: null });
              console.log('[AuthStore] updateAvatar: Аватар обновлен с временным URL (без данных от сервера)');
              
              // Сохраняем временный URL в localStorage для кэширования
              try {
                localStorage.setItem('temp_avatar_url', tempAvatarUrl);
                localStorage.setItem('temp_avatar_timestamp', Date.now().toString());
                console.log('[AuthStore] updateAvatar: Временный URL сохранен в localStorage');
              } catch (error) {
                console.log('[AuthStore] updateAvatar: Не удалось сохранить временный URL в localStorage:', error);
              }
              
              // Очищаем временный URL через большее время для надежности
              setTimeout(() => {
                URL.revokeObjectURL(tempAvatarUrl);
                // Удаляем из localStorage
                try {
                  localStorage.removeItem('temp_avatar_url');
                  localStorage.removeItem('temp_avatar_timestamp');
                } catch (error) {
                  console.log('[AuthStore] updateAvatar: Не удалось удалить временный URL из localStorage:', error);
                }
                console.log('[AuthStore] updateAvatar: Временный URL очищен');
              }, 10000); // Увеличили до 10 секунд
            } else {
              set({ isLoading: false, error: null });
              console.log('[AuthStore] updateAvatar: Аватар обновлен (без данных от сервера, пользователь не найден)');
            }
          }
        } catch (error) {
          console.error('[AuthStore] updateAvatar: Ошибка обновления аватара:', error);
          set({
            isLoading: false,
            error: handleApiError(error, 'Ошибка обновления аватара'),
          });
          throw error;
        }
      },

      setShouldPlayAnimation: (value: boolean) => {
        set({ shouldPlayAnimation: value });
      },
      
      socialLogin: () => {
        console.log('[AuthStore] socialLogin: Подготовка к социальному входу.');
        // Сбрасываем флаг, который мог остаться от предыдущего выхода из системы
        localStorage.removeItem('disableAutoLogin');
        set({ disableAutoLogin: false });
        console.log('[AuthStore] socialLogin: Флаг disableAutoLogin сброшен.');
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
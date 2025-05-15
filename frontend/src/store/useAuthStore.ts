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

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      showEmailConfirmedModal: false,
      disableAutoLogin: true,
      
      login: async (credentials: Credentials) => {
        try {
          set({ isLoading: true, error: null, disableAutoLogin: false });
          localStorage.removeItem('disableAutoLogin');
          console.log('Отправка запроса на вход:', credentials);

          const response = await fetch('http://localhost:8000/api/auth/login/', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(credentials),
            credentials: 'include',
            redirect: 'manual'
          });

          console.log('Статус ответа входа:', response.status);
          const responseText = await response.text();
          console.log('Тело ответа входа:', responseText);
          
          if (!response.ok) {
            try {
              const errorData = JSON.parse(responseText);
              throw new Error(errorData.detail || 'Ошибка авторизации');
            } catch (parseError) {
              throw new Error(`Ошибка авторизации: ${response.status} ${response.statusText}`);
            }
          }

          try {
            const data = JSON.parse(responseText);
            localStorage.removeItem('disableAutoLogin');
            
            if (!data.user) {
              console.error('Пользовательские данные не получены при входе');
              await get().checkAuthStatus();
            } else {
              set({
                isLoading: false,
                isAuthenticated: true,
                user: data.user,
                disableAutoLogin: false,
              });
              console.log('Вход выполнен успешно, данные пользователя:', data.user);
            }
          } catch (parseError) {
            console.error('Ошибка при разборе ответа JSON:', parseError);
            throw new Error('Ошибка при обработке ответа сервера');
          }
        } catch (error) {
          console.error('Ошибка входа:', error);
          set({
            isLoading: false,
            error: error instanceof Error ? error.message : 'Ошибка авторизации',
          });
          throw error;
        }
      },
      
      register: async (data: RegistrationData) => {
        try {
          set({ isLoading: true, error: null });
          localStorage.setItem('disableAutoLogin', 'true');
          console.log('Отправка запроса на регистрацию:', data);

          const url = 'http://localhost:8000/api/auth/registration/';
          console.log('URL для регистрации:', url);

          const response = await fetch(url, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
            redirect: 'manual'
          });

          console.log('Статус ответа регистрации:', response.status);
          const responseText = await response.text();
          console.log('Тело ответа регистрации:', responseText);

          if (!response.ok) {
            try {
              if (!responseText || responseText.trim() === '') {
                throw new Error(`Ошибка сервера: ${response.status} ${response.statusText}. Сервер вернул пустой ответ.`);
              }
              
              const errorData = JSON.parse(responseText);
              if (errorData.email) {
                throw new Error(`Email: ${errorData.email[0]}`);
              }
              if (errorData.username) {
                throw new Error(`Пользователь: ${errorData.username[0]}`); 
              }
              if (errorData.password) {
                throw new Error(`Пароль: ${errorData.password[0]}`);
              }
              if (errorData.non_field_errors) {
                throw new Error(errorData.non_field_errors[0]);
              }
              throw new Error(errorData.detail || 'Ошибка регистрации');
            } catch (parseError) {
              if (parseError instanceof SyntaxError) {
                console.error('Ошибка при разборе ответа:', parseError);
                throw new Error(`Ошибка сервера: ${response.status} ${response.statusText}. Убедитесь, что сервер Django запущен.`);
              }
              throw parseError;
            }
          }

          try {
            let responseData;
            
            if (responseText && responseText.trim() !== '') {
              responseData = JSON.parse(responseText);
              console.log('Успешный ответ регистрации:', responseData);
            } else {
              console.log('Пустой ответ от сервера, но статус успешный');
              responseData = {};
            }
            
            set({
              isLoading: false,
            });
          } catch (parseError) {
            console.error('Ошибка при разборе ответа JSON:', parseError);
            throw new Error('Ошибка при обработке ответа сервера');
          }
        } catch (error) {
          console.error('Ошибка регистрации:', error);
          set({
            isLoading: false,
            error: error instanceof Error ? error.message : 'Ошибка регистрации',
          });
          throw error;
        }
      },
      
      logout: async () => {
        set({ isLoading: true, error: null });
        try {
          const response = await fetch('http://localhost:8000/api/auth/logout/', { 
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            credentials: 'include',
          });
          if (!response.ok) {
            console.warn('Не удалось выполнить выход на стороне сервера, но клиент будет очищен.');
          }
        } catch (error) {
          console.error('Ошибка при выходе на стороне сервера:', error);
        } finally {
          localStorage.setItem('disableAutoLogin', 'true');
          const expirationDate = new Date();
          expirationDate.setDate(expirationDate.getDate() + 30);
          document.cookie = `disableAutoLogin=true; expires=${expirationDate.toUTCString()}; path=/;`;
          
          localStorage.removeItem('auth-storage');
          
          document.cookie = 'sessionid=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
          document.cookie = 'dj_session_id=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
          document.cookie = 'auth_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
          document.cookie = 'csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
          
          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: null,
            disableAutoLogin: true,
          });
          
          try {
            const allKeys = Object.keys(localStorage);
            for (const key of allKeys) {
              if (key.includes('auth') || key.includes('user') || key.includes('token')) {
                localStorage.removeItem(key);
              }
            }
          } catch (err) {
            console.error('Ошибка при очистке localStorage:', err);
          }

          console.log('Выход выполнен успешно, все данные очищены');
        }
      },
      
      clearError: () => set({ error: null }),

      setShowEmailConfirmedModal: (show: boolean) => {
        set({ showEmailConfirmedModal: show });
      },

      setDisableAutoLogin: (disable: boolean) => {
        localStorage.setItem('disableAutoLogin', disable.toString());
        if (disable) {
          const expirationDate = new Date();
          expirationDate.setDate(expirationDate.getDate() + 30);
          document.cookie = `disableAutoLogin=true; expires=${expirationDate.toUTCString()}; path=/;`;
        } else {
          document.cookie = 'disableAutoLogin=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
        }
        set({ disableAutoLogin: disable });
      },

      checkAuthStatus: async () => {
        const state = get();
        
        if (state.isAuthenticated && state.user) {
          console.log('Пользователь уже аутентифицирован, пропускаем проверку');
          return;
        }
        
        const storedDisableAutoLogin = localStorage.getItem('disableAutoLogin') === 'true';
        if (state.disableAutoLogin && storedDisableAutoLogin) {
          console.log('Автоматический вход отключен пользователем через флаг');
          return;
        }
        
        if (state.isLoading) {
          console.log('Проверка авторизации уже выполняется, пропускаем');
          return;
        }
        
        set({ isLoading: true, error: null });
        try {
          console.log('Проверка статуса аутентификации...');
          const response = await fetch('http://localhost:8000/api/auth/user/', {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
            },
            credentials: 'include',
          });

          const responseText = await response.text();
          
          if (response.ok) {
            try {
              const userData = JSON.parse(responseText);
              localStorage.removeItem('disableAutoLogin');
              set({
                user: userData,
                isAuthenticated: true,
                isLoading: false,
                error: null,
                disableAutoLogin: false,
              });
              console.log('Пользователь аутентифицирован, данные:', userData);
            } catch (parseError) {
              console.error('Ошибка при разборе ответа JSON:', parseError);
              set({
                isLoading: false,
                error: 'Ошибка при обработке ответа сервера',
              });
            }
          } else {
            set({
              user: null,
              isAuthenticated: false,
              isLoading: false,
              error: null,
              disableAutoLogin: true,
            });
            localStorage.setItem('disableAutoLogin', 'true');
            console.log('Пользователь не аутентифицирован или сессия истекла.');
          }
        } catch (error) {
          console.error('Ошибка при проверке статуса аутентификации:', error);
          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: error instanceof Error ? error.message : 'Ошибка проверки статуса',
            disableAutoLogin: true,
          });
          localStorage.setItem('disableAutoLogin', 'true');
        }
      },
    }),
    {
      name: 'auth-storage',
    }
  )
); 
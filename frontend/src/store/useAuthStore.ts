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

// Функция для получения CSRF токена из cookie
const getCsrfToken = () => {
  const cookies = document.cookie.split(';');
  const csrfCookie = cookies.find(cookie => cookie.trim().startsWith('csrftoken='));
  return csrfCookie ? csrfCookie.split('=')[1] : '';
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
          const csrfToken = getCsrfToken();
          console.log('CSRF токен для входа:', csrfToken);

          const response = await fetch('/api/auth/login/', {
            method: 'POST',
            credentials: 'include',
            headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': csrfToken,
            },
            body: JSON.stringify(credentials),
          });

          console.log('Статус ответа входа:', response.status);
          const responseText = await response.text();
          console.log('Тело ответа входа:', responseText);

          if (!response.ok) {
            try {
              if (!responseText || responseText.trim() === '') {
                throw new Error(`Ошибка сервера: ${response.status} ${response.statusText}. Сервер вернул пустой ответ.`);
              }
              
              const errorData = JSON.parse(responseText);
              throw new Error(errorData.detail || 'Ошибка входа');
            } catch (parseError) {
              if (parseError instanceof SyntaxError) {
                console.error('Ошибка при разборе ответа:', parseError);
                throw new Error(`Ошибка сервера: ${response.status} ${response.statusText}. Убедитесь, что сервер Django запущен.`);
              }
              throw parseError;
            }
          }

          try {
            let data;
            if (responseText && responseText.trim() !== '') {
              data = JSON.parse(responseText);
              console.log('Успешный ответ входа:', data);
            } else {
              console.log('Пустой ответ от сервера, но статус успешный');
              data = { user: null };
            }

            // Сохраняем токен в localStorage и cookie
            localStorage.setItem('auth-token', data.token);
            document.cookie = `auth-token=${data.token}; path=/; max-age=2592000`; // 30 дней
            
            set({ 
              user: data.user,
              isAuthenticated: true,
              isLoading: false,
              error: null,
              disableAutoLogin: false
            });
            
          } catch (parseError) {
            console.error('Ошибка при разборе ответа JSON:', parseError);
            throw new Error('Ошибка при обработке ответа сервера');
          }
        } catch (error) {
          console.error('Login error:', error);
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
        try {
          set({ isLoading: true, error: null });
          localStorage.setItem('disableAutoLogin', 'true');
          console.log('Отправка запроса на регистрацию:', data);

          const url = '/api/auth/registration/';
          console.log('URL для регистрации:', url);

          // Получаем CSRF токен из cookie
          const csrfToken = getCsrfToken();
          console.log('CSRF токен для регистрации:', csrfToken);

          const response = await fetch(url, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': csrfToken,
            },
            body: JSON.stringify(data),
            credentials: 'include',
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
          const response = await fetch('/api/auth/logout/', { 
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            credentials: 'include',
          });
          
          console.log('Статус выхода:', response.status);
          
          if (!response.ok) {
            console.warn('Не удалось выполнить выход на стороне сервера, но клиент будет очищен.');
          }
        } catch (error) {
          console.error('Ошибка при выходе на стороне сервера:', error);
        } finally {
          // Очищаем все данные авторизации
          localStorage.setItem('disableAutoLogin', 'true');
          
          // Очищаем куки
          document.cookie = 'sessionid=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
          document.cookie = 'csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
          document.cookie = 'auth=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
          document.cookie = 'refresh-token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
          
          // Очищаем состояние
          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: null,
            disableAutoLogin: true,
          });
          
          // Очищаем localStorage
          localStorage.removeItem('auth-storage');
          
          console.log('Выход выполнен успешно, все данные очищены');
          
          // Перезагружаем страницу для полной очистки состояния
          window.location.href = '/';
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
        
        if (state.isLoading) {
          console.log('Проверка авторизации уже выполняется, пропускаем');
          return;
        }

        // Проверяем наличие токена в localStorage
        const token = localStorage.getItem('auth-token');
        
        if (!token) {
          console.log('Нет сохраненных данных авторизации');
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
          console.log('Проверка статуса аутентификации...');
          
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

          const userData = await response.json();
          
          // Обновляем cookie при каждой успешной проверке
          document.cookie = `auth-token=${token}; path=/; max-age=2592000`; // 30 дней
          
          set({
            user: userData,
            isAuthenticated: true,
            isLoading: false,
            error: null,
            disableAutoLogin: false,
          });
          console.log('Пользователь аутентифицирован, данные:', userData);
          
        } catch (error) {
          console.log('Ошибка при проверке статуса:', error);
          // Очищаем все данные авторизации при ошибке
          localStorage.removeItem('auth-token');
          document.cookie = 'auth-token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
          
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
      // Указываем, какие поля нужно сохранять в localStorage
      partialize: (state) => ({ 
        user: state.user,
        isAuthenticated: state.isAuthenticated,
        disableAutoLogin: state.disableAutoLogin
      }),
    }
  )
); 
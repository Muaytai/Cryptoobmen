import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
  id: string;
  username: string;
  email: string;
}

interface Credentials {
  username: string;
  password: string;
}

interface RegistrationData {
  username: string;
  email: string;
  password: string;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  
  login: (credentials: Credentials) => Promise<void>;
  register: (data: RegistrationData) => Promise<void>;
  logout: () => void;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      
      login: async (credentials: Credentials) => {
        try {
          set({ isLoading: true, error: null });
          console.log('Отправка запроса на вход:', credentials);

          const response = await fetch('/api/auth/login/', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(credentials),
            // Убедимся, что Next.js не делает автоматический редирект
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
            // Сохраняем токен (JWT)
            if (data.access) {
              localStorage.setItem('access', data.access);
            }
            set({
              isLoading: false,
              isAuthenticated: true,
              user: data.user || null,
            });
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
          console.log('Отправка запроса на регистрацию:', data);

          // Создаем URL с явным слэшем в конце
          const url = '/api/auth/registration/';
          console.log('URL для регистрации:', url);

          const response = await fetch(url, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
            // Убедимся, что Next.js не делает автоматический редирект
            redirect: 'manual'
          });

          console.log('Статус ответа регистрации:', response.status);
          const responseText = await response.text();
          console.log('Тело ответа регистрации:', responseText);

          if (!response.ok) {
            try {
              // Проверяем, не пустая ли строка
              if (!responseText || responseText.trim() === '') {
                throw new Error(`Ошибка сервера: ${response.status} ${response.statusText}. Сервер вернул пустой ответ.`);
              }
              
              const errorData = JSON.parse(responseText);
              // Обработка ошибок валидации от Django Rest Framework
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
                // Если не можем распарсить JSON, значит, бэкенд вернул не JSON
                console.error('Ошибка при разборе ответа:', parseError);
                throw new Error(`Ошибка сервера: ${response.status} ${response.statusText}. Убедитесь, что сервер Django запущен.`);
              }
              throw parseError; // Пробрасываем ошибки, которые уже были обработаны выше
            }
          }

          try {
            // Пробуем распарсить успешный ответ
            let responseData;
            
            // Проверяем, не пустой ли ответ
            if (responseText && responseText.trim() !== '') {
              responseData = JSON.parse(responseText);
              console.log('Успешный ответ регистрации:', responseData);
            } else {
              console.log('Пустой ответ от сервера, но статус успешный');
              responseData = {};
            }
            
            // Если регистрация успешна, выполняем вход с теми же данными
            await get().login({
              username: data.email,
              password: data.password
            });
            
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
      
      logout: () => {
        // В реальном приложении здесь будет запрос к API для уничтожения токена:
        // fetch('/api/auth/logout/', { method: 'POST' });
        localStorage.removeItem('access');
        set({
          user: null,
          isAuthenticated: false,
          error: null,
        });
      },
      
      clearError: () => set({ error: null }),
    }),
    {
      name: 'auth-storage',
      // В production необходимо добавить шифрование для безопасного хранения
    }
  )
); 
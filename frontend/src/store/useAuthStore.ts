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
          
          // В реальном приложении здесь будет запрос к API:
          // const response = await fetch('/api/auth/login', {
          //   method: 'POST',
          //   headers: {
          //     'Content-Type': 'application/json',
          //   },
          //   body: JSON.stringify(credentials),
          // });
          // 
          // if (!response.ok) {
          //   const errorData = await response.json();
          //   throw new Error(errorData.message || 'Ошибка авторизации');
          // }
          // 
          // const data = await response.json();
          
          // Имитация ответа от сервера:
          await new Promise(resolve => setTimeout(resolve, 1000));
          
          // Проверка демонстрационного логина:
          if (credentials.username === 'demo' && credentials.password === 'password') {
            const mockUser = {
              id: '1',
              username: credentials.username,
              email: 'demo@example.com',
            };
            
            set({
              isLoading: false,
              isAuthenticated: true,
              user: mockUser,
            });
          } else {
            throw new Error('Неверное имя пользователя или пароль');
          }
        } catch (error) {
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
          
          // В реальном приложении здесь будет запрос к API:
          // const response = await fetch('/api/auth/register', {
          //   method: 'POST',
          //   headers: {
          //     'Content-Type': 'application/json',
          //   },
          //   body: JSON.stringify(data),
          // });
          // 
          // if (!response.ok) {
          //   const errorData = await response.json();
          //   throw new Error(errorData.message || 'Ошибка регистрации');
          // }
          // 
          // const responseData = await response.json();
          
          // Имитация ответа от сервера:
          await new Promise(resolve => setTimeout(resolve, 1000));
          
          const mockUser = {
            id: '2',
            username: data.username,
            email: data.email,
          };
          
          set({
            isLoading: false,
            isAuthenticated: true,
            user: mockUser,
          });
        } catch (error) {
          set({
            isLoading: false,
            error: error instanceof Error ? error.message : 'Ошибка регистрации',
          });
          throw error;
        }
      },
      
      logout: () => {
        // В реальном приложении здесь будет запрос к API для уничтожения токена:
        // fetch('/api/auth/logout', { method: 'POST' });
        
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
import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import api from '@/lib/api/axios';
import { User, LoginCredentials, RegisterCredentials } from '@/types/api';

interface AuthState {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isLoading: boolean;
  error: string | null;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (credentials: RegisterCredentials) => Promise<void>;
  logout: () => void;
  getProfile: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      refreshToken: null,
      isLoading: false,
      error: null,

      login: async (credentials) => {
        set({ isLoading: true, error: null });
        try {
          const response = await api.post('/auth/login/', credentials);
          const { access_token, refresh_token, user } = response.data;
          
          localStorage.setItem('token', access_token);
          
          set({
            token: access_token,
            refreshToken: refresh_token,
            user,
            isLoading: false,
          });
        } catch (error: any) {
          set({
            error: error.response?.data?.detail || 'Ошибка при входе',
            isLoading: false,
          });
        }
      },

      register: async (credentials) => {
        set({ isLoading: true, error: null });
        try {
          const response = await api.post('/auth/register/', credentials);
          const { access_token, refresh_token, user } = response.data;
          
          localStorage.setItem('token', access_token);
          
          set({
            token: access_token,
            refreshToken: refresh_token,
            user,
            isLoading: false,
          });
        } catch (error: any) {
          set({
            error: error.response?.data?.detail || 'Ошибка при регистрации',
            isLoading: false,
          });
        }
      },

      logout: () => {
        localStorage.removeItem('token');
        set({ token: null, refreshToken: null, user: null });
      },

      getProfile: async () => {
        set({ isLoading: true, error: null });
        try {
          const response = await api.get('/auth/profile/');
          set({ user: response.data, isLoading: false });
        } catch (error: any) {
          set({
            error: error.response?.data?.detail || 'Ошибка при загрузке профиля',
            isLoading: false,
          });
        }
      },
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => localStorage),
    }
  )
); 
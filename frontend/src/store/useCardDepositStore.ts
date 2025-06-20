import { create } from 'zustand';
import api from '@/lib/api/fetch';

export interface CardDeposit {
  id: number;
  deposit_id: string;
  user: number;
  user_email: string;
  wallet: number;
  crypto_symbol: string;
  amount: string;
  currency: string;
  card_last4: string | null;
  card_brand: string | null;
  status: string;
  status_display: string;
  payment_id: string | null;
  fee: string;
  crypto_amount: string | null;
  exchange_rate: string | null;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}

export interface DepositStats {
  completed_deposits: {
    count: number;
    total_amount: number;
    total_crypto: number;
  };
  processing_deposits: {
    count: number;
    total_amount: number;
  };
  failed_deposits: {
    count: number;
    total_amount: number;
  };
  total_deposits: {
    count: number;
    total_amount: number;
  };
}

interface CardDepositState {
  deposits: CardDeposit[];
  stats: DepositStats | null;
  isLoading: boolean;
  error: string | null;
  
  fetchDeposits: () => Promise<void>;
  fetchDepositStats: () => Promise<void>;
  createDeposit: (walletId: number, amount: number, currency: string) => Promise<any>;
  clearError: () => void;
}

export const useCardDepositStore = create<CardDepositState>((set, get) => ({
  deposits: [],
  stats: null,
  isLoading: false,
  error: null,
  
  fetchDeposits: async () => {
    try {
      set({ isLoading: true, error: null });
      const resp = await api.get('/crypto/card-deposits/');
      const data = Array.isArray(resp) ? resp : (resp as any).data;
      set({ deposits: data, isLoading: false });
    } catch (error) {
      console.error('Ошибка при загрузке пополнений:', error);
      set({ 
        error: 'Не удалось загрузить историю пополнений', 
        isLoading: false 
      });
    }
  },
  
  fetchDepositStats: async () => {
    try {
      set({ isLoading: true, error: null });
      const respS = await api.get('/crypto/card-deposits/stats/');
      const dataS = (respS as any).data ?? respS;
      set({ stats: dataS, isLoading: false });
    } catch (error) {
      console.error('Ошибка при загрузке статистики пополнений:', error);
      set({ 
        error: 'Не удалось загрузить статистику пополнений', 
        isLoading: false 
      });
    }
  },
  
  createDeposit: async (walletId: number, amount: number, currency: string) => {
    try {
      set({ isLoading: true, error: null });
      const response = await api.post('/crypto/card-deposits/', {
        wallet: walletId,
        amount: amount,
        currency: currency
      });
      
      // Обновляем список пополнений
      await get().fetchDeposits();
      await get().fetchDepositStats();
      
      set({ isLoading: false });
      const newDep = (response as any).data ?? response;
      return newDep;
    } catch (error: any) {
      console.error('Ошибка при создании пополнения:', error);
      const errorMessage = error.response?.data?.error || 'Не удалось создать пополнение';
      set({ 
        error: errorMessage, 
        isLoading: false 
      });
      throw error;
    }
  },
  
  clearError: () => {
    set({ error: null });
  }
}));

import { create } from 'zustand';
import { api } from '@/lib/api/fetch';

export interface Wallet {
  id: number;
  crypto: number;
  crypto_name: string;
  crypto_symbol: string;
  crypto_icon: string;
  balance: string;
  available_balance: string;
  locked_balance: string;
  address: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CryptoPrice {
  id: number;
  crypto: number;
  crypto_name: string;
  crypto_symbol: string;
  price_usd: string;
  price_btc?: string;
  price_eth?: string;
  market_cap?: string;
  volume_24h?: string;
  timestamp: string;
}

interface WalletState {
  wallets: Wallet[];
  prices: CryptoPrice[];
  isLoading: boolean;
  error: string | null;
  totalUsdBalance: number;
  
  fetchWallets: () => Promise<void>;
  fetchPrices: () => Promise<void>;
  fetchTotalBalance: () => Promise<void>;
}

export const useWalletStore = create<WalletState>((set, get) => ({
  wallets: [],
  prices: [],
  isLoading: false,
  error: null,
  totalUsdBalance: 0,
  
  fetchWallets: async () => {
    try {
      set({ isLoading: true, error: null });
      const response = await api.get('/crypto/wallets/');
      set({ wallets: response.data, isLoading: false });
    } catch (error) {
      console.error('Ошибка при загрузке кошельков:', error);
      set({ 
        error: 'Не удалось загрузить данные кошельков', 
        isLoading: false 
      });
    }
  },
  
  fetchPrices: async () => {
    try {
      set({ isLoading: true, error: null });
      const response = await api.get('/crypto/prices/latest/');
      set({ prices: response.data, isLoading: false });
    } catch (error) {
      console.error('Ошибка при загрузке цен:', error);
      set({ 
        error: 'Не удалось загрузить данные о ценах', 
        isLoading: false 
      });
    }
  },
  
  fetchTotalBalance: async () => {
    try {
      set({ isLoading: true, error: null });
      const response = await api.get('/crypto/wallets/balance/');
      set({ 
        totalUsdBalance: response.data.total_usd_balance, 
        isLoading: false 
      });
    } catch (error) {
      console.error('Ошибка при загрузке общего баланса:', error);
      set({ 
        error: 'Не удалось загрузить данные об общем балансе', 
        isLoading: false 
      });
    }
  },
}));

import { create } from 'zustand';
import { api } from '@/lib/api/fetch';

export interface InvestmentPlan {
  id: number;
  name: string;
  description: string;
  crypto: number;
  crypto_name: string;
  crypto_symbol: string;
  interest_rate: string;
  duration_value: number;
  duration_unit: string;
  duration_unit_display: string;
  duration_in_days: number;
  min_investment: string;
  max_investment: string;
  is_active: boolean;
  early_withdrawal_allowed: boolean;
  early_withdrawal_fee: string;
  created_at: string;
  updated_at: string;
}

export interface UserInvestment {
  id: number;
  investment_id: string;
  user: number;
  wallet: number;
  plan: number;
  plan_name: string;
  crypto_symbol: string;
  crypto_name: string;
  amount: string;
  expected_return: string;
  interest_rate: string;
  start_date: string;
  end_date: string;
  status: string;
  status_display: string;
  actual_return: string | null;
  completed_date: string | null;
  progress: number;
  created_at: string;
  updated_at: string;
}

export interface InvestmentStats {
  active_investments: {
    count: number;
    total_amount: number;
    expected_return: number;
  };
  completed_investments: {
    count: number;
    total_amount: number;
    total_return: number;
  };
  total_investments: {
    count: number;
    total_amount: number;
  };
}

interface InvestmentState {
  plans: InvestmentPlan[];
  userInvestments: UserInvestment[];
  stats: InvestmentStats | null;
  selectedPlan: InvestmentPlan | null;
  calculatedReturn: any | null;
  isLoading: boolean;
  error: string | null;
  
  fetchPlans: () => Promise<void>;
  fetchPlansByCrypto: (cryptoId: number) => Promise<void>;
  fetchUserInvestments: () => Promise<void>;
  fetchInvestmentStats: () => Promise<void>;
  calculateReturn: (planId: number, amount: number) => Promise<void>;
  createInvestment: (walletId: number, planId: number, amount: number) => Promise<any>;
  withdrawInvestment: (investmentId: number) => Promise<any>;
  setSelectedPlan: (plan: InvestmentPlan | null) => void;
  clearError: () => void;
}

export const useInvestmentStore = create<InvestmentState>((set, get) => ({
  plans: [],
  userInvestments: [],
  stats: null,
  selectedPlan: null,
  calculatedReturn: null,
  isLoading: false,
  error: null,
  
  fetchPlans: async () => {
    try {
      set({ isLoading: true, error: null });
      const response = await api.get('/crypto/investment-plans/');
      set({ plans: response.data, isLoading: false });
    } catch (error) {
      console.error('Ошибка при загрузке инвестиционных планов:', error);
      set({ 
        error: 'Не удалось загрузить инвестиционные планы', 
        isLoading: false 
      });
    }
  },
  
  fetchPlansByCrypto: async (cryptoId: number) => {
    try {
      set({ isLoading: true, error: null });
      const response = await api.get(`/crypto/investment-plans/by_crypto/?crypto_id=${cryptoId}`);
      set({ plans: response.data, isLoading: false });
    } catch (error) {
      console.error('Ошибка при загрузке инвестиционных планов для криптовалюты:', error);
      set({ 
        error: 'Не удалось загрузить инвестиционные планы для выбранной криптовалюты', 
        isLoading: false 
      });
    }
  },
  
  fetchUserInvestments: async () => {
    try {
      set({ isLoading: true, error: null });
      const response = await api.get('/crypto/investments/');
      set({ userInvestments: response.data, isLoading: false });
    } catch (error) {
      console.error('Ошибка при загрузке инвестиций пользователя:', error);
      set({ 
        error: 'Не удалось загрузить ваши инвестиции', 
        isLoading: false 
      });
    }
  },
  
  fetchInvestmentStats: async () => {
    try {
      set({ isLoading: true, error: null });
      const response = await api.get('/crypto/investments/stats/');
      set({ stats: response.data, isLoading: false });
    } catch (error) {
      console.error('Ошибка при загрузке статистики инвестиций:', error);
      set({ 
        error: 'Не удалось загрузить статистику инвестиций', 
        isLoading: false 
      });
    }
  },
  
  calculateReturn: async (planId: number, amount: number) => {
    try {
      set({ isLoading: true, error: null, calculatedReturn: null });
      const response = await api.get(`/crypto/investment-plans/${planId}/calculate_return/?amount=${amount}`);
      set({ calculatedReturn: response.data, isLoading: false });
      return response.data;
    } catch (error: any) {
      console.error('Ошибка при расчете доходности:', error);
      const errorMessage = error.response?.data?.error || 'Не удалось рассчитать доходность';
      set({ 
        error: errorMessage, 
        isLoading: false,
        calculatedReturn: null
      });
      throw error;
    }
  },
  
  createInvestment: async (walletId: number, planId: number, amount: number) => {
    try {
      set({ isLoading: true, error: null });
      const response = await api.post('/crypto/investments/', {
        wallet: walletId,
        plan: planId,
        amount: amount
      });
      
      // Обновляем список инвестиций пользователя
      await get().fetchUserInvestments();
      await get().fetchInvestmentStats();
      
      set({ isLoading: false });
      return response.data;
    } catch (error: any) {
      console.error('Ошибка при создании инвестиции:', error);
      const errorMessage = error.response?.data?.error || 'Не удалось создать инвестицию';
      set({ 
        error: errorMessage, 
        isLoading: false 
      });
      throw error;
    }
  },
  
  withdrawInvestment: async (investmentId: number) => {
    try {
      set({ isLoading: true, error: null });
      const response = await api.post(`/crypto/investments/${investmentId}/withdraw_early/`);
      
      // Обновляем список инвестиций пользователя
      await get().fetchUserInvestments();
      await get().fetchInvestmentStats();
      
      set({ isLoading: false });
      return response.data;
    } catch (error: any) {
      console.error('Ошибка при досрочном выводе инвестиции:', error);
      const errorMessage = error.response?.data?.error || 'Не удалось вывести инвестицию';
      set({ 
        error: errorMessage, 
        isLoading: false 
      });
      throw error;
    }
  },
  
  setSelectedPlan: (plan: InvestmentPlan | null) => {
    set({ selectedPlan: plan });
  },
  
  clearError: () => {
    set({ error: null });
  }
}));

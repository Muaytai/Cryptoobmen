'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/useAuthStore';

interface ExchangeRate {
  from: string;
  to: string;
  rate: number;
}

export default function ExchangePage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const [fromCurrency, setFromCurrency] = useState('BTC');
  const [toCurrency, setToCurrency] = useState('USDT');
  const [amount, setAmount] = useState('');
  const [exchangeRates, setExchangeRates] = useState<ExchangeRate[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }

    // Имитация загрузки курсов обмена
    const fetchExchangeRates = async () => {
      try {
        // В реальном приложении здесь будет API запрос
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        setExchangeRates([
          { from: 'BTC', to: 'USDT', rate: 45000 },
          { from: 'ETH', to: 'USDT', rate: 3000 },
          { from: 'BTC', to: 'ETH', rate: 15 }
        ]);
        
        setIsLoading(false);
      } catch (error) {
        console.error('Ошибка загрузки курсов:', error);
        setIsLoading(false);
      }
    };

    fetchExchangeRates();
  }, [isAuthenticated, router]);

  const calculateExchangeAmount = () => {
    const rate = exchangeRates.find(
      rate => rate.from === fromCurrency && rate.to === toCurrency
    )?.rate || 0;
    
    return parseFloat(amount) * rate;
  };

  const handleExchange = async () => {
    try {
      // В реальном приложении здесь будет API запрос
      await new Promise(resolve => setTimeout(resolve, 1000));
      alert('Обмен успешно выполнен!');
      setAmount('');
    } catch (error) {
      console.error('Ошибка при обмене:', error);
      alert('Произошла ошибка при обмене');
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 py-6 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">
        <div className="bg-white rounded-lg shadow p-6">
          <h1 className="text-2xl font-semibold text-gray-900 mb-6">
            Обмен криптовалют
          </h1>
          
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Отдаю
              </label>
              <div className="flex space-x-4">
                <input
                  type="number"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  placeholder="0.00"
                  className="flex-1 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
                <select
                  value={fromCurrency}
                  onChange={(e) => setFromCurrency(e.target.value)}
                  className="rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                >
                  <option value="BTC">BTC</option>
                  <option value="ETH">ETH</option>
                  <option value="USDT">USDT</option>
                </select>
              </div>
            </div>
            
            <div className="flex justify-center">
              <button
                onClick={() => {
                  const temp = fromCurrency;
                  setFromCurrency(toCurrency);
                  setToCurrency(temp);
                }}
                className="p-2 rounded-full hover:bg-gray-100"
              >
                ↕️
              </button>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Получаю
              </label>
              <div className="flex space-x-4">
                <input
                  type="number"
                  value={calculateExchangeAmount()}
                  disabled
                  className="flex-1 bg-gray-50 rounded-md border-gray-300 shadow-sm"
                />
                <select
                  value={toCurrency}
                  onChange={(e) => setToCurrency(e.target.value)}
                  className="rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                >
                  <option value="BTC">BTC</option>
                  <option value="ETH">ETH</option>
                  <option value="USDT">USDT</option>
                </select>
              </div>
            </div>
            
            <div className="bg-gray-50 p-4 rounded-md">
              <h3 className="text-sm font-medium text-gray-700 mb-2">
                Курс обмена
              </h3>
              <p className="text-lg font-semibold text-gray-900">
                1 {fromCurrency} = {
                  exchangeRates.find(
                    rate => rate.from === fromCurrency && rate.to === toCurrency
                  )?.rate || '—'
                } {toCurrency}
              </p>
            </div>
            
            <div className="flex justify-end space-x-4">
              <button
                onClick={() => router.push('/dashboard')}
                className="px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300 transition-colors"
              >
                Отмена
              </button>
              <button
                onClick={handleExchange}
                disabled={!amount || parseFloat(amount) <= 0}
                className="px-4 py-2 text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Обменять
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 
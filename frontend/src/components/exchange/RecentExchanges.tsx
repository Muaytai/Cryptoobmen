'use client';

import { useState, useEffect } from 'react';
import { RefreshCw } from 'lucide-react';

interface Exchange {
  id: string;
  fromCurrency: string;
  toCurrency: string;
  fromAmount: number;
  toAmount: number;
  timestamp: string;
  status: 'completed' | 'pending' | 'failed';
}

// Функция для генерации случайных обменов (в реальном приложении здесь будет API запрос)
const generateRandomExchanges = (count: number): Exchange[] => {
  const currencies = ['BTC', 'ETH', 'USDT', 'XRP', 'LTC', 'ADA'];
  const now = new Date();
  
  return Array(count).fill(0).map((_, index) => {
    const fromCurrency = currencies[Math.floor(Math.random() * currencies.length)];
    let toCurrency = currencies[Math.floor(Math.random() * currencies.length)];
    
    // Убедимся, что валюты не совпадают
    while (toCurrency === fromCurrency) {
      toCurrency = currencies[Math.floor(Math.random() * currencies.length)];
    }
    
    // Случайная сумма в зависимости от валюты
    const fromAmount = fromCurrency === 'BTC' 
      ? +(Math.random() * 0.5).toFixed(6)
      : fromCurrency === 'ETH'
      ? +(Math.random() * 5).toFixed(4)
      : +(Math.random() * 1000).toFixed(2);
    
    // Случайный курс обмена
    const rate = fromCurrency === 'BTC' && toCurrency === 'USDT'
      ? 45000 + Math.random() * 2000
      : fromCurrency === 'ETH' && toCurrency === 'USDT'
      ? 3000 + Math.random() * 200
      : Math.random() * 100;
    
    const toAmount = +(fromAmount * rate).toFixed(2);
    
    // Случайное время в последние 24 часа
    const timestamp = new Date(now.getTime() - Math.random() * 24 * 60 * 60 * 1000).toISOString();
    
    return {
      id: `tx-${Math.random().toString(36).substring(2, 10)}`,
      fromCurrency,
      toCurrency,
      fromAmount,
      toAmount,
      timestamp,
      status: 'completed'
    };
  });
};

export function RecentExchanges() {
  const [exchanges, setExchanges] = useState<Exchange[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  
  const fetchExchanges = async () => {
    setIsLoading(true);
    try {
      // Имитация API запроса
      await new Promise(resolve => setTimeout(resolve, 1000));
      const data = generateRandomExchanges(10);
      setExchanges(data);
    } catch (error) {
      console.error('Ошибка при загрузке обменов:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  useEffect(() => {
    fetchExchanges();
    
    // Обновляем данные каждые 30 секунд
    const interval = setInterval(fetchExchanges, 30000);
    return () => clearInterval(interval);
  }, []);
  
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
  };
  
  const formatAmount = (amount: number, currency: string) => {
    if (currency === 'BTC') {
      return amount.toFixed(6);
    } else if (currency === 'ETH') {
      return amount.toFixed(4);
    } else {
      return amount.toFixed(2);
    }
  };
  
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 border border-gray-200 dark:border-gray-700">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Последние обмены</h2>
        <button 
          onClick={fetchExchanges}
          className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300"
          disabled={isLoading}
        >
          <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
        </button>
      </div>
      
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left">
          <thead className="text-xs text-gray-700 dark:text-gray-300 uppercase bg-gray-50 dark:bg-gray-700">
            <tr>
              <th className="px-4 py-2">Время</th>
              <th className="px-4 py-2">Отдано</th>
              <th className="px-4 py-2">Получено</th>
              <th className="px-4 py-2">Статус</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {isLoading ? (
              Array(5).fill(0).map((_, index) => (
                <tr key={index} className="animate-pulse">
                  <td className="px-4 py-3"><div className="h-4 bg-gray-200 dark:bg-gray-600 rounded w-16"></div></td>
                  <td className="px-4 py-3"><div className="h-4 bg-gray-200 dark:bg-gray-600 rounded w-24"></div></td>
                  <td className="px-4 py-3"><div className="h-4 bg-gray-200 dark:bg-gray-600 rounded w-24"></div></td>
                  <td className="px-4 py-3"><div className="h-4 bg-gray-200 dark:bg-gray-600 rounded w-20"></div></td>
                </tr>
              ))
            ) : (
              exchanges.map(exchange => (
                <tr key={exchange.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                  <td className="px-4 py-2 text-gray-500 dark:text-gray-400">{formatTime(exchange.timestamp)}</td>
                  <td className="px-4 py-2">
                    <span className="font-medium text-gray-900 dark:text-white">
                      {formatAmount(exchange.fromAmount, exchange.fromCurrency)}
                    </span>
                    <span className="ml-1 text-gray-500 dark:text-gray-400">{exchange.fromCurrency}</span>
                  </td>
                  <td className="px-4 py-2">
                    <span className="font-medium text-gray-900 dark:text-white">
                      {formatAmount(exchange.toAmount, exchange.toCurrency)}
                    </span>
                    <span className="ml-1 text-gray-500 dark:text-gray-400">{exchange.toCurrency}</span>
                  </td>
                  <td className="px-4 py-2">
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-100">
                      Успешно
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      
      <div className="text-xs text-center text-gray-500 dark:text-gray-400 mt-4">
        Все обмены выполняются в автоматическом режиме
      </div>
    </div>
  );
} 